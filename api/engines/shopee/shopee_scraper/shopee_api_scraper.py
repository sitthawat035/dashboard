"""
Shopee Product Scraper (API-based)
===================================
ดึงข้อมูลสินค้าจาก Shopee โดยใช้ API endpoint โดยตรง
ไม่ต้อง login ไม่ต้องเปิด browser

วิธีใช้:
  python shopee_api_scraper.py --keyword "ของตกแต่งบ้าน" --limit 50

ติดตั้ง:
  pip install requests
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
    import requests
except ImportError:
    print("Error: pip install requests")
    sys.exit(1)

BASE_URL = "https://shopee.co.th"
API_SEARCH = "https://shopee.co.th/api/v4/search/search_items"
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shopee_cookies.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://shopee.co.th/",
    "X-Requested-With": "XMLHttpRequest",
    "X-API-SOURCE": "pc",
    "X-Shopee-Language": "th",
    "af-ac-enc-dat": "",
    "sz-token": "",
}


def get_cookies() -> dict:
    """โหลด cookies จากไฟล์ (ถ้ามี)"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            cookies_list = json.load(f)
        return {c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c}
    return {}


def search_products(keyword: str, limit: int = 30, sort: str = "relevant") -> list[dict]:
    """ค้นหาสินค้าผ่าน Shopee API"""
    products = []
    page = 0
    per_page = 60  # Shopee API ส่งได้สูงสุด ~60 items ต่อครั้ง

    sort_map = {
        "relevant": 0,
        "sales": 6,
        "ctime": 1,
        "price_asc": 2,
        "price_desc": 3,
    }
    sort_by = sort_map.get(sort, 0)

    cookies = get_cookies()

    # สร้าง session เพื่อจัดการ cookies
    session = requests.Session()
    session.headers.update(HEADERS)
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".shopee.co.th")

    # ลองเข้าหน้า search ก่อนเพื่อได้ cookies
    print(f"\n🔍 ค้นหา: '{keyword}' (เป้าหมาย {limit} ชิ้น)")
    try:
        session.get(f"{BASE_URL}/search?keyword={keyword}", timeout=15)
        time.sleep(1)
    except Exception as e:
        print(f"Warning: ไม่สามารถเข้าหน้า search ได้: {e}")

    while len(products) < limit:
        offset = page * per_page
        params = {
            "by": "relevancy",
            "keyword": keyword,
            "limit": per_page,
            "newest": offset,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2,
        }
        if sort_by > 0:
            params["order"] = "desc" if sort == "price_desc" else "asc"

        try:
            resp = session.get(API_SEARCH, params=params, timeout=15)

            if resp.status_code == 403:
                print(f"  ⚠️  ถูก block (403) - ลองเพิ่ม cookies หรือเปลี่ยน keyword")
                break

            if resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code}")
                break

            data = resp.json()
            items = data.get("items", [])

            if not items:
                print(f"  ไม่พบสินค้าเพิ่ม (หน้า {page})")
                break

            for item in items:
                if len(products) >= limit:
                    break
                info = item.get("item_basic", item)
                p = parse_item(info)
                if p and p.get("name"):
                    products.append(p)

            print(f"  ดึงแล้ว {len(products)}/{limit} ชิ้น")
            page += 1
            time.sleep(1.5)

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error: {e}")
            break
        except json.JSONDecodeError:
            print(f"  ❌ Response ไม่ใช่ JSON (อาจถูก block)")
            break

    print(f"✅ ดึงข้อมูลสำเร็จ: {len(products)} ชิ้น")
    return products


def parse_item(info: dict) -> dict:
    """แปลงข้อมูลจาก API เป็น dict"""
    try:
        # ราคา
        price = info.get("price", 0) or info.get("price_min", 0)
        price_original = info.get("price_before_discount", 0) or info.get("price_max", 0)

        # แปลงราคา (Shopee ส่งราคาเป็นสตางค์)
        if price > 100000:
            price = price / 100000
        if price_original > 100000:
            price_original = price_original / 100000

        # ส่วนลด
        discount = ""
        if info.get("discount"):
            discount = info["discount"]
        elif price_original > 0 and price_original > price:
            pct = round((1 - price / price_original) * 100)
            discount = f"-{pct}%"

        # จำนวนขาย
        sold = info.get("sold", 0) or info.get("historical_sold", 0)
        sold_str = ""
        if sold >= 10000:
            sold_str = f"{sold/10000:.1f} หมื่น"
        elif sold >= 1000:
            sold_str = f"{sold/1000:.1f} พัน"
        elif sold > 0:
            sold_str = str(sold)

        # ชื่อร้าน
        shop = info.get("shop_name", "") or ""
        if not shop:
            shop = info.get("shopid", "")

        # ที่อยู่ร้าน
        location = info.get("shop_location", "") or ""

        # ลิงก์
        item_id = info.get("itemid", "")
        shop_id = info.get("shopid", "")
        name_slug = info.get("name", "").replace(" ", "-")[:80]
        url = f"{BASE_URL}/{name_slug}-i.{shop_id}.{item_id}" if item_id and shop_id else ""

        # รูปภาพ
        image = ""
        if info.get("image"):
            image = f"https://down-th.img.susercontent.com/file/{info['image']}"
        elif info.get("images"):
            image = f"https://down-th.img.susercontent.com/file/{info['images'][0]}"

        return {
            "name": info.get("name", "")[:200],
            "price": f"{price:.0f}" if price else "",
            "price_original": f"{price_original:.0f}" if price_original and price_original > price else "",
            "discount": discount,
            "sold": sold_str,
            "rating": str(info.get("item_rating", {}).get("rating_star", "") or ""),
            "shop": str(shop),
            "location": location,
            "url": url,
            "image": image,
        }
    except Exception:
        return {}


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
        sold = f" ขายแล้ว {p['sold']}" if p.get("sold") else ""
        print(f"  {i:2}. {name:<44} {price:>10}{sold}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Shopee API Scraper - ดึงข้อมูลสินค้าจาก Shopee API",
        epilog="""
ตัวอย่าง:
  python shopee_api_scraper.py --keyword "เสื้อยืด" --limit 50
  python shopee_api_scraper.py --keyword "iPhone" --sort sales --output phones.csv
  python shopee_api_scraper.py --keyword "รองเท้า" --sort price_asc --limit 30
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

    products = search_products(
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


if __name__ == "__main__":
    main()
