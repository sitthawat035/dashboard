"""
Full pipeline: Upload product image → Generate video with Veo 3.1
Uses React onChange injection for image upload
"""
import asyncio, base64, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
FLOW_URL = "https://labs.google/fx/th/tools/flow"
IMG_PATH = Path(__file__).parent / "input_product.jpg"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "content" / "veo_output" / "full_pipeline"
PROMPT = "A cinematic luxury product video of a white smartwatch. Smooth slow-motion camera orbit around the watch on a marble surface. Professional studio lighting. High-end commercial advertisement. 8 seconds."

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(IMG_PATH, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    flow = None
    for p in ctx.pages:
        if "labs.google" in p.url:
            flow = p
            break
    if not flow:
        flow = await ctx.new_page()

    async def js_click(text):
        return await flow.evaluate(f'''() => {{
            const els = document.querySelectorAll('button, [role=button], [role=tab], [role=menuitem]');
            for (const el of els) {{
                if (el.textContent.includes("{text}") && el.offsetParent !== null) {{
                    el.click(); return "ok";
                }}
            }}
            return "not found";
        }}''')

    async def react_upload():
        """Upload image via React onChange injection"""
        return await flow.evaluate(f'''async () => {{
            const input = document.querySelector('input[type="file"]');
            if (!input) return 'no input';
            const byteChars = atob('{img_b64}');
            const byteArray = new Uint8Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) byteArray[i] = byteChars.charCodeAt(i);
            const blob = new Blob([byteArray], {{ type: 'image/jpeg' }});
            const file = new File([blob], 'product.jpg', {{ type: 'image/jpeg' }});
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            const reactKey = Object.keys(input).find(k => k.startsWith('__reactProps'));
            if (reactKey && input[reactKey]?.onChange) {{
                await input[reactKey].onChange({{ target: input, currentTarget: input, type: 'change', preventDefault: ()=>{{}}, stopPropagation: ()=>{{}} }});
                return 'uploaded via react onChange';
            }}
            return 'no react onChange found';
        }}''')

    # Step 1: Navigate
    print("[1] Navigating to Flow Labs...")
    await flow.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # Step 2: New project
    print("[2] Creating new project...")
    await js_click("โปรเจ็กต์ใหม่")
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")

    # Step 3: Switch to VIDEO mode
    print("[3] Switching to VIDEO mode...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    tab = await flow.evaluate('''() => {
        const t = document.querySelector('[id*=trigger-VIDEO]');
        if (t) { t.click(); return 'clicked tab'; }
        return 'not found';
    }''')
    print(f"   {tab}")
    await asyncio.sleep(2)

    # Step 4: Select Veo 3.1 - Quality
    print("[4] Selecting Veo 3.1 - Quality...")
    await js_click("Veo 3.1 - Quality")
    await asyncio.sleep(1)

    # Step 5: Upload image via React
    print("[5] Uploading product image (React method)...")
    upload_result = await react_upload()
    print(f"   {upload_result}")
    await asyncio.sleep(8)

    # Step 6: Type prompt
    print("[6] Typing prompt...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    textbox = flow.locator('div[role="textbox"]').first
    try:
        await textbox.click(force=True, timeout=3000)
        await flow.keyboard.type(PROMPT, delay=8)
        print(f"   Done ({len(PROMPT)} chars)")
    except Exception as e:
        print(f"   Error: {e}")
    await asyncio.sleep(2)

    await flow.screenshot(path=str(OUTPUT_DIR / "setup.png"), full_page=False)

    # Step 7: Create video
    print("[7] Creating video...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await js_click("arrow_forward")
    await asyncio.sleep(3)
    await flow.screenshot(path=str(OUTPUT_DIR / "generating.png"), full_page=False)

    # Step 8: Monitor progress
    print("[8] Monitoring (max 6 min)...")
    for i in range(36):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        pct = None
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                pct = line
        if pct:
            print(f"   [{i+1:>2}] {pct}")
        if "ดาวน์โหลด" in body and ("เสร็จ" in body or "ดูวิดีโอ" in body):
            # Double check - wait a bit more and verify
            await asyncio.sleep(3)
            body2 = await flow.inner_text("body")
            if "ดาวน์โหลด" in body2:
                print(f"   [{i+1:>2}] VIDEO COMPLETE!")
                break

    # Step 9: Download
    print("[9] Downloading...")
    await flow.screenshot(path=str(OUTPUT_DIR / "complete.png"), full_page=False)
    
    # Get video URL
    video_url = await flow.evaluate('''() => {
        const v = document.querySelector('video');
        if (v && (v.src || v.currentSrc)) return v.src || v.currentSrc;
        const s = document.querySelector('video source');
        if (s) return s.src;
        return null;
    }''')
    
    if video_url:
        api = ctx.request
        resp = await api.get(video_url)
        body_bytes = await resp.body()
        save_path = OUTPUT_DIR / "product_video_final.mp4"
        save_path.write_bytes(body_bytes)
        print(f"   Saved: {save_path.name} ({len(body_bytes)/1024:.1f} KB)")
    else:
        print("   No video URL found!")

    # Summary
    print("\n" + "="*50)
    print("OUTPUT FILES:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
