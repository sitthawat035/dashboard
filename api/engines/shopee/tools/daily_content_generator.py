#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopee Affiliate Daily Content Generator (Simplified AI Edition)
One command = 4 posts ready!
"""

import sys
import os
import csv
import json
import requests
import io
# Force UTF-8 on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

# Load env
import os
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Try to use OpenClaw AI, fallback to OpenRouter
USE_OPENCLAW_AI = True

def call_ai_api(prompt, temperature=0.7):
    """Call AI API - tries OpenClaw AI first, fallback to OpenRouter"""
    
    # Try OpenClaw AI first
    if USE_OPENCLAW_AI:
        try:
            import socket
            # Check if OpenClaw is available locally (port 3000)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 3000))
            sock.close()
            
            if result == 0:
                # OpenClaw is available
                try:
                    from common.ai_client import create_ai_client
                    ai_client = create_ai_client()
                    response = ai_client.generate(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=2000
                    )
                    if response:
                        return response
                except Exception as e:
                    print(f"⚠️ OpenClaw AI error: {e}, trying fallback...")
        except Exception as e:
            pass
    
    # Fallback to OpenRouter
    try:
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_API_KEY":
            print("⚠️ No OpenRouter API key found, using simple fallback")
            return None
            
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"⚠️ API error (OpenRouter): {e}")
        return None


def load_products_from_csv(csv_path):
    """Load products from CSV file"""
    products = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('item_description', '').strip()
                price = row.get('item_price', '').strip()
                link = row.get('item_link', '').strip()
                image = row.get('item_image', '').strip()
                
                if name and link and price:
                    # Clean price (remove ฿ if present)
                    price_clean = price.replace('฿', '').replace(',', '').strip()
                    try:
                        price_num = int(price_clean)
                        if price_num < 500:  # Only products < 500 THB
                            products.append({
                                'name': name[:80],  # Truncate long names
                                'price': price_clean,
                                'link': link,
                                'image': image
                            })
                    except ValueError:
                        continue
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []
    
    return products


def load_products_from_md_fallback(md_path):
    """Load products from markdown template as fallback"""
    products = []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if '|' in line and 'ชื่อสินค้า' not in line and '---' not in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        name = parts[1]
                        price = parts[2].replace('฿', '').replace(',', '').strip()
                        link = parts[3]
                        image = "https://cf.shopee.co.th/file/th-11134207-7r98o-lsth67p9s..." # placeholder
                        
                        if name and link and price:
                            try:
                                price_num = int(float(price))
                                if price_num <= 500:
                                    products.append({
                                        'name': name[:80],
                                        'price': str(price_num),
                                        'link': link,
                                        'image': image
                                    })
                            except ValueError:
                                continue
    except Exception as e:
        print(f"❌ Error loading MD fallback: {e}")
    return products


def ai_select_products(products):
    """Use AI to select best 4 products for today"""
    
    # Format products for AI
    product_list = "\n".join([
        f"{i+1}. {p['name']} - ฿{p['price']}"
        for i, p in enumerate(products[:30])  # Limit to first 30 to avoid token overflow
    ])
    
    prompt = f"""คุณเป็น Content Planner สำหรับ shopee_affiliate (Skincare < 500 THB)

เลือก 4 สินค้าที่ดีที่สุดจากรายการนี้:

{product_list}

เกณฑ์การเลือก:
1. ราคา < 500 บาท
2. ชื่อน่าสนใจ หลากหลาย
3. หลากหลายประเภท (เซรั่ม, ครีม, มาส์ก, คลีนเซอร์, กันแดด)
4. เหมาะกับ time slots:
   - 08:00 - เช้า (ผลิตภัณฑ์สดชื่น เช่น คลีนเซอร์, กันแดด)
   - 12:00 - เที่ยง (บำรุงกลางวัน เช่น เซรั่ม)
   - 18:00 - เย็น (ผ่อนคลาย เช่น มาส์ก)
   - 22:00 - ก่อนนอน (บำรุงกลางคืน เช่น ครีมหน้าใส)

ตอบเป็น JSON format เท่านั้น (ไม่ต้องมี markdown):
{{
  "selections": [
    {{"slot": "08:00", "product_index": 1, "reason": "เหตุผล"}},
    {{"slot": "12:00", "product_index": 5, "reason": "เหตุผล"}},
    {{"slot": "18:00", "product_index": 10, "reason": "เหตุผล"}},
    {{"slot": "22:00", "product_index": 15, "reason": "เหตุผล"}}
  ]
}}"""

    try:
        content = call_ai_api(prompt, temperature=0.7)
        
        if not content:
            raise ValueError("No response from API")
        
        # Parse AI response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            selected = []
            for sel in data['selections']:
                idx = sel['product_index'] - 1  # Convert to 0-indexed
                if 0 <= idx < len(products):
                    selected.append({
                        'slot': sel['slot'],
                        'product': products[idx],
                        'reason': sel.get('reason', '')
                    })
            
            if len(selected) == 4:
                return selected
            else:
                raise ValueError(f"Expected 4 selections, got {len(selected)}")
        else:
            raise ValueError("No JSON found in AI response")
            
    except Exception as e:
        print(f"⚠️ AI selection failed: {e}, using fallback")
        slots = ["08:00", "12:00", "18:00", "22:00"]
        return [
            {
                "slot": slots[i],
                "product": products[i],
                "reason": "Fallback selection"
            }
            for i in range(min(4, len(products)))
        ]


def ai_write_captions(selections):
    """Use AI to write captions for all 4 products"""
    
    products_text = "\n\n".join([
        f"Slot {s['slot']}: {s['product']['name']} - ฿{s['product']['price']}\nLink: {s['product']['link']}"
        for s in selections
    ])
    
    prompt = f"""คุณเป็น Caption Writer สไตล์ "เพื่อนสายป้ายยา"

เขียน caption สำหรับสินค้า 4 ชิ้นนี้:

{products_text}

Tone:
- เป็นกันเอง ใช้ "555" "แกร" "จ้า" "อิอิ"
- ไม่เป็นทางการ แต่ไม่หยาบคาย
- สนุกสนาน มีพลัง

Structure (แต่ละ caption):
1. Hook (1 บรรทัด) - ดึงดูดความสนใจ
2. Problem (2-3 บรรทัด) - ปัญหาที่สินค้านี้แก้ได้
3. Solution (3-4 บรรทัด) - ทำไมสินค้านี้ดี
4. CTA (1 บรรทัด) - ชวนซื้อ + ลิงก์

Length: 150-200 คำต่อ caption

ตอบเป็น JSON format (ไม่ต้องมี markdown):
{{
  "captions": [
    {{"slot": "08:00", "caption": "caption text here"}},
    {{"slot": "12:00", "caption": "caption text here"}},
    {{"slot": "18:00", "caption": "caption text here"}},
    {{"slot": "22:00", "caption": "caption text here"}}
  ]
}}"""

    try:
        content = call_ai_api(prompt, temperature=0.8)
        
        if not content:
            raise ValueError("No response from API")
        
        # Parse AI response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data['captions']
        else:
            raise ValueError("No JSON found in AI response")
            
    except Exception as e:
        print(f"⚠️ AI caption writing failed: {e}, using fallback")
        return [
            {
                'slot': s['slot'],
                'caption': f"{s['product']['name']}\n\nราคาแค่ ฿{s['product']['price']} 555\n\nสั่งเลย: {s['product']['link']}"
            }
            for s in selections
        ]


def download_images(selections, date_str):
    """Download product images"""
    for sel in selections:
        slot = sel['slot'].replace(':', '.')
        image_url = sel['product']['image']
        
        # Support both running contexts
        folder = Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}/{slot}")
        if not folder.parent.parent.exists():
            folder = Path(f"data/05_ReadyToPost/{date_str}/{slot}")
        folder.mkdir(parents=True, exist_ok=True)
        
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                image_path = folder / "product_image.webp"
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"✅ Downloaded image for {slot}")
            else:
                print(f"⚠️ Failed to download image for {slot} (status {response.status_code})")
        except Exception as e:
            print(f"❌ Error downloading image for {slot}: {e}")


def save_captions(captions, date_str):
    """Save captions to files"""
    for cap in captions:
        slot = cap['slot'].replace(':', '.')
        # Support both running contexts
        folder = Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}/{slot}")
        if not folder.parent.parent.exists():
            folder = Path(f"data/05_ReadyToPost/{date_str}/{slot}")
        folder.mkdir(parents=True, exist_ok=True)
        
        caption_path = folder / "caption.txt"
        with open(caption_path, 'w', encoding='utf-8') as f:
            f.write(cap['caption'])
        print(f"✅ Saved caption for {slot}")


def save_plan(selections, date_str):
    """Save daily content plan"""
    plan_path = Path("daily_content_plan.md")
    
    content = f"""# Daily Content Plan - {date_str}

| Slot | Product Name | Price | Link | Image URL |
|------|--------------|-------|------|-----------|
"""
    
    for sel in selections:
        p = sel['product']
        content += f"| {sel['slot']} | {p['name'][:50]} | ฿{p['price']} | {p['link']} | {p['image']} |\n"
    
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Saved plan to {plan_path}")


def main():
    print("🦞 Shopee Affiliate Daily Content Generator\n")
    
    # Step 1: Load products from CSV
    print("\n📂 Step 1: Loading products from CSV...")
    # Support running from both project root and shopee_affiliate folder
    csv_path = Path("shopee_affiliate/data/00_ScrapedData/items.csv")
    if not csv_path.exists():
        csv_path = Path("data/00_ScrapedData/items.csv")
        
    products = []
    if not csv_path.exists():
        print(f"⚠️ CSV file not found at: {csv_path}")
        print("💡 Trying to use fallback: product_input_template.md")
        
        md_path = Path("shopee_affiliate/product_input_template.md")
        if not md_path.exists():
            md_path = Path("product_input_template.md")
        
        if md_path.exists():
            products = load_products_from_md_fallback(md_path)
            if products:
                print(f"✅ Successfully loaded {len(products)} products from template!")
        
        if not products:
            print("❌ Cannot find any products to process (no CSV and no template data).")
            return
    else:
        products = load_products_from_csv(csv_path)
    print(f"✅ Loaded {len(products)} products (< 500 THB)")
    
    if len(products) < 4:
        print("❌ Not enough products (need at least 4)")
        return
    
    # Step 2: AI selects best 4 products
    print("\n🤖 Step 2: AI selecting best 4 products...")
    selections = ai_select_products(products)
    print(f"✅ Selected 4 products:")
    for sel in selections:
        print(f"  - {sel['slot']}: {sel['product']['name'][:50]} (฿{sel['product']['price']})")
        
    # Step 2.5: Convert links
    print("\n🔗 Step 2.5: Converting to Affiliate Links (Playwright)...")
    try:
        # Add tools to path
        sys.path.insert(0, str(script_dir))
        from convert_affiliate_links import convert_links
        import socket
        
        # Check if Chrome is running on port 9222
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chrome_available = sock.connect_ex(('127.0.0.1', 9222)) == 0
        sock.close()
        
        if not chrome_available:
            print("  ⚠️ Chrome not available on port 9222")
            print("  💡 To enable affiliate link conversion:")
            print("     1. Open Chrome/Chromium")
            print("     2. Run: chrome.exe --remote-debugging-port=9222")
            print("     3. Login to https://affiliate.shopee.co.th")
            print("  Keeping original Shopee links for now...\n")
        else:
            orig_links = [sel['product']['link'] for sel in selections]
            
            print("  🌐 Connecting to Chrome on port 9222...")
            try:
                affiliate_links = convert_links(
                    links=orig_links,
                    use_browser=True,
                    cdp_url="http://localhost:9222",
                    headless=False
                )
                
                for idx, sel in enumerate(selections):
                    if idx < len(affiliate_links) and affiliate_links[idx] and affiliate_links[idx] != orig_links[idx]:
                        sel['product']['link'] = affiliate_links[idx]
                        print(f"  ✅ {sel['slot']}: Converted")
                    else:
                        print(f"  ⚠️ {sel['slot']}: Kept original link")
            except Exception as e:
                print(f"  ⚠️ Link conversion error: {e}")
                print(f"  Keeping original links as fallback")
                
    except Exception as e:
        print(f"⚠️ Error during link conversion setup: {e}")
        print(f"  Skipping link conversion (will use original Shopee links)")
    
    # Step 3: AI writes captions
    print("\n✍️ Step 3: AI writing captions...")
    captions = ai_write_captions(selections)
    print(f"✅ Generated {len(captions)} captions")
    
    # Step 4: Download images
    print("\n📸 Step 4: Downloading product images...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    download_images(selections, date_str)
    
    # Step 5: Save captions
    print("\n💾 Step 5: Saving captions...")
    save_captions(captions, date_str)
    
    # Step 6: Save plan
    print("\n📋 Step 6: Saving daily plan...")
    save_plan(selections, date_str)
    
    # Final report
    print(f"\n✅ shopee_affiliate สำเร็จ! 4 โพสต์พร้อมแล้ว")
    print(f"\n📅 วันที่: {date_str}")
    output_dir = Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}/")
    if not output_dir.exists():
        output_dir = Path(f"data/05_ReadyToPost/{date_str}/")
    print(f"📁 Location: {output_dir}")
    print(f"\nSlots:")
    for sel in selections:
        print(f"  - {sel['slot']}: {sel['product']['name'][:40]}... (฿{sel['product']['price']})")
    print(f"\nต้องการโพสต์ต่อไหมครับ? 🚀")


if __name__ == "__main__":
    main()
