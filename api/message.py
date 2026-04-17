# api/message.py — Agent messaging route (extracted from server.py)
from flask import Blueprint, jsonify, request
from api.config import AGENTS
from api.auth import login_required
from api.helpers import gateway_health
import requests

message_bp = Blueprint("message", __name__)


@message_bp.route("/api/message/<agent_key>", methods=["POST"])
@login_required
def send_message(agent_key):
    """Unified message route to talk to OpenClaw v1 API."""
    if agent_key not in AGENTS:
        return jsonify({"success": False, "error": "Unknown agent"}), 404

    data = request.json or {}
    message = data.get("message", "")
    if not message:
        return jsonify({"success": False, "error": "No message provided"}), 400

    agent = AGENTS[agent_key]
    # Dynamic port and health check
    health = gateway_health(agent_key)

    # Use detected port for message if online
    port = health.get("port", agent["port"])
    token = agent["token"]

    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"model": "main", "messages": [{"role": "user", "content": message}]}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        resp_data = r.json()

        reply = "No response"
        if "choices" in resp_data and len(resp_data["choices"]) > 0:
            reply = resp_data["choices"][0].get("message", {}).get("content", "")

        return jsonify({"success": True, "response": reply})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
