#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook API Adapter
Thin wrapper around SocialPoster to provide a simple post_to_facebook() function
expected by the Lookforward pipeline's step_publish_fb.
"""

import os
import requests
from typing import Optional, Dict, Any


def post_to_facebook(
    page_id: str,
    access_token: str,
    message: str,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Post a message (with optional image) to a Facebook Page via Graph API.

    Args:
        page_id:      Facebook Page ID
        access_token: Page Access Token
        message:      Text content to post
        image_path:   Optional path to local image file

    Returns:
        dict with keys:
            success (bool)
            data    (dict)  – on success, contains 'id' (post_id)
            error   (str)   – on failure, human-readable error
    """
    try:
        graph_base = "https://graph.facebook.com/v18.0"

        if image_path and os.path.exists(image_path):
            # ── Upload photo, then attach to feed post ──────────────────
            upload_url = f"{graph_base}/{page_id}/photos"
            with open(image_path, "rb") as f:
                upload_resp = requests.post(
                    upload_url,
                    files={"file": f},
                    data={"published": "false", "access_token": access_token},
                    timeout=60,
                )

            if upload_resp.status_code != 200:
                err = upload_resp.json().get("error", {}).get("message", upload_resp.text)
                return {"success": False, "error": f"Photo upload failed: {err}"}

            media_id = upload_resp.json().get("id")

            import json as _json
            feed_url = f"{graph_base}/{page_id}/feed"
            feed_resp = requests.post(
                feed_url,
                data={
                    "message": message,
                    "attached_media": _json.dumps([{"media_fbid": media_id}]),
                    "access_token": access_token,
                },
                timeout=30,
            )
        else:
            # ── Text-only post ──────────────────────────────────────────
            feed_url = f"{graph_base}/{page_id}/feed"
            feed_resp = requests.post(
                feed_url,
                data={"message": message, "access_token": access_token},
                timeout=30,
            )

        result = feed_resp.json()
        if feed_resp.status_code == 200 and "id" in result:
            return {"success": True, "data": result}
        else:
            err = result.get("error", {}).get("message", str(result))
            return {"success": False, "error": err}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out while posting to Facebook"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
