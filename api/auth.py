# ╔═══════════════════════════════════════════════════════╗
# ║  api/auth.py — Authentication routes & decorator      ║
# ║  Refactored from server.py (Phase 1)                  ║
# ╚═══════════════════════════════════════════════════════╝

from functools import wraps
from flask import Blueprint, jsonify, request, session

from api.config import DASHBOARD_PASSWORD

auth_bp = Blueprint("auth", __name__)


# ─── Decorator ────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function


# ─── Routes ───────────────────────────────────────────────────────────────────
@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    if data.get("password") == DASHBOARD_PASSWORD:
        session.permanent = True
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("logged_in", None)
    return jsonify({"success": True})


@auth_bp.route("/api/ping")
@login_required
def api_ping():
    """Authenticated session check. Returns 200 if session valid, 401 if not."""
    return jsonify({"ok": True})

