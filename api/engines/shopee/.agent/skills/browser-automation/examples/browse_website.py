#!/usr/bin/env python3
"""
Example: Basic Website Browsing
Demonstrates how to navigate to a website and interact with elements.
"""

from playwright.sync_api import sync_playwright

def browse_website():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to website
        print("Navigating to example.com...")
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Get page information
        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")
        
        # Extract text content
        heading = page.locator('h1').inner_text()
        print(f"Heading: {heading}")
        
        # Find and click a link
        links = page.locator('a').all()
        print(f"Found {len(links)} links on the page")
        
        # Take a screenshot
        page.screenshot(path='example_screenshot.png', full_page=True)
        print("Screenshot saved to example_screenshot.png")
        
        browser.close()
        print("Done!")

if __name__ == '__main__':
    browse_website()
