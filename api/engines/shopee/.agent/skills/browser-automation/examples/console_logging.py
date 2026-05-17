#!/usr/bin/env python3
"""
Example: Console Logging
Demonstrates how to capture and analyze browser console logs.
"""

from playwright.sync_api import sync_playwright

def capture_console_logs():
    """Capture console logs during page interaction."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Store console messages
        console_messages = []
        
        # Listen for console events
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', '')}"
            })
            print(f"[{msg.type}] {msg.text}")
        
        page.on('console', handle_console)
        
        # Listen for page errors
        def handle_page_error(error):
            console_messages.append({
                'type': 'error',
                'text': str(error),
                'location': 'page_error'
            })
            print(f"[PAGE ERROR] {error}")
        
        page.on('pageerror', handle_page_error)
        
        # Navigate and interact
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Print summary
        print(f"\nTotal console messages: {len(console_messages)}")
        
        # Filter by type
        errors = [m for m in console_messages if m['type'] == 'error']
        warnings = [m for m in console_messages if m['type'] == 'warning']
        
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        
        browser.close()
        
        return console_messages

def capture_network_requests():
    """Capture network requests and responses."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Store requests
        requests = []
        
        # Listen for request events
        def handle_request(request):
            requests.append({
                'method': request.method,
                'url': request.url,
                'resource_type': request.resource_type
            })
        
        def handle_response(response):
            # Find matching request and add status
            for req in requests:
                if req['url'] == response.url:
                    req['status'] = response.status
                    req['ok'] = response.ok
                    break
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        # Navigate
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')
        
        # Print summary
        print(f"\nTotal requests: {len(requests)}")
        
        # Group by resource type
        by_type = {}
        for req in requests:
            rt = req['resource_type']
            if rt not in by_type:
                by_type[rt] = []
            by_type[rt].append(req)
        
        for rt, reqs in by_type.items():
            print(f"  {rt}: {len(reqs)} requests")
        
        # Check for failed requests
        failed = [r for r in requests if not r.get('ok', True)]
        if failed:
            print(f"\nFailed requests: {len(failed)}")
            for f in failed:
                print(f"  {f['status']} {f['method']} {f['url']}")
        
        browser.close()
        
        return requests

if __name__ == '__main__':
    print("=== Console Logs ===")
    capture_console_logs()
    
    print("\n=== Network Requests ===")
    capture_network_requests()
