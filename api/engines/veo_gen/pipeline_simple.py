"""
SIMPLIFIED PIPELINE: AI Prompt + Video Mode + Veo 3.1
Skips frame selection (product image is already in project from upload)
"""
import asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright
from manual_veo import generate_prompts

CDP = "http://127.0.0.1:9222"
IMG_PATH = Path(r"C:\Users\User\openclaw\dashboard\api\engines\veo_gen\input_product.jpg")
OUTPUT_DIR = Path(r"C:\Users\User\openclaw\dashboard\api\data\content\veo_output\simple_run")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # STEP 0: Generate AI prompts
    print("[0] AI prompts...")
    prompts = generate_prompts(str(IMG_PATH))
    if not prompts:
        print("FAILED!"); return
    kf_prompt = prompts.get("keyframe_generation_prompt", "")
    video_prompt = prompts.get("veo_video_prompt", "")
    with open(OUTPUT_DIR / "prompts.json", "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    print(f"   Keyframe: {len(kf_prompt)} | Video: {len(video_prompt)}")

    with open(IMG_PATH, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    # Connect
    print("\n[1] Connect...")
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

    # New project
    print("[2] New project...")
    try:
        await flow.locator('button:has-text("โปรเจ็กต์ใหม่")').first.click(timeout=8000)
    except: pass
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")
    if "/project/" not in flow.url:
        print("FAILED!"); await pw.stop(); return

    # Upload image
    print("[3] Upload...")
    for _ in range(5):
        has_input = await flow.evaluate('() => !!document.querySelector("input[type=file]")')
        if has_input: break
        await asyncio.sleep(2)

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
    await asyncio.sleep(6)

    # Switch to VIDEO mode
    print("[4] Video mode...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-VIDEO]');
        if (t) { t.click(); return 'clicked'; }
        return 'not found';
    }""")
    await asyncio.sleep(3)

    # Select Veo 3.1 - Fast
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('Veo 3.1 - Fast')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(1)

    # Type VIDEO prompt (the main one with Character DNA + voice over)
    print("[5] Type video prompt...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        await flow.keyboard.press("Control+a")
        await flow.keyboard.press("Delete")
        await asyncio.sleep(0.2)
        await flow.keyboard.type(video_prompt, delay=3)
        print(f"   Done ({len(video_prompt)} chars)")
    except Exception as e:
        print(f"   {e}")
    await asyncio.sleep(2)

    # Verify state before creating
    body_text = await flow.inner_text("body")
    has_video = "วิดีโอ" in body_text or "VIDEO" in body_text
    has_veo = "Veo 3.1" in body_text
    print(f"   Video mode active: {has_video}")
    print(f"   Veo 3.1 selected: {has_veo}")

    try:
        await flow.screenshot(path=str(OUTPUT_DIR / "before_create.png"), full_page=False, timeout=10000)
    except: pass

    # CREATE!
    print("\n[6] CREATE VIDEO!")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('arrow_forward') && b.textContent.includes('สร้าง')) {
                b.click(); return 'clicked create';
            }
        }
        return 'not found';
    }""")
    await asyncio.sleep(5)

    try:
        await flow.screenshot(path=str(OUTPUT_DIR / "generating.png"), full_page=False, timeout=10000)
    except: pass

    # Monitor
    print("[7] Monitor...")
    for i in range(36):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"   [{i+1:>2}] {line}")
        if "ดาวน์โหลด" in body:
            print(f"   [{i+1:>2}] DONE!")
            break

    # Download
    print("[8] Download...")
    try:
        await flow.screenshot(path=str(OUTPUT_DIR / "complete.png"), full_page=False, timeout=10000)
    except: pass

    vurl = await flow.evaluate("""() => {
        const v = document.querySelector('video');
        return v ? (v.src || v.currentSrc) : null;
    }""")
    if vurl:
        resp = await ctx.request.get(vurl)
        data = await resp.body()
        sp = OUTPUT_DIR / "product_video.mp4"
        sp.write_bytes(data)
        print(f"   SAVED: {sp.name} ({len(data)/1024:.1f} KB)")
    else:
        print("   No video URL!")

    print("\nFiles:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
