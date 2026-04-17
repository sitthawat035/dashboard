#!/usr/bin/env python3
"""
Example: Form Automation
Demonstrates how to fill and submit forms automatically.
"""

from playwright.sync_api import sync_playwright

def fill_login_form():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to login page
        print("Navigating to login page...")
        page.goto('https://example.com/login')
        page.wait_for_load_state('networkidle')
        
        # Fill username field
        page.fill('input[name="username"]', 'user@example.com')
        print("Filled username")
        
        # Fill password field
        page.fill('input[name="password"]', 'secret_password')
        print("Filled password")
        
        # Check "remember me" checkbox if present
        checkbox = page.locator('input[name="remember"]')
        if checkbox.count() > 0:
            checkbox.check()
            print("Checked 'remember me'")
        
        # Click submit button
        page.click('button[type="submit"]')
        print("Clicked submit button")
        
        # Wait for navigation
        page.wait_for_load_state('networkidle')
        
        # Check result
        print(f"Current URL: {page.url}")
        
        # Take screenshot of result
        page.screenshot(path='login_result.png', full_page=True)
        print("Screenshot saved to login_result.png")
        
        browser.close()

def fill_complex_form():
    """Example of filling a more complex form with various input types."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://example.com/register')
        page.wait_for_load_state('networkidle')
        
        # Text inputs
        page.fill('#first-name', 'John')
        page.fill('#last-name', 'Doe')
        page.fill('#email', 'john.doe@example.com')
        
        # Select dropdown
        page.select_option('#country', label='United States')
        
        # Radio buttons
        page.check('input[value="male"]')
        
        # Checkboxes
        page.check('input[name="terms"]')
        page.check('input[name="newsletter"]')
        
        # Date input
        page.fill('input[type="date"]', '1990-01-15')
        
        # Textarea
        page.fill('textarea[name="bio"]', 'This is my bio...')
        
        # File upload (if needed)
        # page.set_input_files('input[type="file"]', 'path/to/file.pdf')
        
        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        print(f"Form submitted. Current URL: {page.url}")
        
        browser.close()

if __name__ == '__main__':
    # Run the login form example
    fill_login_form()
    
    # Uncomment to run the complex form example
    # fill_complex_form()
