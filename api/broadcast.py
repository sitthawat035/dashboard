# ╔═══════════════════════════════════════════════════════╗
# ║  api/broadcast.py — Unified Multi-Platform Broadcaster ║
# ╚═══════════════════════════════════════════════════════╝

"""
POST /api/broadcast
  Body: { "message": "...", "platforms": ["facebook", "twitter", "instagram", "youtube"] }
  Fans out to all connected platforms (or specified subset).
  Returns a summary of per-platform results.
"""

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

from api.auth import login_required
from api.config import ROOT_DIR

broadcast_bp = Blueprint("broadcast", __name__)

# ─── Per-platform token files ──────────────────────────────────────────────────

def get_fb_status():
    fb_file = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")
    try:
        if os.path.exists(fb_file):
            with open(fb_file) as f:
                t = json.load(f)
                return t.get("access_token") and t.get("selected_page")
    except Exception as e:
        print(f"[broadcast] Failed to get FB status: {e}")
    return None

def get_tw_status():
    tw_file = os.path.join(ROOT_DIR, "data", "twitter_tokens.json")
    try:
        if os.path.exists(tw_file):
            with open(tw_file) as f:
                t = json.load(f)
                return bool(t.get("bearer_token"))
    except Exception as e:
        print(f"[broadcast] Failed to get TW status: {e}")
    return False

def get_ig_status():
    ig_file = os.path.join(ROOT_DIR, "data", "instagram_tokens.json")
    fb_file = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")
    try:
        if os.path.exists(ig_file) and os.path.exists(fb_file):
            with open(ig_file) as f:
                ig = json.load(f)
            with open(fb_file) as f:
                fb = json.load(f)
            return ig.get("instagram_account_id") and fb.get("access_token")
    except Exception as e:
        print(f"[broadcast] Failed to get IG status: {e}")
    return False

def get_yt_status():
    yt_file = os.path.join(ROOT_DIR, "data", "youtube_tokens.json")
    try:
        if os.path.exists(yt_file):
            with open(yt_file) as f:
                t = json.load(f)
                return bool(t.get("access_token"))
    except Exception as e:
        print(f"[broadcast] Failed to get YT status: {e}")
    return False

# ─── Individual platform posters ───────────────────────────────────────────────

def post_facebook(message, link=None):
    fb_file = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")
    with open(fb_file) as f:
        tokens = json.load(f)

    page = tokens.get("selected_page", {})
    page_token = page.get("access_token")
    page_id = page.get("id")

    if not page_token or not page_id:
        return {"platform": "facebook", "success": False, "error": "No page selected. Run /api/facebook/pages first."}

    try:
        post_data = {"access_token": page_token, "message": message}
        if link:
            post_data["link"] = link

        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{page_id}/feed",
            data=post_data,
            timeout=10
        )
        result = resp.json()

        if "error" in result:
            return {"platform": "facebook", "success": False, "error": result["error"].get("message", "Post failed")}

        return {"platform": "facebook", "success": True, "post_id": result.get("id")}
    except Exception as e:
        return {"platform": "facebook", "success": False, "error": str(e)}

def post_twitter(text):
    tw_file = os.path.join(ROOT_DIR, "data", "twitter_tokens.json")
    with open(tw_file) as f:
        tokens = json.load(f)

    bearer = tokens.get("bearer_token")
    if not bearer:
        return {"platform": "twitter", "success": False, "error": "Not connected"}

    if len(text) > 280:
        return {"platform": "twitter", "success": False, "error": "Exceeds 280 characters"}

    try:
        resp = requests.post(
            "https://api.twitter.com/2/tweets",
            headers={
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=10
        )
        result = resp.json()

        if resp.status_code >= 400:
            return {"platform": "twitter", "success": False, "error": result.get("detail", "Post failed")}

        return {"platform": "twitter", "success": True, "tweet_id": result.get("data", {}).get("id")}
    except Exception as e:
        return {"platform": "twitter", "success": False, "error": str(e)}

def post_instagram(message, image_url):
    ig_file = os.path.join(ROOT_DIR, "data", "instagram_tokens.json")
    fb_file = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")

    with open(ig_file) as f:
        ig_tokens = json.load(f)
    with open(fb_file) as f:
        fb_tokens = json.load(f)

    ig_account_id = ig_tokens.get("instagram_account_id")
    access_token = fb_tokens.get("access_token")

    if not ig_account_id or not access_token:
        return {"platform": "instagram", "success": False, "error": "Not connected. Run /api/instagram/connect first."}

    if not image_url:
        return {"platform": "instagram", "success": False, "error": "Instagram posts require image_url"}

    try:
        container_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
            data={"image_url": image_url, "caption": message, "access_token": access_token},
            timeout=10
        )
        container = container_resp.json()

        if "id" not in container:
            return {"platform": "instagram", "success": False, "error": container.get("error", "Failed to create media")}

        publish_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish",
            data={"creation_id": container["id"], "access_token": access_token},
            timeout=10
        )
        publish = publish_resp.json()

        if "id" in publish:
            return {"platform": "instagram", "success": True, "media_id": publish["id"]}

        return {"platform": "instagram", "success": False, "error": publish.get("error", "Publish failed")}
    except Exception as e:
        return {"platform": "instagram", "success": False, "error": str(e)}

def post_youtube(text):
    yt_file = os.path.join(ROOT_DIR, "data", "youtube_tokens.json")
    with open(yt_file) as f:
        tokens = json.load(f)

    access_token = tokens.get("access_token")
    channel_id = tokens.get("channel_id")

    if not access_token or not channel_id:
        return {"platform": "youtube", "success": False, "error": "Not connected. Run /api/youtube/me first."}

    try:
        resp = requests.post(
            "https://www.googleapis.com/youtube/v3/activities",
            params={"part": "snippet"},
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "snippet": {
                    "type": "community",
                    "channelId": channel_id,
                    "description": text,
                }
            },
            timeout=10
        )
        result = resp.json()

        if "error" in result:
            return {"platform": "youtube", "success": False, "error": result["error"].get("message", "Post failed")}

        return {"platform": "youtube", "success": True, "activity_id": result.get("id")}
    except Exception as e:
        return {"platform": "youtube", "success": False, "error": str(e)}

# ─── Broadcast Endpoint ────────────────────────────────────────────────────────

@broadcast_bp.route("/api/broadcast", methods=["POST"])
@login_required
def broadcast():
    """
    Fan out a post to all (or specified) connected platforms.
    Body: {
        "message": "Hello world!",   # required
        "link": "https://...",        # optional, Facebook only
        "image_url": "https://...",   # optional, Instagram only
        "platforms": ["facebook", "twitter"]  # optional, defaults to all connected
    }
    """
    data = request.json or {}
    message = data.get("message", "")
    link = data.get("link")
    image_url = data.get("image_url")
    target_platforms = data.get("platforms", [])  # empty = all

    if not message:
        return jsonify({"error": "message required"}), 400

    results = []
    success_count = 0
    fail_count = 0

    # Determine which platforms to post to
    platforms_to_post = []

    if not target_platforms or "facebook" in target_platforms:
        if get_fb_status():
            platforms_to_post.append(("facebook", post_facebook, {"link": link}))

    if not target_platforms or "twitter" in target_platforms:
        if get_tw_status():
            platforms_to_post.append(("twitter", post_twitter, {}))

    if not target_platforms or "instagram" in target_platforms:
        if get_ig_status():
            platforms_to_post.append(("instagram", post_instagram, {"image_url": image_url}))

    if not target_platforms or "youtube" in target_platforms:
        if get_yt_status():
            platforms_to_post.append(("youtube", post_youtube, {}))

    if not platforms_to_post:
        return jsonify({
            "error": "No connected platforms available. Connect at least one platform first."
        }), 400

    for platform_name, poster_fn, extra_kwargs in platforms_to_post:
        try:
            result = poster_fn(message, **extra_kwargs)
        except Exception as e:
            result = {"platform": platform_name, "success": False, "error": str(e)}

        results.append(result)
        if result.get("success"):
            success_count += 1
        else:
            fail_count += 1

    return jsonify({
        "success": fail_count == 0,
        "total": len(results),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
    })

@broadcast_bp.route("/api/broadcast/status", methods=["GET"])
def broadcast_status():
    """Return connection status of all platforms."""
    return jsonify({
        "facebook": get_fb_status() is not None,
        "twitter": get_tw_status(),
        "instagram": get_ig_status(),
        "youtube": get_yt_status(),
    })
