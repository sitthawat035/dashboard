#!/usr/bin/env python3
"""
Form Filling Script - Automatically fill and submit web forms
"""

import argparse
import json
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description='Fill and submit web forms automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Fill a login form
  python form_fill.py --url "https://example.com/login" \\
    --fields '{"username": "user@example.com", "password": "secret"}' \\
    --submit "button[type=submit]"

  # Fill form from JSON file
  python form_fill.py --url "https://example.com/register" \\
    --fields-file "form_data.json" --submit ".submit-btn"

  # Fill and wait for result
  python form_fill.py --url "https://example.com/search" \\
    --fields '{"q": "search term"}' --submit "button.search" \\
    --wait-for ".results"
        '''
    )
    
    parser.add_argument('--url', required=True, help='URL of the form page')
    parser.add_argument('--fields', help='JSON string of field name:value pairs')
    parser.add_argument('--fields-file', help='Path to JSON file with field data')
    parser.add_argument('--submit', help='CSS selector for submit button')
    parser.add_argument('--wait-for', help='CSS selector to wait for after submission')
    parser.add_argument('--wait-timeout', type=int, default=30000, help='Wait timeout in ms')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--timeout', type=int, default=30000, help='Page load timeout in ms')
    parser.add_argument('--screenshot', help='Take screenshot after submission')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--cookies', help='Path to cookies JSON file')
    parser.add_argument('--user-agent', help='Custom user agent')
    parser.add_argument('--delay', type=int, default=100, help='Delay between field fills (ms)')
    parser.add_argument('--clear-first', action='store_true', help='Clear fields before filling')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: Playwright not installed. Install with: pip install playwright && playwright install")
        sys.exit(1)
    
    # Parse field data
    fields = {}
    if args.fields:
        try:
            fields = json.loads(args.fields)
        except json.JSONDecodeError as e:
            print(f"Error parsing fields JSON: {e}")
            sys.exit(1)
    elif args.fields_file:
        with open(args.fields_file, 'r', encoding='utf-8') as f:
            fields = json.load(f)
    else:
        print("Error: No field data provided. Use --fields or --fields-file")
        sys.exit(1)
    
    results = {
        'url': args.url,
        'fields_filled': 0,
        'success': False,
        'final_url': None,
        'screenshot': None,
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            
            context_options = {}
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
            
            # Navigate to form page
            print(f"Navigating to: {args.url}")
            page.goto(args.url, wait_until='networkidle')
            
            # Fill each field
            for field_name, field_value in fields.items():
                try:
                    # Try different selector strategies
                    selectors = [
                        f'input[name="{field_name}"]',
                        f'#{field_name}',
                        f'[name="{field_name}"]',
                        f'textarea[name="{field_name}"]',
                        f'select[name="{field_name}"]',
                    ]
                    
                    filled = False
                    for selector in selectors:
                        element = page.locator(selector)
                        if element.count() > 0:
                            if args.clear_first:
                                element.first.clear()
                            
                            # Handle different input types
                            tag = element.first.evaluate('el => el.tagName.toLowerCase()')
                            if tag == 'select':
                                element.first.select_option(label=str(field_value))
                            elif element.first.get_attribute('type') == 'checkbox':
                                if field_value:
                                    element.first.check()
                                else:
                                    element.first.uncheck()
                            elif element.first.get_attribute('type') == 'radio':
                                element.first.check()
                            else:
                                element.first.fill(str(field_value))
                            
                            print(f"Filled field '{field_name}' with '{field_value}'")
                            results['fields_filled'] += 1
                            filled = True
                            break
                    
                    if not filled:
                        print(f"Warning: Could not find field '{field_name}'")
                    
                    # Delay between fills
                    if args.delay > 0:
                        page.wait_for_timeout(args.delay)
                        
                except Exception as e:
                    print(f"Error filling field '{field_name}': {e}")
            
            # Submit form
            if args.submit:
                print(f"Clicking submit button: {args.submit}")
                page.click(args.submit)
                page.wait_for_load_state('networkidle')
            
            # Wait for specific element
            if args.wait_for:
                print(f"Waiting for element: {args.wait_for}")
                page.wait_for_selector(args.wait_for, timeout=args.wait_timeout)
            
            # Take screenshot
            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)
                results['screenshot'] = args.screenshot
                print(f"Screenshot saved: {args.screenshot}")
            
            # Get final state
            results['final_url'] = page.url
            results['title'] = page.title()
            results['success'] = True
            
            browser.close()
            
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
