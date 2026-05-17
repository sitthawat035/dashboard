# ╔═══════════════════════════════════════════════════════╗
# ║  api/facebook.py — Facebook OAuth & Graph API        ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, request, session, jsonify

from api.auth import login_required
from api.config import ROOT_DIR

facebook_bp = Blueprint("facebook", __name__)

# Facebook OAuth configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FACEBOOK_OAUTH_REDIRECT = os.getenv("FACEBOOK_OAUTH_REDIRECT", "http://localhost:5050/facebook/callback")
FB_TOKEN_FILE = os.path.join(ROOT_DIR, "data", "facebook_tokens.json")

# ─── Token Management ─────────────────────────────────────────────────────────

def load_tokens():
    """Load stored Facebook tokens."""
    try:
        if os.path.exists(FB_TOKEN_FILE):
            with open(FB_TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_tokens(tokens):
    """Save Facebook tokens to file."""
    os.makedirs(os.path.dirname(FB_TOKEN_FILE), exist_ok=True)
    with open(FB_TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

# ─── OAuth Routes ──────────────────────────────────────────────────────────────

@facebook_bp.route("/api/facebook/oauth/url", methods=["GET"])
def get_oauth_url():
    """Generate Facebook OAuth URL."""
    if not FACEBOOK_APP_ID:
        return jsonify({"error": "Facebook App ID not configured"}), 400
    
    import urllib.parse
    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": FACEBOOK_OAUTH_REDIRECT,
        "scope": "pages_manage_posts,pages_read_engagement,public_profile",
        "response_type": "code",
    }
    url = f"https://www.facebook.com/v18.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return jsonify({"url": url})

@facebook_bp.route("/api/facebook/oauth/callback", methods=["GET"])
def oauth_callback():
    """Handle OAuth callback."""
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return jsonify({"error": f"OAuth error: {error}"}), 400
    
    if not code:
        return jsonify({"error": "No authorization code received"}), 400
    
    # Exchange code for token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "redirect_uri": FACEBOOK_OAUTH_REDIRECT,
        "code": code,
    }
    
    try:
        resp = requests.get(token_url, params=params, timeout=10)
        data = resp.json()
        
        if "access_token" in data:
            tokens = load_tokens()
            tokens["access_token"] = data["access_token"]
            tokens["token_type"] = data.get("token_type", "Bearer")
            tokens["expires_in"] = data.get("expires_in")
            tokens["obtained_at"] = datetime.now().isoformat()
            save_tokens(tokens)
            return jsonify({"success": True, "message": "Facebook connected successfully"})
        
        return jsonify({"error": data.get("error", "Unknown error")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@facebook_bp.route("/api/facebook/status", methods=["GET"])
def get_status():
    """Get Facebook connection status."""
    tokens = load_tokens()
    connected = "access_token" in tokens
    
    return jsonify({
        "connected": connected,
        "token_type": tokens.get("token_type") if connected else None,
        "obtained_at": tokens.get("obtained_at") if connected else None,
    })

@facebook_bp.route("/api/facebook/disconnect", methods=["POST"])
@login_required
def disconnect():
    """Remove Facebook tokens."""
    tokens = load_tokens()
    if "access_token" in tokens:
        del tokens["access_token"]
        save_tokens(tokens)
    return jsonify({"success": True})

# ─── Page Management ───────────────────────────────────────────────────────────

@facebook_bp.route("/api/facebook/pages", methods=["GET"])
def get_pages():
    """Get list of pages the user manages."""
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    
    if not access_token:
        return jsonify({"error": "Not connected to Facebook"}), 401
    
    try:
        # Get user's pages
        resp = requests.get(
            "https://graph.facebook.com/v18.0/me/accounts",
            params={"access_token": access_token},
            timeout=10
        )
        data = resp.json()
        
        if "error" in data:
            return jsonify({"error": data["error"].get("message", "API Error")}), 400
        
        pages = [
            {"id": p["id"], "name": p["name"], "access_token": p.get("access_token")}
            for p in data.get("data", [])
        ]
        return jsonify({"pages": pages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@facebook_bp.route("/api/facebook/pages/<page_id>/select", methods=["POST"])
@login_required
def select_page(page_id):
    """Select a page to post to."""
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    
    if not access_token:
        return jsonify({"error": "Not connected to Facebook"}), 401
    
    try:
        # Verify user has access to this page
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/{page_id}",
            params={"access_token": access_token},
            timeout=10
        )
        data = resp.json()
        
        if "error" in data:
            return jsonify({"error": data["error"].get("message", "Cannot access page")}), 400
        
        # Save selected page
        tokens["selected_page"] = {
            "id": page_id,
            "name": data.get("name"),
        }
        save_tokens(tokens)
        return jsonify({"success": True, "page": tokens["selected_page"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Posting ──────────────────────────────────────────────────────────────────

@facebook_bp.route("/api/facebook/post", methods=["POST"])
@login_required
def create_post():
    """Create a post on the selected page."""
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    selected_page = tokens.get("selected_page")
    
    if not access_token:
        return jsonify({"error": "Not connected to Facebook"}), 401
    
    if not selected_page:
        return jsonify({"error": "No page selected"}), 400
    
    data = request.json or {}
    message = data.get("message", "")
    link = data.get("link")
    
    if not message and not link:
        return jsonify({"error": "Message or link required"}), 400
    
    page_access_token = selected_page.get("access_token")
    if not page_access_token:
        return jsonify({"error": "Page access token not available"}), 400
    
    try:
        post_data = {
            "access_token": page_access_token,
            "message": message,
        }
        if link:
            post_data["link"] = link
        
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{selected_page['id']}/feed",
            data=post_data,
            timeout=10
        )
        result = resp.json()
        
        if "error" in result:
            return jsonify({"error": result["error"].get("message", "Post failed")}), 400
        
        return jsonify({
            "success": True,
            "post_id": result.get("id"),
            "message": "Posted successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Post History ─────────────────────────────────────────────────────────────

@facebook_bp.route("/api/facebook/posts", methods=["GET"])
@login_required
def get_posts():
    """Get recent posts from the selected page."""
    tokens = load_tokens()
    selected_page = tokens.get("selected_page")
    
    if not selected_page:
        return jsonify({"error": "No page selected"}), 400
    
    page_access_token = selected_page.get("access_token")
    if not page_access_token:
        return jsonify({"error": "Page access token not available"}), 400
    
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/{selected_page['id']}/posts",
            params={
                "access_token": page_access_token,
                "fields": "message,created_time,id,permalink_url,full_picture",
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
                "message": p.get("message", ""),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "full_picture": p.get("full_picture"),
            }
            for p in data.get("data", [])
        ]
        return jsonify({"posts": posts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Auto-Pilot Post History ─────────────────────────────────────────────────

POST_HISTORY_FILE = os.path.join(ROOT_DIR, "data", "post_history.json")

@facebook_bp.route("/api/facebook/pipeline-history", methods=["GET"])
def get_pipeline_history():
    """Return auto-pilot post history from facebook_poster.py logs."""
    try:
        if not os.path.exists(POST_HISTORY_FILE):
            return jsonify({"history": []})
        with open(POST_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        limit = int(request.args.get("limit", 30))
        return jsonify({"history": history[:limit]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
