#!/usr/bin/env python3
"""
Example: Web Scraping
Demonstrates how to extract data from web pages.
"""

import json
from playwright.sync_api import sync_playwright

def scrape_links():
    """Extract all links from a page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Get all links
        links = []
        elements = page.locator('a[href]').all()
        
        for el in elements:
            links.append({
                'href': el.get_attribute('href'),
                'text': el.inner_text()
            })
        
        print(f"Found {len(links)} links")
        
        # Save to JSON
        with open('links.json', 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        print("Links saved to links.json")
        
        browser.close()

def scrape_table():
    """Extract table data from a page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com/data')
        page.wait_for_load_state('networkidle')
        
        # Extract table data
        tables = []
        table_elements = page.locator('table').all()
        
        for table in table_elements:
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Get headers
            headers = table.locator('th').all()
            for th in headers:
                table_data['headers'].append(th.inner_text())
            
            # Get rows
            rows = table.locator('tr').all()
            for row in rows:
                cells = row.locator('td').all()
                if cells:
                    row_data = [cell.inner_text() for cell in cells]
                    table_data['rows'].append(row_data)
            
            tables.append(table_data)
        
        print(f"Found {len(tables)} tables")
        
        with open('tables.json', 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)
        print("Tables saved to tables.json")
        
        browser.close()

def scrape_with_selectors():
    """Extract specific elements using CSS selectors."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com/products')
        page.wait_for_load_state('networkidle')
        
        # Define selectors for data to extract
        selectors = {
            'titles': '.product-title',
            'prices': '.product-price',
            'descriptions': '.product-description'
        }
        
        data = {}
        for name, selector in selectors.items():
            elements = page.locator(selector).all()
            data[name] = [el.inner_text() for el in elements]
            print(f"Extracted {len(data[name])} {name}")
        
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Products saved to products.json")
        
        browser.close()

def scrape_with_pagination():
    """Scrape data across multiple pages."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        all_products = []
        max_pages = 5
        
        for page_num in range(1, max_pages + 1):
            url = f'https://example.com/products?page={page_num}'
            print(f"Scraping page {page_num}: {url}")
            
            page.goto(url)
            page.wait_for_load_state('networkidle')
            
            # Extract products
            products = page.locator('.product').all()
            for product in products:
                all_products.append({
                    'title': product.locator('.title').inner_text(),
                    'price': product.locator('.price').inner_text()
                })
            
            # Check for next page
            next_btn = page.locator('.pagination .next')
            if next_btn.count() == 0 or not next_btn.is_enabled():
                print("No more pages")
                break
        
        print(f"Total products scraped: {len(all_products)}")
        
        with open('all_products.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print("All products saved to all_products.json")
        
        browser.close()

if __name__ == '__main__':
    # Run examples
    scrape_links()
    # scrape_table()
    # scrape_with_selectors()
    # scrape_with_pagination()
