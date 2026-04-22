"""
Full pipeline v3: Upload + Start Frame Assignment + Video Generation
"""
import asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright

CDP = "http://127.0.0.1:9222"
IMG_PATH = Path(r"C:\Users\User\openclaw\dashboard\api\engines\veo_gen\input_product.jpg")
OUTPUT_DIR = Path(r"C:\Users\User\openclaw\dashboard\api\data\content\veo_output\run3")
PROMPT = "A cinematic luxury product video of a white smartwatch on marble surface. Smooth slow-motion camera orbit around the watch. Professional studio lighting with dramatic reflections. High-end commercial advertisement. 8 seconds."

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(IMG_PATH, "rb") as f:
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

    async def react_upload():
        code = """
        async () => {
            const input = document.querySelector('input[type="file"]');
            if (!input) return 'no input';
            const imgB64 = '""" + img_b64 + """';
            const byteChars = atob(imgB64);
            const ba = new Uint8Array(byteChars.length);
            for (let i=0;i<byteChars.length;i++) ba[i]=byteChars.charCodeAt(i);
            const file = new File([new Blob([ba],{type:'image/jpeg'})],'product.jpg',{type:'image/jpeg'});
            const dt = new DataTransfer(); dt.items.add(file);
            input.files = dt.files;
            const rk = Object.keys(input).find(k=>k.startsWith('__reactProps'));
            if(rk&&input[rk].onChange) {
                await input[rk].onChange({target:input,currentTarget:input,type:'change',preventDefault:()=>{},stopPropagation:()=>{}});
                return 'uploaded!';
            }
            return 'no onChange';
        }"""
        return await flow.evaluate(code)

    async def js_click(text):
        return await flow.evaluate(f"""() => {{
            const els = document.querySelectorAll('button, [role=button], [role=tab], div');
            for (const el of els) {{
                const t = el.textContent?.trim();
                if (t === '{text}' && el.offsetParent !== null) {{
                    el.click(); return 'clicked: ' + el.tagName;
                }}
            }}
            // fallback: contains
            for (const el of els) {{
                if (el.textContent?.includes('{text}') && el.offsetParent !== null) {{
                    el.click(); return 'clicked contains: ' + el.textContent.trim().substring(0,40);
                }}
            }}
            return 'not found: {text}';
        }}""")

    # Step 1: Navigate
    print("[1] Navigate...")
    await flow.goto(CDP.replace("9222", "9222"), wait_until="domcontentloaded", timeout=30000)
    # Actually navigate to Flow
    await flow.goto("https://labs.google/fx/th/tools/flow", wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)

    # Step 2: Create new project
    print("[2] New project...")
    r = await js_click("add_2โปรเจ็กต์ใหม่")
    print(f"   {r}")
    if "not found" in str(r):
        r = await js_click("โปรเจ็กต์ใหม่")
        print(f"   retry: {r}")
    await asyncio.sleep(5)
    print(f"   URL: {flow.url}")

    if "/project/" not in flow.url:
        print("FAILED to create project!")
        await flow.screenshot(path=str(OUTPUT_DIR / "fail.png"))
        await pw.stop()
        return

    # Step 3: Upload image via React
    print("[3] Upload image...")
    r = await react_upload()
    print(f"   {r}")
    await asyncio.sleep(6)

    # Step 4: Open start frame selector
    print("[4] Open start frame...")
    await flow.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        for (const d of divs) {
            if (d.textContent.trim() === 'เริ่ม' && d.className.includes('jekiem')) {
                d.click(); return;
            }
        }
    }""")
    await asyncio.sleep(2)
    await flow.screenshot(path=str(OUTPUT_DIR / "step4_frame_selector.png"), full_page=False)

    # Step 5: Select product.jpg in the frame selector
    print("[5] Select product.jpg...")
    r = await flow.evaluate("""() => {
        // Click on product.jpg text or its preview
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const t = el.textContent?.trim();
            if (t === 'product.jpg') {
                el.click();
                return 'clicked product.jpg';
            }
        }
        // Try clicking the first image in the selector area
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 80 && r.width < 300 && r.y > 100 && r.y < 400) {
                img.click();
                return 'clicked img y=' + r.y;
            }
        }
        return 'not found';
    }""")
    print(f"   {r}")
    await asyncio.sleep(2)

    # Check for confirm button
    confirm = await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            const t = b.textContent?.trim();
            if (t && (t.includes('ใช้') || t.includes('เสร็จ') || t.includes('ตกลง'))) {
                b.click();
                return 'clicked confirm: ' + t.substring(0,30);
            }
        }
        return 'no confirm button';
    }""")
    print(f"   confirm: {confirm}")
    await asyncio.sleep(1)

    # Close frame selector
    await flow.keyboard.press("Escape")
    await asyncio.sleep(1)
    await flow.screenshot(path=str(OUTPUT_DIR / "step5_after_select.png"), full_page=False)

    # Step 6: Switch to VIDEO mode
    print("[6] Video mode...")
    tab = await flow.evaluate("""() => {
        const t = document.querySelector('[id*=trigger-VIDEO]');
        if (t) { t.click(); return 'clicked tab'; }
        return 'not found';
    }""")
    print(f"   {tab}")
    await asyncio.sleep(2)

    # Select Veo 3.1 - Fast
    await flow.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('Veo 3.1 - Fast')) { b.click(); return; }
        }
    }""")
    await asyncio.sleep(1)

    # Step 7: Type prompt
    print("[7] Type prompt...")
    await flow.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    tb = flow.locator('div[role="textbox"]').first
    try:
        await tb.click(force=True, timeout=3000)
        await flow.keyboard.type(PROMPT, delay=8)
        print("   Done")
    except Exception as e:
        print(f"   Error: {e}")
    await asyncio.sleep(2)
    await flow.screenshot(path=str(OUTPUT_DIR / "step7_ready.png"), full_page=False)

    # Step 8: CREATE
    print("[8] CREATE!")
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
    await flow.screenshot(path=str(OUTPUT_DIR / "step8_generating.png"), full_page=False)

    # Step 9: Monitor
    print("[9] Monitoring (max 6 min)...")
    for i in range(36):
        await asyncio.sleep(10)
        body = await flow.inner_text("body")
        for line in body.split("\n"):
            line = line.strip()
            if "%" in line and len(line) < 20:
                print(f"   [{i+1:>2}] {line}")
        if "ดาวน์โหลด" in body:
            print(f"   [{i+1:>2}] COMPLETE!")
            break

    # Step 10: Download
    print("[10] Download...")
    await flow.screenshot(path=str(OUTPUT_DIR / "step10_complete.png"), full_page=False)
    vurl = await flow.evaluate("""() => {
        const v = document.querySelector('video');
        if (v && (v.src || v.currentSrc)) return v.src || v.currentSrc;
        return null;
    }""")
    if vurl:
        resp = await ctx.request.get(vurl)
        data = await resp.body()
        sp = OUTPUT_DIR / "final_product_video.mp4"
        sp.write_bytes(data)
        print(f"   Saved: {sp.name} ({len(data)/1024:.1f} KB)")
    else:
        print("   No video URL!")

    # Summary
    print("\n" + "=" * 50)
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size/1024:.1f} KB)")

    await pw.stop()
    print("\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
