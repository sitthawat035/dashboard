
import os
import sys
import glob
from pathlib import Path
import re

# Try to import pyperclip for clipboard support
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

def get_latest_post_dir():
    # Find latest date folder (YYYY-MM-DD format only)
    drafts_root = Path("04_Drafts")
    if not drafts_root.exists():
        print("Error: 04_Drafts directory not found.")
        return None
        
    # Get only dirs that look like dates (starts with 20)
    date_dirs = []
    for d in drafts_root.iterdir():
        if d.is_dir() and d.name.startswith("20"):
            date_dirs.append(d)
                
    date_dirs.sort(key=lambda x: x.name, reverse=True)
    
    if not date_dirs:
        print("Error: No date directories (202X-XX-XX) found in Drafts.")
        return None
        
    latest_date_dir = date_dirs[0]
    
    # Find latest topic folder inside date directory
    topic_dirs = sorted([d for d in latest_date_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not topic_dirs:
        print(f"Error: No topic directories found in {latest_date_dir}")
        return None
        
    return topic_dirs[0]

def extract_ready_to_post(raw_content):
    """
    Extracts only the body and hashtags from the MD file.
    Returns a combined string ready for posting.
    """
    # Split by the HR separators
    parts = raw_content.split("---")
    
    if len(parts) < 3:
        # Fallback to simple logic if separators are missing
        return raw_content.strip()
    
    # Main Body is usually the second part
    body = parts[1].strip()
    
    # Metadata is the third part
    metadata_part = parts[2].strip()
    
    # Extract hashtags using regex
    hashtag_match = re.search(r"\*\*Hashtags\*\*:\s*(.*)", metadata_part, re.IGNORECASE)
    hashtags = hashtag_match.group(1).strip() if hashtag_match else ""
    
    # Extract Caption (for reference in terminal, though not in clipboard)
    caption_match = re.search(r"\*\*Caption\*\*:\s*(.*)", metadata_part, re.IGNORECASE)
    caption = caption_match.group(1).strip() if caption_match else ""
    
    # Construct final post
    final_post = body
    if hashtags:
        final_post += f"\n\n{hashtags}"
        
    return final_post, caption

def main():
    latest_dir = get_latest_post_dir()
    if not latest_dir:
        return

    content_file = latest_dir / "02_content.md"
    prompts_file = latest_dir / "03_visual_prompts.md"
    
    if not content_file.exists():
        print(f"Error: Content file not found in {latest_dir}")
        return

    print(f"\n📂 FOUND LATEST DRAFT: {latest_dir.name}")

    # Read Content
    with open(content_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()
        
    # Extract finalized content and caption
    final_post, caption = extract_ready_to_post(raw_content)
        
    # Print to console
    print("\n" + "="*50)
    print("� READY-TO-POST CONTENT (COMPACT VIEW)")
    print("="*50)
    
    if caption:
        print(f"📌 HOOK/CAPTION: {caption[:100]}...")
        
    print("\n" + "."*50)
    # Print a snippet of the body
    body_lines = final_post.split('\n')
    print('\n'.join(body_lines[:5]) + ("\n..." if len(body_lines) > 5 else ""))
    print("."*50)
    
    # Clipboard
    if CLIPBOARD_AVAILABLE:
        try:
            pyperclip.copy(final_post)
            print("\n✅ READY! Content + Hashtags copied to CLIPBOARD.")
            print("   You can PASTE (Ctrl+V) directly to Facebook now.")
        except Exception as e:
            print(f"\n⚠️ Clipboard error: {e}")
    else:
        print("\nℹ️ Install 'pyperclip' to enable auto-copy: pip install pyperclip")

    # Image Prompts (Directly shown for AI Studio)
    if prompts_file.exists():
        print("\n" + "-"*50)
        print("🖼️ VISUAL PROMPTS (Use these in AI Studio / Midjourney)")
        print("-"*50)
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = f.read().strip()
            print(prompts)
        print("-" * 50)
    else:
        print("\n⚠️ No visual prompts file found.")
        
    print(f"\n📍 Draft Path: {latest_dir}")

if __name__ == "__main__":
    main()

