"""
Quick test: Full pipeline with proper image upload + video generation
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
FLOW_URL = "https://labs.google/fx/th/tools/flow"
IMG_PATH = Path(__file__).parent / "input_product.jpg"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "content" / "veo_output" / "quick_test"
PROMPT = "A cinematic luxury product video of a smartwatch on black marble. Smooth slow-motion camera orbit around the watch. Professional studio lighting with dramatic reflections on the metal case. High-end commercial advertisement style. 8 seconds."

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]

    # Find or create flow page
    flow = None
    for p in ctx.pages:
        if "labs.google" in p.url:
            flow = p
            break
    if not flow:
        flow = await ctx.new_page()

    async def safe_click(text, timeout=5000):
        """Click via JS to avoid overlay issues"""
        result = await flow.evaluate(f'''() => {{
            const btns = document.querySelectorAll('button, [role=button], [role=tab]');
            for (const b of btns) {{
                if (b.textContent.includes("{text}")) {{
                    b.click();
                    return "clicked: " + b.textContent.trim().substring(0, 50);
                }}
            }}
            return "not found";
        }}''')
        return result

    # Step 1: Navigate to Flow
    print("[1] Navigating to Flow Labs...")
    await flow.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)

    # Step 2: Close announcements / popups
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # Step 3: Click New Project
    print("[2] Creating new project...")
    await safe_click("โปรเจ็กต์ใหม่")
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")

    # Step 4: Switch to Video mode
    print("[3] Switching to VIDEO mode...")
    # First close any popups
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    # Click video tab
    tab_result = await flow.evaluate('''() => {
        const tab = document.querySelector('[id*=trigger-VIDEO]');
        if (tab) { tab.click(); return "clicked video tab"; }
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('videocam') && b.textContent.includes('วิดีโอ')) {
                b.click();
                return "clicked video button";
            }
        }
        return "not found";
    }''')
    print(f"   {tab_result}")
    await asyncio.sleep(2)

    # Step 5: Select Veo 3.1 - Fast model
    print("[4] Selecting Veo 3.1 - Fast...")
    await safe_click("Veo 3.1 - Fast")
    await asyncio.sleep(1)

    # Step 6: Upload image via hidden file input
    print("[5] Uploading product image...")
    file_input = await flow.query_selector('input[type="file"]')
    if file_input:
        await file_input.set_input_files(str(IMG_PATH))
        await flow.evaluate('''() => {
            const input = document.querySelector('input[type="file"]');
            if (input) {
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }''')
        await asyncio.sleep(6)
        print("   Image set on file input")
    else:
        print("   WARNING: No file input found!")

    # Step 7: Type prompt
    print("[6] Typing prompt...")
    textbox = flow.locator('div[role="textbox"]').first
    try:
        await textbox.click(force=True, timeout=3000)
        await asyncio.sleep(0.5)
        await flow.keyboard.type(PROMPT, delay=10)
        print(f"   Prompt typed ({len(PROMPT)} chars)")
    except Exception as e:
        print(f"   Prompt error: {e}")
    await asyncio.sleep(2)

    # Screenshot before create
    await flow.screenshot(path=str(OUTPUT_DIR / "before_create.png"), full_page=False)

    # Step 8: Click CREATE
    print("[7] Clicking สร้าง...")
    await safe_click("arrow_forward")
    await asyncio.sleep(3)
    await flow.screenshot(path=str(OUTPUT_DIR / "after_create.png"), full_page=False)

    # Step 9: Monitor progress (up to 5 minutes)
    print("[8] Monitoring video generation...")
    done = False
    for i in range(30):  # 30 x 10s = 5 min max
        await asyncio.sleep(10)
        body = await flow.inner_text("body")

        # Check for completion
        if "ดาวน์โหลด" in body and "เสร็จ" in body:
            print(f"   [{i+1}] VIDEO COMPLETE!")
            done = True
            break

        # Check for percentage
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"   [{i+1}] Progress: {line}")

    if not done:
        print("   Timeout waiting for video!")

    # Step 10: Download video
    print("[9] Downloading video...")
    await flow.screenshot(path=str(OUTPUT_DIR / "complete.png"), full_page=False)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    try:
        dl_btn = flow.locator('button:has-text("ดาวน์โหลด")').first
        async with flow.expect_download(timeout=30000) as dl_info:
            await dl_btn.click(force=True, timeout=5000)
        dl = await dl_info.value
        save_path = OUTPUT_DIR / "product_video.mp4"
        await dl.save_as(str(save_path))
        size_kb = save_path.stat().st_size / 1024
        print(f"   DOWNLOADED: {save_path} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"   Download button failed: {e}")
        # Fallback: find video src
        video_src = await flow.evaluate('''() => {
            const v = document.querySelector('video');
            return v ? (v.src || v.currentSrc) : null;
        }''')
        if video_src:
            print(f"   Video src found: {video_src[:80]}")

    # Final summary
    print("\n" + "=" * 50)
    print("OUTPUT FILES:")
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
