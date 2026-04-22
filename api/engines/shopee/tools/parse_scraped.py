import csv
import sys
from pathlib import Path

def parse_csv(file_path):
    print(f"--- 🔍 Reading: {file_path.name} ---")
    results = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # แก้ให้ตรงตามหัวตารางของ Shopee Scraper เป๊ะๆ
                name = row.get('item_description') or row.get('name') or row.get('title')
                price = row.get('item_price') or row.get('price')
                link = row.get('item_link') or row.get('link') or row.get('url')
                
                if name and link:
                    # ตัดชื่อให้สั้นลงหน่อยถ้ามันยาวไป (Shopee ชอบใส่ Keyword เยอะ)
                    short_name = name.strip()[:60] + "..." if len(name.strip()) > 60 else name.strip()
                    results.append(f"| {short_name} | ฿{price.strip()} | {link.strip()} |")
        
        if results:
            print("\n✅ ดึงข้อมูลสำเร็จ! ก๊อปตารางนี้ไปแปะใน daily_content_plan.md ได้เลยแกรรร:\n")
            print("| ชื่อสินค้า | ราคา | Link |")
            print("|------------|------|------|")
            for item in results[:10]: # เอามาโชว์ 10 ชิ้นเด็ดๆ
                print(item)
            print(f"\n💡 ทั้งหมด {len(results)} รายการ (เลือกเอาเฉพาะที่ชอบนะแก)")
        else:
            print("❌ ไม่เจอข้อมูลที่ต้องการ (ลองเช็คชื่อหัวตารางใน CSV ดูนะแกร)")
            
    except Exception as e:
        print(f"❌ พังจ้า: {e}")

if __name__ == "__main__":
    data_dir = Path("00_ScrapedData")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("💡 ยังไม่มีไฟล์ CSV ใน 00_ScrapedData เลยแก โยนมาเร็ว!")
    else:
        # รันไฟล์ล่าสุด
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        parse_csv(latest_file)
