#!/usr/bin/env python3
"""
Web Scraping Script - Extract data from web pages
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any

def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract data from web pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract all links
  python scrape.py --url "https://example.com" --links --output "links.json"

  # Extract specific elements
  python scrape.py --url "https://example.com" \\
    --selectors '{"titles": "h2", "prices": ".price"}' \\
    --output "data.json"

  # Extract tables
  python scrape.py --url "https://example.com/data" \\
    --tables --output "tables.json"

  # Extract with pagination
  python scrape.py --url "https://example.com/products" \\
    --selectors '{"name": ".product-name", "price": ".product-price"}' \\
    --next ".pagination .next" --max-pages 5 --output "products.json"
        '''
    )
    
    parser.add_argument('--url', required=True, help='URL to scrape')
    parser.add_argument('--selectors', help='JSON string of name:selector pairs')
    parser.add_argument('--selectors-file', help='Path to JSON file with selectors')
    parser.add_argument('--links', action='store_true', help='Extract all links')
    parser.add_argument('--images', action='store_true', help='Extract all images')
    parser.add_argument('--tables', action='store_true', help='Extract all tables')
    parser.add_argument('--text', action='store_true', help='Extract page text')
    parser.add_argument('--output', '-o', help='Output file (JSON)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--timeout', type=int, default=30000, help='Page load timeout in ms')
    parser.add_argument('--wait-for', help='CSS selector to wait for before scraping')
    parser.add_argument('--wait-timeout', type=int, default=30000, help='Wait timeout in ms')
    parser.add_argument('--next', help='CSS selector for next page button')
    parser.add_argument('--max-pages', type=int, default=1, help='Maximum pages to scrape')
    parser.add_argument('--cookies', help='Path to cookies JSON file')
    parser.add_argument('--user-agent', help='Custom user agent')
    parser.add_argument('--delay', type=int, default=500, help='Delay between page navigations (ms)')
    parser.add_argument('--attribute', help='Extract specific attribute instead of text')
    parser.add_argument('--clean-text', action='store_true', help='Clean extracted text')
    
    return parser.parse_args()

def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_links(page) -> List[Dict[str, str]]:
    """Extract all links from the page."""
    links = []
    elements = page.locator('a[href]').all()
    for el in elements:
        href = el.get_attribute('href')
        text = el.inner_text()
        links.append({
            'href': href,
            'text': clean_text(text) if text else ''
        })
    return links

def extract_images(page) -> List[Dict[str, str]]:
    """Extract all images from the page."""
    images = []
    elements = page.locator('img').all()
    for el in elements:
        src = el.get_attribute('src')
        alt = el.get_attribute('alt')
        images.append({
            'src': src,
            'alt': alt or ''
        })
    return images

def extract_tables(page) -> List[Dict[str, Any]]:
    """Extract all tables from the page."""
    tables = []
    table_elements = page.locator('table').all()
    
    for i, table in enumerate(table_elements):
        table_data = {
            'index': i,
            'headers': [],
            'rows': []
        }
        
        # Extract headers
        headers = table.locator('th').all()
        for th in headers:
            table_data['headers'].append(clean_text(th.inner_text()))
        
        # Extract rows
        rows = table.locator('tr').all()
        for row in rows:
            cells = row.locator('td').all()
            if cells:
                row_data = [clean_text(cell.inner_text()) for cell in cells]
                table_data['rows'].append(row_data)
        
        tables.append(table_data)
    
    return tables

def extract_with_selectors(page, selectors: Dict[str, str], args) -> Dict[str, List[str]]:
    """Extract data using CSS selectors."""
    results = {}
    
    for name, selector in selectors.items():
        elements = page.locator(selector).all()
        extracted = []
        
        for el in elements:
            if args.attribute:
                value = el.get_attribute(args.attribute)
            else:
                value = el.inner_text()
            
            if args.clean_text and value:
                value = clean_text(value)
            
            extracted.append(value)
        
        results[name] = extracted
        print(f"Extracted {len(extracted)} items for '{name}'")
    
    return results

def main():
    args = parse_args()
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: Playwright not installed. Install with: pip install playwright && playwright install")
        sys.exit(1)
    
    # Parse selectors
    selectors = {}
    if args.selectors:
        try:
            selectors = json.loads(args.selectors)
        except json.JSONDecodeError as e:
            print(f"Error parsing selectors JSON: {e}")
            sys.exit(1)
    elif args.selectors_file:
        with open(args.selectors_file, 'r', encoding='utf-8') as f:
            selectors = json.load(f)
    
    results = {
        'url': args.url,
        'pages_scraped': 0,
        'data': {},
        'success': False,
        'error': None
    }
    
    all_data: Dict[str, List] = {}
    all_links: List[Dict] = []
    all_images: List[Dict] = []
    all_tables: List[Dict] = []
    
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
            
            current_url = args.url
            page_num = 0
            
            while page_num < args.max_pages:
                page_num += 1
                print(f"Scraping page {page_num}: {current_url}")
                
                page.goto(current_url, wait_until='networkidle')
                
                # Wait for specific element
                if args.wait_for:
                    page.wait_for_selector(args.wait_for, timeout=args.wait_timeout)
                
                # Extract links
                if args.links:
                    links = extract_links(page)
                    all_links.extend(links)
                    print(f"Extracted {len(links)} links")
                
                # Extract images
                if args.images:
                    images = extract_images(page)
                    all_images.extend(images)
                    print(f"Extracted {len(images)} images")
                
                # Extract tables
                if args.tables:
                    tables = extract_tables(page)
                    all_tables.extend(tables)
                    print(f"Extracted {len(tables)} tables")
                
                # Extract text
                if args.text:
                    results['page_text'] = clean_text(page.content())
                
                # Extract with selectors
                if selectors:
                    extracted = extract_with_selectors(page, selectors, args)
                    for key, values in extracted.items():
                        if key not in all_data:
                            all_data[key] = []
                        all_data[key].extend(values)
                
                results['pages_scraped'] = page_num
                
                # Check for next page
                if args.next and page_num < args.max_pages:
                    next_btn = page.locator(args.next)
                    if next_btn.count() > 0 and next_btn.is_enabled():
                        next_btn.click()
                        page.wait_for_load_state('networkidle')
                        if args.delay > 0:
                            page.wait_for_timeout(args.delay)
                        current_url = page.url
                    else:
                        print("No more pages available")
                        break
                else:
                    break
            
            browser.close()
            results['success'] = True
            
    except Exception as e:
        results['error'] = str(e)
        print(f"Error: {e}")
        sys.exit(1)
    
    # Compile results
    if all_links:
        results['data']['links'] = all_links
    if all_images:
        results['data']['images'] = all_images
    if all_tables:
        results['data']['tables'] = all_tables
    if all_data:
        results['data']['extracted'] = all_data
    
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
