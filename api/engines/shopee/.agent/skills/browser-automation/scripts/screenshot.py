#!/usr/bin/env python3
"""
Screenshot Script - Capture screenshots of web pages
"""

import argparse
import json
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description='Take screenshots of web pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Full page screenshot
  python screenshot.py --url "https://example.com" --output "screenshot.png"

  # Element-specific screenshot
  python screenshot.py --url "https://example.com" --selector ".main-content" --output "content.png"

  # Mobile viewport screenshot
  python screenshot.py --url "https://example.com" --mobile --output "mobile.png"

  # Multiple viewports
  python screenshot.py --url "https://example.com" --viewports desktop,tablet,mobile --output-dir "./screenshots"
        '''
    )
    
    parser.add_argument('--url', required=True, help='URL to capture')
    parser.add_argument('--output', '-o', default='screenshot.png', help='Output file path')
    parser.add_argument('--output-dir', help='Output directory for multiple screenshots')
    parser.add_argument('--selector', help='CSS selector for specific element')
    parser.add_argument('--full-page', action='store_true', default=True, help='Capture full page')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--timeout', type=int, default=30000, help='Page load timeout in ms')
    parser.add_argument('--wait-for', help='CSS selector to wait for before screenshot')
    parser.add_argument('--wait-timeout', type=int, default=30000, help='Wait timeout in ms')
    parser.add_argument('--mobile', action='store_true', help='Use mobile viewport')
    parser.add_argument('--viewport-width', type=int, help='Custom viewport width')
    parser.add_argument('--viewport-height', type=int, help='Custom viewport height')
    parser.add_argument('--viewports', help='Comma-separated viewports: desktop,tablet,mobile')
    parser.add_argument('--user-agent', help='Custom user agent')
    parser.add_argument('--cookies', help='Path to cookies JSON file')
    parser.add_argument('--dark-mode', action='store_true', help='Enable dark mode')
    parser.add_argument('--format', choices=['png', 'jpeg', 'webp'], default='png', help='Image format')
    parser.add_argument('--quality', type=int, default=80, help='Image quality for jpeg/webp (1-100)')
    
    return parser.parse_args()

# Predefined viewport sizes
VIEWPORT_PRESETS = {
    'desktop': {'width': 1920, 'height': 1080},
    'laptop': {'width': 1366, 'height': 768},
    'tablet': {'width': 768, 'height': 1024},
    'mobile': {'width': 375, 'height': 812},
}

def take_screenshot(page, args, viewport_name=None, output_path=None):
    """Take a screenshot with the given parameters."""
    
    # Wait for specific element if provided
    if args.wait_for:
        page.wait_for_selector(args.wait_for, timeout=args.wait_timeout)
    
    # Determine output path
    if output_path is None:
        output_path = args.output
    
    # Add viewport name to filename if multiple viewports
    if viewport_name and args.output_dir:
        base_name = Path(args.output).stem
        output_path = str(Path(args.output_dir) / f"{base_name}_{viewport_name}.{args.format}")
    
    # Take screenshot
    screenshot_options = {
        'path': output_path,
        'type': args.format,
    }
    
    if args.format in ['jpeg', 'webp']:
        screenshot_options['quality'] = args.quality
    
    if args.full_page and not args.selector:
        screenshot_options['full_page'] = True
    
    if args.selector:
        element = page.locator(args.selector)
        element.screenshot(**screenshot_options)
        print(f"Element screenshot saved: {output_path}")
    else:
        page.screenshot(**screenshot_options)
        print(f"Page screenshot saved: {output_path}")
    
    return output_path

def main():
    args = parse_args()
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: Playwright not installed. Install with: pip install playwright && playwright install")
        sys.exit(1)
    
    # Create output directory if needed
    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine viewports to use
    viewports = []
    if args.viewports:
        for v in args.viewports.split(','):
            v = v.strip().lower()
            if v in VIEWPORT_PRESETS:
                viewports.append((v, VIEWPORT_PRESETS[v]))
    elif args.mobile:
        viewports = [('mobile', VIEWPORT_PRESETS['mobile'])]
    elif args.viewport_width and args.viewport_height:
        viewports = [('custom', {'width': args.viewport_width, 'height': args.viewport_height})]
    else:
        viewports = [('desktop', VIEWPORT_PRESETS['desktop'])]
    
    results = {
        'url': args.url,
        'success': False,
        'screenshots': [],
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            
            for viewport_name, viewport in viewports:
                context_options = {
                    'viewport': viewport
                }
                
                if args.user_agent:
                    context_options['user_agent'] = args.user_agent
                
                if args.dark_mode:
                    context_options['color_scheme'] = 'dark'
                
                context = browser.new_context(**context_options)
                
                # Load cookies if provided
                if args.cookies and Path(args.cookies).exists():
                    with open(args.cookies, 'r') as f:
                        cookies = json.load(f)
                        context.add_cookies(cookies)
                
                page = context.new_page()
                page.set_default_timeout(args.timeout)
                
                # Navigate to URL
                print(f"Navigating to: {args.url} (viewport: {viewport_name})")
                page.goto(args.url, wait_until='networkidle')
                
                # Take screenshot
                screenshot_path = take_screenshot(page, args, viewport_name)
                results['screenshots'].append({
                    'viewport': viewport_name,
                    'path': screenshot_path,
                    'dimensions': viewport
                })
                
                context.close()
            
            browser.close()
            results['success'] = True
            
    except Exception as e:
        results['error'] = str(e)
        print(f"Error: {e}")
        sys.exit(1)
    
    print(json.dumps(results, indent=2))
    return results

if __name__ == '__main__':
    main()
