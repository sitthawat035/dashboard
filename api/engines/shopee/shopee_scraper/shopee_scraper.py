"""
Shopee Product Scraper (Playwright + Login)
============================================
ดึงข้อมูลสินค้าจาก Shopee โดยใช้ Playwright
ต้อง login ก่อนเพื่อเข้าถึงข้อมูล

วิธีใช้งาน:
  python shopee_scraper.py --keyword "เสื้อยืด" --limit 50

  ครั้งแรกจะเปิด Browser ให้ login ด้วยตนเอง
  หลัง login สำเร็จจะ scrape อัตโนมัติ

ติดตั้ง:
  pip install playwright
  python -m playwright install chromium
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
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Error: pip install playwright && python -m playwright install chromium")
    sys.exit(1)


BASE_URL = "https://shopee.co.th"
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shopee_cookies.json")


class ShopeeScraper:
    """Shopee scraper ด้วย Playwright + manual login"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.pw = None
        self.browser = None
        self.context = None
        self.page = None

    # ---- Browser lifecycle ----

    def start(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(
            headless=self.headless,
            slow_mo=300,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="th-TH",
            timezone_id="Asia/Bangkok",
        )
        self.context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

        # โหลด cookies เก่า (ถ้ามี)
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, "r") as f:
                cookies = json.load(f)
            self.context.add_cookies(cookies)
            print(f"โหลด cookies จากไฟล์ ({len(cookies)} cookies)")

        self.page = self.context.new_page()

    def stop(self):
        # บันทึก cookies ก่อนปิด
        cookies = self.context.cookies()
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"บันทึก cookies ({len(cookies)} cookies)")

        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    # ---- Login ----

    def ensure_login(self) -> bool:
        """ตรวจสอบว่า login แล้วหรือยัง ถ้ายังจะเปิดให้ login ด้วยตนเอง"""
        print("\nตรวจสอบสถานะ login ...")
        self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # ถ้าเห็นปุ่ม login แสดงว่ายังไม่ login
        login_btn = self.page.query_selector('button:has-text("เข้าสู่ระบบ"), a:has-text("เข้าสู่ระบบ")')

        if not login_btn:
            # ลองเช็คอีกแบบ
            page_text = self.page.inner_text("body")
            if "เข้าสู่ระบบ" in page_text and "ออกจากระบบ" not in page_text:
                login_btn = True

        if not login_btn:
            print("✅  login แล้ว!")
            return True

        # ยังไม่ login - เปิดให้ user login ด้วยตนเอง
        print("\n" + "="*60)
        print("  ⚠️  ยังไม่ได้ login!")
        print("  Browser จะเปิดหน้า Shopee ให้ login ด้วยตนเอง")
        print("  หลัง login สำเร็จ กด Enter ใน terminal นี้")
        print("="*60)

        self.headless = False  # ต้องแสดง browser

        # ไปที่หน้า login
        login_url = f"{BASE_URL}/buyer/login"
        self.page.goto(login_url, wait_until="domcontentloaded", timeout=30000)

        # รอให้ user login (5 นาที)
        print("\n  >>> มีเวลา 5 นาที ในการ Login <<< ")
        print("  >>> สคริปต์จะทำงานต่ออัตโนมัติ <<< ")
        time.sleep(300)

        # ตรวจสอบว่า login สำเร็จหรือไม่
        self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        page_text = self.page.inner_text("body")
        if "ออกจากระบบ" in page_text or "บัญชีของฉัน" in page_text or "ตะกร้าสินค้า" in page_text:
            print("✅  Login สำเร็จ!")
            return True
        else:
            print("❌  Login ไม่สำเร็จ ลองใหม่อีกครั้ง")
            return False

    # ---- Search ----

    def search(self, keyword: str, limit: int = 30, sort: str = "relevant") -> list[dict]:
        """ค้นหาสินค้า"""
        products = []
        page_num = 0

        print(f"\n🔍 ค้นหา: '{keyword}' (เป้าหมาย {limit} ชิ้น)")

        sort_param = ""
        if sort == "sales":
            sort_param = "&sortBy=sales"
        elif sort == "ctime":
            sort_param = "&sortBy=ctime"
        elif sort == "price_asc":
            sort_param = "&sortBy=price&order=asc"
        elif sort == "price_desc":
            sort_param = "&sortBy=price&order=desc"

        while len(products) < limit:
            url = f"{BASE_URL}/search?keyword={keyword}&page={page_num}{sort_param}"

            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            # Scroll ลงเพื่อให้สินค้าโหลด
            for _ in range(3):
                self.page.mouse.wheel(0, 800)
                time.sleep(0.5)

            time.sleep(2)

            # ดึงข้อมูลสินค้า
            new_products = self._extract_products()

            if not new_products:
                print(f"  ไม่พบสินค้าเพิ่ม (หน้า {page_num})")
                break

            for p in new_products:
                if len(products) >= limit:
                    break
                products.append(p)

            print(f"  ดึงแล้ว {len(products)}/{limit} ชิ้น")
            page_num += 1
            time.sleep(1.5)

        print(f"✅ ดึงข้อมูลสำเร็จ: {len(products)} ชิ้น")
        return products

    def _extract_products(self) -> list[dict]:
        """ดึงข้อมูลสินค้าจากหน้าปัจจุบัน"""
        products = []

        # ลอง selector หลายๆ แบบ
        selectors = [
            "a[data-sqe='link']",
            "[data-sqe='item']",
            ".shopee-search-item-result__item",
            "li.col-xs-2-4",
            "[data-item-id]",
            ".shopee-item-card--clickable",
        ]

        items = []
        used_sel = ""
        for sel in selectors:
            items = self.page.query_selector_all(sel)
            if items:
                used_sel = sel
                break

        if not items:
            # Debug: ลองหา links ที่มี /product/
            items = self.page.query_selector_all("a[href*='/product/']")
            if items:
                used_sel = "a[href*='/product/']"

        if not items:
            return products

        for item in items:
            try:
                p = self._parse_item(item, used_sel)
                if p and p.get("name"):
                    products.append(p)
            except Exception:
                continue

        return products

    def _parse_item(self, item, selector: str) -> dict:
        """แปลง element เป็นข้อมูลสินค้า"""
        p = {
            "name": "",
            "price": "",
            "price_original": "",
            "discount": "",
            "sold": "",
            "rating": "",
            "shop": "",
            "location": "",
            "url": "",
            "image": "",
        }

        # ชื่อสินค้า - ลองหลาย selector
        for sel in ["a.text-color-primary", "[class*='product-name']", "._44qnta", "a"]:
            el = item.query_selector(sel)
            if el:
                text = el.inner_text().strip()
                if len(text) > 5 and "฿" not in text:
                    p["name"] = text[:200]
                    break

        # ถ้าเป็น link element ให้ดึง text ตรงๆ
        if not p["name"]:
            text = item.inner_text().strip()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if lines:
                p["name"] = lines[0][:200]

        # ราคา
        text = item.inner_text()
        prices = re.findall(r'฿([\d,]+(?:\.\d+)?)', text)
        if prices:
            p["price"] = prices[0].replace(",", "")
        elif re.search(r'[\d,]+(?:\.\d+)?', text):
            # หาตัวเลขที่ดูเหมือนราคา
            nums = re.findall(r'(\d[\d,]*)', text)
            for n in nums:
                val = int(n.replace(",", ""))
                if 10 <= val <= 999999:
                    p["price"] = n.replace(",", "")
                    break

        # ส่วนลด
        disc_match = re.search(r'(\d+%\s*off|ลด\s*\d+%|-\d+%)', text, re.IGNORECASE)
        if disc_match:
            p["discount"] = disc_match.group(0)

        # จำนวนขาย
        sold_match = re.search(r'(?:ขายแล้ว|sold)\s*([\d.]+\s*(?:พัน|หมื่น|แสน|ล้าน|k|K)*)', text)
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
    parser = argparse.ArgumentParser(
        description="Shopee Scraper - ดึงข้อมูลสินค้าจาก Shopee",
        epilog="""
ตัวอย่าง:
  python shopee_scraper.py --keyword "เสื้อยืด" --limit 50
  python shopee_scraper.py --keyword "iPhone" --sort sales --output phones.csv
  python shopee_scraper.py --keyword "รองเท้า" --sort price_asc --limit 30
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--keyword", "-k", required=True, help="คำค้นหา")
    parser.add_argument("--limit", "-l", type=int, default=30, help="จำนวนสูงสุด (default: 30)")
    parser.add_argument("--sort", default="relevant",
                        choices=["relevant", "sales", "ctime", "price_asc", "price_desc"])
    parser.add_argument("--output", "-o", help="ชื่อไฟล์ output")
    parser.add_argument("--format", default="csv", choices=["csv", "json"])
    parser.add_argument("--no-summary", action="store_true")

    args = parser.parse_args()

    scraper = ShopeeScraper(headless=False)
    products = []

    try:
        scraper.start()

        # Login ก่อน
        if not scraper.ensure_login():
            print("ไม่สามารถ login ได้ - ยกเลิก")
            sys.exit(1)

        # ค้นหา
        products = scraper.search(
            keyword=args.keyword,
            limit=args.limit,
            sort=args.sort,
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

    except KeyboardInterrupt:
        print("\nยกเลิก")
        if products:
            save_csv(products, "shopee_partial.csv")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
