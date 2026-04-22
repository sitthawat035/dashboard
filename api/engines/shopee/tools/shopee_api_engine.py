#!/usr/bin/env python3
"""
Shopee API Engine — Hybrid Mode (CSV Reader)
=============================================
อ่านข้อมูลสินค้าจาก CSV ที่ได้จาก Console Snippet

วิธีใช้:
  1. ไป shopee.co.th → ค้นหาสินค้า → scroll ให้เห็นสินค้า
  2. กด F12 → Console → วาง script จาก shopee_console_scraper.js
  3. ไฟล์ CSV จะดาวน์โหลด → ย้ายมาที่ data/content/shopee/scraped/
  4. หรือถ้า Dashboard เปิดอยู่ → snippet จะส่งข้อมูลให้ Dashboard อัตโนมัติ

Usage (CLI - verify CSV):
  python shopee_api_engine.py --verify
  python shopee_api_engine.py --import path/to/downloaded.csv
"""

import argparse
import csv
import sys
import io
import shutil
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_ROOT = SCRIPT_DIR.parent
API_DIR = ENGINE_ROOT.parent.parent
DASHBOARD_DIR = API_DIR.parent
OUTPUT_DIR = DASHBOARD_DIR / "data" / "content" / "shopee" / "scraped"


def verify_csv():
    """Check and display latest scraped CSV."""
    items_csv = OUTPUT_DIR / "items.csv"
    if not items_csv.exists():
        # Look for any CSV in the directory
        csvs = sorted(OUTPUT_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True) if OUTPUT_DIR.exists() else []
        if csvs:
            items_csv = csvs[0]
        else:
            print("❌ ไม่พบ CSV — ยังไม่ได้ scrape")
            print(f"   ไปที่ shopee.co.th → ค้นหา → F12 Console → วาง script")
            print(f"   Script อยู่ที่: {SCRIPT_DIR / 'shopee_console_scraper.js'}")
            return False

    print(f"📄 Found: {items_csv.name}")
    print(f"   Modified: {items_csv.stat().st_mtime}")
    
    with open(items_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        products = list(reader)
    
    if not products:
        print("❌ CSV is empty")
        return False
    
    print(f"✅ {len(products)} products\n")
    print(f"{'─'*65}")
    print(f"  {'#':>3}  {'ชื่อสินค้า':<40}  {'ราคา':>8}")
    print(f"{'─'*65}")
    for i, p in enumerate(products[:15], 1):
        name = p.get("name", "?")
        name = (name[:38] + "..") if len(name) > 38 else name
        price = f"฿{p.get('price', '?')}"
        print(f"  {i:>3}  {name:<40}  {price:>8}")
    if len(products) > 15:
        print(f"  ... +{len(products)-15} more")
    print(f"{'─'*65}")
    
    return True


def import_csv(csv_path):
    """Import an external CSV into the pipeline directory."""
    src = Path(csv_path)
    if not src.exists():
        print(f"❌ File not found: {csv_path}")
        return False
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = OUTPUT_DIR / "items.csv"
    shutil.copy2(str(src), str(dst))
    print(f"✅ Imported {src.name} → {dst}")
    
    # Also keep a copy with original name
    shutil.copy2(str(src), str(OUTPUT_DIR / src.name))
    
    return verify_csv()


def main():
    parser = argparse.ArgumentParser(
        description="Shopee Engine — Hybrid CSV Mode",
        epilog="""
วิธีใช้:
  1. เปิด Chrome → shopee.co.th → ค้นหาสินค้า
  2. F12 → Console → วาง script จาก shopee_console_scraper.js
  3. CSV จะดาวน์โหลด + ส่งไป Dashboard อัตโนมัติ
  4. รัน: python shopee_api_engine.py --verify
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("keyword", nargs="?", default=None, help="(ไม่ใช้ — สำหรับ compatibility กับ engine registry)")
    parser.add_argument("--count", type=int, default=15, help="(ไม่ใช้)")
    parser.add_argument("--verify", action="store_true", help="ตรวจสอบ CSV ล่าสุด")
    parser.add_argument("--import-csv", dest="import_csv", help="Import CSV file")

    args = parser.parse_args()

    if args.import_csv:
        import_csv(args.import_csv)
    elif args.verify:
        verify_csv()
    else:
        # Default: show instructions + verify if CSV exists
        print("🛒 Shopee Engine — Hybrid Mode")
        print("=" * 50)
        print()
        print("📋 ขั้นตอน:")
        print("  1. เปิด Chrome → shopee.co.th")
        print("  2. ค้นหาสินค้าที่ต้องการ")
        print("  3. Scroll ให้เห็นสินค้าทั้งหมด")
        print("  4. กด F12 → Console tab")
        print("  5. วาง script (Copy จากด้านล่าง) → Enter")
        print("  6. CSV จะดาวน์โหลดอัตโนมัติ ✅")
        print()
        
        # Show the minified snippet for easy copy
        js_file = SCRIPT_DIR / "shopee_console_scraper.js"
        if js_file.exists():
            print(f"📄 Script อยู่ที่: {js_file}")
        
        print()
        
        if OUTPUT_DIR.exists():
            csvs = sorted(OUTPUT_DIR.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
            if csvs:
                print("📊 CSV ล่าสุด:")
                verify_csv()
            else:
                print("ℹ️ ยังไม่มี CSV — ทำตามขั้นตอนด้านบน")


if __name__ == "__main__":
    main()
