"""
Shopee Scraper v3 - Chrome CDP Mode
=====================================
เชื่อมกับ Chrome จริงที่ login แล้ว (ไม่ใช่ headless)
ทำงานเหมือน Chrome Extension Data Scraper

วิธีใช้:
  1. ปิด Chrome ทั้งหมด
  2. รัน start_chrome.bat
  3. ไป Shopee login (ถ้าต้อง)
  4. รัน: python shopee_cdp.py --keyword "ของตกแต่งบ้าน" --limit 30
"""

import argparse
import csv
import json
import os
import re
import sys
import io
import time
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: pip install playwright")
    sys.exit(1)

BASE_URL = "https://shopee.co.th"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def search_products(keyword: str, limit: int = 30, sort: str = "relevant") -> list[dict]:
    products = []

    sort_map = {
        "relevant": "",
        "sales": "&sortBy=sales",
        "ctime": "&sortBy=ctime",
        "price_asc": "&sortBy=price&order=asc",
        "price_desc": "&sortBy=price&order=desc",
    }
    sort_param = sort_map.get(sort, "")

    pw = sync_playwright().start()

    # เชื่อมกับ Chrome จริงผ่าน CDP
    print("เชื่อมต่อกับ Chrome...")
    try:
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อ Chrome ได้: {e}")
        print("\nทำตามขั้นตอน:")
        print("  1. ปิด Chrome ทั้งหมด")
        print("  2. รัน start_chrome.bat")
        print("  3. ไป Shopee login")
        print("  4. รันสคริปต์นี้อีกครั้ง")
        pw.stop()
        return []

    print("✅ เชื่อมต่อสำเร็จ!")

    # ใช้ context แรกของ Chrome (มี session/login อยู่แล้ว)
    contexts = browser.contexts
    if not contexts:
        print("❌ ไม่พบ browser context")
        browser.close()
        pw.stop()
        return []

    context = contexts[0]
    page = context.new_page()

    print(f"\n🔍 ค้นหา: '{keyword}' (เป้าหมาย {limit} ชิ้น)")

    page_num = 0
    while len(products) < limit:
        url = f"{BASE_URL}/search?keyword={keyword}&page={page_num}{sort_param}"
        print(f"  โหลดหน้า {page_num} ...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            break

        # รอ React render
        time.sleep(5)

        # Scroll เพื่อ trigger lazy load
        for _ in range(5):
            page.mouse.wheel(0, 600)
            time.sleep(0.8)
        time.sleep(3)

        # ดึงข้อมูลสินค้า
        new_products = extract_products(page)

        if not new_products:
            print(f"  ไม่พบสินค้าเพิ่ม (หน้า {page_num})")
            break

        for p in new_products:
            if len(products) >= limit:
                break
            products.append(p)

        print(f"  ดึงแล้ว {len(products)}/{limit} ชิ้น")
        page_num += 1
        time.sleep(2)

    # ปิด tab ที่เปิด (ไม่ปิด Chrome จริง)
    page.close()

    print(f"\n✅ ดึงข้อมูลสำเร็จ: {len(products)} ชิ้น")
    return products


def extract_products(page) -> list[dict]:
    """ดึงข้อมูลสินค้าจากหน้าปัจจุบัน"""
    products = []

    selectors = [
        "a[data-sqe='link']",
        "[data-sqe='item']",
        "a[data-sqe]",
        "a[href*='-i.']",
        "a[href*='/product/']",
        ".shopee-search-item-result__item",
        "li.col-xs-2-4",
        "[data-item-id]",
        ".shopee-item-card--clickable",
        "[class*='item-card']",
        "[class*='product-card']",
    ]

    items = []
    used_sel = ""
    for sel in selectors:
        try:
            items = page.query_selector_all(sel)
            if items and len(items) >= 3:
                used_sel = sel
                break
        except Exception:
            continue

    if not items:
        # ลอง JS extraction
        try:
            result = page.evaluate("""() => {
                const links = document.querySelectorAll('a');
                const prodLinks = [];
                for (const a of links) {
                    if (a.href && a.href.match(/-i\\.\\d+\\.\\d+/)) {
                        prodLinks.push(a);
                    }
                }
                return prodLinks.length;
            }""")
            if result > 0:
                print(f"    [DEBUG] พบ {result} product links (JS)")
        except Exception:
            pass

    if not items:
        return products

    print(f"    ใช้ selector: {used_sel} ({len(items)} items)")

    for item in items[:60]:
        try:
            p = parse_item(item, used_sel)
            if p and p.get("name"):
                products.append(p)
        except Exception:
            continue

    return products


def parse_item(item, selector: str) -> dict:
    """แปลง element เป็นข้อมูลสินค้า"""
    p = {
        "name": "", "price": "", "price_original": "", "discount": "",
        "sold": "", "rating": "", "shop": "", "location": "",
        "url": "", "image": "",
    }

    try:
        full_text = item.inner_text().strip()
    except Exception:
        full_text = ""

    # ชื่อสินค้า
    for sel in ["a.text-color-primary", "[class*='product-name']", "._44qnta", "a"]:
        el = item.query_selector(sel)
        if el:
            try:
                text = el.inner_text().strip()
                if len(text) > 5 and "฿" not in text:
                    p["name"] = text[:200]
                    break
            except Exception:
                continue

    if not p["name"] and full_text:
        lines = [l.strip() for l in full_text.split("\n") if l.strip()]
        for line in lines:
            if len(line) > 5 and "฿" not in line and "%" not in line:
                p["name"] = line[:200]
                break

    # ราคา
    prices = re.findall(r'฿([\d,]+(?:\.\d+)?)', full_text)
    if prices:
        p["price"] = prices[0].replace(",", "")

    # ส่วนลด
    disc_match = re.search(r'(\d+%\s*off|ลด\s*\d+%|-\d+%)', full_text, re.IGNORECASE)
    if disc_match:
        p["discount"] = disc_match.group(0)

    # จำนวนขาย
    sold_match = re.search(r'(?:ขายแล้ว|sold)\s*([\d.]+\s*(?:พัน|หมื่น|แสน|ล้าน|k|K)*)', full_text, re.IGNORECASE)
    if sold_match:
        p["sold"] = sold_match.group(1).strip()

    # ลิงก์
    if selector.startswith("a"):
        href = item.get_attribute("href") or ""
    else:
        link = item.query_selector("a[href]")
        href = link.get_attribute("href") if link else ""

    if href:
        if not href.startswith("http"):
            href = BASE_URL + href
        p["url"] = href

    # รูปภาพ
    img = item.query_selector("img")
    if img:
        p["image"] = img.get_attribute("src") or ""

    return p


def save_csv(products: list[dict], filename: str):
    if not products:
        return
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=products[0].keys())
        w.writeheader()
        w.writerows(products)
    print(f"💾 บันทึก: {filename} ({len(products)} ชิ้น)")


def save_json(products: list[dict], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"💾 บันทึก: {filename} ({len(products)} ชิ้น)")


def print_summary(products: list[dict]):
    if not products:
        print("ไม่พบสินค้า")
        return
    print(f"\n{'='*60}")
    print(f"  📊 สรุป ({len(products)} ชิ้น)")
    print(f"{'='*60}")
    for i, p in enumerate(products[:15], 1):
        name = (p["name"][:40] + "..") if len(p["name"]) > 40 else p["name"]
        price = f"฿{p['price']}" if p.get("price") else "N/A"
        print(f"  {i:2}. {name:<44} {price:>10}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Shopee Scraper v3 - Chrome CDP")
    parser.add_argument("--keyword", "-k", required=True, help="คำค้นหา")
    parser.add_argument("--limit", "-l", type=int, default=30, help="จำนวนสูงสุด (default: 30)")
    parser.add_argument("--sort", default="relevant",
                        choices=["relevant", "sales", "ctime", "price_asc", "price_desc"])
    parser.add_argument("--output", "-o", help="ชื่อไฟล์ output")
    parser.add_argument("--format", default="csv", choices=["csv", "json"])
    parser.add_argument("--no-summary", action="store_true")
    args = parser.parse_args()

    products = search_products(
        keyword=args.keyword, limit=args.limit, sort=args.sort,
    )

    if products and not args.no_summary:
        print_summary(products)

    if products:
        if args.output:
            filename = args.output
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = re.sub(r'[^\w]', '_', args.keyword)
            filename = f"shopee_{safe}_{ts}.{args.format}"
        if filename.endswith(".json"):
            save_json(products, filename)
        else:
            save_csv(products, filename)


if __name__ == "__main__":
    main()
