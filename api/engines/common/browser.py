"""
Browser automation utilities using Playwright with Chrome CDP.
"""

import asyncio
import logging
import random
import math
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .utils import print_error, print_success, print_warning, print_info

# Import stealth configuration
try:
    from .stealth_config import (
        StealthStrategy,
        BrowserFingerprint,
        get_random_delay,
        get_typing_delay,
        get_scroll_distance,
        is_likely_bot_detection_page,
    )
except ImportError:
    # Fallback if stealth_config not available
    StealthStrategy = None
    BrowserFingerprint = None
    def get_random_delay(min_ms=100, max_ms=500):
        return random.uniform(min_ms, max_ms) / 1000
    def get_typing_delay():
        return random.uniform(0.05, 0.15)
    def get_scroll_distance():
        return random.randint(100, 400)
    def is_likely_bot_detection_page(html_content):
        return False


class BrowserManager:
    """
    Manage browser automation with anti-bot measures and CDP connection.
    Now includes advanced stealth measures for bypassing detection.
    """
    
    def __init__(
        self,
        cdp_url: str = "http://localhost:9222",
        headless: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize BrowserManager.
        
        Args:
            cdp_url: Chrome DevTools Protocol URL
            headless: Run in headless mode
            logger: Logger instance
        """
        self.cdp_url = cdp_url
        self.headless = headless
        self.logger = logger or logging.getLogger(__name__)
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def connect(self) -> bool:
        """
        Connect to existing Chrome instance via CDP.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.playwright:
                return True
                
            self.playwright = await async_playwright().start()
            
            # Connect to existing Chrome instance
            self.logger.info(f"Connecting to Chrome at {self.cdp_url}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # Get default context or create new one
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context()
            
            # Create new page
            self.page = await self.context.new_page()
            
            # Apply stealth measures
            await self._apply_stealth(self.page)
            
            print_success(f"Connected to Chrome at {self.cdp_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Chrome: {e}")
            print_error(f"Chrome connection failed: {e}")
            return False
    
    async def _apply_stealth(self, page: Page) -> None:
        """
        Apply advanced anti-bot detection measures.
        
        Args:
            page: Playwright page instance
        """
        # Use stealth strategy if available
        if StealthStrategy:
            stealth_script = StealthStrategy.get_init_script()
            await page.add_init_script(stealth_script)
            self.logger.info("Applied advanced stealth measures")
        else:
            # Fallback to basic stealth measures
            await self._apply_basic_stealth(page)
    
    async def _apply_basic_stealth(self, page: Page) -> None:
        """
        Apply basic stealth measures (fallback).
        
        Args:
            page: Playwright page instance
        """
        # Override navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Override plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override languages
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['th-TH', 'th', 'en-US', 'en']
            });
        """)
    
    async def human_like_scroll(self) -> None:
        """
        Perform human-like scrolling to avoid detection.
        """
        if not self.page:
            return
            
        # Get random scroll distance
        distance = get_scroll_distance() if get_scroll_distance else random.randint(100, 400)
        
        # Scroll with random delay
        await self.page.evaluate(f"window.scrollBy(0, {distance})")
        await asyncio.sleep(get_random_delay(500, 1500))

    def _calculate_bezier_curve(self, start: Tuple[float, float], end: Tuple[float, float], control: Tuple[float, float], steps: int) -> List[Tuple[float, float]]:
        """Calculate points on a quadratic Bezier curve."""
        points = []
        for i in range(steps):
            t = i / max(1, steps - 1)
            # Quadratic Bezier formula: P = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            x = (1 - t)**2 * start[0] + 2 * (1 - t) * t * control[0] + t**2 * end[0]
            y = (1 - t)**2 * start[1] + 2 * (1 - t) * t * control[1] + t**2 * end[1]
            points.append((x, y))
        return points

    async def human_like_mouse_move(self) -> None:
        """
        Perform random human-like mouse movements using Bezier curves.
        """
        if not self.page:
            return
            
        try:
            width = await self.page.evaluate("window.innerWidth")
            height = await self.page.evaluate("window.innerHeight")
            
            # Current mouse position is generally tracked by playwright internally but we'll assume a random starting point
            # if we don't have a known position. We'll simulate moving between a few random points.
            
            current_x = random.randint(10, max(10, width - 10))
            current_y = random.randint(10, max(10, height - 10))
            await self.page.mouse.move(current_x, current_y)
            
            for _ in range(random.randint(1, 4)):
                target_x = random.randint(10, max(10, width - 10))
                target_y = random.randint(10, max(10, height - 10))
                
                # Create a control point off to the side to make a curve
                dx = target_x - current_x
                dy = target_y - current_y
                distance = math.hypot(dx, dy)
                
                # Control point perpendicular deviation
                deviation = min(distance * 0.3, random.uniform(50, 200)) * random.choice([-1, 1])
                angle = math.atan2(dy, dx) + (math.pi / 2 if deviation > 0 else -math.pi / 2)
                control_x = current_x + dx/2 + math.cos(angle) * abs(deviation)
                control_y = current_y + dy/2 + math.sin(angle) * abs(deviation)
                
                # Generate points along curve
                steps = max(5, int(distance / random.randint(15, 30)))
                points = self._calculate_bezier_curve((current_x, current_y), (target_x, target_y), (control_x, control_y), steps)
                
                # Move through points with slight jitter and varying speed
                for i, (px, py) in enumerate(points):
                    # Add tiny jitter (1-2 pixels)
                    jx = px + random.uniform(-1, 1)
                    jy = py + random.uniform(-1, 1)
                    
                    # Ease out effect: delay gets slightly longer towards the end
                    progress = i / max(1, len(points) - 1)
                    delay_factor = 1.0 + (progress * 1.5)
                    step_delay = random.uniform(5, 15) * delay_factor / 1000.0
                    
                    await self.page.mouse.move(jx, jy)
                    await asyncio.sleep(step_delay)
                
                current_x, current_y = target_x, target_y
                
                # Pause between distinct movement segments
                await asyncio.sleep(get_random_delay(100, 300))
        except Exception as e:
            self.logger.warning(f"Mouse move failed: {e}")
    
    async def _human_like_type(self, page: Page, selector: str, text: str) -> None:
        """
        Perform human-like typing to avoid detection.
        
        Args:
            page: Playwright page instance
            selector: Element selector
            text: Text to type
        """
        if not page:
            return
            
        element = await page.query_selector(selector)
        if element:
            await element.click()
            await asyncio.sleep(get_random_delay(100, 300) / 1000)
            
            # Type character by character with random delays
            for char in text:
                await element.type(char, delay=get_typing_delay() * 1000)
    
    async def _check_for_captcha(self, page: Page) -> bool:
        """
        Check if page has captcha or bot detection.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if captcha/detection detected
        """
        if not page:
            return False
            
        try:
            # Check URL for verification
            url = page.url.lower()
            if "verify" in url or "captcha" in url or "challenge" in url:
                return True
            
            # Check page content
            content = await page.content()
            if is_likely_bot_detection_page(content):
                return True
                
        except Exception as e:
            self.logger.warning(f"Error checking for captcha: {e}")
            
        return False
    
    async def goto(
        self,
        url: str,
        wait_until: str = "networkidle",
        timeout: int = 30000
    ) -> bool:
        """
        Navigate to URL.
        
        Args:
            url: Target URL
            wait_until: Wait condition (load, domcontentloaded, networkidle)
            timeout: Timeout in milliseconds
            
        Returns:
            True if successful
        """
        if not self.page:
            self.logger.error("Page not initialized")
            return False
        
        try:
            self.logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            print_success(f"Navigated to {url}")
            return True
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            print_error(f"Failed to navigate: {e}")
            return False
    
    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 10000,
        state: str = "visible"
    ) -> bool:
        """
        Wait for element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            state: Element state (visible, attached, hidden)
            
        Returns:
            True if element found
        """
        if not self.page:
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception as e:
            self.logger.warning(f"Element not found: {selector} - {e}")
            return False
    
    async def get_text(self, selector: str) -> Optional[str]:
        """
        Get text content from element.
        
        Args:
            selector: CSS selector
            
        Returns:
            Text content or None
        """
        if not self.page:
            return None
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception as e:
            self.logger.warning(f"Failed to get text: {e}")
        
        return None
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get attribute value from element.
        
        Args:
            selector: CSS selector
            attribute: Attribute name
            
        Returns:
            Attribute value or None
        """
        if not self.page:
            return None
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
        except Exception as e:
            self.logger.warning(f"Failed to get attribute: {e}")
        
        return None
    
    async def screenshot(
        self,
        path: str | Path,
        full_page: bool = False
    ) -> bool:
        """
        Take screenshot.
        
        Args:
            path: Output file path
            full_page: Capture full page
            
        Returns:
            True if successful
        """
        if not self.page:
            return False
        
        try:
            await self.page.screenshot(path=str(path), full_page=full_page)
            self.logger.info(f"Screenshot saved to {path}")
            return True
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return False
    
    async def scroll_down(self, distance: int = 500, delay: float = 0.5) -> None:
        """
        Scroll down the page.
        
        Args:
            distance: Scroll distance in pixels
            delay: Delay between scrolls in seconds
        """
        if not self.page:
            return
        
        await self.page.evaluate(f"window.scrollBy(0, {distance})")
        await asyncio.sleep(delay)
    
    async def scroll_to_bottom(self, max_scrolls: int = 10, delay: float = 1.0) -> None:
        """
        Scroll to bottom of page.
        
        Args:
            max_scrolls: Maximum number of scroll attempts
            delay: Delay between scrolls
        """
        if not self.page:
            return
        
        for _ in range(max_scrolls):
            previous_height = await self.page.evaluate("document.body.scrollHeight")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay)
            new_height = await self.page.evaluate("document.body.scrollHeight")
            
            if new_height == previous_height:
                break
    
    async def close(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            
            # Don't close context/browser if connected via CDP
            # as it would close the user's Chrome instance
            
            if self.playwright:
                await self.playwright.stop()
            
            print_info("Browser connection closed")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


async def create_browser_manager(
    cdp_url: str = "http://localhost:9222",
    logger: Optional[logging.Logger] = None
) -> BrowserManager:
    """
    Create and connect BrowserManager instance.
    
    Args:
        cdp_url: Chrome DevTools Protocol URL
        logger: Logger instance
        
    Returns:
        Connected BrowserManager
    """
    manager = BrowserManager(cdp_url=cdp_url, logger=logger)
    await manager.connect()
    return manager
