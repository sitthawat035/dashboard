"""
Facebook Graph API Utility for Automated Posting
"""

import os
import requests
from typing import Dict, Any, Optional
from common.utils import print_info, print_success, print_error

def post_to_facebook(page_id: str, access_token: str, message: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Posts a message (and optionally an image) to a Facebook Page using Graph API.
    
    Args:
        page_id: Facebook Page ID
        access_token: Never-Expiring Page Access Token
        message: The caption/text to post
        image_path: Absolute path to the physical image file (optional)
        
    Returns:
        Dict containing success status and raw response.
    """
    if not page_id or not access_token:
        error_msg = "Facebook Page ID or Access Token is missing."
        print_error(f"❌ FB Publish Failed: {error_msg}")
        return {"success": False, "error": error_msg}

    try:
        if image_path and os.path.exists(image_path):
            # POST to /photos (Image + Caption)
            url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
            payload = {'message': message}
            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                print_info(f"Uploading image to Facebook API...")
                response = requests.post(url, data=payload, files=files, params={'access_token': access_token}, timeout=60)
        else:
            # POST to /feed (Text Only)
            if image_path:
                print_error(f"⚠️ Image path provided but file not found: {image_path}. Falling back to text-only post.")
            
            url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
            payload = {'message': message, 'access_token': access_token}
            response = requests.post(url, data=payload, timeout=30)
            
        data = response.json()
        
        if response.status_code == 200:
            post_id = data.get('id', 'Unknown')
            print_success(f"✅ Successfully posted to Facebook! (Post ID: {post_id})")
            return {"success": True, "data": data}
        else:
            err = data.get('error', {})
            err_msg = err.get('message', 'Unknown API Error')
            print_error(f"❌ FB Publish API Error ({response.status_code}): {err_msg}")
            return {"success": False, "error": err_msg, "raw": data}
            
    except Exception as e:
        print_error(f"❌ Exception during Facebook post: {str(e)}")
        return {"success": False, "error": str(e)}

