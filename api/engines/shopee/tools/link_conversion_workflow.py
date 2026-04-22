#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Link Conversion Workflow:
1. Extract links from captions
2. Convert to affiliate links (via convert_affiliate_links.py)
3. Update captions with converted links

Usage:
    python link_conversion_workflow.py [date]
    
Example:
    python link_conversion_workflow.py 2026-02-21
    
Requirements:
    - Chrome must be running with: chrome.exe --remote-debugging-port=9222
    - Login to https://affiliate.shopee.co.th before running
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_workflow(date_str=None):
    """Run complete link conversion workflow"""
    
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    print("="*70)
    print("🔗 Shopee Affiliate Link Conversion Workflow")
    print("="*70)
    print()
    
    script_dir = Path(__file__).resolve().parent
    
    # Step 1: Extract links
    print("📝 Step 1: Extracting links from captions...")
    print("-" * 70)
    try:
        result = subprocess.run(
            [sys.executable, str(script_dir / "extract_links_from_captions.py"), date_str],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Step 2: Convert links
    print("🔄 Step 2: Converting links to affiliate links...")
    print("-" * 70)
    print("⚠️  Make sure Chrome is running with:")
    print("    chrome.exe --remote-debugging-port=9222")
    print("    and logged in to https://affiliate.shopee.co.th")
    print()
    
    try:
        # Determine output_base path
        output_base = Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}")
        if not output_base.exists():
            output_base = Path(f"data/05_ReadyToPost/{date_str}")
        
        links_to_convert = output_base / "_links_to_convert.txt"
        converted_links = output_base / "_converted_links.txt"
        
        result = subprocess.run(
            [
                sys.executable, 
                str(script_dir / "convert_affiliate_links.py"),
                "--file", str(links_to_convert),
                "--output", str(converted_links),
                "--cdp-url", "http://localhost:9222"
            ],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            print()
            print("⚠️  Link conversion failed or timed out")
            print("   You can try again manually with:")
            print(f"    python convert_affiliate_links.py --file {links_to_convert} --output {converted_links}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Link conversion timeout (Chrome not responding?)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Step 3: Update captions
    print("📝 Step 3: Updating captions with converted links...")
    print("-" * 70)
    try:
        result = subprocess.run(
            [
                sys.executable, 
                str(script_dir / "update_captions_with_converted_links.py"),
                date_str,
                "--input", "_converted_links.txt"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    print("="*70)
    print("✅ Link conversion workflow completed!")
    print("="*70)
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Complete link conversion workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert links for today
  python link_conversion_workflow.py
  
  # Convert links for specific date
  python link_conversion_workflow.py 2026-02-21
  
Requirements:
  1. Chrome must be running: chrome.exe --remote-debugging-port=9222
  2. Must be logged in to: https://affiliate.shopee.co.th
  3. Captions must already exist (from daily_content_generator.py)
        """
    )
    parser.add_argument("date", nargs="?", help="Date folder (YYYY-MM-DD), default: today")
    args = parser.parse_args()
    
    success = run_workflow(args.date)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
