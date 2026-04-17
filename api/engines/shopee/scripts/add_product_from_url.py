#!/usr/bin/env python3
"""
Simple Product URL to Affiliate Content
Usage: python add_product_from_url.py <shopee_url>
"""

import sys
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime

# Setup path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from common_shared.browser import create_browser_manager
from common_shared.utils import setup_logger, print_success, print_error, print_info
from common_shared.state_manager import StateManager
import os

logger = setup_logger("AddProductFromURL")

async def add_product_from_url(url: str):
    """Add a single product from URL to affiliate pipeline"""
    
    print_info(f"🛍️ Processing: {url}")
    
    async with await create_browser_manager(logger=logger) as browser:
        if not browser.page:
            print_error("Cannot connect to Chrome. Make sure it is open with --remote-debugging-port=9222")
            return None
        
        try:
            # Navigate to product page
            await browser.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract product data
            product_data = {}
            
            # Get page content
            content = await browser.page.content()
            
            # Try to find JSON data in page
            json_match = re.search(r'\"item\":\s*(\{.*?\})[,}]', content)
            if json_match:
                try:
                    item_data = json.loads(json_match.group(1))
                    product_data['name'] = item_data.get('name', 'Unknown')
                    product_data['price'] = item_data.get('price', 0)
                    product_data['image'] = item_data.get('image', '')
                except:
                    pass
            
            # Fallback: get title
            if not product_data.get('name'):
                product_data['name'] = await browser.page.title()
            
            # Get price (fallback)
            if not product_data.get('price'):
                price_elem = await browser.page.query_selector('.price')
                if price_elem:
                    product_data['price'] = await price_elem.inner_text()
            
            # Get image
            if not product_data.get('image'):
                img_elem = await browser.page.query_selector('img[data-src*="shopee"]')
                if img_elem:
                    product_data['image'] = await img_elem.get_attribute('data-src') or await img_elem.get_attribute('src')
            
            product_data['url'] = url
            product_data['added_at'] = datetime.now().isoformat()
            
            # Save to pending
            output_dir = project_root / "shopee_affiliate" / "data" / "00_ScrapedData"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            output_file = output_dir / f"url_product_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, ensure_ascii=False, indent=2)
            
            print_success(f"✅ Product saved: {product_data.get('name', 'Unknown')}")
            print_info(f"📁 File: {output_file.name}")
            
            return product_data
            
        except Exception as e:
            print_error(f"Failed: {str(e)}")
            return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_product_from_url.py <shopee_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = asyncio.run(add_product_from_url(url))
    
    if result:
        print("\n✅ Product added! Run the pipeline to generate content.")
    else:
        print("\n❌ Failed to add product.")
        sys.exit(1)
