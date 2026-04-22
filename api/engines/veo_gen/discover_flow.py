# =============================================================================
# discover_flow.py — Deep DOM Inspector for Google Flow Labs
# =============================================================================
# เปิดหน้า Flow Labs แล้ว inspect ทุก interactive element
# เพื่อสร้าง selector map ที่ถูกต้อง
# =============================================================================

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

CDP_ENDPOINT = "http://127.0.0.1:9222"
FLOW_URL = "https://labs.google/fx/th/tools/flow"
OUTPUT_DIR = Path(__file__).parent / "_discovery"


async def deep_inspect():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(CDP_ENDPOINT)

    ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    print(f"📄 Current page: {page.url}")

    # Navigate if not already on Flow
    if "labs.google" not in page.url:
        await page.goto(FLOW_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(3)

    # Screenshot current state
    await page.screenshot(path=str(OUTPUT_DIR / "00_landing.png"))
    print("📸 Screenshot: 00_landing.png")

    # =========================================================================
    # Phase 1: Inspect ALL interactive elements on landing page
    # =========================================================================
    print("\n🔍 Phase 1: Inspecting landing page...")
    landing_elements = await page.evaluate("""() => {
        const results = [];
        const interactiveSelectors = [
            'button', 'a', 'input', 'textarea', 'select',
            '[role="button"]', '[role="textbox"]', '[role="combobox"]',
            '[role="listbox"]', '[role="option"]', '[role="tab"]',
            '[contenteditable]', '[data-testid]', '[aria-label]',
            'mat-icon', 'mat-button', 'mat-select'
        ];

        interactiveSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                const rect = el.getBoundingClientRect();
                results.push({
                    tag: el.tagName,
                    id: el.id || null,
                    classes: el.className ? String(el.className).substring(0, 200) : null,
                    role: el.getAttribute('role'),
                    ariaLabel: el.getAttribute('aria-label'),
                    type: el.getAttribute('type'),
                    placeholder: el.getAttribute('placeholder'),
                    text: (el.textContent || '').trim().substring(0, 100),
                    href: el.getAttribute('href'),
                    dataAttrs: Object.keys(el.dataset || {}),
                    visible: rect.width > 0 && rect.height > 0,
                    rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
                    selector: sel,
                });
            });
        });
        return results;
    }""")

    # Save raw data
    with open(OUTPUT_DIR / "01_landing_elements.json", "w", encoding="utf-8") as f:
        json.dump(landing_elements, f, indent=2, ensure_ascii=False)
    print(f"📝 Found {len(landing_elements)} interactive elements on landing page")

    # Print summary of useful elements
    print("\n📋 Key elements on landing page:")
    for el in landing_elements:
        if el.get("visible"):
            tag = el["tag"]
            text = el.get("text", "")[:60]
            aria = el.get("ariaLabel", "")
            role = el.get("role", "")
            placeholder = el.get("placeholder", "")
            el_id = el.get("id", "")
            if text or aria or placeholder:
                print(f"  {tag:12} | id={el_id or '-':20} | aria={aria or '-':30} | text={text or '-'}")

    # =========================================================================
    # Phase 2: Try to navigate to the prompt/create view
    # =========================================================================
    print("\n🔍 Phase 2: Looking for 'New Project' / prompt entry point...")

    # Look for clickable cards or buttons that lead to prompt input
    nav_targets = await page.evaluate("""() => {
        const targets = [];
        // Look for "new project" or "+" button or any card
        const candidates = document.querySelectorAll(
            'button, a, [role="button"], [role="link"]'
        );
        for (const el of candidates) {
            const text = (el.textContent || '').trim().toLowerCase();
            const aria = (el.getAttribute('aria-label') || '').toLowerCase();
            if (
                text.includes('new') || text.includes('ใหม่') || text.includes('create') ||
                text.includes('สร้าง') || text.includes('+') ||
                aria.includes('new') || aria.includes('create')
            ) {
                const rect = el.getBoundingClientRect();
                targets.push({
                    tag: el.tagName,
                    text: (el.textContent || '').trim().substring(0, 80),
                    ariaLabel: el.getAttribute('aria-label'),
                    classes: String(el.className).substring(0, 150),
                    visible: rect.width > 0 && rect.height > 0,
                    rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
                });
            }
        }
        return targets;
    }""")

    print(f"📝 Found {len(nav_targets)} potential 'new project' targets:")
    for t in nav_targets:
        print(f"  {t['tag']} | text: {t['text'][:50]} | visible: {t['visible']}")

    # Try to click the first visible "new project" target
    clicked = False
    if nav_targets:
        for t in nav_targets:
            if t.get("visible") and t.get("text"):
                try:
                    await page.get_by_text(t["text"][:30], exact=False).first.click(timeout=5_000)
                    print(f"✅ Clicked: {t['text'][:50]}")
                    clicked = True
                    await asyncio.sleep(3)
                    break
                except Exception:
                    continue

    # If we couldn't find a "new project" button, try clicking the textarea directly
    if not clicked:
        textarea = await page.query_selector("textarea")
        if textarea:
            print("📝 Found textarea on landing page — clicking it...")
            await textarea.click()
            await asyncio.sleep(2)
            clicked = True

    # =========================================================================
    # Phase 3: Inspect the prompt/create view
    # =========================================================================
    await page.screenshot(path=str(OUTPUT_DIR / "02_after_click.png"))
    print("📸 Screenshot: 02_after_click.png")

    print("\n🔍 Phase 3: Inspecting prompt/create view...")
    create_elements = await page.evaluate("""() => {
        const results = [];
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const tag = el.tagName;
            const rect = el.getBoundingClientRect();

            // Only care about visible, interactive, or important elements
            if (rect.width === 0 || rect.height === 0) continue;

            const isInteractive = ['BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'A'].includes(tag);
            const hasRole = el.getAttribute('role');
            const hasAria = el.getAttribute('aria-label');
            const isEditable = el.getAttribute('contenteditable');
            const hasDataTestId = el.getAttribute('data-testid');

            if (isInteractive || hasRole || hasAria || isEditable || hasDataTestId) {
                results.push({
                    tag: tag,
                    id: el.id || null,
                    classes: el.className ? String(el.className).substring(0, 200) : null,
                    role: hasRole,
                    ariaLabel: hasAria,
                    type: el.getAttribute('type'),
                    name: el.getAttribute('name'),
                    placeholder: el.getAttribute('placeholder'),
                    contentEditable: isEditable,
                    dataTestId: hasDataTestId,
                    text: (el.textContent || '').trim().substring(0, 100),
                    rect: { x: Math.round(rect.x), y: Math.round(rect.y),
                            w: Math.round(rect.width), h: Math.round(rect.height) },
                });
            }
        }
        return results;
    }""")

    with open(OUTPUT_DIR / "03_create_view_elements.json", "w", encoding="utf-8") as f:
        json.dump(create_elements, f, indent=2, ensure_ascii=False)
    print(f"📝 Found {len(create_elements)} interactive elements in create view")

    # Filter for high-value elements
    print("\n📋 High-value elements (buttons, inputs, selectors):")
    for el in create_elements:
        tag = el["tag"]
        if tag in ("BUTTON", "INPUT", "TEXTAREA", "SELECT") or el.get("contentEditable") or el.get("role") in ("button", "textbox", "combobox", "listbox", "option", "tab", "menuitem"):
            text = el.get("text", "")[:50]
            aria = el.get("ariaLabel", "") or ""
            placeholder = el.get("placeholder", "") or ""
            role = el.get("role", "") or ""
            el_id = el.get("id", "") or ""
            classes = el.get("classes", "") or ""
            rect = el.get("rect", {})
            print(f"  {tag:10} | id={el_id[:15]:15} | role={role[:10]:10} | aria={aria[:25]:25} | ph={placeholder[:20]:20} | text={text}")

    # =========================================================================
    # Phase 4: Look for Shadow DOM / Web Components
    # =========================================================================
    print("\n🔍 Phase 4: Checking for Shadow DOM...")
    shadow_hosts = await page.evaluate("""() => {
        const hosts = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                hosts.push({
                    tag: el.tagName,
                    id: el.id,
                    classes: String(el.className).substring(0, 100),
                    childCount: el.shadowRoot.childElementCount,
                });
            }
        });
        return hosts;
    }""")
    print(f"📝 Found {len(shadow_hosts)} shadow DOM hosts")
    for h in shadow_hosts:
        print(f"  {h['tag']} (id={h['id'] or '-'}) — {h['childCount']} shadow children")

    # =========================================================================
    # Final: Full page inspection with scroll
    # =========================================================================
    # Take a full page screenshot
    await page.screenshot(path=str(OUTPUT_DIR / "04_full_page.png"), full_page=True)
    print("\n📸 Full page screenshot: 04_full_page.png")

    # Get page title and URL
    title = await page.title()
    print(f"\n📊 Summary:")
    print(f"   Title: {title}")
    print(f"   URL: {page.url}")
    print(f"   Output dir: {OUTPUT_DIR.absolute()}")

    await pw.stop()
    print("\n✅ Discovery complete!")


if __name__ == "__main__":
    asyncio.run(deep_inspect())
