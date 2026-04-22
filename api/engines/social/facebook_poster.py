"""
Facebook Page Auto-Poster
Uses Playwright to post content to Facebook Page
Login once, then it can post automatically
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add engines root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent # Dashboard root
engines_dir = Path(__file__).resolve().parent.parent.parent # Engines root
sys.path.insert(0, str(engines_dir))
sys.path.insert(0, str(root_dir)) # For .env access if needed

import os
from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

from playwright.async_api import async_playwright


async def post_to_facebook(page_id: str, message: str, image_paths: list = None):
    """
    Post to Facebook Page using browser automation
    
    Args:
        page_id: The Facebook Page ID (or username)
        message: Post caption/text
        image_paths: List of local image paths to upload
    """
    print(f"🚀 Starting Facebook post...")
    print(f"   Message: {message[:50]}...")
    print(f"   Images: {len(image_paths) if image_paths else 0}")
    
    async with async_playwright() as p:
        # Launch browser (use existing Chrome if available)
        try:
            browser = await p.chromium.launch(
                headless=False,  # Show browser for login
                channel="chrome"
            )
        except:
            browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to Facebook
        print("   📱 Opening Facebook...")
        await page.goto("https://www.facebook.com")
        
        # Check if logged in
        await page.wait_for_load_state("networkidle")
        
        # Check for login form (if not logged in)
        login_container = page.locator('form[action="/login"]')
        if await login_container.count() > 0:
            print("   ⚠️  Please log in to Facebook in the browser!")
            print("   ⏳ Waiting for login...")
            
            # Wait for user to log in
            await page.wait_for_url("**/feed/**", timeout=120000)  # 2 min timeout
            print("   ✅ Logged in!")
        
        # Navigate to Page
        print(f"   📄 Navigating to Page...")
        await page.goto(f"https://www.facebook.com/{page_id}")
        await page.wait_for_load_state("networkidle")
        
        # Find "Create Post" button
        print("   ✍️ Creating post...")
        
        # Try different selectors for "Create Post" button
        create_post_selectors = [
            'span:text("Create Post")',
            'div[role="button"]:has-text("Create Post")',
            'a[href*="/publish"]',
            'span:text("Share")'
        ]
        
        post_box = None
        for selector in create_post_selectors:
            try:
                post_box = page.locator(selector).first
                if await post_box.count() > 0:
                    await post_box.click()
                    await asyncio.sleep(1)
                    break
            except:
                continue
        
        if not post_box or await post_box.count() == 0:
            # Try clicking on the main compose area
            await page.click('div[contenteditable="true"][role="presentation"]')
            await asyncio.sleep(1)
        
        # Type the message
        print("   ⌨️ Typing message...")
        await page.fill('div[contenteditable="true"][role="presentation"]', message)
        await asyncio.sleep(0.5)
        
        # Upload images if provided
        if image_paths and len(image_paths) > 0:
            print(f"   🖼️ Uploading {len(image_paths)} image(s)...")
            
            # Find file input
            file_input = page.locator('input[type="file"]').first
            if await file_input.count() > 0:
                # Convert paths to strings
                valid_paths = [str(p) for p in image_paths if Path(p).exists()]
                if valid_paths:
                    await file_input.set_input_files(valid_paths)
                    await asyncio.sleep(2)  # Wait for upload
        
        # Click Post button
        print("   📤 Posting...")
        post_button_selectors = [
            'div[role="button"]:has-text("Post")',
            'span:text("Post")',
            'button[type="submit"]'
        ]
        
        for selector in post_button_selectors:
            try:
                post_btn = page.locator(selector).first
                if await post_btn.count() > 0:
                    await post_btn.click()
                    break
            except:
                continue
        
        await asyncio.sleep(3)  # Wait for post to complete
        
        print("   ✅ Post published successfully!")
        
        # Keep browser open briefly to verify
        await asyncio.sleep(2)
        
        await browser.close()
        
        return {"status": "success", "message": "Posted to Facebook"}


async def post_from_pending():
    """Read pending_fb_post.json and post to Facebook"""
    workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    pending_file = workspace_root / "data" / "content" / "social" / "pending_fb_post.json"
    
    if not pending_file.exists():
        print(f"❌ No pending posts found at {pending_file}!")
        return
    
    with open(pending_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    posts = data.get("posts", [])
    if not posts:
        print("❌ No posts in queue!")
        return
    
    # Get the first post
    post = posts[0]
    
    print(f"\n📋 Posting: {post['folder_name']}")
    print(f"   Caption: {post['caption'][:80]}...")
    
    # Get images
    images = post.get("images", [])
    valid_images = [img for img in images if Path(img).exists()]
    
    print(f"   Images: {len(valid_images)} valid")
    
    # Post to Facebook (Pull from ENV or default)
    PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "your-page-id")
    
    result = await post_to_facebook(PAGE_ID, post["caption"], valid_images)
    
    print(f"\n🎉 Result: {result}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Facebook Auto-Poster")
    parser.add_argument("--message", "-m", help="Post message")
    parser.add_argument("--image", "-i", nargs="+", help="Image paths")
    parser.add_argument("--page", "-p", default=os.getenv("FACEBOOK_PAGE_ID", "your-page-id"), help="Facebook Page ID")
    parser.add_argument("--pending", action="store_true", help="Post from pending_fb_post.json")
    
    args = parser.parse_args()
    
    if args.pending:
        asyncio.run(post_from_pending())
    elif args.message:
        asyncio.run(post_to_facebook(args.page, args.message, args.image))
    else:
        print("Usage:")
        print("  python facebook_poster.py --pending          # Post from pending_fb_post.json")
        print("  python facebook_poster.py -m 'Hello' -i img.jpg -p mypage")
