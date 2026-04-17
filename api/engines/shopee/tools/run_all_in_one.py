#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-Command: Extract Links + Open Chrome
รวมการเปิด Chrome กับ extract links ในคำสั่งเดียว

Usage:
    python run_all_in_one.py [date]
    
Example:
    python run_all_in_one.py 2026-02-21
    python run_all_in_one.py  # Uses today
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import time
import socket

def is_chrome_running(port=9222):
    """Check if Chrome is already running on the port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def open_chrome(port=9222):
    """Open Chrome with debugging port"""
    print(f"🌐 Opening Chrome on port {port}...")
    
    # Find Chrome executable
    chrome_paths = [
        "chrome.exe",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        f"{Path.home()}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
    ]
    
    chrome_exe = None
    for path in chrome_paths:
        if Path(path).exists() or path == "chrome.exe":
            chrome_exe = path
            break
    
    if not chrome_exe:
        print("❌ Chrome not found! Install Chrome or add to PATH")
        return False
    
    try:
        subprocess.Popen([chrome_exe, f"--remote-debugging-port={port}"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("✅ Chrome started (minimized)")
        print(f"   Port: {port}")
        print(f"   URL: https://affiliate.shopee.co.th")
        time.sleep(3)  # Wait for Chrome to fully start
        return True
    except Exception as e:
        print(f"⚠️  Error starting Chrome: {e}")
        return False

def extract_links(date_str):
    """Extract links from captions"""
    print(f"\n📝 Extracting links for {date_str}...")
    
    script_dir = Path(__file__).resolve().parent
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_dir / "extract_links_from_captions.py"), date_str],
            capture_output=True,
            text=True,
            timeout=30,
            env={**dict(subprocess.os.environ), 'PYTHONIOENCODING': 'utf-8'}
        )
        print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="One-Command: Extract Links + Open Chrome",
        epilog="""
Examples:
  python run_all_in_one.py 2026-02-21
  python run_all_in_one.py
        """
    )
    parser.add_argument("date", nargs="?", help="Date (YYYY-MM-DD), default: today")
    args = parser.parse_args()
    
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 70)
    print("🔗 One-Command: Extract Links + Open Chrome")
    print("=" * 70)
    print()
    
    # Step 1: Check if Chrome already running
    if is_chrome_running():
        print("✅ Chrome already running on port 9222")
    else:
        # Step 2: Open Chrome
        if not open_chrome():
            print("\n⚠️  Chrome failed to start, but continuing anyway...")
            print("   Make sure to open Chrome manually:")
            print("   chrome.exe --remote-debugging-port=9222")
    
    # Step 3: Extract links
    success = extract_links(date_str)
    
    print()
    print("=" * 70)
    if success:
        print("✅ Extraction complete!")
        print("=" * 70)
        print()
        print("📋 Next steps:")
        print()
        print("1. Login to Chrome at: https://affiliate.shopee.co.th")
        print()
        print("2. Run link conversion workflow:")
        print(f"   python tools/link_conversion_workflow.py {date_str}")
        print()
    else:
        print("❌ Extraction failed")
        print("=" * 70)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
