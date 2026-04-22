#!/usr/bin/env python3
"""
Example: Element Discovery
Demonstrates how to discover and inspect elements on a page.
"""

import json
from playwright.sync_api import sync_playwright

def discover_all_elements():
    """Discover all interactive elements on a page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        elements = {
            'buttons': [],
            'links': [],
            'inputs': [],
            'selects': [],
            'textareas': [],
            'forms': []
        }
        
        # Discover buttons
        buttons = page.locator('button').all()
        for btn in buttons:
            elements['buttons'].append({
                'text': btn.inner_text(),
                'type': btn.get_attribute('type'),
                'disabled': btn.is_disabled()
            })
        
        # Discover links
        links = page.locator('a[href]').all()
        for link in links:
            elements['links'].append({
                'text': link.inner_text(),
                'href': link.get_attribute('href')
            })
        
        # Discover inputs
        inputs = page.locator('input').all()
        for inp in inputs:
            elements['inputs'].append({
                'type': inp.get_attribute('type'),
                'name': inp.get_attribute('name'),
                'placeholder': inp.get_attribute('placeholder'),
                'id': inp.get_attribute('id')
            })
        
        # Discover selects
        selects = page.locator('select').all()
        for sel in selects:
            options = sel.locator('option').all()
            elements['selects'].append({
                'name': sel.get_attribute('name'),
                'id': sel.get_attribute('id'),
                'options_count': len(options)
            })
        
        # Discover textareas
        textareas = page.locator('textarea').all()
        for ta in textareas:
            elements['textareas'].append({
                'name': ta.get_attribute('name'),
                'placeholder': ta.get_attribute('placeholder'),
                'id': ta.get_attribute('id')
            })
        
        # Discover forms
        forms = page.locator('form').all()
        for form in forms:
            elements['forms'].append({
                'action': form.get_attribute('action'),
                'method': form.get_attribute('method'),
                'id': form.get_attribute('id')
            })
        
        # Print summary
        print("Element Discovery Results:")
        for element_type, items in elements.items():
            print(f"  {element_type}: {len(items)}")
        
        # Save to JSON
        with open('discovered_elements.json', 'w', encoding='utf-8') as f:
            json.dump(elements, f, indent=2, ensure_ascii=False)
        print("\nResults saved to discovered_elements.json")
        
        browser.close()
        
        return elements

def inspect_element_properties():
    """Inspect detailed properties of specific elements."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Get all buttons with their properties
        buttons = page.locator('button').all()
        
        print("Button Properties:")
        for i, btn in enumerate(buttons):
            print(f"\nButton {i + 1}:")
            print(f"  Text: {btn.inner_text()}")
            print(f"  Type: {btn.get_attribute('type')}")
            print(f"  Class: {btn.get_attribute('class')}")
            print(f"  ID: {btn.get_attribute('id')}")
            print(f"  Disabled: {btn.is_disabled()}")
            print(f"  Visible: {btn.is_visible()}")
            
            # Get computed styles
            styles = btn.evaluate('el => window.getComputedStyle(el)')
            print(f"  Background: {styles.get("backgroundColor", "N/A")}")
            print(f"  Color: {styles.get("color", "N/A")}")
        
        browser.close()

def find_clickable_elements():
    """Find all clickable elements including buttons, links, and clickable divs."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        clickable = []
        
        # Find elements with cursor: pointer
        pointer_elements = page.evaluate('''
            () => {
                const elements = document.querySelectorAll('*');
                const clickable = [];
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.cursor === 'pointer') {
                        clickable.push({
                            tag: el.tagName,
                            text: el.innerText?.substring(0, 50),
                            class: el.className,
                            id: el.id
                        });
                    }
                });
                return clickable;
            }
        ''')
        
        clickable.extend(pointer_elements)
        
        print(f"Found {len(clickable)} clickable elements")
        
        for i, el in enumerate(clickable[:10]):  # Show first 10
            print(f"{i + 1}. {el['tag']}: {el['text']}")
        
        browser.close()
        
        return clickable

if __name__ == '__main__':
    print("=== Discover All Elements ===")
    discover_all_elements()
    
    print("\n=== Inspect Element Properties ===")
    inspect_element_properties()
    
    print("\n=== Find Clickable Elements ===")
    find_clickable_elements()
