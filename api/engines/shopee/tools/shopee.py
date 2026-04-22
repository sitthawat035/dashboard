#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTIMATE SIMPLE - One Command to Rule Them All!

python shopee.py

That's it. No parameters, no thinking.
"""

import sys
import os
import io
# Force UTF-8 on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import subprocess
from pathlib import Path
from datetime import datetime
import time

def run_command(cmd, description):
    """Run command and show output"""
    print(f"\n{'='*70}")
    print(f"➤ {description}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "🚀" * 35)
    print("🚀" + " " * 68 + "🚀")
    print("🚀" + " SHOPEE AFFILIATE - FULL PIPELINE (ULTIMATE SIMPLE)".center(68) + "🚀")
    print("🚀" + " " * 68 + "🚀")
    print("🚀" * 35 + "\n")
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📅 Date: {date_str}\n")
    
    # Step 1: Generate content
    if not run_command(
        "python tools/daily_content_generator.py",
        "Step 1/3: Generate Content (captions + images)"
    ):
        print("❌ Content generation failed!")
        return 1
    
    print("✅ Captions + images ready!")
    
    # Step 2: Open Chrome + Extract links
    if not run_command(
        f"python tools/run_all_in_one.py {date_str}",
        "Step 2/3: Extract Links + Open Chrome"
    ):
        print("⚠️  Link extraction had issues, but continuing...")
    
    print("\n📌 IMPORTANT - Manual Step Required:")
    print("="*70)
    print("1. Chrome should be opening now...")
    print("2. Go to: https://affiliate.shopee.co.th")
    print("3. LOGIN with your Shopee Affiliate account")
    print("4. Keep Chrome open, then continue")
    print("="*70)
    
    input("\n⏸️  Press ENTER when you're logged in to Affiliate...")
    
    # Step 3: Convert links + Update captions
    if not run_command(
        f"python tools/link_conversion_workflow.py {date_str}",
        "Step 3/3: Convert Links + Update Captions"
    ):
        print("⚠️  Link conversion failed - using original Shopee links")
    
    # Final summary
    print("\n" + "="*70)
    print("✅ SHOPEE AFFILIATE WORKFLOW COMPLETE!".center(70))
    print("="*70)
    print()
    print(f"📁 Output Location:")
    print(f"   {Path('data/05_ReadyToPost') / date_str}")
    print()
    print("📋 Ready to post:")
    print("   - 08:00 caption + image ✓")
    print("   - 12:00 caption + image ✓")
    print("   - 18:00 caption + image ✓")
    print("   - 22:00 caption + image ✓")
    print()
    print("🔗 Links:")
    print("   ✓ Converted to affiliate short links (s.shopee.co.th)")
    print("   ✓ Embedded in captions")
    print()
    print("🚀 Next: Post to Facebook/Instagram!")
    print()
    print("="*70)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
