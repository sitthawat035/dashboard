#!/usr/bin/env python3
"""
Shopee Affiliate Pipeline Runner
Main entry point with backward-compatible CLI

Usage:
    # Legacy mode (backward compatible)
    python run_affiliate_pipeline.py
    
    # New modes
    python run_affiliate_pipeline.py --mode full
    python run_affiliate_pipeline.py --mode quick
    python run_affiliate_pipeline.py --mode content-only
    python run_affiliate_pipeline.py --step load_products
    
    # With options
    python run_affiliate_pipeline.py --count 6 --max-price 300
    python run_affiliate_pipeline.py --csv data/products.csv
    python run_affiliate_pipeline.py --dry-run
"""

import os
import sys
import argparse
import io

# Force UTF-8 on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

# Import common utilities
try:
    from common_shared.utils import (
        setup_logger, get_date_str, ensure_dir,
        print_header, print_success, print_error, print_info, print_warning
    )
    from common_shared.ai_client import create_ai_client
    from common_shared.config import Config
    HAS_COMMON = True
except ImportError:
    HAS_COMMON = False
    # Fallback implementations
    def setup_logger(name): 
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)
    def get_date_str(): return datetime.now().strftime("%Y-%m-%d")
    def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)
    def print_header(s): print(f"\n{'='*60}\n{s}\n{'='*60}")
    def print_success(s): print(f"✓ {s}")
    def print_error(s): print(f"✗ {s}")
    def print_info(s): print(f"ℹ {s}")
    def print_warning(s): print(f"⚠ {s}")

# Import pipeline controller
from pipeline_controller import AffiliatePipeline, create_parser
try:
    from shopee_affiliate.tools.convert_affiliate_links import convert_links
except ImportError:
    # Fallback to appending tools directory to sys.path
    tools_dir = project_root / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.append(str(tools_dir))
    from convert_affiliate_links import convert_links


# ============================================================================
# Legacy Functions (Backward Compatibility)
# ============================================================================

def load_products_legacy(max_price=500):
    """Legacy product loading function"""
    import csv
    
    # New organized data structure
    data_dir = root_dir / "data" / "input" / "shopee" / "products"
    
    # Find CSV — prefer items.csv (product catalog), otherwise newest CSV
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        print_error("No CSV files found!")
        return []
    
    # Prefer items.csv as the primary product source
    items_csv = [f for f in csv_files if f.name == "items.csv"]
    if items_csv:
        latest_csv = items_csv[0]
        print_info(f"Using primary product catalog: {latest_csv.name}")
    else:
        latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
    print_info(f"Loading: {latest_csv.name}")
    
    products = []
    with open(latest_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Actual CSV headers from shopee_search_scraper.py: name, price, url, image_url
                price_str = row.get('price', '0').replace('฿', '').replace(',', '').strip()
                price = float(price_str) if price_str else 0
                
                if price <= max_price:
                    products.append({
                        'name': row.get('name', ''),
                        'original_price': row.get('price', ''),
                        'discount_price': row.get('price', ''),
                        'coins': '0',
                        'url': row.get('url', ''),
                        'image_url': row.get('image_url', '')
                    })
            except Exception as e:
                continue
    
    return products


def select_products_ai_legacy(products, count=4, ai_client=None):
    """Legacy AI product selection"""
    if not ai_client:
        print_warning("No AI client, using first products")
        return products[:count]
    
    SYSTEM_PROMPT = """คุณคือ Senior Merchandiser ของ Shopee Affiliate
หน้าที่คือคัดเลือกสินค้า "ตัวเด็ด" ประจำวัน 4 ชิ้น
เกณฑ์: น่าสนใจ, หลากหลาย, คุ้มค่า

ตอบเป็น JSON: {"selected_indices": [1, 5, 8, 12], "reason": "เหตุผล"}"""
    
    items_str = "\n".join([f"{i+1}. {p['name']} ({p['original_price']})" 
                          for i, p in enumerate(products[:40])])
    
    user_prompt = f"รายการสินค้า:\n{items_str}\n\nเลือก {count} ชิ้นที่ดีที่สุด!"
    
    try:
        import json
        response = ai_client.generate(user_prompt, system=SYSTEM_PROMPT)
        
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(response)
        indices = [i-1 for i in data.get("selected_indices", [])]
        
        selected = [products[i] for i in indices if 0 <= i < len(products)]
        return selected if selected else products[:count]
        
    except Exception as e:
        print_warning(f"AI selection failed: {e}")
        return products[:count]


def generate_caption_legacy(product, ai_client=None):
    """Legacy caption generation"""
    if not ai_client:
        return (f"""🧴 {product['name']}
💰 ราคา: {product['original_price']}
🔗 ลิงก์: [LINK]""", ["shopee", "beauty"])
    
    SYSTEM_PROMPT = """คุณคือเพื่อนสายป้ายยาสินค้า Shopee ที่เขียน caption แบบสนุก จริงใจ และดึงดูดคนคลิก
เป้าหมาย: ทำให้คนอยากช้อปทันที!

สไตล์:
- Hook แรงในบรรทัดแรก (ตั้งคำถาม / บอกราคาถูก / บอกว่าดีมาก)
- บอกจุดเด่น 1-2 จุดสั้นๆ กระชับ
- มีอิโมจิสนุกสนาน 🔥✨💸😍
- ปิดด้วย CTA ชัดเจน "จิ้มลิงก์เลยนะ!"
- ลิงก์ให้เขียนว่า [LINK] เท่านั้น
- hashtag 3-5 อัน ที่เกี่ยวข้องกับสินค้า

ตอบเป็น JSON เท่านั้น:
{"caption": "แคปชั่นเต็ม...", "hashtags": ["tag1", "tag2"]}"""
    
    user_prompt = f"""สินค้า: {product['name']}
ราคา: {product['original_price']}
ลิงก์: {product['url']}

เขียนแคปชั่น!"""
    
    try:
        import json
        response = ai_client.generate(user_prompt, system=SYSTEM_PROMPT)
        
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(response)
        return data.get("caption", ""), data.get("hashtags", [])
        
    except Exception as e:
        return f"🧴 {product['name']}\n💰 {product['original_price']}\n🔗 [LINK]", ["shopee"]


def run_legacy_mode(max_price=500, count=4):
    """Run in legacy mode (backward compatible)"""
    print_header("🛒 Shopee Affiliate Pipeline (Legacy Mode)")
    
    # Load products
    print_header("📂 Loading Products")
    products = load_products_legacy(max_price)
    
    if not products:
        print_error("No products found!")
        return 1
    
    print_success(f"Found {len(products)} products")
    
    # Create AI client
    ai_client = None
    if HAS_COMMON:
        try:
            # create_ai_client takes logger, not config
            ai_client = create_ai_client()
        except Exception as e:
            print_warning(f"AI client not available: {e}")
    
    # Select products
    print_header(f"[AI] Selecting Top {count}")
    selected = select_products_ai_legacy(products, count, ai_client)
    print_success(f"Selected {len(selected)} products")
    
    # NEW: Convert links to Affiliate
    print_header("🔗 Converting Affiliate Links")
    original_links = [p['url'] for p in selected if p.get('url')]
    if original_links:
        try:
            # Note: convert_links expects a Chrome session or will try to connect to 9222
            affiliate_links = convert_links(original_links)
            # Map back to products
            for i, p in enumerate(selected):
                if i < len(affiliate_links):
                    p['affiliate_url'] = affiliate_links[i]
                else:
                    p['affiliate_url'] = p['url'] # Fallback
            print_success("Link conversion complete")
        except Exception as e:
            print_warning(f"Link conversion failed: {e}. Using original links.")
            for p in selected: p['affiliate_url'] = p['url']
    else:
        for p in selected: p['affiliate_url'] = p.get('url', '')

    # Generate content
    print_header("[AI] Generating Captions")
    
    date_str = get_date_str()
    output_dir = project_root / "data" / "ready_to_post" / date_str
    ensure_dir(output_dir)
    
    for i, product in enumerate(selected):
        print(f"\n  [{i+1}/{len(selected)}] {product['name'][:40]}...")
        
        caption, hashtags = generate_caption_legacy(product, ai_client)
        
        # Replace link placeholder (More robust replacement)
        final_link = product.get('affiliate_url') or product.get('url', '')
        placeholders = [
            "[LINK]", "[ลิงค์]", "[ลิงก์]", "[ลิงค์สินค้า]", "[Link]", 
            "[ใส่ลิงก์ Shopee]", "[ใส่ลิงก์]", "[ลิงก์สินค้า]", 
            "ใส่ลิงก์ Shopee", "[ใส่ลิงก์ตรงนี้]", "[ใส่ลิงก์ Affiliate]",
            "[ลิงก์ Affiliate]", "[Affiliate Link]", "[affiliate link]",
        ]
        final_caption = caption
        for p_holder in placeholders:
            final_caption = final_caption.replace(p_holder, final_link)
        
        # If no placeholder was replaced, append link at the end
        if final_link not in final_caption:
            final_caption += f"\n\n🔗 สนใจจิ้มเลย: {final_link}"
        
        # Save
        safe_name = "".join(c if c.isalnum() else "_" for c in product['name'][:30])
        post_dir = output_dir / f"{safe_name}_{i+1}"
        ensure_dir(post_dir)
        
        # Save caption + hashtags
        full_content = f"{final_caption}\n\n" + " ".join([f"#{t}" for t in hashtags])
        
        with open(post_dir / "post.txt", 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        # Download image
        if product.get('image_url'):
            try:
                img_res = requests.get(product['image_url'], timeout=10)
                if img_res.status_code == 200:
                    with open(post_dir / "image.webp", 'wb') as f:
                        f.write(img_res.content)
                    print_success("  Image downloaded!")
            except Exception as e:
                print_warning(f"  Failed to download image: {e}")
        
        print_success("  Done!")
    
    print_header("✓ Complete!")
    print_info(f"Output: {output_dir}")
    
    return 0


# ============================================================================
# New Pipeline Runner
# ============================================================================

def run_new_pipeline(args):
    """Run using new pipeline controller"""
    from common_shared.state_manager import StateManager
    
    # Use project root for unified state management (standard v2.0)
    state_manager = StateManager(project_root, "shopee_affiliate")
    
    # Create pipeline
    output_dir = Path(args.output) if args.output else None
    
    pipeline = AffiliatePipeline(
        mode=args.mode,
        output_dir=output_dir,
        state_manager=state_manager
    )
    
    # Handle single step
    if args.step:
        result = pipeline.run_single_step(args.step)
        print(f"\nStep result: {'Success' if result.success else 'Failed'}")
        return 0 if result.success else 1
    
    # Run full pipeline
    result = pipeline.run(
        topic=args.topic,
        count=args.count,
        max_price=args.max_price,
        csv_file=args.csv
    )
    
    return 0 if result["success"] else 1


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point with backward compatibility"""
    parser = argparse.ArgumentParser(
        description="Shopee Affiliate Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Legacy mode (default, backward compatible)
  python run_affiliate_pipeline.py
  
  # New modes
  python run_affiliate_pipeline.py --mode full
  python run_affiliate_pipeline.py --mode quick --count 6
  python run_affiliate_pipeline.py --mode content-only
  python run_affiliate_pipeline.py --step load_products
  
  # With options
  python run_affiliate_pipeline.py --max-price 300 --count 6
  python run_affiliate_pipeline.py --csv products.csv
  python run_affiliate_pipeline.py --dry-run
        """
    )
    
    # Mode options
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "quick", "content-only", "links-only", "legacy"],
        default="legacy",
        help="Pipeline mode (default: legacy for backward compatibility)"
    )
    
    # Product options
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=4,
        help="Number of products to select (default: 4)"
    )
    
    parser.add_argument(
        "--max-price",
        type=int,
        default=500,
        help="Maximum price filter (default: 500)"
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        help="Specific CSV file to load"
    )
    
    # Content options
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="Topic for content generation"
    )
    
    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    parser.add_argument(
        "--step",
        type=str,
        help="Run single step only"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Handle dry run
    if args.dry_run:
        print_header("🔍 DRY RUN")
        print(f"Mode: {args.mode}")
        print(f"Product count: {args.count}")
        print(f"Max price: {args.max_price}")
        return 0
    
    # Run in appropriate mode
    if args.mode == "legacy":
        return run_legacy_mode(
            max_price=args.max_price,
            count=args.count
        )
    else:
        return run_new_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
