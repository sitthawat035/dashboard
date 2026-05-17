# ╔═══════════════════════════════════════════════════════╗
# ║  api/instagram.py — Instagram Graph API (via Meta)   ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

from api.auth import login_required
from api.config import ROOT_DIR

instagram_bp = Blueprint("instagram", __name__)

# Instagram uses Facebook Graph API (Meta) — reuse FB tokens
# Instagram Business Account requires connecting via Facebook Page
FB_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")
IG_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "instagram_tokens.json")

# ─── Token Management ─────────────────────────────────────────────────────────

def load_fb_tokens():
    try:
        if os.path.exists(FB_TOKEN_FILE):
            with open(FB_TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def load_ig_tokens():
    try:
        if os.path.exists(IG_TOKEN_FILE):
            with open(IG_TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_ig_tokens(tokens):
    os.makedirs(os.path.dirname(IG_TOKEN_FILE), exist_ok=True)
    with open(IG_TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

# ─── Status ───────────────────────────────────────────────────────────────────

@instagram_bp.route("/api/instagram/status", methods=["GET"])
def get_status():
    """Get Instagram connection status (linked via Facebook)."""
    ig_tokens = load_ig_tokens()
    fb_tokens = load_fb_tokens()

    ig_connected = "instagram_account_id" in ig_tokens
    fb_connected = "access_token" in fb_tokens

    return jsonify({
        "connected": ig_connected and fb_connected,
        "username": ig_tokens.get("username"),
        "fb_connected": fb_connected,
        "obtained_at": ig_tokens.get("obtained_at"),
    })

@instagram_bp.route("/api/instagram/connect", methods=["POST"])
@login_required
def connect_instagram():
    """
    Link Instagram Business Account to a Facebook Page.
    Requires Facebook page access token with instagram_basic,
    instagram_manage_insights, pages_read_engagement permissions.
    """
    fb_tokens = load_fb_tokens()
    access_token = fb_tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "Facebook not connected. Connect Facebook first."}), 401

    data = request.json or {}
    fb_page_id = data.get("facebook_page_id")

    if not fb_page_id:
        return jsonify({"error": "facebook_page_id required"}), 400

    try:
        # Get Instagram account linked to the page
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/{fb_page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": access_token,
            },
            timeout=10
        )
        result = resp.json()

        if "instagram_business_account" not in result:
            return jsonify({"error": "No Instagram account linked to this Facebook page"}), 400

        ig_account_id = result["instagram_business_account"]["id"]

        # Get Instagram username
        ig_resp = requests.get(
            f"https://graph.facebook.com/v18.0/{ig_account_id}",
            params={"fields": "username", "access_token": access_token},
            timeout=10
        )
        ig_data = ig_resp.json()

        tokens = load_ig_tokens()
        tokens["instagram_account_id"] = ig_account_id
        tokens["facebook_page_id"] = fb_page_id
        tokens["username"] = ig_data.get("username")
        tokens["obtained_at"] = datetime.now().isoformat()
        save_ig_tokens(tokens)

        return jsonify({
            "success": True,
            "instagram_account_id": ig_account_id,
            "username": ig_data.get("username")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@instagram_bp.route("/api/instagram/disconnect", methods=["POST"])
@login_required
def disconnect():
    tokens = load_ig_tokens()
    keys = ["instagram_account_id", "facebook_page_id", "username"]
    for k in keys:
        tokens.pop(k, None)
    save_ig_tokens(tokens)
    return jsonify({"success": True})

# ─── Posting ──────────────────────────────────────────────────────────────────

@instagram_bp.route("/api/instagram/post", methods=["POST"])
@login_required
def create_post():
    """Create an Instagram post (image + caption)."""
    ig_tokens = load_ig_tokens()
    fb_tokens = load_fb_tokens()

    ig_account_id = ig_tokens.get("instagram_account_id")
    access_token = fb_tokens.get("access_token")

    if not ig_account_id or not access_token:
        return jsonify({"error": "Instagram not connected. Run /api/instagram/connect first."}), 401

    data = request.json or {}
    caption = data.get("caption", "")
    image_url = data.get("image_url", "")

    if not image_url:
        return jsonify({"error": "image_url required for Instagram posts"}), 400

    try:
        # Create media container
        container_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token,
            },
            timeout=10
        )
        container = container_resp.json()

        if "id" not in container:
            return jsonify({"error": container.get("error", "Failed to create media container")}), 400

        # Publish media
        publish_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish",
            data={
                "creation_id": container["id"],
                "access_token": access_token,
            },
            timeout=10
        )
        publish = publish_resp.json()

        if "id" in publish:
            return jsonify({
                "success": True,
                "media_id": publish["id"],
                "message": "Instagram post published successfully"
            })

        return jsonify({"error": publish.get("error", "Publish failed")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@instagram_bp.route("/api/instagram/posts", methods=["GET"])
@login_required
def get_posts():
    """Get recent Instagram posts."""
    ig_tokens = load_ig_tokens()
    fb_tokens = load_fb_tokens()

    ig_account_id = ig_tokens.get("instagram_account_id")
    access_token = fb_tokens.get("access_token")

    if not ig_account_id or not access_token:
        return jsonify({"error": "Instagram not connected"}), 401

    try:
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink",
                "access_token": access_token,
                "limit": 20
            },
            timeout=10
        )
        data = resp.json()

        if "error" in data:
            return jsonify({"error": data["error"].get("message", "API Error")}), 400

        posts = [
            {
                "id": p.get("id"),
                "caption": p.get("caption", ""),
                "media_type": p.get("media_type"),
                "media_url": p.get("media_url") or p.get("thumbnail_url"),
                "permalink": p.get("permalink"),
                "timestamp": p.get("timestamp"),
            }
            for p in data.get("data", [])
        ]
        return jsonify({"posts": posts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
