# ╔═══════════════════════════════════════════════════════╗
# ║  api/youtube.py — YouTube Data API (Google OAuth)    ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

from api.auth import login_required
from api.config import ROOT_DIR

youtube_bp = Blueprint("youtube", __name__)

# YouTube Data API v3 via Google OAuth
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:5050/youtube/callback")
YT_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "youtube_tokens.json")

# ─── Token Management ─────────────────────────────────────────────────────────

def load_tokens():
    try:
        if os.path.exists(YT_TOKEN_FILE):
            with open(YT_TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_tokens(tokens):
    os.makedirs(os.path.dirname(YT_TOKEN_FILE), exist_ok=True)
    with open(YT_TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def get_access_token():
    tokens = load_tokens()
    return tokens.get("access_token")

# ─── OAuth Routes ──────────────────────────────────────────────────────────────

@youtube_bp.route("/api/youtube/oauth/url", methods=["GET"])
def get_oauth_url():
    """Generate Google OAuth URL for YouTube."""
    if not YOUTUBE_CLIENT_ID:
        return jsonify({"error": "YouTube Client ID not configured"}), 400

    import urllib.parse
    params = {
        "client_id": YOUTUBE_CLIENT_ID,
        "redirect_uri": YOUTUBE_REDIRECT_URI,
        "scope": "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return jsonify({"url": url})

@youtube_bp.route("/api/youtube/callback", methods=["GET"])
def oauth_callback():
    """Handle OAuth callback."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify({"error": f"OAuth error: {error}"}), 400
    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": YOUTUBE_CLIENT_ID,
        "client_secret": YOUTUBE_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": YOUTUBE_REDIRECT_URI,
    }

    try:
        resp = requests.post(token_url, data=data, timeout=10)
        result = resp.json()

        if "access_token" in result:
            tokens = load_tokens()
            tokens["access_token"] = result["access_token"]
            tokens["refresh_token"] = result.get("refresh_token")
            tokens["expires_in"] = result.get("expires_in")
            tokens["token_type"] = result.get("token_type", "Bearer")
            tokens["obtained_at"] = datetime.now().isoformat()
            save_tokens(tokens)
            return jsonify({"success": True, "message": "YouTube connected successfully"})

        return jsonify({"error": result.get("error_description", "Unknown error")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@youtube_bp.route("/api/youtube/status", methods=["GET"])
def get_status():
    """Get YouTube connection status."""
    tokens = load_tokens()
    connected = "access_token" in tokens

    return jsonify({
        "connected": connected,
        "channel_title": tokens.get("channel_title"),
        "channel_id": tokens.get("channel_id"),
        "obtained_at": tokens.get("obtained_at"),
    })

@youtube_bp.route("/api/youtube/disconnect", methods=["POST"])
@login_required
def disconnect():
    tokens = load_tokens()
    keys = ["access_token", "refresh_token", "channel_id", "channel_title"]
    for k in keys:
        tokens.pop(k, None)
    save_tokens(tokens)
    return jsonify({"success": True})

# ─── Channel Info ─────────────────────────────────────────────────────────────

@youtube_bp.route("/api/youtube/me", methods=["GET"])
def get_me():
    """Get authenticated channel info."""
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Not connected to YouTube"}), 401

    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet,contentDetails", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        data = resp.json()

        if "items" in data and len(data["items"]) > 0:
            channel = data["items"][0]
            snippet = channel.get("snippet", {})
            tokens = load_tokens()
            tokens["channel_id"] = channel.get("id")
            tokens["channel_title"] = snippet.get("title")
            save_tokens(tokens)

            return jsonify({
                "channel_id": channel.get("id"),
                "title": snippet.get("title"),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            })

        return jsonify({"error": data.get("error", {}).get("message", "API Error")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Posting ──────────────────────────────────────────────────────────────────
# Note: Video uploads require resumable upload protocol (complex).
# This stub handles community post text which is simpler.

@youtube_bp.route("/api/youtube/post", methods=["POST"])
@login_required
def create_post():
    """Create a community post on YouTube channel."""
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Not connected to YouTube"}), 401

    tokens = load_tokens()
    channel_id = tokens.get("channel_id")
    if not channel_id:
        return jsonify({"error": "Channel ID not found. Call /api/youtube/me first."}), 400

    data = request.json or {}
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "Post text required"}), 400

    try:
        # YouTube community posts via activity insert
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
            return jsonify({"error": result["error"].get("message", "Post failed")}), 400

        return jsonify({
            "success": True,
            "activity_id": result.get("id"),
            "message": "YouTube post created successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@youtube_bp.route("/api/youtube/posts", methods=["GET"])
@login_required
def get_posts():
    """Get recent channel activities."""
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Not connected to YouTube"}), 401

    tokens = load_tokens()
    channel_id = tokens.get("channel_id")
    if not channel_id:
        return jsonify({"error": "Channel not configured"}), 400

    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/activities",
            params={
                "part": "snippet,contentDetails",
                "channelId": channel_id,
                "maxResults": 20,
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        data = resp.json()

        if "error" in data:
            return jsonify({"error": data["error"].get("message", "API Error")}), 400

        posts = [
            {
                "id": a.get("id"),
                "type": a.get("snippet", {}).get("type"),
                "description": a.get("snippet", {}).get("description"),
                "published": a.get("snippet", {}).get("publishedAt"),
            }
            for a in data.get("items", [])
        ]
        return jsonify({"posts": posts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
