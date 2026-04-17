
import asyncio
import sys
import json
import logging
import pyperclip
from pathlib import Path

# ==========================================
# 🛠️ SHARED LIBRARY INTEGRATION
# ==========================================
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
workspace_root = project_root.parent
sys.path.insert(0, str(workspace_root))

from common_shared.browser import create_browser_manager
from common_shared.utils import setup_logger, print_success, print_error, print_info, print_warning
from common_shared.config import get_config

# Config
LOGGER = setup_logger("ShopeeAutoLink", workspace_root / ".agent" / "logs" / "shopee_auto.log")
CONFIG = get_config()

async def automate_links():
    """
    Automate the conversion of Shopee links using the existing Chrome instance.
    """
    # 1. Find the latest run folder
    from common_shared.utils import get_date_str
    date_str = get_date_str()
    
    # Path specific to Shopee project (vs shared config)
    ready_to_post_dir = workspace_root / "shopee_affiliate" / "data" / "09_ReadyToPost"
    date_dir = ready_to_post_dir / date_str
    
    if not date_dir.exists():
        print_error(f"No date folder found: {date_dir}")
        return

    # Find latest run
    run_folders = sorted([f for f in date_dir.iterdir() if f.is_dir() and f.name.startswith("run_")])
    if not run_folders:
        print_error("No run folders found!")
        return
        
    latest_run = run_folders[-1]
    print_info(f"Processing Run: {latest_run.name}")
    
    map_file = latest_run / "_links_map.json"
    paste_file = latest_run / "_paste_converted_links_here.txt"

    if not map_file.exists():
        print_error("No _links_map.json found!")
        return

    # Load links
    with open(map_file, 'r', encoding='utf-8') as f:
        links_data = json.load(f)
        
    print_info(f"Found {len(links_data)} links to convert.")

    # 2. Connect to Browser
    async with await create_browser_manager(logger=LOGGER) as browser:
        if not browser.page:
            print_error("Could not connect to browser. Is Chrome open with --remote-debugging-port=9222?")
            return

        # Navigate to Custom Link Page
        target_url = "https://affiliate.shopee.co.th/offer/custom_link"
        await browser.goto(target_url)
        
        # Check if logged in
        if "login" in browser.page.url:
            print_error("Please log in to Shopee Affiliate first!")
            return

        converted_links = []
        
        for i, item in enumerate(links_data):
            original = item["original_link"]
            print_info(f"[{i+1}/{len(links_data)}] Converting: {original[:30]}...")
            
            try:
                # 1. Paste Link into Input
                # Selector for the input box (MIGHT CHANGE - Need to be robust)
                # Strategy: Look for input with placeholder or specific class
                input_selector = "input[placeholder='Paste your link here']" 
                # If placeholder doesn't work, try generic textarea or input
                if not await browser.wait_for_selector(input_selector, timeout=5000):
                     input_selector = "textarea.shopee-input__input" # Fallback
                
                # Clear and Type
                await browser.page.fill(input_selector, "")
                await browser.page.fill(input_selector, original)
                
                # 2. Click "Get Link"
                # Button usually says "Get Link" or "Generate"
                btn_selector = "button:has-text('Get Link')"
                if not await browser.wait_for_selector(btn_selector, timeout=3000):
                     btn_selector = "button.shopee-button--primary" # Fallback
                
                await browser.page.click(btn_selector)
                
                # 3. Wait for result (Copy button appearing usually indicates success)
                # Wait for the "Copy Link" button or the result container
                copy_btn_selector = "button:has-text('Copy Link')"
                if await browser.wait_for_selector(copy_btn_selector, timeout=5000):
                    # Click Copy
                    await browser.page.click(copy_btn_selector)
                    
                    # Get from clipboard (Pyperclip is reliable here since we clicked copy)
                    # Alternatively, read the input value if it shows the short link
                    # Let's try to read the value from the result input first
                    
                    # Shopee usually shows the result in a new input or the same one
                    # Let's trust the clipboard for now as it's the intended user flow
                    await asyncio.sleep(0.5) # Wait for clipboard update
                    short_link = pyperclip.paste()
                    
                    # Basic validation
                    if "shope.ee" in short_link or "shopee.co.th" in short_link:
                         print_success(f"   -> {short_link}")
                         converted_links.append(short_link)
                    else:
                         print_warning(f"   -> Clipboard content suspicious: {short_link}")
                         converted_links.append(original) # Fallback to original
                else:
                     print_error("   -> Conversion failed (No result)")
                     converted_links.append(original)

                # Reset for next (Click 'Convert another' if exists, or just clear input)
                # Some UIs require clearing text manually
                
            except Exception as e:
                print_error(f"   -> Error: {e}")
                converted_links.append(original)
            
            await asyncio.sleep(1) # Gentle delay
            
        # 3. Save to file
        with open(paste_file, 'w', encoding='utf-8') as f:
            for link in converted_links:
                f.write(f"{link}\n")
                
        print_success(f"Saved {len(converted_links)} converted links to {paste_file.name}")

if __name__ == "__main__":
    from datetime import datetime
    try:
        asyncio.run(automate_links())
    except KeyboardInterrupt:
        print("\nStopped.")
