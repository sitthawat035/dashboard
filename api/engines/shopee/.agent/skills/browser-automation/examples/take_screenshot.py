#!/usr/bin/env python3
"""
Example: Screenshot Capture
Demonstrates how to capture screenshots of web pages.
"""

from playwright.sync_api import sync_playwright

def take_full_page_screenshot():
    """Take a full page screenshot."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Full page screenshot
        page.screenshot(path='full_page.png', full_page=True)
        print("Full page screenshot saved to full_page.png")
        
        browser.close()

def take_element_screenshot():
    """Take a screenshot of a specific element."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Screenshot of specific element
        element = page.locator('h1')
        element.screenshot(path='heading.png')
        print("Element screenshot saved to heading.png")
        
        browser.close()

def take_multiple_viewport_screenshots():
    """Take screenshots at different viewport sizes."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        viewports = [
            ('desktop', {'width': 1920, 'height': 1080}),
            ('tablet', {'width': 768, 'height': 1024}),
            ('mobile', {'width': 375, 'height': 812}),
        ]
        
        for name, viewport in viewports:
            context = browser.new_context(viewport=viewport)
            page = context.new_page()
            
            page.goto('https://example.com')
            page.wait_for_load_state('networkidle')
            
            page.screenshot(path=f'screenshot_{name}.png', full_page=True)
            print(f"Screenshot saved to screenshot_{name}.png")
            
            context.close()
        
        browser.close()

def take_dark_mode_screenshot():
    """Take a screenshot with dark mode enabled."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            color_scheme='dark'
        )
        page = context.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        page.screenshot(path='dark_mode.png', full_page=True)
        print("Dark mode screenshot saved to dark_mode.png")
        
        browser.close()

if __name__ == '__main__':
    # Run examples
    take_full_page_screenshot()
    take_element_screenshot()
    take_multiple_viewport_screenshots()
    take_dark_mode_screenshot()
