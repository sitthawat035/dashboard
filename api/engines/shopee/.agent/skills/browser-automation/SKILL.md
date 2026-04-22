---
name: browser-automation
description: Comprehensive browser automation skill for web browsing, testing, and automation tasks. Use this skill when users want to browse websites, interact with web pages, fill forms, click buttons, take screenshots, scrape data, or test web applications. Supports both general web browsing and webapp testing workflows.
license: MIT
metadata:
  category: automation
  features:
    - web browsing
    - form filling
    - screenshot capture
    - web scraping
    - webapp testing
    - UI automation
---

# Browser Automation

This skill provides comprehensive browser automation capabilities using Playwright. It supports both general web browsing tasks and web application testing workflows.

## Capabilities

- **Web Browsing**: Navigate to websites, click links, fill forms, extract content
- **Screenshot Capture**: Take full-page or element-specific screenshots
- **Web Scraping**: Extract data from web pages using CSS selectors
- **Form Automation**: Fill and submit forms automatically
- **Webapp Testing**: Test local web applications with server management
- **Console Monitoring**: Capture and analyze browser console logs

## Decision Tree: Choosing Your Approach

```
User task → What type of task?
    ├─ Browse website → Use browse.py script
    │   └─ Navigate, interact, extract data
    │
    ├─ Take screenshot → Use screenshot.py script
    │   └─ Full page or specific element
    │
    ├─ Fill form → Use form_fill.py script
    │   └─ Auto-fill forms with provided data
    │
    ├─ Scrape data → Use scrape.py script
    │   └─ Extract structured data from pages
    │
    └─ Test webapp → Is the server already running?
        ├─ No → Use with_server.py helper
        │        Then write Playwright script
        │
        └─ Yes → Write Playwright script directly
```

## Quick Start Scripts

**Always run scripts with `--help` first** to see usage options.

### 1. Web Browsing (`scripts/browse.py`)

For general web browsing tasks:

```bash
python scripts/browse.py --help
```

Example usage:
```bash
# Navigate to a website and take screenshot
python scripts/browse.py --url "https://example.com" --screenshot

# Click a button and wait for navigation
python scripts/browse.py --url "https://example.com" --click "button.submit" --wait

# Extract text from elements
python scripts/browse.py --url "https://example.com" --extract "h1, .content"
```

### 2. Screenshot Capture (`scripts/screenshot.py`)

For taking screenshots:

```bash
python scripts/screenshot.py --help
```

Example usage:
```bash
# Full page screenshot
python scripts/screenshot.py --url "https://example.com" --output "screenshot.png"

# Element-specific screenshot
python scripts/screenshot.py --url "https://example.com" --selector ".main-content" --output "content.png"

# Mobile viewport screenshot
python scripts/screenshot.py --url "https://example.com" --mobile --output "mobile.png"
```

### 3. Form Filling (`scripts/form_fill.py`)

For automated form filling:

```bash
python scripts/form_fill.py --help
```

Example usage:
```bash
# Fill a login form
python scripts/form_fill.py --url "https://example.com/login" \
  --fields '{"username": "user@example.com", "password": "secret"}' \
  --submit "button[type=submit]"
```

### 4. Web Scraping (`scripts/scrape.py`)

For data extraction:

```bash
python scripts/scrape.py --help
```

Example usage:
```bash
# Extract all links
python scripts/scrape.py --url "https://example.com" --links --output "links.json"

# Extract specific elements
python scripts/scrape.py --url "https://example.com" \
  --selectors '{"titles": "h2", "prices": ".price"}' \
  --output "data.json"
```

### 5. Webapp Testing (`scripts/with_server.py`)

For testing local web applications:

```bash
python scripts/with_server.py --help
```

**Single server:**
```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_test.py
```

**Multiple servers (backend + frontend):**
```bash
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_test.py
```

## Writing Custom Playwright Scripts

For complex automation tasks, write custom Playwright scripts:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Navigate and wait for page load
    page.goto('https://example.com')
    page.wait_for_load_state('networkidle')
    
    # Take screenshot
    page.screenshot(path='screenshot.png', full_page=True)
    
    # Click element
    page.click('button.submit')
    
    # Fill form
    page.fill('input[name="email"]', 'user@example.com')
    
    # Extract content
    title = page.title()
    content = page.content()
    text = page.locator('.content').inner_text()
    
    # Get all matching elements
    links = page.locator('a').all()
    for link in links:
        print(link.get_attribute('href'))
    
    browser.close()
```

## Reconnaissance-Then-Action Pattern

For dynamic web applications:

1. **Inspect rendered DOM**:
   ```python
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   elements = page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

## Common Pitfalls

- **Don't** inspect the DOM before waiting for `networkidle` on dynamic apps
- **Do** wait for `page.wait_for_load_state('networkidle')` before inspection
- **Don't** forget to close the browser when done
- **Do** use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs

## Best Practices

- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Add appropriate waits: `page.wait_for_selector()` or `page.wait_for_timeout()`
- Use `--help` flag to understand script options before using
- For authentication, consider using browser contexts with stored state

## Reference Files

- **examples/** - Examples showing common patterns:
  - `browse_website.py` - Basic website browsing
  - `fill_form.py` - Form automation
  - `take_screenshot.py` - Screenshot capture
  - `scrape_data.py` - Data extraction
  - `element_discovery.py` - Discovering page elements
  - `console_logging.py` - Capturing console logs
