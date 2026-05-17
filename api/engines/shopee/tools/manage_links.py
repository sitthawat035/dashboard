import os
import re
from pathlib import Path
from datetime import datetime
import argparse

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def extract_links_from_plan():
    plan_path = Path("daily_content_plan.md")
    if not plan_path.exists():
        print("❌ ไม่พบไฟล์ daily_content_plan.md")
        return []
    
    content = plan_path.read_text(encoding='utf-8')
    table_match = re.search(r'\| Slot \|.*?\|\n\|[-| ]+\|\n(.*?)(?=\n\n|\n---|$)', content, re.DOTALL)
    if not table_match:
        print("❌ ไม่พบตารางในแผนงาน")
        return []
        
    rows = table_match.group(1).strip().split('\n')
    links = []
    for row in rows:
        cols = [c.strip() for c in row.split('|') if c.strip()]
        if len(cols) >= 4:
            links.append({
                "slot": cols[0].replace(':', '.'),
                "url": cols[3]
            })
    return links

def show_links():
    links = extract_links_from_plan()
    if not links: return
    
    # บันทึกเป็นไฟล์ต้นฉบับเพื่อใช้แมตช์ตอนเปลี่ยน
    with open("temp_orig_links.txt", "w", encoding="utf-8") as f:
        for item in links:
            f.write(f"{item['slot']}|{item['url']}\n")
    
    # สร้างไฟล์รอรับลิงก์ Affiliate
    with open("affiliate_links_here.txt", "w", encoding="utf-8") as f:
        f.write("# วางลิงก์ Affiliate ที่แปลงแล้ว 4 ลิงก์ เรียงบรรทัดกันได้เลยแกรรร\n")
        f.write("# (ลบบรรทัดที่ขึ้นต้นด้วย # ออกให้หมดนะ)\n")
        for item in links:
            f.write(f"--- วางลิงก์ของ {item['slot']} ที่นี่ ---\n")

    print("\n--- 🔗 ก๊อปปี้ลิงก์ไปแปลงเลยแกรรร ---")
    for item in links:
        print(item['url'])
    
    print("\n✅ ฉันสร้างไฟล์ 'affiliate_links_here.txt' ไว้ให้แล้ว!")
    print("👉 เอาลิงก์ที่แปลงเสร็จมาวางในไฟล์นั้น (เรียงตามลำดับ) แล้วบันทึกไฟล์ด้วยนะ")

def apply_links():
    today = get_today_str()
    if not Path("temp_orig_links.txt").exists() or not Path("affiliate_links_here.txt").exists():
        print("❌ ไม่พบไฟล์สำหรับทำงาน กรุณารันโหมด --get ก่อนนะ")
        return

    # อ่านลิงก์ใหม่จากเครื่อง
    with open("affiliate_links_here.txt", "r", encoding="utf-8") as f:
        new_links = [line.strip() for line in f if not line.startswith("#") and "http" in line]

    if len(new_links) == 0:
        print("❌ แกรยังไม่ได้วางลิงก์ใหม่ใน affiliate_links_here.txt เลย!")
        return

    # อ่านข้อมูลเดิม
    orig_data = []
    with open("temp_orig_links.txt", "r", encoding="utf-8") as f:
        for line in f:
            orig_data.append(line.strip().split("|"))

    base_path = Path("05_ReadyToPost") / today
    
    count = 0
    for idx, (slot, orig_url) in enumerate(orig_data):
        if idx >= len(new_links): break
        new_url = new_links[idx]
        
        caption_path = base_path / slot / "caption.txt"
        if caption_path.exists():
            content = caption_path.read_text(encoding="utf-8")
            # เปลี่ยนจากลิงก์เดิมเป็นลิงก์ใหม่
            new_content = content.replace(orig_url, new_url)
            caption_path.write_text(new_content, encoding="utf-8")
            print(f"✨ เปลี่ยนลิงก์ใน {slot}/caption.txt สำเร็จ!")
            count += 1
        else:
            print(f"⚠️ ไม่พบไฟล์ {caption_path} (อาจจะรันไม่ผ่านรอบก่อน)")

    print(f"\n🎉 เรียบร้อย! อัปเดตไปทั้งหมด {count} ไฟล์จ้าาา")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--get", action="store_true", help="ดึงลิงก์ไปแปลง")
    parser.add_argument("--apply", action="store_true", help="วางลิงก์ที่แปลงแล้ว")
    args = parser.parse_args()
    
    if args.get:
        show_links()
    elif args.apply:
        apply_links()
    else:
        print("ใส่โหมดด้วยนะแกร: --get หรือ --apply")
