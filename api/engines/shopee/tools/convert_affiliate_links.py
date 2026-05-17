#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopee Affiliate Link Converter
Automatically convert regular Shopee links to affiliate links using Playwright.
Enhanced with stealth mode to bypass anti-bot detection.
"""

import sys
import os
import io
import time
import json
import asyncio
import re
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Force UTF-8 on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
# Add engines root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent # Dashboard root
engines_dir = Path(__file__).resolve().parent.parent.parent # Engines root
sys.path.insert(0, str(engines_dir))

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError as e:
    print(f"[ERROR] Playwright not installed: {e}")
    print("Please run: pip install playwright && playwright install chromium")
    # Also log to a file for better debugging in dashboard
    try:
        with open("pipeline_error.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Playwright Import Error: {e}\n")
    except:
        pass
    sys.exit(1)

# Import stealth configuration from common
try:
    from common.stealth_config import (
        StealthStrategy,
        BrowserFingerprint,
        get_random_delay,
        get_typing_delay,
        get_retry_delay,
        is_likely_bot_detection_page,
        get_shopee_headers,
    )
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    # Fallback functions
    def get_random_delay(min_ms=100, max_ms=500):
        import random
        return random.uniform(min_ms, max_ms) / 1000
    def get_typing_delay():
        import random
        return random.uniform(0.05, 0.15)
    def get_retry_delay(attempt, base_delay=1.0, max_delay=60.0):
        import random
        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay + delay * random.uniform(-0.25, 0.25)


class StealthAffiliateConverter:
    """
    Enhanced affiliate link converter with stealth mode.
    Uses Playwright instead of Selenium for better anti-bot bypass.
    """
    
    def __init__(self, cdp_url: str = "http://localhost:9222", headless: bool = False):
        """
        Initialize the converter.
        
        Args:
            cdp_url: Chrome DevTools Protocol URL for connecting to existing Chrome
            headless: Run in headless mode (not recommended for stealth)
        """
        self.cdp_url = cdp_url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def connect(self) -> bool:
        """
        Connect to existing Chrome instance via CDP.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Try to connect to existing Chrome
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
                contexts = self.browser.contexts
                if contexts:
                    self.context = contexts[0]
                else:
                    self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                print("✅ Connected to existing Chrome via CDP")
            except Exception as e:
                print(f"⚠️ Could not connect to existing Chrome: {e}")
                print("   Trying to launch new browser with stealth mode...")
                
                # Launch new browser with stealth settings
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=self._get_stealth_args()
                )
                self.context = await self.browser.new_context(
                    **self._get_context_options()
                )
                self.page = await self.context.new_page()
                print("✅ Launched new browser with stealth mode")
            
            # Apply stealth measures
            await self._apply_stealth()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            return False
    
    def _get_stealth_args(self) -> List[str]:
        """Get Chrome arguments for stealth mode."""
        if STEALTH_AVAILABLE:
            return StealthStrategy.get_browser_args()
        else:
            return [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
    
    def _get_context_options(self) -> Dict[str, Any]:
        """Get browser context options."""
        if STEALTH_AVAILABLE:
            fingerprint = BrowserFingerprint.random()
            options = fingerprint.get_context_args()
            # Add Shopee specific headers
            options["extra_http_headers"] = get_shopee_headers(user_agent=options["user_agent"])
            return options
        else:
            import random
            return {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "locale": "th-TH",
                "timezone_id": "Asia/Bangkok",
                "extra_http_headers": {"X-Shopee-Language": "th"}
            }
    
    async def _apply_stealth(self) -> None:
        """Apply stealth measures to the page."""
        page = self.page
        if not page:
            return
            
        if STEALTH_AVAILABLE:
            stealth_script = StealthStrategy.get_init_script()
            await page.add_init_script(stealth_script)
            
            # Set additional headers on the page
            await page.set_extra_http_headers({"X-Shopee-Language": "th"})
            print("✅ Applied advanced stealth measures and Shopee headers")
        else:
            # Basic stealth
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            await page.set_extra_http_headers({"X-Shopee-Language": "th"})

    async def _human_like_interaction(self) -> None:
        """Perform subtle human-like interactions to avoid bot detection."""
        page = self.page
        if not page:
            return
            
        try:
            # Random scroll
            if random.random() < 0.3:
                scroll_y = random.randint(100, 300)
                await page.evaluate(f"window.scrollBy(0, {scroll_y})")
                await asyncio.sleep(get_random_delay(200, 500))
                await page.evaluate(f"window.scrollBy(0, -{scroll_y})")
            
            # Sublte mouse move (simulated)
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(get_random_delay(100, 300))
        except:
            pass

    async def _bezier_move(self, target_elem) -> None:
        """Simulate human-like mouse movement using Bezier curve approximation."""
        try:
            box = await target_elem.bounding_box()
            if not box: return
            
            # Start coordinates (random current mouse position)
            start_x = random.randint(100, 800)
            start_y = random.randint(100, 600)
            
            # Target with slight jitter
            import random
            target_x = box['x'] + (box['width'] / 2) + random.uniform(-box['width']*0.2, box['width']*0.2)
            target_y = box['y'] + (box['height'] / 2) + random.uniform(-box['height']*0.2, box['height']*0.2)
            
            steps = random.randint(10, 20)
            for i in range(steps):
                t = i / steps
                # ease out quad for realistic slow down near target
                ease_t = t * (2 - t)
                
                current_x = start_x + (target_x - start_x) * ease_t + random.uniform(-5, 5)
                current_y = start_y + (target_y - start_y) * ease_t + random.uniform(-5, 5)
                
                await self.page.mouse.move(current_x, current_y)
                import asyncio
                await asyncio.sleep(random.uniform(0.01, 0.04))
                
            # final precision move
            await self.page.mouse.move(target_x, target_y)
            await asyncio.sleep(get_random_delay(200, 500))
        except Exception as e:
            print(f"   ⚠️ Bezier move error: {e}")
    
    async def check_login_status(self) -> bool:
        """
        Check if logged in to Shopee Affiliate.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check if any existing page is already on shopee affiliate
            for page in self.context.pages:
                if "affiliate.shopee.co.th" in page.url.lower() and "login" not in page.url.lower():
                    print(f"✅ Found existing logged-in Shopee tab: {page.url}")
                    self.page = page
                    return True

            await self.page.goto("https://affiliate.shopee.co.th/dashboard", timeout=15000)
            await asyncio.sleep(2)
            
            # Check if redirected to login
            current_url = self.page.url.lower()
            if "login" in current_url:
                return False
            
            # Check for login-related elements
            try:
                await self.page.wait_for_selector("[class*='dashboard'], [class*='user'], [class*='profile']", timeout=5000)
                return True
            except:
                return False
                
        except Exception as e:
            print(f"⚠️ Error checking login status: {e}")
            return False
    
    async def wait_for_captcha(self, max_wait: int = 60) -> bool:
        """
        Wait for user to solve captcha if detected.
        
        Args:
            max_wait: Maximum wait time in seconds
            
        Returns:
            True if captcha solved, False if timeout
        """
        print("🔍 Checking for captcha verification...")
        
        # Create flag file in workspace data dir
        workspace_root = root_dir.parent
        flag_path = workspace_root / "data" / "status" / "CAPTCHA_REQUIRED.json"
        from common.utils import ensure_dir
        ensure_dir(flag_path.parent)
        with open(flag_path, "w", encoding="utf-8") as f:
            json.dump({
                "project": "shopee_affiliate",
                "step": "link_conversion",
                "url": self.page.url,
                "timestamp": datetime.now().isoformat()
            }, f)
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Check URL
            url = self.page.url.lower()
            if "verify" not in url and "captcha" not in url and "challenge" not in url:
                # Check page content
                try:
                    content = await self.page.content()
                    if not is_likely_bot_detection_page(content):
                        print("✅ Captcha verified / No captcha detected")
                        # Clear flag file
                        flag_path = project_root / "CAPTCHA_REQUIRED.json"
                        if flag_path.exists():
                            flag_path.unlink()
                        return True
                except:
                    pass
            
            print(f"   Waiting... ({int(max_wait - (time.time() - start_time))}s remaining)")
            await asyncio.sleep(3)
        
        print("⚠️ Captcha wait timeout")
        return False
    
    async def convert_links(self, links: List[str], affiliate_id: str) -> List[str]:
        """
        Convert regular Shopee links to affiliate links.
        
        Args:
            links: List of Shopee product URLs
            affiliate_id: Shopee affiliate ID
            
        Returns:
            List of converted affiliate links
        """
        if not links:
            print("⚠️ No links to convert")
            return []
        
        print(f"🔄 Starting link conversion for {len(links)} links...")
        
        # Navigate to affiliate portal
        print("🌐 Opening Shopee Affiliate portal...")
        try:
            await self.page.goto("https://affiliate.shopee.co.th/offer/custom_link", timeout=20000)
            await asyncio.sleep(3)
            
            # Check for captcha
            if not await self.wait_for_captcha():
                print("⚠️ Captcha required - please solve manually")
                # Save current state for later
                await self._save_session_state()
            
            # Check login status again
            if "login" in self.page.url.lower():
                print("⚠️ Not logged in to Shopee Affiliate!")
                
                # Create flag file in workspace data dir
                workspace_root = root_dir.parent
                flag_path = workspace_root / "data" / "status" / "CAPTCHA_REQUIRED.json"
                from common.utils import ensure_dir
                ensure_dir(flag_path.parent)
                with open(flag_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "project": "shopee_affiliate",
                        "step": "login_required",
                        "url": self.page.url,
                        "timestamp": datetime.now().isoformat()
                    }, f)
                
                print("Please login first at https://affiliate.shopee.co.th")
                return links  # Return original links as fallback
            
        except Exception as e:
            print(f"❌ Error navigating to affiliate portal: {e}")
            return links
        
        # Process links in batches
        # Adjusted batch_size to 2 based on Joe's insight to avoid field length/timeout issues
        batch_size = 2  # Process 2 links at a time
        affiliate_links = []
        
        for i in range(0, len(links), batch_size):
            batch = links[i:i+batch_size]
            print(f"\n📝 Processing batch {i//batch_size + 1}/{(len(links) + batch_size - 1)//batch_size}...")
            
            try:
                batch_results = await self._convert_batch(batch, affiliate_id)
                affiliate_links.extend(batch_results)
            except Exception as e:
                print(f"   ❌ Batch conversion error: {e}")
                # Fallback: use original links for this batch
                affiliate_links.extend(batch)
            
            # Random delay between batches
            if i + batch_size < len(links):
                delay = get_random_delay(2000, 5000)
                print(f"   ⏳ Waiting {delay:.1f}s before next batch...")
                await asyncio.sleep(delay)
        
        print(f"\n✅ Conversion complete! {len(affiliate_links)}/{len(links)} links converted")
        return affiliate_links
    
    async def _convert_batch(self, links: List[str], affiliate_id: str) -> List[str]:
        """
        Convert a batch of links.
        
        Args:
            links: List of links to convert
            affiliate_id: Affiliate ID
            
        Returns:
            List of converted links
        """
        # Find the input textarea
        try:
            textarea = await self.page.wait_for_selector("textarea", timeout=10000)
        except Exception as e:
            print(f"   ⚠️ Could not find textarea: {e}")
            return links
        
        # Clear and input links
        await self._human_like_interaction()
        await textarea.click()
        await asyncio.sleep(get_random_delay(300, 600))
        
        # Clear existing content
        await self.page.keyboard.press("Control+a")
        await asyncio.sleep(get_random_delay(100, 300))
        await self.page.keyboard.press("Backspace")
        await asyncio.sleep(get_random_delay(200, 400))
        
        # Type links with human-like delay
        print(f"   ⌨️ Typing {len(links)} links...")
        batch_input = "\n".join(links)
        
        # Human-like insertion: Focus, simulate paste using insert_text or clipboard
        await textarea.focus()
        await asyncio.sleep(get_random_delay(100, 300))
        
        # Simulate Paste instead of fast fill which triggers Anti-bot
        try:
            # We try executing a clipboard write first
            escaped_input = batch_input.replace('\n', '\\n')
            await self.page.evaluate(f"navigator.clipboard.writeText(`{escaped_input}`)")
            await textarea.press("Control+v")
        except Exception:
            # Fallback to insert_text if clipboard permissions fail
            await self.page.keyboard.insert_text(batch_input)
            
        # Trigger input events manually just in case React needs it
        await textarea.press("Space")
        await textarea.press("Backspace")
        
        await asyncio.sleep(get_random_delay(400, 1000))
        
        # Find and click convert button
        convert_button = None
        button_selectors = [
            "button:has-text('เอา ลิงก์')",
            "button:has-text('Obtain')",
            "button:has-text('ลิงก์')",
            "button.ant-btn-primary",
            "button[type='submit']",
        ]
        
        for selector in button_selectors:
            try:
                convert_button = await self.page.query_selector(selector)
                if convert_button:
                    break
            except:
                continue
        
        if convert_button:
            # Simulate human hesitating/hovering before clicking
            await self._bezier_move(convert_button)
            await convert_button.hover()
            import random
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            await convert_button.click(delay=int(get_random_delay(50, 150)))
            print(f"   ✅ Clicked convert button")
        else:
            print(f"   ⚠️ Convert button not found")
            return links
        
        # Wait for results
        wait_time = get_random_delay(3000, 5000)
        await asyncio.sleep(wait_time)
        
        # Check for captcha after clicking
        if await self._check_for_captcha():
            print("   ⚠️ Captcha detected after clicking!")
            await self.wait_for_captcha()
        
        # Extract results from page
        results = await self._extract_affiliate_links()
        
        # Close any modals that might be blocking the next batch
        try:
            # Look for close button in modal (X or 'ปิด')
            close_buttons = await self.page.query_selector_all(".ant-modal-close, button:has-text('ปิด'), .ant-modal-close-x")
            for btn in close_buttons:
                if await btn.is_visible():
                    await btn.click()
                    print("   ✅ Closed modal")
                    await asyncio.sleep(1)
        except:
            pass
            
        return results if results else links
    
    async def _extract_affiliate_links(self) -> List[str]:
        """Extract affiliate links from the result page."""
        affiliate_links = []
        
        try:
            # Strategy 1: Look for result items
            result_items = await self.page.query_selector_all("[class*='result-item'], [class*='link-result'], .ant-table-row")
            
            for item in result_items:
                text = await item.text_content()
                # Also look for the "Copy" buttons or input fields in the table
                if "shope.ee" in text or "s.shopee.co.th" in text:
                    match = re.search(r'https://(?:shope\.ee|s\.shopee\.co\.th)/[a-zA-Z0-9]+', text)
                    if match:
                        affiliate_links.append(match.group(0))
            
            # If still nothing, look for all inputs/textareas that might contain the link
            if not affiliate_links:
                elements = await self.page.query_selector_all("input, textarea")
                for el in elements:
                    val = await el.input_value()
                    if "shope.ee" in val or "s.shopee.co.th" in val:
                        match = re.search(r'https://(?:shope\.ee|s\.shopee\.co\.th)/[a-zA-Z0-9]+', val)
                        if match and match.group(0) not in affiliate_links:
                            affiliate_links.append(match.group(0))
            
            # Strategy 2: Scan entire page for short links
            if not affiliate_links:
                page_text = await self.page.evaluate("document.body.innerText")
                found_links = re.findall(r'https://(?:shope\.ee|s\.shopee\.co\.th)/[a-zA-Z0-9]+', page_text)
                
                seen = set()
                for link in found_links:
                    if link not in seen:
                        seen.add(link)
                        affiliate_links.append(link)
            
            # Strategy 3: Check input field for echoed results
            if not affiliate_links:
                try:
                    textarea = await self.page.query_selector("textarea")
                    if textarea:
                        value = await textarea.input_value()
                        found_links = re.findall(r'https://(?:shope\.ee|s\.shopee\.co\.th)/[a-zA-Z0-9]+', value)
                        for link in found_links:
                            if link not in seen:
                                seen.add(link)
                                affiliate_links.append(link)
                except:
                    pass
                    
        except Exception as e:
            print(f"   ⚠️ Error extracting links: {e}")
        
        return affiliate_links
    
    async def _check_for_captcha(self) -> bool:
        """Check if captcha or verification is required."""
        try:
            url = self.page.url.lower()
            if "verify" in url or "captcha" in url or "challenge" in url:
                return True
            
            content = await self.page.content()
            return is_likely_bot_detection_page(content)
        except:
            return False
    
    async def _save_session_state(self) -> None:
        """Save current session state for later recovery."""
        try:
            cookies = await self.context.cookies()
            storage_state = {
                "cookies": cookies,
                "url": self.page.url,
                "timestamp": datetime.now().isoformat()
            }
            
            workspace_root = root_dir.parent
            session_file = workspace_root / "data" / "status" / "shopee_session_state.json"
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, 'w') as f:
                json.dump(storage_state, f, indent=2)
            
            print(f"   💾 Session state saved to {session_file}")
        except Exception as e:
            print(f"   ⚠️ Could not save session: {e}")
    
    async def close(self) -> None:
        """Close the browser and cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("✅ Browser closed")
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


# =============================================================================
# FALLBACK: Simple URL-based conversion (no browser needed)
# =============================================================================

def convert_links_simple(links: List[str], affiliate_id: str) -> List[str]:
    """
    Simple URL-based conversion without browser.
    Uses URL parameter injection instead of affiliate portal.
    
    Args:
        links: List of Shopee product URLs
        affiliate_id: Shopee affiliate ID
        
    Returns:
        List of converted links (may not be true affiliate links)
    """
    converted = []
    
    for url in links:
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Add affiliate ID
            query_params['af_id'] = [affiliate_id]
            
            # Try to convert to short link format
            path = parsed.path
            item_id = None
            
            # Extract item ID from path
            if '/product/' in path:
                parts = path.strip('/').split('/')
                if len(parts) >= 3:
                    item_id = parts[-1]
            elif 'product-i.' in path:
                match = re.search(r'product-i\.(\d+)\.(\d+)', path)
                if match:
                    item_id = match.group(2)
            
            if item_id:
                # Use Shopee's universal link format
                new_url = f"https://shopee.co.th/universal-link/{item_id}?af_id={affiliate_id}"
            else:
                # Fallback: add as query parameter
                new_query = urlencode(query_params, doseq=True)
                new_url = urlunparse(parsed._replace(query=new_query))
            
            converted.append(new_url)
            
        except Exception as e:
            print(f"   ⚠️ Error converting {url}: {e}")
            converted.append(url)  # Use original on error
    
    return converted


# =============================================================================
# MAIN CONVERSION FUNCTION
# =============================================================================

async def convert_links_async(
    links: List[str],
    affiliate_id: str = None,
    use_browser: bool = True,
    cdp_url: str = "http://localhost:9222",
    headless: bool = False
) -> List[str]:
    """
    Convert Shopee links to affiliate links.
    
    Args:
        links: List of Shopee product URLs
        affiliate_id: Shopee affiliate ID (from env if not provided)
        use_browser: Use browser automation (True) or simple URL conversion (False)
        cdp_url: Chrome CDP URL for browser connection
        headless: Run browser in headless mode
        
    Returns:
        List of affiliate links
    """
    # Get affiliate ID from environment if not provided
    if not affiliate_id:
        affiliate_id = os.getenv("SHOPEE_AFFILIATE_ID", "")
        if not affiliate_id:
            # Try to get from .env file
            env_file = project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("SHOPEE_AFFILIATE_ID"):
                            affiliate_id = line.split("=")[1].strip().strip('"')
                            break
    
    if not affiliate_id:
        print("⚠️ No SHOPEE_AFFILIATE_ID found, using placeholder")
        affiliate_id = "YOUR_AFFILIATE_ID"
    
    print(f"  Using Affiliate ID: {affiliate_id}")
    
    if use_browser:
        # Use browser-based conversion with stealth mode
        try:
            async with StealthAffiliateConverter(cdp_url=cdp_url, headless=headless) as converter:
                # Check login status
                if not await converter.check_login_status():
                    print("⚠️ Not logged in! Please login to Shopee Affiliate first.")
                    print("   Falling back to simple URL conversion...")
                    return convert_links_simple(links, affiliate_id)
                
                return await converter.convert_links(links, affiliate_id)
                
        except Exception as e:
            print(f"❌ Browser conversion failed: {e}")
            print("   Falling back to simple URL conversion...")
            return convert_links_simple(links, affiliate_id)
    else:
        # Use simple URL-based conversion
        return convert_links_simple(links, affiliate_id)


def convert_links(
    links: List[str],
    affiliate_id: str = None,
    use_browser: bool = True,
    cdp_url: str = "http://localhost:9222",
    headless: bool = False
) -> List[str]:
    """
    Synchronous wrapper for convert_links_async.
    """
    return asyncio.run(convert_links_async(
        links=links,
        affiliate_id=affiliate_id,
        use_browser=use_browser,
        cdp_url=cdp_url,
        headless=headless
    ))


# =============================================================================
# CLI MAIN
# =============================================================================

def main():
    """Main function to convert links from file."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Shopee links to affiliate links")
    parser.add_argument("--links", nargs="+", help="List of links to convert")
    parser.add_argument("--file", type=str, help="File containing links (one per line)")
    parser.add_argument("--output", type=str, help="Output file for converted links")
    parser.add_argument("--no-browser", action="store_true", help="Use simple URL conversion (no browser)")
    parser.add_argument("--headful", action="store_true", help="Run in headful mode (visible browser)")
    parser.add_argument("--cdp-url", type=str, default="http://localhost:9222", help="Chrome CDP URL")
    
    args = parser.parse_args()
    
    # Get links from file or arguments
    links = []
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"📂 Loaded {len(links)} links from {args.file}")
        else:
            print(f"❌ File not found: {args.file}")
            return
    elif args.links:
        links = args.links
    else:
        # Try default file
        default_file = project_root / "shopee_affiliate" / "data" / "09_ReadyToPost" / datetime.now().strftime("%Y-%m-%d") / "_links_to_convert.txt"
        if default_file.exists():
            with open(default_file, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"📂 Loaded {len(links)} links from {default_file}")
        else:
            print("❌ No links provided and no default file found")
            return
    
    if not links:
        print("⚠️ No links to convert")
        return
    
    print(f"🔄 Starting link conversion for {len(links)} links...")
    
    # Convert links
    headless = not args.headful
    affiliate_links = convert_links(
        links,
        use_browser=not args.no_browser,
        cdp_url=args.cdp_url,
        headless=headless
    )
    
    if not affiliate_links:
        print("❌ No links were converted")
        return
    
    # Save results
    output_file = args.output
    if not output_file:
        workspace_root = root_dir.parent
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = workspace_root / "data" / "content" / "shopee" / "converted" / date_str
        output_file = output_dir / "_converted_affiliate_links.txt"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for link in affiliate_links:
            f.write(f"{link}\n")
    
    print(f"\n✅ Conversion complete!")
    print(f"📁 Saved to: {output_path}")
    print(f"\n📋 Converted links:")
    for i, link in enumerate(affiliate_links, 1):
        print(f"  {i}. {link}")


if __name__ == "__main__":
    main()
