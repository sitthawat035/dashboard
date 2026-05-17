# ╔═══════════════════════════════════════════════════════╗
# ║  api/twitter.py — Twitter/X OAuth & API v2           ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, request, session, jsonify

from api.auth import login_required
from api.config import ROOT_DIR

twitter_bp = Blueprint("twitter", __name__)

# Twitter OAuth configuration
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_OAUTH_REDIRECT = os.getenv("TWITTER_OAUTH_REDIRECT", "http://localhost:5050/twitter/callback")
TW_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "twitter_tokens.json")

# ─── Token Management ─────────────────────────────────────────────────────────

def load_tokens():
    """Load stored Twitter tokens."""
    try:
        if os.path.exists(TW_TOKEN_FILE):
            with open(TW_TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_tokens(tokens):
    """Save Twitter tokens to file."""
    os.makedirs(os.path.dirname(TW_TOKEN_FILE), exist_ok=True)
    with open(TW_TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def get_bearer_token():
    """Get active bearer token (oauth token file or env)."""
    tokens = load_tokens()
    return tokens.get("bearer_token") or TWITTER_BEARER_TOKEN

def get_user_token():
    """Get user-level access token + secret."""
    tokens = load_tokens()
    return tokens.get("access_token"), tokens.get("access_token_secret")

# ─── OAuth Routes ──────────────────────────────────────────────────────────────

@twitter_bp.route("/api/twitter/oauth/url", methods=["GET"])
def get_oauth_url():
    """Generate Twitter OAuth URL (OAuth 1.0a PIN flow)."""
    if not TWITTER_API_KEY:
        return jsonify({"error": "Twitter API Key not configured"}), 400

    # For simplicity we return a manual URL; real implementation would use requests_oauthlib
    params = {
        "client_id": TWITTER_API_KEY,
        "redirect_uri": TWITTER_OAUTH_REDIRECT,
        "scope": "tweet.read tweet.write users.read offline.access",
        "response_type": "code",
        "state": "twitter_oauth_state",
    }
    import urllib.parse
    url = "https://twitter.com/i/oauth2/authorize?" + urllib.parse.urlencode(params)
    return jsonify({
        "url": url,
        "note": "Twitter uses OAuth 2.0 PKCE or OAuth 1.0a. Store tokens in data/twitter_tokens.json after auth."
    })

@twitter_bp.route("/api/twitter/oauth/callback", methods=["GET"])
def oauth_callback():
    """Handle OAuth callback (store tokens)."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify({"error": f"OAuth error: {error}"}), 400
    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    # Exchange code for bearer token (OAuth 2.0 PKCE flow)
    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "client_id": TWITTER_API_KEY,
        "client_secret": TWITTER_API_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": TWITTER_OAUTH_REDIRECT,
    }

    try:
        resp = requests.post(token_url, data=data, timeout=10)
        result = resp.json()

        if "access_token" in result:
            tokens = load_tokens()
            tokens["bearer_token"] = result.get("access_token")
            tokens["refresh_token"] = result.get("refresh_token")
            tokens["expires_in"] = result.get("expires_in")
            tokens["token_type"] = result.get("token_type", "Bearer")
            tokens["obtained_at"] = datetime.now().isoformat()
            save_tokens(tokens)
            return jsonify({"success": True, "message": "Twitter connected successfully"})

        return jsonify({"error": result.get("error_description", "Unknown error")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@twitter_bp.route("/api/twitter/status", methods=["GET"])
def get_status():
    """Get Twitter connection status."""
    tokens = load_tokens()
    connected = bool(tokens.get("bearer_token") or TWITTER_BEARER_TOKEN)

    return jsonify({
        "connected": connected,
        "token_type": tokens.get("token_type") if connected else None,
        "obtained_at": tokens.get("obtained_at") if connected else None,
    })

@twitter_bp.route("/api/twitter/disconnect", methods=["POST"])
@login_required
def disconnect():
    """Remove Twitter tokens."""
    tokens = load_tokens()
    keys_to_remove = ["bearer_token", "access_token", "access_token_secret", "refresh_token"]
    for key in keys_to_remove:
        tokens.pop(key, None)
    save_tokens(tokens)
    return jsonify({"success": True})

# ─── User Info ─────────────────────────────────────────────────────────────────

@twitter_bp.route("/api/twitter/me", methods=["GET"])
def get_me():
    """Get authenticated user info."""
    bearer = get_bearer_token()
    if not bearer:
        return jsonify({"error": "Not connected to Twitter"}), 401

    try:
        resp = requests.get(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {bearer}"},
            params={"user.fields": "name,username,profile_image_url"},
            timeout=10
        )
        data = resp.json()

        if "data" in data:
            user = data["data"]
            return jsonify({
                "id": user.get("id"),
                "name": user.get("name"),
                "username": user.get("username"),
                "profile_image_url": user.get("profile_image_url"),
            })

        return jsonify({"error": data.get("detail", "API Error")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Posting ──────────────────────────────────────────────────────────────────

@twitter_bp.route("/api/twitter/post", methods=["POST"])
@login_required
def create_tweet():
    """Post a tweet."""
    bearer = get_bearer_token()
    if not bearer:
        return jsonify({"error": "Not connected to Twitter"}), 401

    data = request.json or {}
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "Tweet text required"}), 400

    if len(text) > 280:
        return jsonify({"error": "Tweet exceeds 280 characters"}), 400

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
            return jsonify({"error": result.get("detail", result.get("error", "Post failed"))}), 400

        return jsonify({
            "success": True,
            "tweet_id": result.get("data", {}).get("id"),
            "message": "Tweet posted successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@twitter_bp.route("/api/twitter/tweets", methods=["GET"])
@login_required
def get_tweets():
    """Get recent tweets from authenticated user."""
    bearer = get_bearer_token()
    if not bearer:
        return jsonify({"error": "Not connected to Twitter"}), 401

    try:
        # First get user ID
        me_resp = requests.get(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {bearer}"},
            params={"user.fields": "id"},
            timeout=10
        )
        me_data = me_resp.json()
        user_id = me_data.get("data", {}).get("id")

        if not user_id:
            return jsonify({"error": "Could not determine user ID"}), 400

        resp = requests.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers={"Authorization": f"Bearer {bearer}"},
            params={"max_results": 20, "tweet.fields": "created_at,public_metrics"},
            timeout=10
        )
        data = resp.json()

        if "data" in data:
            tweets = [
                {
                    "id": t.get("id"),
                    "text": t.get("text"),
                    "created_at": t.get("created_at"),
                    "retweets": t.get("public_metrics", {}).get("retweet_count", 0),
                    "likes": t.get("public_metrics", {}).get("like_count", 0),
                }
                for t in data["data"]
            ]
            return jsonify({"tweets": tweets})

        return jsonify({"tweets": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
