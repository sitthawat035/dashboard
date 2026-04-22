"""
FINAL PIPELINE v2: Fixed screenshot timeout + frame selection
"""
import asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright
from manual_veo import generate_prompts

CDP = "http://127.0.0.1:9222"
IMG_PATH = Path(r"C:\Users\User\openclaw\dashboard\api\engines\veo_gen\input_product.jpg")
OUTPUT_DIR = Path(r"C:\Users\User\openclaw\dashboard\api\data\content\veo_output\final_v2")

async def ss(page, name):
    """Safe screenshot with timeout"""
    try:
        await page.screenshot(path=str(OUTPUT_DIR / f"{name}.png"), full_page=False, timeout=15000)
    except Exception as e:
        print(f"   [ss fail: {name}: {str(e)[:40]}]")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # STEP 0: Generate AI prompts
    print("[0] Generating AI prompts...")
    prompts = generate_prompts(str(IMG_PATH))
    if not prompts:
        print("FAILED!"); return
    kf_prompt = prompts.get("keyframe_generation_prompt", "")
    video_prompt = prompts.get("veo_video_prompt", "")
    with open(OUTPUT_DIR / "prompts.json", "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    print(f"   Keyframe: {len(kf_prompt)} chars | Video: {len(video_prompt)} chars")

    with open(IMG_PATH, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    # STEP 1: Connect
    print("\n[1] Connecting...")
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    flow = None
    for p in ctx.pages:
        if "labs.google" in p.url:
            flow = p; break
    if not flow:
        flow = await ctx.new_page()

    await flow.goto("https://labs.google/fx/th/tools/flow", wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # STEP 2: New project
    print("[2] New project...")
    try:
        await flow.locator('button:has-text("โปรเจ็กต์ใหม่")').first.click(timeout=8000)
    except: pass
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")
    if "/project/" not in flow.url:
        print("FAILED!"); await pw.stop(); return

    # Wait for file input to appear
    for _ in range(5):
        has_input = await flow.evaluate('() => !!document.querySelector("input[type=file]")')
        if has_input: break
        await asyncio.sleep(2)

    # STEP 3: Upload product image
    print("[3] Upload image...")
    react_code = f"""async () => {{
        const input = document.querySelector('input[type="file"]');
        if (!input) return 'no input';
        const bc = atob('{img_b64}');
        const ba = new Uint8Array(bc.length);
        for (let i=0;i<bc.length;i++) ba[i]=bc.charCodeAt(i);
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
    await asyncio.sleep(8)
    await ss(flow, "step3_after_upload")

    # STEP 4: Set Start Frame
    print("[4] Set Start Frame...")
    # Click 'เริ่ม' label
    await flow.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        for (const d of divs) {
            if (d.textContent.trim() === 'เริ่ม' && d.offsetWidth > 0) {
                d.click(); return;
            }
        }
    }""")
    await asyncio.sleep(3)
    await ss(flow, "step4_frame_selector")

    # Select product.jpg (or the first available image)
    r = await flow.evaluate("""() => {
        // Try clicking product.jpg
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const t = (el.textContent || '').trim();
            if (t === 'product.jpg') {
                el.click();
                return 'clicked product.jpg';
            }
        }
        // Try clicking the first image in the overlay/selector area
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 100 && r.width < 400 && r.y > 50 && r.y < 500 && r.height > 100) {
                img.click();
                return 'clicked img ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' at y=' + Math.round(r.y);
            }
        }
        return 'not found';
    }""")
    print(f"   {r}")
    await asyncio.sleep(2)

    # Close panel
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    await ss(flow, "step4_frame_done")

    # STEP 5: IMAGE MODE - Generate Keyframe
    print("\n[5] KEYFRAME (Nano Banana 2)...")
    # Make sure image mode
    await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-IMAGE]');
        if (t && t.getAttribute('data-state') !== 'active') t.click();
    }""")
    await asyncio.sleep(2)

    # Type keyframe prompt
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        await flow.keyboard.press("Control+a")
        await flow.keyboard.press("Delete")
        await asyncio.sleep(0.2)
        await flow.keyboard.type(kf_prompt, delay=3)
        print(f"   Prompt typed ({len(kf_prompt)} chars)")
    except Exception as e:
        print(f"   Error: {e}")
    await asyncio.sleep(2)

    # Create
    print("   Creating keyframe...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('arrow_forward') && b.textContent.includes('สร้าง')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(5)
    await ss(flow, "step5_generating")

    # Wait for keyframe (image gen is usually fast ~30s)
    print("   Waiting...")
    for i in range(18):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"     [{i+1:>2}] {line}")
        if "ดาวน์โหลด" in body:
            print(f"     [{i+1:>2}] KEYFRAME DONE!")
            break

    # Get keyframe URL
    kf_url = await flow.evaluate("""() => {
        const imgs = document.querySelectorAll('img[src*="googleusercontent"], img[src*="media.getMedia"]');
        let best = null, maxA = 0;
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            const a = r.width * r.height;
            if (a > maxA && r.width > 200) { best = img; maxA = a; }
        }
        return best ? best.src : null;
    }""")
    if kf_url:
        resp = await ctx.request.get(kf_url)
        kf_data = await resp.body()
        (OUTPUT_DIR / "keyframe.png").write_bytes(kf_data)
        print(f"   Keyframe saved ({len(kf_data)/1024:.1f} KB)")
    else:
        print("   No keyframe URL!")

    await ss(flow, "step5_done")

    # STEP 6: VIDEO MODE - Generate Video
    print("\n[6] VIDEO (Veo 3.1)...")

    # Switch to video
    await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-VIDEO]');
        if (t) t.click();
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

    # Type video prompt
    print("   Typing video prompt...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        await flow.keyboard.press("Control+a")
        await flow.keyboard.press("Delete")
        await asyncio.sleep(0.2)
        await flow.keyboard.type(video_prompt, delay=3)
        print(f"   Typed ({len(video_prompt)} chars)")
    except Exception as e:
        print(f"   Error: {e}")
    await asyncio.sleep(2)
    await ss(flow, "step6_ready")

    # Create video
    print("   Creating video...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('arrow_forward') && b.textContent.includes('สร้าง')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(5)
    await ss(flow, "step6_generating")

    # STEP 7: Monitor
    print("[7] Monitoring (max 6 min)...")
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

    # STEP 8: Download
    print("[8] Download...")
    await ss(flow, "step8_complete")
    vurl = await flow.evaluate("""() => {
        const v = document.querySelector('video');
        return v ? (v.src || v.currentSrc) : null;
    }""")
    if vurl:
        resp = await ctx.request.get(vurl)
        data = await resp.body()
        sp = OUTPUT_DIR / "FINAL_product_video.mp4"
        sp.write_bytes(data)
        print(f"   SAVED: {sp.name} ({len(data)/1024:.1f} KB)")
    else:
        print("   No video URL!")

    # SUMMARY
    print("\n" + "=" * 55)
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
