# api/message.py — Agent messaging route (extracted from server.py)
from flask import Blueprint, jsonify, request
from api.config import AGENTS
from api.auth import login_required
from api.helpers import gateway_health
import requests

message_bp = Blueprint("message", __name__)

# ─── Chat Streaming Socket.IO State ──────────────────────────────────────────
_chat_socketio = None


def init_chat_socketio(socketio_instance):
    """Initialize chat streaming socket handlers."""
    global _chat_socketio
    _chat_socketio = socketio_instance
    socketio_instance.on_event("chat_message_send", handle_chat_message_send)


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


# ─── Chat Streaming via Socket.IO ────────────────────────────────────────────

def handle_chat_message_send(data):
    """Handle streaming chat message via Socket.IO."""
    from flask_socketio import emit
    from functools import wraps

    def socket_login_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import session
            if not session.get("logged_in"):
                return
            return f(*args, **kwargs)
        return wrapper

    agent_key = data.get("agent_key")
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not agent_key or not message:
        emit("chat_stream_error", {"error": "Missing agent_key or message"})
        return

    if agent_key not in AGENTS:
        emit("chat_stream_error", {"error": "Unknown agent", "agent_key": agent_key})
        return

    agent = AGENTS[agent_key]
    health = gateway_health(agent_key)
    port = health.get("port", agent["port"])
    token = agent["token"]

    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"model": "main", "messages": [{"role": "user", "content": message}]}

    # Emit start event
    emit("chat_stream_start", {
        "agent_key": agent_key,
        "session_id": session_id,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

    try:
        # Use stream=True for streaming response
        with requests.post(url, json=payload, headers=headers, stream=True, timeout=120) as r:
            r.raise_for_status()
            full_response = ""

            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = line.decode("utf-8")
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str == "[DONE]":
                            break
                        import json as _json
                        chunk_data = _json.loads(data_str)
                        content = ""
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_response += content
                                emit("chat_stream_chunk", {
                                    "agent_key": agent_key,
                                    "session_id": session_id,
                                    "chunk": content,
                                    "full": full_response
                                })
                except Exception:
                    continue

            # Emit complete event
            emit("chat_stream_complete", {
                "agent_key": agent_key,
                "session_id": session_id,
                "full_response": full_response,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })

    except Exception as e:
        emit("chat_stream_error", {
            "error": str(e),
            "agent_key": agent_key,
            "session_id": session_id
        })
