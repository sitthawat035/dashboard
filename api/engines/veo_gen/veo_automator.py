# =============================================================================
# veo_automator.py — Google Flow Labs Playwright CDP Automation
# =============================================================================
# Full end-to-end automation: Product Image → Keyframe → Video
# Connects to existing Chrome session via CDP (port 9222)
# =============================================================================

# Windows console encoding fix
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# os already imported above
import sys
import json
import time
import shutil
import logging
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Playwright async imports
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Local imports
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from flow_selectors import SELECTORS, FLOW_URL

# =============================================================================
# Configuration
# =============================================================================

CDP_ENDPOINT = "http://127.0.0.1:9222"
DEFAULT_TIMEOUT = 60_000        # 60s for normal actions
GENERATION_TIMEOUT = 300_000    # 5min for image/video generation
INTER_STEP_DELAY = 5            # seconds between steps
POST_GENERATION_DELAY = 30      # seconds after generation (rate limit buffer)
MAX_RETRIES = 3
SCREENSHOT_ENABLED = True

# Output directory base
OUTPUT_BASE = SCRIPT_DIR.parent.parent / "data" / "content" / "veo_output"

# =============================================================================
# Logger
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("veo_automator")

# =============================================================================
# Helper: find first matching selector
# =============================================================================

async def find_element(page: Page, selector_key: str, timeout: int = 10_000):
    """Try each fallback selector until one matches."""
    selectors = SELECTORS.get(selector_key, [])
    for sel in selectors:
        try:
            el = page.locator(sel).first
            await el.wait_for(state="visible", timeout=timeout)
            return el
        except Exception:
            continue
    return None


async def find_element_any(page: Page, selector_key: str, timeout: int = 5_000):
    """Find element without requiring visibility (for hidden file inputs)."""
    selectors = SELECTORS.get(selector_key, [])
    for sel in selectors:
        try:
            el = page.locator(sel).first
            await el.wait_for(state="attached", timeout=timeout)
            return el
        except Exception:
            continue
    return None

# =============================================================================
# Core: VeoAutomator
# =============================================================================

class VeoAutomator:
    """Automates Google Flow Labs via Playwright CDP."""

    def __init__(self, output_dir: Optional[Path] = None, headless: bool = False):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = headless

        # Setup output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir or (OUTPUT_BASE / timestamp)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

        self.step_counter = 0
        self.log_lines = []

    # --- Logging ---
    def _log(self, msg: str, level: str = "info"):
        getattr(log, level)(msg)
        self.log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    async def _screenshot(self, name: str):
        """Take a screenshot (non-blocking — failures don't stop the pipeline)."""
        if SCREENSHOT_ENABLED and self.page:
            self.step_counter += 1
            path = self.screenshots_dir / f"{self.step_counter:02d}_{name}.png"
            try:
                await self.page.screenshot(path=str(path), full_page=False, timeout=10_000)
                self._log(f"📸 Screenshot: {path.name}")
            except Exception:
                self._log(f"⚠️ Screenshot skipped (timeout): {name}")

    def _save_log(self):
        log_file = self.output_dir / "run.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.log_lines))

    # ------------------------------------------------------------------
    # Connect
    # ------------------------------------------------------------------
    async def connect(self) -> bool:
        """Connect to existing Chrome via CDP."""
        self._log("🔌 Connecting to Chrome via CDP...")
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(CDP_ENDPOINT)

            # Use existing contexts (where user is logged in)
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                self._log(f"✅ Connected — reusing existing context ({len(contexts)} found)")
            else:
                self.context = await self.browser.new_context()
                self._log("⚠️ No existing context — created new one (may need Google login)")

            # Get or create a page
            pages = self.context.pages
            if pages:
                self.page = pages[0]
                self._log(f"📄 Using existing page: {self.page.url[:80]}")
            else:
                self.page = await self.context.new_page()
                self._log("📄 New page created")

            # Set generous default timeout
            self.page.set_default_timeout(DEFAULT_TIMEOUT)
            return True

        except Exception as e:
            self._log(f"❌ CDP connection failed: {e}", "error")
            self._log("   → ตรวจสอบว่า Chrome เปิดด้วย --remote-debugging-port=9222", "error")
            return False

    # ------------------------------------------------------------------
    # Navigate to Flow Labs
    # ------------------------------------------------------------------
    async def navigate_to_flow(self) -> bool:
        """Navigate to Google Flow Labs landing page."""
        self._log(f"🌐 Navigating to {FLOW_URL}")
        try:
            await self.page.goto(FLOW_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(3)  # Let dynamic content load
            await self._screenshot("navigate_flow")

            current_url = self.page.url
            if "labs.google" in current_url:
                self._log(f"✅ On Flow Labs: {current_url[:80]}")
                return True
            else:
                self._log(f"⚠️ Unexpected URL: {current_url}", "warning")
                return True

        except Exception as e:
            self._log(f"❌ Navigation failed: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # Create New Project (Landing → Project View)
    # ------------------------------------------------------------------
    async def create_new_project(self) -> bool:
        """Click 'โปรเจ็กต์ใหม่' to enter the project/create view.
        This is required before we can type prompts or select models."""
        self._log("📁 Creating new project...")

        try:
            # Check if we're already in a project view (has prompt input)
            prompt_el = await find_element(self.page, "prompt_input", timeout=3_000)
            if prompt_el:
                self._log("✅ Already in project view — skipping new project creation")
                return True

            # Click "โปรเจ็กต์ใหม่"
            new_btn = await find_element(self.page, "new_project_button", timeout=10_000)
            if new_btn:
                await new_btn.click()
                self._log("✅ Clicked 'New Project' button")
                await asyncio.sleep(3)  # Wait for project view to load
                await self._screenshot("new_project_created")

                # Verify we're in the project view now
                prompt_el = await find_element(self.page, "prompt_input", timeout=10_000)
                if prompt_el:
                    self._log("✅ Project view loaded — prompt input found")
                    return True
                else:
                    self._log("⚠️ Project view loaded but prompt input not found", "warning")
                    return True  # Proceed anyway
            else:
                self._log("⚠️ 'New Project' button not found — may already be in project", "warning")
                return True

        except Exception as e:
            self._log(f"❌ Create new project failed: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # Discovery: Inspect current page for matching selectors
    # ------------------------------------------------------------------
    async def discover_selectors(self) -> Dict[str, Any]:
        """Inspect the current page and report which selectors match.
        Use this to calibrate flow_selectors.py."""
        self._log("🔍 Discovering UI selectors...")
        results = {}
        for key, selector_list in SELECTORS.items():
            found = []
            for sel in selector_list:
                try:
                    count = await self.page.locator(sel).count()
                    if count > 0:
                        # Get some info about the first match
                        el = self.page.locator(sel).first
                        tag = await el.evaluate("e => e.tagName")
                        text = await el.evaluate("e => (e.textContent || '').trim().substring(0, 60)")
                        found.append({
                            "selector": sel,
                            "count": count,
                            "tag": tag,
                            "text": text,
                        })
                except Exception:
                    pass
            results[key] = found
            if found:
                self._log(f"  ✅ {key}: {len(found)} selector(s) match")
            else:
                self._log(f"  ❌ {key}: no match")

        # Save discovery report
        report_path = self.output_dir / "selector_discovery.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        self._log(f"📝 Discovery report saved: {report_path}")

        await self._screenshot("discovery")
        return results

    # ------------------------------------------------------------------
    # Upload Image
    # ------------------------------------------------------------------
    async def upload_image(self, image_path: str) -> bool:
        """Upload a product image to Flow Labs."""
        image_path = Path(image_path)
        if not image_path.exists():
            self._log(f"❌ Image not found: {image_path}", "error")
            return False

        self._log(f"📤 Uploading image: {image_path.name}")

        # Copy image to output dir for reference
        shutil.copy2(str(image_path), str(self.output_dir / image_path.name))

        try:
            # Method 1: Find and click upload button, then use file chooser
            upload_btn = await find_element(self.page, "upload_button", timeout=8_000)
            if upload_btn:
                async with self.page.expect_file_chooser(timeout=10_000) as fc_info:
                    await upload_btn.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(str(image_path.absolute()))
                self._log("✅ Image uploaded via button")
                await asyncio.sleep(3)
                await self._screenshot("upload_image")
                return True

            # Method 2: Direct file input
            file_input = await find_element_any(self.page, "upload_input", timeout=5_000)
            if file_input:
                await file_input.set_input_files(str(image_path.absolute()))
                self._log("✅ Image uploaded via file input")
                await asyncio.sleep(3)
                await self._screenshot("upload_image")
                return True

            # Method 3: Drag and drop simulation
            self._log("⚠️ No upload element found — trying drag & drop")
            await self.page.dispatch_event("body", "drop", {})
            await self._screenshot("upload_attempt_dnd")
            return False

        except Exception as e:
            self._log(f"❌ Upload failed: {e}", "error")
            await self._screenshot("upload_error")
            return False

    # ------------------------------------------------------------------
    # Select Model
    # ------------------------------------------------------------------
    async def select_model(self, model_name: str) -> bool:
        """Select a model (e.g., 'Nano Banana 2' or 'Veo 3.1')."""
        self._log(f"🎯 Selecting model: {model_name}")

        try:
            # First, find and click the model selector dropdown/button
            selector_btn = await find_element(self.page, "model_selector", timeout=8_000)
            if selector_btn:
                await selector_btn.click()
                await asyncio.sleep(1)

            # Then select the specific model
            option_key = "model_option_nano" if "nano" in model_name.lower() or "banana" in model_name.lower() else "model_option_veo"
            option = await find_element(self.page, option_key, timeout=8_000)
            if option:
                await option.click()
                self._log(f"✅ Model selected: {model_name}")
                await asyncio.sleep(1)
                await self._screenshot("model_selected")
                return True

            # Fallback: Try clicking text directly
            self._log("⚠️ Model option not found via selectors — trying text match")
            try:
                await self.page.get_by_text(model_name, exact=False).first.click(timeout=5_000)
                self._log(f"✅ Model selected via text: {model_name}")
                return True
            except Exception:
                pass

            self._log(f"⚠️ Could not select model: {model_name}", "warning")
            return False

        except Exception as e:
            self._log(f"❌ Model selection failed: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # Submit Prompt
    # ------------------------------------------------------------------
    async def submit_prompt(self, prompt_text: str) -> bool:
        """Type a prompt into div[role=textbox] and submit it.
        Flow Labs uses a contenteditable div, not a regular textarea,
        so we must use keyboard.type() instead of fill()."""
        self._log(f"✍️ Submitting prompt ({len(prompt_text)} chars)...")

        try:
            # Find prompt input (div[role=textbox] in Flow Labs)
            input_el = await find_element(self.page, "prompt_input", timeout=15_000)
            if not input_el:
                self._log("❌ Prompt input not found", "error")
                await self._screenshot("prompt_input_missing")
                return False

            # Focus the input
            await input_el.click()
            await asyncio.sleep(0.5)

            # Clear existing text
            await self.page.keyboard.press("Control+a")
            await self.page.keyboard.press("Delete")
            await asyncio.sleep(0.3)

            # Check if it's a contenteditable div or regular input
            tag = await input_el.evaluate("e => e.tagName")
            is_contenteditable = await input_el.evaluate(
                "e => e.getAttribute('contenteditable') === 'true' || e.getAttribute('role') === 'textbox'"
            )

            if is_contenteditable:
                # For contenteditable divs: use clipboard paste (fastest + reliable)
                self._log(f"  📝 Input is {tag} (contenteditable) — using clipboard paste")
                await self.page.evaluate(
                    "(text) => navigator.clipboard.writeText(text)",
                    prompt_text,
                )
                await self.page.keyboard.press("Control+v")
                await asyncio.sleep(0.5)

                # Verify text was pasted
                pasted = await input_el.evaluate("e => (e.textContent || '').trim()")
                if len(pasted) < 10:
                    # Clipboard paste failed — fallback to keyboard.type
                    self._log("  ⚠️ Clipboard paste may have failed — using keyboard.type fallback")
                    await input_el.click()
                    await self.page.keyboard.press("Control+a")
                    await self.page.keyboard.press("Delete")
                    await asyncio.sleep(0.3)
                    # Type in chunks to avoid timeout on very long prompts
                    chunk_size = 200
                    for i in range(0, len(prompt_text), chunk_size):
                        chunk = prompt_text[i:i + chunk_size]
                        await self.page.keyboard.type(chunk, delay=5)
                        await asyncio.sleep(0.1)
            else:
                # Regular input/textarea — use fill()
                self._log(f"  📝 Input is {tag} — using fill()")
                try:
                    await input_el.fill(prompt_text)
                except Exception:
                    await self.page.keyboard.type(prompt_text, delay=5)

            await asyncio.sleep(1)
            await self._screenshot("prompt_typed")

            # Submit: try send button first, then Enter key
            send_btn = await find_element(self.page, "send_button", timeout=5_000)
            if send_btn:
                await send_btn.click()
                self._log("✅ Prompt submitted via 'สร้าง' button")
            else:
                self._log("⚠️ Send button not found — trying Enter key")
                await self.page.keyboard.press("Enter")
                self._log("✅ Prompt submitted via Enter key")

            await asyncio.sleep(2)
            await self._screenshot("prompt_submitted")
            return True

        except Exception as e:
            self._log(f"❌ Prompt submission failed: {e}", "error")
            await self._screenshot("prompt_error")
            return False

    # ------------------------------------------------------------------
    # Wait for Generation
    # ------------------------------------------------------------------
    async def wait_for_generation(self, mode: str = "image", timeout_ms: int = GENERATION_TIMEOUT) -> bool:
        """Wait for image or video generation to complete."""
        self._log(f"⏳ Waiting for {mode} generation (timeout: {timeout_ms//1000}s)...")

        result_key = "result_image" if mode == "image" else "result_video"
        start = time.time()
        poll_interval = 5  # seconds

        while (time.time() - start) * 1000 < timeout_ms:
            # Check if result appeared
            result_el = await find_element(self.page, result_key, timeout=3_000)
            if result_el:
                elapsed = time.time() - start
                self._log(f"✅ {mode.capitalize()} generated in {elapsed:.0f}s")
                await asyncio.sleep(2)  # Let it fully render
                await self._screenshot(f"{mode}_generated")
                return True

            # Check if still loading
            loading = await find_element(self.page, "loading_indicator", timeout=1_000)
            if loading:
                elapsed = time.time() - start
                self._log(f"  ⏳ Still generating... ({elapsed:.0f}s)")

            await asyncio.sleep(poll_interval)

        self._log(f"❌ {mode} generation timed out after {timeout_ms//1000}s", "error")
        await self._screenshot(f"{mode}_timeout")
        return False

    # ------------------------------------------------------------------
    # Download Result
    # ------------------------------------------------------------------
    async def download_result(self, mode: str = "image") -> Optional[str]:
        """Download the generated image or video."""
        self._log(f"💾 Downloading {mode}...")

        try:
            # Method 1: Click download button
            download_btn = await find_element(self.page, "download_button", timeout=8_000)
            if download_btn:
                async with self.page.expect_download(timeout=30_000) as dl_info:
                    await download_btn.click()
                download = await dl_info.value

                ext = ".png" if mode == "image" else ".mp4"
                filename = f"keyframe{ext}" if mode == "image" else f"video{ext}"
                save_path = self.output_dir / filename
                await download.save_as(str(save_path))
                self._log(f"✅ Downloaded: {save_path}")
                return str(save_path)

            # Method 2: Extract src URL and download manually
            result_key = "result_image" if mode == "image" else "result_video"
            result_el = await find_element(self.page, result_key, timeout=5_000)
            if result_el:
                src = await result_el.get_attribute("src")
                if src:
                    self._log(f"📎 Found {mode} src: {src[:80]}...")

                    # If blob URL, use page to download
                    if src.startswith("blob:"):
                        ext = ".png" if mode == "image" else ".mp4"
                        filename = f"keyframe{ext}" if mode == "image" else f"video{ext}"
                        save_path = self.output_dir / filename

                        # Use JS to fetch blob and convert to base64
                        import base64
                        b64_data = await self.page.evaluate("""
                            async (src) => {
                                const resp = await fetch(src);
                                const blob = await resp.blob();
                                return new Promise((resolve) => {
                                    const reader = new FileReader();
                                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                    reader.readAsDataURL(blob);
                                });
                            }
                        """, src)
                        raw = base64.b64decode(b64_data)
                        with open(save_path, "wb") as f:
                            f.write(raw)
                        self._log(f"✅ Downloaded from blob: {save_path}")
                        return str(save_path)

                    # Regular URL — download via request
                    elif src.startswith("http"):
                        import requests
                        ext = ".png" if mode == "image" else ".mp4"
                        filename = f"keyframe{ext}" if mode == "image" else f"video{ext}"
                        save_path = self.output_dir / filename
                        resp = requests.get(src, timeout=60)
                        with open(save_path, "wb") as f:
                            f.write(resp.content)
                        self._log(f"✅ Downloaded from URL: {save_path}")
                        return str(save_path)

            self._log(f"⚠️ Could not download {mode} — no download method worked", "warning")
            await self._screenshot(f"download_{mode}_failed")
            return None

        except Exception as e:
            self._log(f"❌ Download failed: {e}", "error")
            return None

    # ------------------------------------------------------------------
    # Click "Start Video" on generated keyframe
    # ------------------------------------------------------------------
    async def start_video_from_keyframe(self) -> bool:
        """Click 'Start' / 'เริ่ม' button on the generated keyframe image."""
        self._log("🎬 Looking for 'Start Video' button on keyframe...")

        try:
            # Hover over the generated image first (some UIs show buttons on hover)
            result_img = await find_element(self.page, "result_image", timeout=8_000)
            if result_img:
                await result_img.hover()
                await asyncio.sleep(1)

            start_btn = await find_element(self.page, "start_video_button", timeout=10_000)
            if start_btn:
                await start_btn.click()
                self._log("✅ Clicked 'Start Video' button")
                await asyncio.sleep(3)
                await self._screenshot("start_video_clicked")
                return True

            self._log("⚠️ 'Start Video' button not found", "warning")
            await self._screenshot("start_video_missing")
            return False

        except Exception as e:
            self._log(f"❌ Start video failed: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # Full Pipeline: STEP 1 + STEP 2
    # ------------------------------------------------------------------
    async def run_full_pipeline(
        self,
        image_path: str,
        prompts: Dict[str, str],
        skip_keyframe: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the complete 2-step pipeline:
          STEP 1: Upload image + keyframe prompt → Nano Banana 2 → download keyframe
          STEP 2: Start video on keyframe + video prompt → Veo 3.1 → download video

        Args:
            image_path: Path to the product image
            prompts: Dict with 'keyframe_generation_prompt' and 'veo_video_prompt'
            skip_keyframe: If True, skip STEP 1 (assume keyframe already exists)

        Returns:
            Dict with paths to outputs and status
        """
        result = {
            "success": False,
            "keyframe_path": None,
            "video_path": None,
            "output_dir": str(self.output_dir),
            "errors": [],
        }

        # Save prompts to output dir
        prompts_file = self.output_dir / "prompts.json"
        with open(prompts_file, "w", encoding="utf-8") as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

        kf_prompt = prompts.get("keyframe_generation_prompt", "")
        video_prompt = prompts.get("veo_video_prompt", "")

        if not kf_prompt and not skip_keyframe:
            result["errors"].append("Missing keyframe_generation_prompt")
            self._log("❌ No keyframe prompt found", "error")
            self._save_log()
            return result

        if not video_prompt:
            result["errors"].append("Missing veo_video_prompt")
            self._log("❌ No video prompt found", "error")
            self._save_log()
            return result

        # =====================================================================
        # STEP 1: Generate Keyframe (Nano Banana 2)
        # =====================================================================
        if not skip_keyframe:
            self._log("=" * 60)
            self._log("🖼️  STEP 1: Generate Keyframe (Nano Banana 2)")
            self._log("=" * 60)

            # Navigate to Flow Labs landing page
            if not await self.navigate_to_flow():
                result["errors"].append("Failed to navigate to Flow Labs")
                self._save_log()
                return result

            # Create new project (enters the project/create view)
            if not await self.create_new_project():
                result["errors"].append("Failed to create new project")
                self._save_log()
                return result

            await asyncio.sleep(INTER_STEP_DELAY)

            # Upload image (via "เพิ่มสื่อ" button)
            if not await self.upload_image(image_path):
                result["errors"].append("Failed to upload image")
                # Continue anyway — some workflows may not require upload

            await asyncio.sleep(INTER_STEP_DELAY)

            # Select Nano Banana 2 model (should already be default based on discovery)
            await self.select_model("Nano Banana 2")

            await asyncio.sleep(INTER_STEP_DELAY)

            # Submit keyframe prompt
            if not await self.submit_prompt(kf_prompt):
                result["errors"].append("Failed to submit keyframe prompt")
                self._save_log()
                return result

            # Wait for generation
            if await self.wait_for_generation(mode="image"):
                keyframe_path = await self.download_result(mode="image")
                result["keyframe_path"] = keyframe_path
                self._log(f"🖼️ Keyframe saved: {keyframe_path}")
            else:
                result["errors"].append("Keyframe generation timed out")
                self._log("⚠️ Keyframe generation failed, continuing to STEP 2 anyway...")

        # =====================================================================
        # STEP 2: Generate Video (Veo 3.1)
        # =====================================================================
        self._log("")
        self._log("=" * 60)
        self._log("🎬 STEP 2: Generate Video (Veo 3.1)")
        self._log("=" * 60)

        await asyncio.sleep(POST_GENERATION_DELAY)

        # Click "Start" button on keyframe to enter video mode
        if not skip_keyframe:
            if not await self.start_video_from_keyframe():
                self._log("⚠️ Could not click Start — trying to submit prompt directly")

        # Select Veo 3.1 model
        await self.select_model("Veo 3.1")

        await asyncio.sleep(INTER_STEP_DELAY)

        # Submit video prompt
        if not await self.submit_prompt(video_prompt):
            result["errors"].append("Failed to submit video prompt")
            self._save_log()
            return result

        # Wait for video generation (longer timeout)
        if await self.wait_for_generation(mode="video", timeout_ms=GENERATION_TIMEOUT):
            video_path = await self.download_result(mode="video")
            result["video_path"] = video_path
            self._log(f"🎬 Video saved: {video_path}")
        else:
            result["errors"].append("Video generation timed out")

        # =====================================================================
        # Final Result
        # =====================================================================
        if result["video_path"] or result["keyframe_path"]:
            result["success"] = True

        self._log("")
        self._log("=" * 60)
        if result["success"]:
            self._log("✅ Pipeline completed successfully!")
        else:
            self._log("❌ Pipeline completed with errors")
        self._log(f"   Output dir: {self.output_dir}")
        self._log(f"   Keyframe: {result['keyframe_path'] or 'N/A'}")
        self._log(f"   Video: {result['video_path'] or 'N/A'}")
        self._log(f"   Errors: {result['errors'] or 'None'}")
        self._log("=" * 60)

        self._save_log()
        return result

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    async def close(self):
        """Clean up resources (don't close the user's browser!)."""
        self._save_log()
        if self.playwright:
            await self.playwright.stop()
        self._log("🔌 Disconnected from Chrome")


# =============================================================================
# Main: CLI Entry Point
# =============================================================================

async def async_main():
    parser = argparse.ArgumentParser(description="VEO Full Automation — Google Flow Labs")
    parser.add_argument("--image", help="Path to product image")
    parser.add_argument("--prompts-json", help="Path to pre-generated prompts JSON file")
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--discover", action="store_true", help="Run selector discovery mode only")
    parser.add_argument("--skip-keyframe", action="store_true", help="Skip STEP 1 (keyframe generation)")
    parser.add_argument("--cdp-port", type=int, default=9222, help="Chrome CDP port (default: 9222)")
    args = parser.parse_args()

    global CDP_ENDPOINT
    CDP_ENDPOINT = f"http://127.0.0.1:{args.cdp_port}"

    output_dir = Path(args.output_dir) if args.output_dir else None
    automator = VeoAutomator(output_dir=output_dir)

    # Connect to Chrome
    if not await automator.connect():
        print("❌ ไม่สามารถเชื่อมต่อ Chrome ได้")
        print("   วิธีแก้: ปิด Chrome ทั้งหมด แล้วรัน:")
        print(f'   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port={args.cdp_port}')
        sys.exit(1)

    try:
        # Discovery mode
        if args.discover:
            await automator.navigate_to_flow()
            results = await automator.discover_selectors()
            print(json.dumps(results, indent=2, ensure_ascii=False))
            return

        # Get prompts
        prompts = None

        if args.prompts_json:
            # Load from file
            with open(args.prompts_json, "r", encoding="utf-8") as f:
                prompts = json.load(f)

        elif args.image:
            # Generate prompts using manual_veo.py
            print("🤖 Generating prompts from image via veo_gen engine...")
            from manual_veo import generate_prompts
            prompts = generate_prompts(args.image)
            if not prompts:
                print("❌ Failed to generate prompts")
                sys.exit(1)

        else:
            print("❌ ต้องระบุ --image หรือ --prompts-json")
            parser.print_help()
            sys.exit(1)

        # Run pipeline
        image_path = args.image or SCRIPT_DIR / "input_product.jpg"
        result = await automator.run_full_pipeline(
            image_path=str(image_path),
            prompts=prompts,
            skip_keyframe=args.skip_keyframe,
        )

        # Print result summary
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["success"] else 1)

    finally:
        await automator.close()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
