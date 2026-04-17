import asyncio
import sys
import csv
import json
import re
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
# Add engines root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent # Dashboard root
engines_dir = Path(__file__).resolve().parent.parent.parent # Engines root
sys.path.insert(0, str(engines_dir))

from common.browser import create_browser_manager
from common.utils import setup_logger, print_header, print_success, print_error, print_info, ensure_dir
from common.stealth_config import get_random_delay, BrowserFingerprint

logger = setup_logger("ShopeeScraper")

async def scrape_shopee_search(keyword: str, max_items: int = 10):
    """
    Search Shopee and scrape results using the connected Chrome instance.
    """
    print_header = f"🔍 Searching Shopee for: {keyword}"
    print_info(print_header)

    async with await create_browser_manager(logger=logger) as browser:
        if not browser.page:
            print_error("Cannot connect to Chrome. Make sure it is open with --remote-debugging-port=9222")
            return []

        # 1. Navigate to Search Page
        search_url = f"https://shopee.co.th/search?keyword={keyword}"
        
        # Ensure we are on the page and it's active
        try:
            await browser.page.bring_to_front()
        except:
            pass

        print_info(f"Navigating to: {search_url}")
        # Switch to domcontentloaded to allow earlier intervention
        await browser.goto(search_url, wait_until="domcontentloaded")
        
        # Add random human-like delay and mouse movements to avoid early detection
        await asyncio.sleep(get_random_delay(1000, 3000))
        await browser.human_like_mouse_move()
        
        # --- Check for Captcha/Verify Page ---
        retries = 0
        max_retries = 3
        while retries < max_retries:
            current_url = browser.page.url
            if "verify" in current_url.lower() or "captcha" in current_url.lower():
                print_error(f"🚨 ต๊ะเอ๋! ติดด่าน Captcha จ้าพี่เคน! (ครั้งที่ {retries + 1}/{max_retries})")
                
                # Create flag file in workspace data dir
                workspace_root = root_dir.parent
                flag_path = workspace_root / "data" / "status" / "CAPTCHA_REQUIRED.json"
                ensure_dir(flag_path.parent)
                with open(flag_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "project": "shopee_affiliate",
                        "step": "scrape",
                        "url": current_url,
                        "timestamp": datetime.now().isoformat()
                    }, f)
                
                print_info("🚨 สภาพ! พี่ช่วยไปกดแก้ใน Chrome ให้เจ้หน่อยน้าาา เดี๋ยวเจ้รอตรงนี้ 60 วิฯ จ้า!")
                
                # Wait for user to solve it
                solved = False
                for _ in range(30):
                    await asyncio.sleep(2)
                    if "verify" not in browser.page.url.lower() and "captcha" not in browser.page.url.lower():
                        print_success("✅ ขอบคุณจ้าพี่! ผ่านด่านแล้ว ลุยต่อเลยน้าาา")
                        solved = True
                        await asyncio.sleep(2)
                        break
                
                if not solved:
                    print_error("❌ รอจนเหงือกแห้งแล้วจ้า! ขอรีเฟรชหน้าดูอีกทีก่อนนะ...")
                    await browser.page.reload(wait_until="domcontentloaded")
                    await asyncio.sleep(3)
                    retries += 1
                else:
                    # Clear flag file if solved
                    flag_path = project_root / "CAPTCHA_REQUIRED.json"
                    if flag_path.exists():
                        flag_path.unlink()
                    break
            else:
                break
            
        if retries >= max_retries:
            print_error("❌ พยายามแล้วนะพี่ แต่มันไม่ยอมจริงๆ ขอผ่านรอบนี้ไปก่อนจ้า!")
            return []
            
        # --- WAIT FOR PRODUCTS TO APPEAR ---
        print_info("Waiting for products to load...")
        product_found = False
        target_selectors = ["div[data-sqe='item']", ".shopee-search-item-result__item", "div.col-xs-2-4"]
        
        for sel in target_selectors:
            try:
                # Wait for at least one item to be visible
                await browser.page.wait_for_selector(sel, timeout=10000)
                product_found = True
                print_info(f"   ✨ ตาวาว! เจอสินค้าด้วยระบบ: {sel}")
                break
            except:
                continue
        
        if not product_found:
            print_error("❌ ไม่เจอสินค้าชิ้นไหนเลยจ้าพี่!")
            # Save debug screenshot in workspace data dir
            workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            debug_path = workspace_root / "data" / "logs" / "shopee" / "latest_scrape_error.png"
            ensure_dir(debug_path.parent)
            await browser.page.screenshot(path=str(debug_path))
            print_info(f"   📸 ถ่ายรูปหลักฐานไว้ที่: {debug_path}")
            # Keep open briefly for user to see
            await asyncio.sleep(5)
            return []

        # Scroll down slowly to trigger all lazy loading
        print_info("Scrolling to discover more items...")
        for i in range(4):
            # Mix standard scroll and human-like scroll and mouse movement
            await browser.human_like_scroll()
            await browser.scroll_down(random.randint(400, 800), get_random_delay(800, 1500))
            if random.random() > 0.5:
                await browser.human_like_mouse_move()
            await asyncio.sleep(get_random_delay(1000, 3000))

        # 2. Extract Items
        print_info("Extracting product data...")
        
        # Multiple selector strategies
        items = []
        for selector in target_selectors:
            items = await browser.page.query_selector_all(selector)
            if len(items) > 0:
                break
        
        results = []
        # Increase max items to scrape to give AI more choice
        for i, item in enumerate(items[:20]):
            try:
                # Name
                name = "Unknown"
                name_selectors = ["div[data-sqe='name'] > div", ".shopee-item-card__name", "div._10Wbs-", ".line-clamp-2"]
                for sel in name_selectors:
                    name_el = await item.query_selector(sel)
                    if name_el:
                        name = await name_el.text_content()
                        if name: name = name.strip()
                        break
                
                # Price - Shopee now uses utility-first CSS (like Tailwind), old class selectors don't work.
                # Use JavaScript evaluate to find ฿ span and extract the adjacent price number.
                price_text = "0"
                try:
                    price_text = await browser.page.evaluate("""
                        (el) => {
                            // Strategy 1: Find ฿ span, get combined text of it + next sibling
                            const spans = Array.from(el.querySelectorAll('span'));
                            for (let i = 0; i < spans.length; i++) {
                                const txt = (spans[i].innerText || '').trim();
                                if (txt === '฿' || txt.startsWith('฿')) {
                                    // Combine ฿ span and the next span (price number)
                                    const nextTxt = spans[i+1] ? (spans[i+1].innerText || '').trim() : '';
                                    if (nextTxt && /\\d/.test(nextTxt)) {
                                        return txt + nextTxt;
                                    }
                                    if (/\\d/.test(txt)) return txt;
                                }
                            }
                            // Strategy 2: Find container div with flex/items-baseline (Shopee price row)
                            const priceRow = el.querySelector('div.flex.items-baseline, div.truncate.flex');
                            if (priceRow) {
                                const rowText = (priceRow.innerText || '').trim();
                                if (rowText && /\\d/.test(rowText)) return rowText;
                            }
                            // Strategy 3: Find any leaf element containing ฿ + digit
                            const allEls = el.querySelectorAll('*');
                            for (const node of allEls) {
                                if (node.children.length === 0) {
                                    const t = (node.innerText || '').trim();
                                    if (t && /฿\\s*\\d/.test(t)) return t;
                                }
                            }
                            return '0';
                        }
                    """, item)
                except Exception:
                    price_text = "0"
                
                # Clean price: remove ฿, commas, spaces; handle ranges like "199 - 250" (take first)
                price_cleaned = re.sub(r'[^\d]', '', price_text.split('-')[0])
                if not price_cleaned:
                    price_cleaned = "0"
                
                # Link
                link = ""
                # Check if the item itself is an anchor or has one
                is_link = await browser.page.evaluate("(el) => el.tagName === 'A'", item)
                if is_link:
                    link = await item.get_attribute("href")
                else:
                    link_el = await item.query_selector("a")
                    link = await link_el.get_attribute("href") if link_el else ""
                
                if link and not link.startswith("http"):
                    link = "https://shopee.co.th" + link
                
                # Image
                image = ""
                img_el = await item.query_selector("img")
                if img_el:
                    image = await img_el.get_attribute("src")
                    if not image or "gif" in image or "data:image" in image:
                        image = await img_el.get_attribute("data-src")
                
                if name and name != "Unknown" and link:
                    results.append({
                        'name': name,
                        'price': price_cleaned,
                        'url': link,
                        'image_url': image or ""
                    })
                    print_info(f"   ✅ [{len(results)}] {name[:30]}... (฿{price_cleaned})")

                
                if len(results) >= max_items:
                    break
                    
            except Exception as e:
                print_error(f"   ❌ ข้ามตัวที่ {i+1} เพราะ: {str(e)}")
                continue

        # 3. Save to CSV
        if results:
            workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            scraped_dir = workspace_root / "data" / "content" / "shopee" / "scraped"
            ensure_dir(scraped_dir)
            keys = results[0].keys()
            
            # Save as keyword-named CSV (safe filename)
            safe_keyword = re.sub(r'[^\w\u0E00-\u0E7F]', '_', keyword).strip('_') or "scraped"
            keyword_csv = scraped_dir / f"{safe_keyword}.csv"
            with open(keyword_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(results)
            print_success(f"Saved {len(results)} items to {keyword_csv.name}")
            
            # Also save as items.csv (for pipeline compatibility), skip if file is locked
            main_csv = scraped_dir / "items.csv"
            try:
                with open(main_csv, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(results)
                print_success(f"Also saved to items.csv")
            except PermissionError:
                print_info(f"ℹ️ items.csv ถูกเปิดอยู่ — ข้ามไป ใช้ {keyword_csv.name} แทนได้เลย")
            
            return results
        else:
            print_error("Failed to extract any usable data.")
            return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="Product to search for")
    parser.add_argument("--count", type=int, default=10, help="Max items to scrape")
    args = parser.parse_args()
    
    asyncio.run(scrape_shopee_search(args.keyword, args.count))
