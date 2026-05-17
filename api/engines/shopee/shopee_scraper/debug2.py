"""Debug: ดูว่า Shopee render อะไรบ้าง"""
import sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "debug2.txt")

pw = sync_playwright().start()
browser = pw.chromium.launch(
    headless=True,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
)
ctx = browser.new_context(
    viewport={"width": 1366, "height": 900},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    locale="th-TH",
    timezone_id="Asia/Bangkok",
)
ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")

page = ctx.new_page()

with open(OUT, "w", encoding="utf-8") as f:
    def log(msg):
        f.write(msg + "\n")
        f.flush()

    try:
        page.goto("https://shopee.co.th/search?keyword=ของตกแต่งบ้าน", wait_until="networkidle", timeout=45000)
    except:
        page.goto("https://shopee.co.th/search?keyword=ของตกแต่งบ้าน", wait_until="domcontentloaded", timeout=30000)

    time.sleep(8)

    # Scroll
    for _ in range(5):
        page.mouse.wheel(0, 600)
        time.sleep(0.5)
    time.sleep(3)

    log(f"URL: {page.url}")
    log(f"Title: {page.title()}")

    # ใช้ JS ดึงข้อมูล
    result = page.evaluate("""() => {
        const info = {};

        // นับ links ทั้งหมด
        const allLinks = document.querySelectorAll('a');
        info.totalLinks = allLinks.length;

        // หา product links (-i.{shop}.{item} pattern)
        const prodLinks = [];
        for (const a of allLinks) {
            if (a.href && a.href.match(/-i\\.\\d+\\.\\d+/)) {
                prodLinks.push({
                    href: a.href,
                    text: a.innerText.substring(0, 100),
                    className: a.className.substring(0, 80)
                });
            }
        }
        info.productLinks = prodLinks.slice(0, 10);
        info.productLinksCount = prodLinks.length;

        // หา elements ที่มี data-sqe
        const sqeEls = document.querySelectorAll('[data-sqe]');
        info.dataSqeCount = sqeEls.length;
        const sqeValues = [];
        for (const el of sqeEls) {
            sqeValues.push(el.getAttribute('data-sqe'));
        }
        info.dataSqeValues = [...new Set(sqeValues)];

        // หา elements ที่มี data-item-id
        const itemEls = document.querySelectorAll('[data-item-id]');
        info.dataItemIdCount = itemEls.length;

        // body text sample
        info.bodyTextSample = document.body.innerText.substring(0, 2000);

        // Check for anti-bot/captcha
        info.hasCaptcha = !!document.querySelector('[class*="captcha"], [id*="captcha"]');
        info.hasAntiCrawler = document.body.innerText.includes('anticrawler') || document.body.innerText.includes('verify');

        // Count by tag
        const divs = document.querySelectorAll('div');
        info.divCount = divs.length;

        // Find any images
        const imgs = document.querySelectorAll('img');
        info.imgCount = imgs.length;

        return info;
    }""")

    log(f"\n=== Results ===")
    log(f"Total links: {result.get('totalLinks')}")
    log(f"Product links (-i.): {result.get('productLinksCount')}")
    log(f"data-sqe elements: {result.get('dataSqeCount')}")
    log(f"data-sqe values: {result.get('dataSqeValues')}")
    log(f"data-item-id elements: {result.get('dataItemIdCount')}")
    log(f"DIV count: {result.get('divCount')}")
    log(f"IMG count: {result.get('imgCount')}")
    log(f"Has captcha: {result.get('hasCaptcha')}")
    log(f"Has anti-crawler: {result.get('hasAntiCrawler')}")

    log(f"\n=== Product Links (first 10) ===")
    for pl in result.get('productLinks', []):
        log(f"  {pl['href']}")
        log(f"    text: {pl['text'][:60]}")
        log(f"    class: {pl['className'][:60]}")

    log(f"\n=== Body Text Sample ===")
    log(result.get('bodyTextSample', ''))

browser.close()
pw.stop()
log("\n=== DONE ===")
