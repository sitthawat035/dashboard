#!/usr/bin/env python3
"""
Web Browsing Script - Navigate and interact with websites
"""

import argparse
import json
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description='Browse websites and interact with web pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Navigate and take screenshot
  python browse.py --url "https://example.com" --screenshot

  # Click a button
  python browse.py --url "https://example.com" --click "button.submit"

  # Extract text from elements
  python browse.py --url "https://example.com" --extract "h1, .content"

  # Wait for element and click
  python browse.py --url "https://example.com" --wait-for ".result" --click ".next"
        '''
    )
    
    parser.add_argument('--url', required=True, help='URL to navigate to')
    parser.add_argument('--screenshot', action='store_true', help='Take a screenshot')
    parser.add_argument('--screenshot-path', default='screenshot.png', help='Screenshot output path')
    parser.add_argument('--click', help='CSS selector for element to click')
    parser.add_argument('--wait-for', help='CSS selector to wait for before proceeding')
    parser.add_argument('--wait-timeout', type=int, default=30000, help='Wait timeout in ms')
    parser.add_argument('--extract', help='CSS selectors to extract text from (comma-separated)')
    parser.add_argument('--output', '-o', help='Output file for extracted data (JSON)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--timeout', type=int, default=30000, help='Page load timeout in ms')
    parser.add_argument('--viewport-width', type=int, default=1280, help='Viewport width')
    parser.add_argument('--viewport-height', type=int, default=720, help='Viewport height')
    parser.add_argument('--user-agent', help='Custom user agent')
    parser.add_argument('--cookies', help='Path to cookies JSON file')
    parser.add_argument('--wait-after-load', type=int, default=0, help='Additional wait time after page load (ms)')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: Playwright not installed. Install with: pip install playwright && playwright install")
        sys.exit(1)
    
    results = {
        'url': args.url,
        'success': False,
        'extracted': {},
        'screenshot': None,
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            
            context_options = {
                'viewport': {'width': args.viewport_width, 'height': args.viewport_height}
            }
            if args.user_agent:
                context_options['user_agent'] = args.user_agent
            
            context = browser.new_context(**context_options)
            
            # Load cookies if provided
            if args.cookies and Path(args.cookies).exists():
                with open(args.cookies, 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
            
            page = context.new_page()
            page.set_default_timeout(args.timeout)
            
            # Navigate to URL
            print(f"Navigating to: {args.url}")
            page.goto(args.url, wait_until='networkidle')
            
            # Additional wait if specified
            if args.wait_after_load > 0:
                page.wait_for_timeout(args.wait_after_load)
            
            # Wait for specific element
            if args.wait_for:
                print(f"Waiting for element: {args.wait_for}")
                page.wait_for_selector(args.wait_for, timeout=args.wait_timeout)
            
            # Take screenshot
            if args.screenshot:
                print(f"Taking screenshot: {args.screenshot_path}")
                page.screenshot(path=args.screenshot_path, full_page=True)
                results['screenshot'] = args.screenshot_path
            
            # Click element
            if args.click:
                print(f"Clicking element: {args.click}")
                page.click(args.click)
                page.wait_for_load_state('networkidle')
            
            # Extract content
            if args.extract:
                selectors = [s.strip() for s in args.extract.split(',')]
                for selector in selectors:
                    elements = page.locator(selector).all()
                    texts = [el.inner_text() for el in elements]
                    results['extracted'][selector] = texts
                    print(f"Extracted from '{selector}': {len(texts)} elements")
            
            # Get page info
            results['title'] = page.title()
            results['url_final'] = page.url
            
            browser.close()
            results['success'] = True
            
    except Exception as e:
        results['error'] = str(e)
        print(f"Error: {e}")
        sys.exit(1)
    
    # Output results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {args.output}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results

if __name__ == '__main__':
    main()
