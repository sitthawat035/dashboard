#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FacebookPoster - Automate posting to Facebook Page (100% Free)

Usage:
    python poster.py --file "path/to/draft.md"
    python poster.py --file "path/to/draft.md" --media "path/to/image.jpg"
"""

import sys
import argparse
import asyncio
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, load_markdown, get_date_str,
    print_header, print_success, print_error, print_info, print_warning
)
from shared.config import get_config
from shared.browser import create_browser_manager


class FacebookPoster:
    """
    Automate Facebook posting using Playwright and Chrome CDP.
    """
    
    def __init__(self):
        """Initialize poster."""
        self.config = get_config()
        self.logger = setup_logger(
            "FacebookPoster",
            self.config.paths["error_logs"] / f"{get_date_str()}_FacebookPoster.log"
        )
        self.page_url = "https://www.facebook.com/profile.php?id=61572626079965" # Replace with actual page ID if different
    
    async def post_content(self, content_file: str, media_path: str = None) -> bool:
        """
        Post content to Facebook.
        
        Args:
            content_file: Path to markdown draft
            media_path: Path to media file (optional)
            
        Returns:
            True if successful
        """
        print_header("📢 FACEBOOK POSTER - START")
        
        # 1. Load content
        try:
            content = load_markdown(content_file)
            # Extract content between code blocks if present (the draft format)
            if "```" in content:
                # Simple extraction: take content between first pair of ```
                parts = content.split("```")
                if len(parts) >= 2:
                    post_text = parts[1].strip()
                else:
                    post_text = content
            else:
                post_text = content
                
            print_info(f"Loaded content from: {content_file}")
            print_info(f"Text length: {len(post_text)} chars")
            
            if media_path:
                print_info(f"Media attachment: {media_path}")
                if not Path(media_path).exists():
                    print_error(f"Media file not found: {media_path}")
                    return False
                    
        except Exception as e:
            print_error(f"Failed to load content: {e}")
            return False

        # 2. Connect to Browser
        try:
            async with await create_browser_manager() as browser:
                if not browser.page:
                    print_error("Failed to initialize page")
                    return False
                
                # 3. Navigate to Page
                url = self.page_url
                if not await browser.goto(url):
                    return False
                
                # Wait for load
                await asyncio.sleep(5)
                
                # 4. Click "What's on your mind?"
                # Selectors are tricky and dynamic. Using generic text matching often works better.
                print_info("Looking for 'Create Post' input...")
                
                # Try multiple selectors/strategies
                clicked = False
                
                # Strategy 1: "What's on your mind?" text
                try:
                    # Generic way to find the create post area
                    create_post_triggers = [
                        "What's on your mind?",
                        "คุณคิดอะไรอยู่",
                        "Create Post",
                        "สร้างโพสต์"
                    ]
                    
                    for trigger in create_post_triggers:
                        try:
                            element = await browser.page.get_by_text(trigger, exact=False).first
                            if await element.is_visible():
                                await element.click()
                                clicked = True
                                print_success(f"Clicked '{trigger}'")
                                break
                        except:
                            continue
                    
                    if not clicked:
                        # Fallback: specific div roles
                        print_warning("Text triggers failed, trying selectors...")
                        await browser.page.click("div[role='button'] div[dir='auto']") # Common pattern for post input
                        clicked = True
                        
                except Exception as e:
                    print_error(f"Failed to open post dialog: {e}")
                    # Screenshot for debugging
                    await browser.screenshot("error_open_dialog.png")
                    return False

                await asyncio.sleep(3)
                
                # 5. Input Text
                print_info("Typing content...")
                try:
                    # Focus on the active element (the input box we just clicked)
                    await browser.page.keyboard.type(post_text, delay=50) # Typing simulates human behavior
                    
                    # Alternatively, if typing is too slow/buggy for emojis:
                    # await browser.page.evaluate(f"document.activeElement.innerText = '{post_text}'")
                    # But Playwright .type or .fill is safer for triggering events
                    
                except Exception as e:
                    print_error(f"Failed to input text: {e}")
                    return False
                
                await asyncio.sleep(2)
                
                # 6. Upload Media (if any)
                if media_path:
                    print_info("Uploading media...")
                    try:
                        # Find file input
                        # Facebook's file input is often hidden. We need to set it on the file chooser.
                        
                        # Click the "Photo/Video" button/icon to trigger file picker
                        # Often has aria-label="Photo/video" or similar
                        
                        async with browser.page.expect_file_chooser() as fc_info:
                            # Try clicking the photo button
                            photo_btn = browser.page.locator("div[aria-label='Photo/video'], div[aria-label='รูปภาพ/วิดีโอ']")
                            if await photo_btn.count() > 0:
                                await photo_btn.first.click()
                            else:
                                # Fallback: look for generic green/image icon pattern
                                print_warning("Photo button not found by label, trying generic approach...")
                                # This is risky. Let's try to just find input[type=file]
                                # often it's present in DOM
                                pass

                        file_chooser = await fc_info.value
                        await file_chooser.set_files(media_path)
                        print_success("Media attached")
                        
                        # Wait for upload (look for loading spinner or just wait)
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        print_error(f"Failed to upload media: {e}")
                        # Don't fail the whole post? No, media is important.
                        # But maybe we can proceed with text only if configured.
                        # For now, return False
                        await browser.screenshot("error_media_upload.png")
                        return False
                
                # 7. Click Post
                print_info("Clicking 'Post' button...")
                try:
                    # Find 'Post' button
                    # Usually: generic 'Post' text or 'โพสต์'
                    post_btn = browser.page.locator("div[aria-label='Post'], div[aria-label='โพสต์']")
                    
                    # Ensure it's enabled (sometimes disabled while uploading)
                    # We might need to wait
                    
                    await asyncio.sleep(2)
                    
                    if await post_btn.count() > 0:
                        await post_btn.first.click()
                        print_success("Clicked 'Post'!")
                    else:
                        print_error("Post button not found!")
                        await browser.screenshot("error_post_btn_not_found.png")
                        return False
                        
                except Exception as e:
                    print_error(f"Failed to click Post: {e}")
                    return False
                
                # 8. Verify Success
                print_info("Verifying posting status...")
                # Wait for "Posting..." to disappear or "Posted" toast
                await asyncio.sleep(5)
                
                # Look for "Just now" or "Sending" disappearing
                # Simple check: take screenshot for verification
                await browser.screenshot("post_success.png")
                print_success("Post action completed (Check screenshot to verify)")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Browser error: {e}")
            print_error(f"Browser automation failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Automate Facebook Posting")
    parser.add_argument("--file", required=True, help="Path to markdown draft file")
    parser.add_argument("--media", help="Path to image/video file")
    
    args = parser.parse_args()
    
    poster = FacebookPoster()
    
    # Run async main
    success = asyncio.run(poster.post_content(args.file, args.media))
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
