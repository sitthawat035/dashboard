"""
Facebook Page Auto-Poster (Graph API Version)
Uses Facebook Graph API to post content and images instantly.
Zero browser overhead, 100% Mobile/Termux compatible!
"""

import os
import sys
import json
import requests
import asyncio
from pathlib import Path
from datetime import datetime

# Add engines root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent # Dashboard root
engines_dir = Path(__file__).resolve().parent.parent.parent # Engines root
sys.path.insert(0, str(engines_dir))
sys.path.insert(0, str(root_dir)) # For .env access if needed

from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

def post_to_facebook_graph(page_id: str, access_token: str, message: str, image_paths: list = None):
    print(f"🚀 Starting Facebook Graph API post...")
    print(f"   Page ID: {page_id}")
    print(f"   Message length: {len(message)}")
    print(f"   Images: {len(image_paths) if image_paths else 0}")
    
    if not access_token:
        print("❌ Error: FACEBOOK_PAGE_TOKEN is missing from .env!")
        return {"status": "error", "message": "Missing token"}
        
    base_url = f"https://graph.facebook.com/v19.0"
    
    try:
        if not image_paths or len(image_paths) == 0:
            # Text only post
            url = f"{base_url}/{page_id}/feed"
            payload = {
                "message": message,
                "access_token": access_token
            }
            print("   📤 Posting text only...")
            response = requests.post(url, data=payload)
            response.raise_for_status()
            res_data = response.json()
            print(f"   ✅ Post successful! ID: {res_data.get('id')}")
            return {"status": "success", "id": res_data.get('id')}
            
        elif len(image_paths) == 1:
            # Single image post
            url = f"{base_url}/{page_id}/photos"
            payload = {
                "message": message,
                "access_token": access_token
            }
            files = {
                "source": open(image_paths[0], "rb")
            }
            print(f"   🖼️ Uploading and posting 1 image...")
            response = requests.post(url, data=payload, files=files)
            files["source"].close()
            response.raise_for_status()
            res_data = response.json()
            print(f"   ✅ Post successful! ID: {res_data.get('post_id', res_data.get('id'))}")
            return {"status": "success", "id": res_data.get('post_id', res_data.get('id'))}
            
        else:
            # Multiple images post
            print(f"   🖼️ Uploading {len(image_paths)} images...")
            attached_media = []
            
            for img_path in image_paths:
                url = f"{base_url}/{page_id}/photos"
                payload = {
                    "published": "false",
                    "access_token": access_token
                }
                files = {
                    "source": open(img_path, "rb")
                }
                print(f"      Upload -> {Path(img_path).name}...")
                response = requests.post(url, data=payload, files=files)
                files["source"].close()
                response.raise_for_status()
                photo_id = response.json().get('id')
                attached_media.append({"media_fbid": photo_id})
                
            # Create the actual post with attached media
            print("   📤 Publishing post with attached images...")
            post_url = f"{base_url}/{page_id}/feed"
            post_payload = {
                "message": message,
                "attached_media": json.dumps(attached_media),
                "access_token": access_token
            }
            response = requests.post(post_url, data=post_payload)
            response.raise_for_status()
            res_data = response.json()
            print(f"   ✅ Post successful! ID: {res_data.get('id')}")
            return {"status": "success", "id": res_data.get('id')}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Details: {e.response.text}")
        return {"status": "error", "message": str(e)}

async def post_to_facebook(page_id: str, message: str, image_paths: list = None):
    """Wrapper to maintain compatibility with existing async calls"""
    token = os.getenv("FACEBOOK_PAGE_TOKEN")
    return post_to_facebook_graph(page_id, token, message, image_paths)

async def post_from_pending():
    """Read latest ready_to_post and post it to Facebook via Graph API"""
    workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    ready_dir = workspace_root / "data" / "content" / "lookforward" / "ready_to_post"
    
    # Auto detect latest package
    if not ready_dir.exists():
        print(f"❌ No ready_to_post directory found at {ready_dir}!")
        return
        
    date_folders = sorted([d for d in ready_dir.iterdir() if d.is_dir() and d.name.startswith("20")], reverse=True)
    if not date_folders:
        print("❌ No ready_to_post date folders found!")
        return
        
    latest_date = date_folders[0]
    packages = sorted([d for d in latest_date.iterdir() if d.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not packages:
        print("❌ No packages found in date folder!")
        return
        
    latest_package = packages[0]
    print(f"\n📋 Posting latest package: {latest_package.name}")
    
    post_file = latest_package / "post.txt"
    if not post_file.exists():
        print(f"❌ Missing post.txt in {latest_package.name}")
        return
        
    with open(post_file, "r", encoding="utf-8") as f:
        message = f.read()
        
    # Get images
    media_dir = latest_package / "media"
    valid_images = []
    if media_dir.exists():
        valid_images = sorted([str(p) for p in media_dir.iterdir() if p.suffix.lower() in [".png", ".jpg", ".jpeg"]])
        
    print(f"   Images found: {len(valid_images)}")
    
    PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "your-page-id")
    TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN", "")
    
    result = post_to_facebook_graph(PAGE_ID, TOKEN, message, valid_images)
    print(f"\n🎉 Result: {result}")
    
    # Mark as posted
    meta_path = latest_package / "_metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["posted"] = True
            meta["posted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            meta["fb_post_id"] = result.get("id", "")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not update metadata: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Facebook Auto-Poster (Graph API)")
    parser.add_argument("--message", "-m", help="Post message")
    parser.add_argument("--image", "-i", nargs="+", help="Image paths")
    parser.add_argument("--page", "-p", default=os.getenv("FACEBOOK_PAGE_ID", "your-page-id"), help="Facebook Page ID")
    parser.add_argument("--pending", action="store_true", help="Post the latest ready_to_post package")
    
    args = parser.parse_args()
    
    if args.message:
        token = os.getenv("FACEBOOK_PAGE_TOKEN", "")
        post_to_facebook_graph(args.page, token, args.message, args.image)
    else:
        # Default behavior: post the latest generated package
        asyncio.run(post_from_pending())
