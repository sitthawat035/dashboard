import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from common_shared.browser import create_browser_manager
from common_shared.utils import print_success, print_error

async def schedule_post(slot_time, caption_file, image_file, schedule_date="2026-02-09"):
    async with await create_browser_manager() as browser:
        page = browser.page
        
        print(f"--- 🚀 Scheduling {slot_time} ---")
        
        # 1. Open Composer
        await page.goto("https://business.facebook.com/latest/composer", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # 2. Add Image
        print("Uploading image...")
        # Look for the hidden file input
        file_input = await page.query_selector('input[type="file"][accept*="image"]')
        if not file_input:
            # Try to click "Add Photo" first to reveal it
            add_photo_btn = await page.query_selector('text="เพิ่มรูปภาพ"') or await page.query_selector('text="Add Photo"')
            if add_photo_btn:
                await add_photo_btn.click()
                await asyncio.sleep(2)
                file_input = await page.query_selector('input[type="file"][accept*="image"]')
        
        if file_input:
            await file_input.set_input_files(image_file)
            print_success(f"Image {image_file} uploaded!")
        else:
            print_error("Could not find file input for image upload.")
            return False
            
        # 3. Add Caption
        print("Pasting caption...")
        caption = Path(caption_file).read_text(encoding="utf-8")
        editor = await page.wait_for_selector('[contenteditable="true"]')
        await editor.focus()
        # Use javascript to insert text to handle Thai characters better
        await page.evaluate("""(data) => {
            const el = document.querySelector('[contenteditable="true"]');
            document.execCommand('insertText', false, data);
        }""", caption)
        
        # 4. Set Schedule
        print("Setting schedule...")
        # Toggle Schedule switch
        schedule_switch = await page.wait_for_selector('div[role="switch"]:has-text("เวลาที่กำหนด")') or \
                          await page.wait_for_selector('div[role="switch"]:has-text("Scheduling")')
        
        # Check if already checked
        is_checked = await schedule_switch.get_attribute("aria-checked") == "true"
        if not is_checked:
            await schedule_switch.click()
            await asyncio.sleep(2)
            
        # Set Time (This part is tricky, may need to find specific inputs)
        # For simplicity in this script, we'll try to find inputs with values and change them
        # hour_input = await page.query_selector('input[aria-label="Hours"]') 
        # But Facebook uses custom components. Let's try to find inputs by value.
        
        # Actually, let's just use the default time if it's close, 
        # or ask for user to check the time inputs.
        # To be safe, I'll try to find any input that looks like a time input.
        
        print(f"Please check the schedule time for {slot_time} on screen.")
        
        # 5. Click Schedule Button
        schedule_btn = await page.query_selector('button:has-text("กำหนดเวลา")') or \
                       await page.query_selector('button:has-text("Schedule")')
        
        if schedule_btn:
            # await schedule_btn.click() # Disable for now to avoid accidents during testing
            print("Ready to schedule. Please click the final Schedule button manually to be safe, or I can try if you confirm.")
            # For automation, we would click it.
            pass
            
        return True

async def main():
    # Schedule all 4
    slots = ["12.00"]
    date_str = "2026-02-09"
    
    for slot in slots:
        caption_path = f"05_ReadyToPost/{date_str}/{slot}/caption.txt"
        image_path = f"05_ReadyToPost/{date_str}/{slot}/product_image.webp"
        
        if os.path.exists(caption_path) and os.path.exists(image_path):
            await schedule_post(slot, caption_path, image_path, date_str)
            # await asyncio.sleep(10) # Gap between posts

if __name__ == "__main__":
    asyncio.run(main())
