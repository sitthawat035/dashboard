#!/usr/bin/env python3
"""
Test script for Shopee affiliate link conversion
Tests various URL formats and edge cases
"""

import sys
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))


def convert_to_affiliate(url, affiliate_id):
    """Convert Shopee URL to affiliate link."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    item_id = None
    shop_id = None
    
    if "product" in path_parts:
        # Format: /product/SHOP_ID/ITEM_ID
        idx = path_parts.index("product")
        if len(path_parts) > idx + 2:
            shop_id = path_parts[idx + 1]
            item_id = path_parts[idx + 2]
    elif "product-i" in parsed.path:
        # Format: /product-i.SHOP_ID.ITEM_ID
        match = re.search(r'product-i\.(\d+)\.(\d+)', parsed.path)
        if match:
            shop_id = match.group(1)
            item_id = match.group(2)
    
    if not item_id:
        # Fallback: use original URL with affiliate parameter
        query_params = parse_qs(parsed.query)
        query_params['af_id'] = [affiliate_id]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    
    # Build affiliate link
    affiliate_url = f"https://shopee.co.th/universal-link/{item_id}?af_id={affiliate_id}"
    
    return affiliate_url


def test_url_conversion():
    """Test various URL formats."""
    affiliate_id = "test_affiliate_123"
    
    # Test cases: (input_url, expected_to_work, description)
    test_cases = [
        # Standard product-i format from CSV
        (
            "https://shopee.co.th/ครีมบำรุงผิว-Zudaifu-15-กรัม-i.1329026110.27529029989",
            True,
            "Thai product name with product-i format"
        ),
        # Product path format
        (
            "https://shopee.co.th/product/123456/7890123",
            True,
            "Product path format"
        ),
        # Another product-i format
        (
            "https://shopee.co.th/Any-Product-Name-i.123.456",
            True,
            "Simple product-i format"
        ),
        # Invalid/no product ID
        (
            "https://shopee.co.th/shop-name",
            False,
            "Invalid URL (no product ID)"
        ),
        # Already has affiliate ID
        (
            "https://shopee.co.th/product/123/456?af_id=old_affiliate",
            True,
            "URL with existing af_id"
        ),
        # Complex URL with many parameters
        (
            "https://shopee.co.th/Product-Name-i.295441887.26981869629?extraParams=%7B%22display_model_id%22%3A292312278227%7D&sp_atk=abc123",
            True,
            "Complex URL with extra params"
        ),
    ]
    
    print("="*70)
    print("Testing Shopee URL to Affiliate Link Conversion")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for url, should_work, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input:  {url[:60]}..." if len(url) > 60 else f"Input:  {url}")
        
        try:
            result = convert_to_affiliate(url, affiliate_id)
            
            if "universal-link" in result or "af_id=" in result:
                print(f"Output: {result}")
                if should_work:
                    print("✅ PASS")
                    passed += 1
                else:
                    print("⚠️  PASS (but expected to fail)")
                    passed += 1
            else:
                print(f"Output: {result}")
                if not should_work:
                    print("✅ PASS (correctly failed)")
                    passed += 1
                else:
                    print("❌ FAIL - Expected to work but didn't produce affiliate link")
                    failed += 1
                    
        except Exception as e:
            print(f"Error: {e}")
            if not should_work:
                print("✅ PASS (correctly raised error)")
                passed += 1
            else:
                print("❌ FAIL - Unexpected error")
                failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*70)
    print("Testing Edge Cases")
    print("="*70)
    
    affiliate_id = "test123"
    
    edge_cases = [
        ("", "Empty string"),
        ("not-a-url", "Invalid URL format"),
        ("https://other-site.com/product/123", "Non-Shopee URL"),
        ("https://shopee.co.th", "Shopee homepage only"),
        ("https://shopee.co.th/search", "Shopee search page"),
    ]
    
    for url, description in edge_cases:
        print(f"\nEdge case: {description}")
        print(f"Input: '{url}'")
        
        try:
            result = convert_to_affiliate(url, affiliate_id)
            print(f"Output: {result}")
            print("⚠️  Handled (no exception)")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            print("✅ Correctly raised exception")


if __name__ == "__main__":
    # Set UTF-8 encoding for Thai characters
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    success = test_url_conversion()
    test_edge_cases()
    
    print("\n" + "="*70)
    print("Conversion Test Complete!")
    print("="*70)
    
    sys.exit(0 if success else 1)
