"""Debug script - ดู HTML structure ของ Shopee search page"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright
import time

keyword = "เสื้อยืด"
url = f"https://shopee.co.th/search?keyword={keyword}"

print(f"กำลังเปิด: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        locale="th-TH",
        timezone_id="Asia/Bangkok",
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)
    page = context.new_page()

    print(f"ไปที่: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    # บันทึก screenshot
    page.screenshot(path="shopee_debug.png", full_page=False)
    print("บันทึก screenshot: shopee_debug.png")

    # ดึง HTML บางส่วน
    html = page.content()
    print(f"\nHTML length: {len(html)} chars")

    # หา product elements
    selectors_to_try = [
        '[data-sqe="item"]',
        ".shopee-search-item-result__item",
        "li.col-xs-2-4",
        "[data-item-id]",
        ".shopee-search-result-item",
        "a[data-sqe='link']",
        ".col-xs-2-4",
        ".shopee-item-card",
        "[class*='shop']",
        "[class*='item']",
    ]

    print("\n=== Testing selectors ===")
    for sel in selectors_to_try:
        count = page.locator(sel).count()
        print(f"  {sel}: {count} elements")

    # หา links ที่มี product
    links = page.query_selector_all("a[href*='/product/']")
    print(f"\n  Links with /product/: {len(links)}")
    if links:
        for link in links[:3]:
            href = link.get_attribute("href") or ""
            print(f"    {href[:80]}")

    # แสดง body บางส่วน
    body = page.query_selector("body")
    if body:
        text = body.inner_text()
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 5]
        print(f"\n=== Page text (first 30 lines) ===")
        for line in lines[:30]:
            print(f"  {line[:80]}")

    browser.close()

print("\nDebug เสร็จแล้ว!")
