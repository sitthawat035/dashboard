"""
FINAL PIPELINE: AI Prompt Gen + Upload + Start Frame + Keyframe + Video
Uses the REAL prompts from manual_veo.py (with Character DNA)
"""
import asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright
from manual_veo import generate_prompts

CDP = "http://127.0.0.1:9222"
IMG_PATH = Path(r"C:\Users\User\openclaw\dashboard\api\engines\veo_gen\input_product.jpg")
OUTPUT_DIR = Path(r"C:\Users\User\openclaw\dashboard\api\data\content\veo_output\final_run")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ===== STEP 0: Generate AI prompts =====
    print("[0] Generating AI prompts from product image...")
    prompts = generate_prompts(str(IMG_PATH))
    if not prompts:
        print("FAILED to generate prompts!")
        return

    kf_prompt = prompts.get("keyframe_generation_prompt", "")
    video_prompt = prompts.get("veo_video_prompt", "")

    # Save prompts
    with open(OUTPUT_DIR / "prompts.json", "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

    print(f"   Keyframe prompt: {len(kf_prompt)} chars")
    print(f"   Video prompt: {len(video_prompt)} chars")

    # Read image for upload
    with open(IMG_PATH, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    # ===== STEP 1: Connect to Chrome =====
    print("\n[1] Connecting to Chrome...")
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

    # Navigate to Flow
    await flow.goto("https://labs.google/fx/th/tools/flow", wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # ===== STEP 2: Create new project =====
    print("[2] Creating new project...")
    try:
        await flow.locator('button:has-text("โปรเจ็กต์ใหม่")').first.click(timeout=8000)
    except:
        pass
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")
    if "/project/" not in flow.url:
        print("FAILED!")
        await pw.stop()
        return

    # ===== STEP 3: Upload product image (React method) =====
    print("[3] Uploading product image...")
    react_code = f"""async () => {{
        const input = document.querySelector('input[type="file"]');
        if (!input) return 'no input';
        const byteChars = atob('{img_b64}');
        const ba = new Uint8Array(byteChars.length);
        for (let i=0;i<byteChars.length;i++) ba[i]=byteChars.charCodeAt(i);
        const file = new File([new Blob([ba],{{type:'image/jpeg'}})],'product.jpg',{{type:'image/jpeg'}});
        const dt = new DataTransfer(); dt.items.add(file);
        input.files = dt.files;
        const rk = Object.keys(input).find(k=>k.startsWith('__reactProps'));
        if(rk&&input[rk].onChange) {{
            await input[rk].onChange({{target:input,currentTarget:input,type:'change',preventDefault:()=>{{}},stopPropagation:()=>{{}}}});
            return 'uploaded!';
        }}
        return 'no onChange';
    }}"""
    r = await flow.evaluate(react_code)
    print(f"   {r}")
    await asyncio.sleep(6)

    # ===== STEP 4: Set product.jpg as Start Frame =====
    print("[4] Setting Start Frame...")
    # Click 'เริ่ม' label
    await flow.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        for (const d of divs) {
            if (d.textContent.trim() === 'เริ่ม' && d.className.includes('jekiem')) {
                d.click(); return;
            }
        }
    }""")
    await asyncio.sleep(2)

    # Select product.jpg
    r = await flow.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.textContent?.trim() === 'product.jpg') {
                el.click();
                return 'selected product.jpg';
            }
        }
        // fallback: click first image in selector
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 80 && r.width < 300 && r.y > 100 && r.y < 400) {
                img.click();
                return 'clicked img at y=' + r.y;
            }
        }
        return 'not found';
    }""")
    print(f"   {r}")
    await asyncio.sleep(1)

    # Close frame selector
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    await flow.screenshot(path=str(OUTPUT_DIR / "step4_frame_set.png"), full_page=False)

    # ===== STEP 5: IMAGE MODE - Generate Keyframe =====
    print("\n[5] STEP 1: Generating KEYFRAME (Nano Banana 2)...")
    # Make sure we're in image mode
    await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-IMAGE]');
        if (t) { t.click(); return; }
    }""")
    await asyncio.sleep(2)

    # Select Nano Banana 2
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('Nano Banana 2')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(1)

    # Type keyframe prompt
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        await flow.keyboard.type(kf_prompt, delay=5)
        print(f"   Keyframe prompt typed ({len(kf_prompt)} chars)")
    except Exception as e:
        print(f"   Prompt error: {e}")
    await asyncio.sleep(2)

    # CREATE keyframe
    print("   Creating keyframe...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('arrow_forward') && b.textContent.includes('สร้าง')) {
                b.click(); return;
            }
        }
    }""")
    await asyncio.sleep(3)
    await flow.screenshot(path=str(OUTPUT_DIR / "step5_keyframe_gen.png"), full_page=False)

    # Wait for keyframe
    print("   Waiting for keyframe...")
    keyframe_url = None
    for i in range(24):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"     [{i+1:>2}] {line}")
        if "ดาวน์โหลด" in body:
            print(f"     [{i+1:>2}] KEYFRAME COMPLETE!")
            break

    # Get keyframe image URL
    keyframe_url = await flow.evaluate("""() => {
        const imgs = document.querySelectorAll('img[src*="googleusercontent"], img[src*="media"]');
        let biggest = null;
        let maxArea = 0;
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            const area = r.width * r.height;
            if (area > maxArea && r.width > 200) {
                biggest = img;
                maxArea = area;
            }
        }
        return biggest ? biggest.src : null;
    }""")

    if keyframe_url:
        resp = await ctx.request.get(keyframe_url)
        kf_data = await resp.body()
        kf_path = OUTPUT_DIR / "keyframe.png"
        kf_path.write_bytes(kf_data)
        print(f"   Keyframe saved: {kf_path.name} ({len(kf_data)/1024:.1f} KB)")
    else:
        print("   No keyframe URL found!")

    await flow.screenshot(path=str(OUTPUT_DIR / "step5_keyframe_done.png"), full_page=False)

    # ===== STEP 6: VIDEO MODE - Generate Video =====
    print("\n[6] STEP 2: Generating VIDEO (Veo 3.1)...")

    # Click 'เริ่ม' to set keyframe as start frame
    print("   Setting keyframe as Start Frame...")
    await flow.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        for (const d of divs) {
            if (d.textContent.trim() === 'เริ่ม' && d.className.includes('jekiem')) {
                d.click(); return;
            }
        }
    }""")
    await asyncio.sleep(2)
    # Select latest/keyframe
    await flow.evaluate("""() => {
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 80 && r.width < 300 && r.y > 100 && r.y < 400) {
                img.click();
                return;
            }
        }
    }""")
    await asyncio.sleep(1)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # Switch to VIDEO mode
    print("   Switching to video mode...")
    await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-VIDEO]');
        if (t) { t.click(); return; }
    }""")
    await asyncio.sleep(2)

    # Select Veo 3.1 - Fast
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('Veo 3.1 - Fast')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(1)

    # Clear old prompt and type video prompt
    print("   Typing video prompt...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        # Select all and delete old prompt
        await flow.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await flow.keyboard.press("Delete")
        await asyncio.sleep(0.2)
        await flow.keyboard.type(video_prompt, delay=5)
        print(f"   Video prompt typed ({len(video_prompt)} chars)")
    except Exception as e:
        print(f"   Error: {e}")
    await asyncio.sleep(2)
    await flow.screenshot(path=str(OUTPUT_DIR / "step6_ready.png"), full_page=False)

    # CREATE video
    print("   Creating video...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('arrow_forward') && b.textContent.includes('สร้าง')) {
                b.click(); return;
            }
        }
    }""")
    await asyncio.sleep(5)
    await flow.screenshot(path=str(OUTPUT_DIR / "step6_generating.png"), full_page=False)

    # ===== STEP 7: Monitor video generation =====
    print("[7] Monitoring video (max 6 min)...")
    for i in range(36):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"   [{i+1:>2}] {line}")
        if "ดาวน์โหลด" in body:
            print(f"   [{i+1:>2}] VIDEO COMPLETE!")
            break

    # ===== STEP 8: Download video =====
    print("[8] Downloading video...")
    await flow.screenshot(path=str(OUTPUT_DIR / "step8_complete.png"), full_page=False)

    vurl = await flow.evaluate("""() => {
        const v = document.querySelector('video');
        if (v && (v.src || v.currentSrc)) return v.src || v.currentSrc;
        return null;
    }""")
    if vurl:
        resp = await ctx.request.get(vurl)
        data = await resp.body()
        sp = OUTPUT_DIR / "product_video_ai_prompts.mp4"
        sp.write_bytes(data)
        print(f"   Saved: {sp.name} ({len(data)/1024:.1f} KB)")
    else:
        print("   No video URL found!")

    # ===== SUMMARY =====
    print("\n" + "=" * 55)
    print("FINAL OUTPUT:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
