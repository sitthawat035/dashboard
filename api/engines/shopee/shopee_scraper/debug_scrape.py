"""Debug: ตรวจจับ element ในหน้า Shopee search"""
import sys, io, time, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_output.txt")

pw = sync_playwright().start()
browser = pw.chromium.launch(
    headless=True,
    args=["--disable-blink-features=AutomationControlled"],
)
ctx = browser.new_context(
    viewport={"width": 1366, "height": 768},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    locale="th-TH",
    timezone_id="Asia/Bangkok",
)
ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")

# Load cookies
ck_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shopee_cookies.json")
if os.path.exists(ck_path):
    with open(ck_path, "r") as f:
        ctx.add_cookies(json.load(f))

page = ctx.new_page()

with open(OUT, "w", encoding="utf-8") as log:
    def write(msg):
        log.write(msg + "\n")
        log.flush()

    try:
        write("=== Navigating to search page ===")
        page.goto(
            "https://shopee.co.th/search?keyword=ของตกแต่งบ้าน",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        time.sleep(5)

        write(f"URL: {page.url}")
        write(f"Title: {page.title()}")

        # Scroll
        for _ in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(0.5)
        time.sleep(2)

        # Save full HTML for analysis
        html = page.content()
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_page.html")
        with open(html_path, "w", encoding="utf-8") as hf:
            hf.write(html)
        write(f"Saved HTML ({len(html)} chars) to debug_page.html")

        # Try selectors
        selectors = [
            'a[data-sqe="link"]',
            '[data-sqe="item"]',
            'a[data-sqe]',
            'a[href*="/product/"]',
            '.shopee-search-item-result__item',
            'li.col-xs-2-4',
            '[data-item-id]',
            '.shopee-item-card--clickable',
            '[class*="item-card"]',
            '[class*="product-card"]',
            '[class*="search-item"]',
            'div[data-sqe]',
        ]
        for sel in selectors:
            try:
                count = len(page.query_selector_all(sel))
                if count > 0:
                    write(f"FOUND: {sel} -> {count}")
            except:
                pass

        # Sample classes
        classes = re.findall(r'class="([^"]{5,100})"', html[:50000])
        write(f"\nSample classes ({len(classes)} total):")
        for c in classes[:50]:
            write(f"  {c}")

    except Exception as e:
        write(f"ERROR: {e}")
        import traceback
        write(traceback.format_exc())

browser.close()
pw.stop()
write("\n=== DONE ===")
