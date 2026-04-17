#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CaptionFullWriter - The "Bestie Reviewer" Final Edition
Generated content for Shopee Affiliate with Gemini 2.5 Flash.
"""

import sys
import os
import re
from pathlib import Path

# --- จุดสำคัญ: ถอยหลัง 4 ชั้นเพื่อให้เจอโฟลเดอร์ shared ---
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))

try:
    from shared.utils import (
        setup_logger, get_date_str, ensure_dir,
        print_header, print_success, print_error, print_info
    )
    from shared.config import get_config
    from shared.ai_client import create_ai_client
except ModuleNotFoundError:
    print(f"❌ ยังหา 'shared' ไม่เจอที่พิกัด: {root_path}")
    sys.exit(1)

class AffiliateWriter:
    def __init__(self):
        self.config = get_config()
        self.ai = create_ai_client(None)
        self.base_ready_dir = Path(self.config.paths["ready"])

    def parse_plan(self, plan_path: Path):
        """อ่านข้อมูลสินค้าจาก daily_content_plan.md"""
        products = []
        if not plan_path.exists():
            return products

        content = plan_path.read_text(encoding='utf-8')
        # ค้นหาตาราง (Slot | Product | ราคา | Link)
        table_match = re.search(r'\| Slot \|.*?\|\n\|[-| ]+\|\n(.*?)(?=\n\n|\n---|$)', content, re.DOTALL)
        
        if table_match:
            rows = table_match.group(1).strip().split('\n')
            for row in rows:
                cols = [c.strip() for c in row.split('|') if c.strip()]
                if len(cols) >= 4:
                    products.append({
                        "slot": cols[0].replace(':', '.'), # 08:00 -> 08.00
                        "name": cols[1],
                        "price": cols[2],
                        "link": cols[3],
                        "theme": cols[4] if len(cols) > 4 else "รีวิวของดี"
                    })
        return products

    def generate_bestie_caption(self, product_data: dict) -> str:
        """สร้างแคปชั่นป้ายยาสไตล์เพื่อนสนิท"""
        system_prompt = """คุณคือ 'แอดมินสายป้ายา' เพื่อนสนิทที่ชอบรีวิวของดีราคาถูกจาก Shopee
กฎเหล็ก:
1. ใช้ภาษาไทยกลางวัยรุ่น/วัยทำงาน (Friendly & Fun)
2. ห้ามใช้คำที่เป็นทางการ (เช่น เป็นระบบ, เหมาะสำหรับ, มีคุณค่า) 
3. เน้นความรู้สึก 'ของมันต้องมี', 'แกรรร', 'ปังมาก', 'กรี๊ดดด'
4. ใช้ 555+ และ Emoji สื่ออารมณ์ให้เยอะแต่ดูจริงใจ
5. ปิดท้ายด้วย Call to Action ที่เร้าใจแต่ไม่ยัดเยียด
6. ห้ามทวนคำสั่ง หรือพูดเป็นหุ่นยนต์เด็ดขาด!
7. กฎเหล็กสูงสุด: ห้ามใช้คำว่า 'ลิ้นกวาดลิงก์' หรือคำแปลกๆ ที่ดูไม่ใช่คนพูดเด็ดขาด!"""
        
        user_prompt = f"""แกรๆ ป้ายยาสิ่งนี้ให้หน่อย เพื่อนๆ ในเพจรออยู่:
สินค้า: {product_data.get('name')}
ราคา: {product_data.get('price')}
ธีมวันนี้: {product_data.get('theme')}
ลิงก์: {product_data.get('link')}

เขียนให้ดูตื่นเต้น มีพลังแบบเพื่อนบอกเพื่อนนะเพื่อนสาววว!"""

        if self.ai:
            try:
                return self.ai.generate(user_prompt, system=system_prompt)
            except Exception as e:
                print_error(f"❌ ป้ายยาพลาด ({product_data.get('name')}): {e}")
        return "⚠️ แปะลิงค์ไว้ก่อนนะเพื่อน เดี๋ยวมาเขียนรีวิวให้!"

    def save_caption(self, slot: str, date_str: str, caption: str):
        """บันทึกแคปชั่นลงโฟลเดอร์ ReadyToPost"""
        target_dir = self.base_ready_dir / date_str / slot
        ensure_dir(target_dir)
        
        file_path = target_dir / "caption.txt"
        file_path.write_text(caption, encoding='utf-8')
        return file_path

def main():
    print_header("🛍️ BESTIE REVIEWER (GEMINI 2.5 EDITION)")
    
    writer = AffiliateWriter()
    plan_file = root_path / "daily_content_plan.md"
    today = get_date_str() # YYYY-MM-DD
    
    print_info(f"📅 กำลังอ่านแผนงานวันที่: {today}")
    products = writer.parse_plan(plan_file)
    
    if not products:
        print_error("ไม่พบตารางสินค้าใน daily_content_plan.md")
        return

    for p in products:
        print_info(f"✨ กำลังป้ายยา Slot {p['slot']}: {p['name']}...")
        caption = writer.generate_bestie_caption(p)
        
        if caption:
            # เพิ่มพิกัด (ลิงก์) ต่อท้ายแคปชั่นถ้า AI ลืม
            if p['link'] not in caption:
                caption += f"\n\n📍 พิกัดไปตำ: {p['link']}"
                
            path = writer.save_caption(p['slot'], today, caption)
            print_success(f"✅ บันทึกแล้ว: {path}")
        else:
            print_error(f"❌ ข้าม {p['name']} เนื่องจาก AI ไม่ตอบสนอง")

    print_header("🎉 เสร็จเรียบร้อย! พร้อมโพสต์แล้วแกรรร")

if __name__ == "__main__":
    main()