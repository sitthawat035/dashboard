"""
╔══════════════════════════════════════════════════════════════════╗
║  HERMES AGENT BRIDGE — SSE → Socket.IO Bridge                   ║
║                                                                  ║
║  Connects to Hermes API Server (port 8642) and bridges SSE       ║
║  events into OpenClaw Dashboard Socket.IO for live streaming.    ║
║                                                                  ║
║  Endpoints:                                                      ║
║    GET  /api/hermes/status          — Health check + gateway     ║
║    POST /api/hermes/run             — Start a new agent run      ║
║    GET  /api/hermes/runs             — List active runs          ║
║    POST /api/hermes/runs/<id>/stop  — Interrupt a running task   ║
║                                                                  ║
║  Socket.IO Events (Server → Client):                             ║
║    hermes:status         — Gateway health update                 ║
║    hermes:run:started    — New run started (run_id)              ║
║    hermes:run:message    — Text delta (live response streaming)  ║
║    hermes:run:tool_start — Tool invocation started               ║
║    hermes:run:tool_end   — Tool invocation completed             ║
║    hermes:run:complete   — Run finished successfully             ║
║    hermes:run:failed     — Run failed with error                 ║
║    hermes:run:log        — Raw log line for live log panel       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import os
import threading
import time
import requests
from functools import wraps
from flask import request as flask_request, session
from flask import Blueprint, jsonify, request
from flask_socketio import emit
from api.auth import login_required

# ─── Config ───────────────────────────────────────────────────────────────────

HERMES_API_PORT = os.getenv("HERMES_API_PORT", "9119")  # Hermes dashboard IS the API server
HERMES_API_BASE = f"http://127.0.0.1:{HERMES_API_PORT}"
HERMES_API_KEY = ""  # Not used — Hermes uses session cookie auth
STREAM_TIMEOUT = 30  # seconds between SSE events before considering dead
RECONNECT_DELAY = 3  # seconds before reconnecting on error

# Session-based auth — Hermes dashboard sets a session cookie on the HTML page.
# We scrape the token from the page on first request and maintain it in a shared session.
_hermes_session = requests.Session()

def _get_hermes_session_token():
    """Scrape the session token from Hermes dashboard HTML page."""
    try:
        resp = _hermes_session.get(HERMES_API_BASE, timeout=5)
        import re
        m = re.search(r'__HERMES_SESSION_TOKEN__\s*=\s*"([^"]+)"', resp.text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""

_hermes_session.headers.update({
    "Accept": "application/json",
})

# ─── Blueprint ────────────────────────────────────────────────────────────────

hermes_bp = Blueprint("hermes", __name__, url_prefix="/api/hermes")

# ─── Module State ─────────────────────────────────────────────────────────────

_active_runs = {}  # run_id -> {thread, started_at, status}
_socketio = None   # set by init_hermes_bridge()


def _hermes_headers():
    """Build auth headers for Hermes API."""
    headers = {"Accept": "application/json"}
    if HERMES_API_KEY:
        headers["Authorization"] = f"Bearer {HERMES_API_KEY}"
    return headers


def _hermes_stream_headers():
    """Build headers for SSE streaming."""
    headers = {"Accept": "text/event-stream"}
    if HERMES_API_KEY:
        headers["Authorization"] = f"Bearer {HERMES_API_KEY}"
    return headers


# ─── SSE Bridge Thread ───────────────────────────────────────────────────────

def _sse_bridge_thread(run_id, sse_url):
    """
    Background thread that consumes SSE events from Hermes and
    re-emits them as Socket.IO events to dashboard clients.
    """
    global _active_runs
    _active_runs[run_id] = {
        "thread": threading.current_thread(),
        "started_at": time.time(),
        "status": "running",
    }

    def emit_event(event_name, data):
        if _socketio:
            _socketio.emit(event_name, data)
            _socketio.emit("hermes:run:log", {
                "run_id": run_id,
                "event": event_name,
                "data": data,
                "timestamp": time.time(),
            })

    try:
        emit_event("hermes:run:started", {"run_id": run_id, "status": "running"})

        while True:
            try:
                resp = requests.get(
                    sse_url,
                    headers=_hermes_stream_headers(),
                    stream=True,
                    timeout=(10, STREAM_TIMEOUT),
                )

                if resp.status_code != 200:
                    emit_event("hermes:run:failed", {
                        "run_id": run_id,
                        "error": f"SSE returned {resp.status_code}",
                    })
                    break

                current_event = None
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if raw_line is None:
                        continue

                    line = raw_line.strip()
                    if not line:
                        # Empty line = dispatch accumulated event
                        current_event = None
                        continue

                    if line.startswith(":"):
                        # Comment/keepalive
                        continue

                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                        continue

                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            emit_event("hermes:run:complete", {"run_id": run_id})
                            _active_runs[run_id]["status"] = "completed"
                            return

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            data = {"raw": data_str}

                        _dispatch_sse_event(run_id, current_event, data, emit_event)

            except requests.exceptions.ReadTimeout:
                # Connection timed out waiting for events
                emit_event("hermes:run:complete", {
                    "run_id": run_id,
                    "note": "stream ended (timeout)",
                })
                break
            except requests.exceptions.ConnectionError:
                emit_event("hermes:run:failed", {
                    "run_id": run_id,
                    "error": "connection lost to Hermes API",
                })
                break
            except Exception as e:
                emit_event("hermes:run:failed", {
                    "run_id": run_id,
                    "error": str(e),
                })
                break

    finally:
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "ended"
            _active_runs[run_id]["ended_at"] = time.time()


def _dispatch_sse_event(run_id, event_type, data, emit_event):
    """
    Map Hermes SSE events to Socket.IO events.

    Hermes SSE event types:
      - response.created         → run created
      - response.output_text.delta → message delta
      - response.output_text.done  → message complete
      - response.output_item.added → tool call started
      - response.output_item.done  → tool call completed (with result)
      - response.completed       → run finished
      - response.failed          → run failed
      - tool.started             → (Runs API) tool invocation
      - tool.completed           → (Runs API) tool invocation done
      - message.delta            → (Runs API) text delta
      - run.completed            → (Runs API) run finished
      - run.failed               → (Runs API) run failed
    """
    if event_type is None:
        return

    # --- Runs API events ---
    if event_type == "message.delta":
        emit_event("hermes:run:message", {
            "run_id": run_id,
            "delta": data.get("delta", ""),
        })

    elif event_type == "tool.started":
        emit_event("hermes:run:tool_start", {
            "run_id": run_id,
            "tool": data.get("tool_name", "unknown"),
            "preview": data.get("preview", ""),
        })

    elif event_type == "tool.completed":
        emit_event("hermes:run:tool_end", {
            "run_id": run_id,
            "tool": data.get("tool_name", "unknown"),
            "duration": data.get("duration"),
            "error": data.get("error"),
        })

    elif event_type == "run.completed":
        emit_event("hermes:run:complete", {
            "run_id": run_id,
            "output": data.get("output", ""),
            "usage": data.get("usage", {}),
        })
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "completed"

    elif event_type == "run.failed":
        emit_event("hermes:run:failed", {
            "run_id": run_id,
            "error": data.get("error", "unknown error"),
        })
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "failed"

    # --- Responses API events ---
    elif event_type == "response.output_text.delta":
        emit_event("hermes:run:message", {
            "run_id": run_id,
            "delta": data.get("delta", ""),
        })

    elif event_type == "response.output_item.added":
        item = data.get("item", {})
        if item.get("type") == "function_call":
            emit_event("hermes:run:tool_start", {
                "run_id": run_id,
                "tool": item.get("name", "unknown"),
                "preview": item.get("arguments", "")[:200],
            })

    elif event_type == "response.output_item.done":
        item = data.get("item", {})
        if item.get("type") == "function_call":
            emit_event("hermes:run:tool_end", {
                "run_id": run_id,
                "tool": item.get("name", "unknown"),
            })

    elif event_type == "response.completed":
        emit_event("hermes:run:complete", {
            "run_id": run_id,
            "output": "",
            "usage": data.get("usage", {}),
        })
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "completed"

    elif event_type == "response.failed":
        emit_event("hermes:run:failed", {
            "run_id": run_id,
            "error": data.get("error", "unknown error"),
        })
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "failed"


# ─── Chat Completions Bridge (alternative to Runs API) ───────────────────────

def _chat_completions_bridge_thread(run_id, messages, model=None):
    """
    Bridge for /v1/chat/completions with stream=true.
    Uses OpenAI-compatible SSE format.
    """
    global _active_runs
    _active_runs[run_id] = {
        "thread": threading.current_thread(),
        "started_at": time.time(),
        "status": "running",
    }

    def emit_event(event_name, data):
        if _socketio:
            _socketio.emit(event_name, data)

    try:
        emit_event("hermes:run:started", {"run_id": run_id, "status": "running"})

        payload = {
            "messages": messages,
            "stream": True,
        }
        if model:
            payload["model"] = model

        resp = requests.post(
            f"{HERMES_API_BASE}/v1/chat/completions",
            headers=_hermes_stream_headers(),
            json=payload,
            stream=True,
            timeout=(10, 300),
        )

        if resp.status_code != 200:
            emit_event("hermes:run:failed", {
                "run_id": run_id,
                "error": f"HTTP {resp.status_code}: {resp.text[:500]}",
            })
            return

        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line or line.startswith(":"):
                continue
            if line == "data: [DONE]":
                emit_event("hermes:run:complete", {"run_id": run_id})
                break
            if line.startswith("data:"):
                try:
                    chunk = json.loads(line[5:].strip())
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            emit_event("hermes:run:message", {
                                "run_id": run_id,
                                "delta": content,
                            })
                        # Check for tool calls in streaming
                        tool_calls = delta.get("tool_calls", [])
                        for tc in tool_calls:
                            fn = tc.get("function", {})
                            if fn.get("name"):
                                emit_event("hermes:run:tool_start", {
                                    "run_id": run_id,
                                    "tool": fn["name"],
                                    "preview": fn.get("arguments", "")[:200],
                                })
                except json.JSONDecodeError:
                    pass

            # Hermes custom events
            elif line.startswith("event:"):
                event_name = line[6:].strip()
                if event_name == "hermes.tool.progress":
                    # Next line should be data:
                    pass

    except Exception as e:
        emit_event("hermes:run:failed", {
            "run_id": run_id,
            "error": str(e),
        })
    finally:
        if run_id in _active_runs:
            _active_runs[run_id]["status"] = "ended"
            _active_runs[run_id]["ended_at"] = time.time()


# ─── API Routes ───────────────────────────────────────────────────────────────

@hermes_bp.route("/status", methods=["GET"])
def hermes_status():
    """Check Hermes API health and gateway status."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/health/detailed",
            headers=_hermes_headers(),
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            data["connected"] = True
            return jsonify(data)
        return jsonify({"connected": False, "error": f"HTTP {resp.status_code}"})
    except requests.exceptions.ConnectionError:
        return jsonify({"connected": False, "error": f"Hermes API not reachable on port {os.getenv('HERMES_API_PORT', '8642')}"})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@hermes_bp.route("/run", methods=["POST"])
@login_required
def hermes_run():
    """
    Start a new Hermes agent run.

    Body:
      { "message": "...", "model": "optional-model" }
    """
    body = request.get_json(silent=True) or {}
    message = body.get("message", "")
    model = body.get("model")

    if not message:
        return jsonify({"error": "Missing 'message' field"}), 400

    # Try Runs API first (structured events)
    try:
        payload = {"input": message}
        if model:
            payload["model"] = model

        resp = requests.post(
            f"{HERMES_API_BASE}/v1/runs",
            headers=_hermes_headers(),
            json=payload,
            timeout=10,
        )

        if resp.status_code == 202:
            data = resp.json()
            run_id = data.get("run_id")
            sse_url = data.get("events_url", f"/v1/runs/{run_id}/events")

            # Start SSE bridge thread
            thread = threading.Thread(
                target=_sse_bridge_thread,
                args=(run_id, f"{HERMES_API_BASE}{sse_url}"),
                daemon=True,
            )
            thread.start()

            return jsonify({"run_id": run_id, "status": "started", "mode": "runs_api"})
    except Exception:
        pass

    # Fallback: use chat/completions streaming
    run_id = f"chat_{int(time.time() * 1000)}"
    messages = [{"role": "user", "content": message}]

    thread = threading.Thread(
        target=_chat_completions_bridge_thread,
        args=(run_id, messages, model),
        daemon=True,
    )
    thread.start()

    return jsonify({"run_id": run_id, "status": "started", "mode": "chat_completions"})


@hermes_bp.route("/runs", methods=["GET"])
def hermes_list_runs():
    """List active tracked runs."""
    runs = {}
    for rid, info in _active_runs.items():
        runs[rid] = {
            "status": info["status"],
            "started_at": info.get("started_at"),
            "ended_at": info.get("ended_at"),
        }
    return jsonify(runs)


@hermes_bp.route("/runs/<run_id>/stop", methods=["POST"])
@login_required
def hermes_stop_run(run_id):
    """Stop tracking a run (thread will be cleaned up naturally)."""
    if run_id in _active_runs:
        _active_runs[run_id]["status"] = "stopped"
        return jsonify({"stopped": True, "run_id": run_id})
    return jsonify({"error": "run not found"}), 404


@hermes_bp.route("/cron", methods=["GET"])
def hermes_cron_list():
    """Proxy: list Hermes cron jobs."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/api/jobs",
            headers=_hermes_headers(),
            timeout=5,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503


@hermes_bp.route("/cron/<job_id>/run", methods=["POST"])
def hermes_cron_run(job_id):
    """Proxy: trigger a cron job immediately."""
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/api/jobs/{job_id}/run",
            headers=_hermes_headers(),
            timeout=5,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503


@hermes_bp.route("/cron/create", methods=["POST"])
@login_required
def hermes_cron_create():
    """Proxy: create a new cron job."""
    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()
    schedule = body.get("schedule", "").strip()
    prompt = body.get("prompt", "")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not schedule:
        return jsonify({"error": "Schedule is required"}), 400
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/api/jobs",
            headers=_hermes_headers(),
            json={"name": name, "schedule": schedule, "prompt": prompt},
            timeout=10,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Sessions ─────────────────────────────────────────────────────────────────

@hermes_bp.route("/sessions", methods=["GET"])
def hermes_list_sessions():
    """Proxy: list Hermes sessions."""
    page = request.args.get("page", 1, type=int)
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/sessions",
            headers=_hermes_headers(),
            params={"page": page},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/sessions/<session_id>/delete", methods=["POST"])
@login_required
def hermes_delete_session(session_id):
    """Proxy: delete a Hermes session."""
    try:
        resp = requests.delete(
            f"{HERMES_API_BASE}/sessions/{session_id}",
            headers=_hermes_headers(),
            timeout=10,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/sessions/search", methods=["GET"])
def hermes_search_sessions():
    """Proxy: search Hermes sessions."""
    q = request.args.get("q", "")
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/sessions/search",
            headers=_hermes_headers(),
            params={"q": q},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Analytics ────────────────────────────────────────────────────────────────

@hermes_bp.route("/analytics", methods=["GET"])
def hermes_analytics():
    """Proxy: get Hermes analytics data."""
    period = request.args.get("period", "30d")
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/analytics",
            headers=_hermes_headers(),
            params={"period": period},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Models ──────────────────────────────────────────────────────────────────

@hermes_bp.route("/models", methods=["GET"])
def hermes_models():
    """Proxy: list available models."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/models",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/models/switch", methods=["POST"])
@login_required
def hermes_switch_model():
    """Switch the active model."""
    body = request.get_json(silent=True) or {}
    model = body.get("model")
    if not model:
        return jsonify({"error": "Missing 'model' field"}), 400
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/models/switch",
            headers=_hermes_headers(),
            json={"model": model},
            timeout=10,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Logs ─────────────────────────────────────────────────────────────────────

@hermes_bp.route("/logs", methods=["GET"])
def hermes_logs():
    """Proxy: get Hermes logs."""
    log_type = request.args.get("type", "agent")  # agent | errors | gateway
    level = request.args.get("level", "all")
    component = request.args.get("component", "all")
    lines = request.args.get("lines", 100, type=int)
    auto_refresh = request.args.get("auto_refresh", "false")
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/logs",
            headers=_hermes_headers(),
            params={"type": log_type, "level": level, "component": component, "lines": lines, "auto_refresh": auto_refresh},
            timeout=15,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Skills ──────────────────────────────────────────────────────────────────

@hermes_bp.route("/skills", methods=["GET"])
def hermes_skills():
    """Proxy: list Hermes skills."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/skills",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/skills/toggle", methods=["POST"])
@login_required
def hermes_toggle_skill():
    """Enable or disable a skill."""
    body = request.get_json(silent=True) or {}
    skill_name = body.get("skill")
    enabled = body.get("enabled")
    if not skill_name:
        return jsonify({"error": "Missing 'skill' field"}), 400
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/skills/toggle",
            headers=_hermes_headers(),
            json={"skill": skill_name, "enabled": enabled},
            timeout=10,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Plugins ─────────────────────────────────────────────────────────────────

@hermes_bp.route("/plugins", methods=["GET"])
def hermes_plugins():
    """Proxy: list Hermes plugins."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/plugins",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/plugins/toggle", methods=["POST"])
@login_required
def hermes_toggle_plugin():
    """Enable or disable a plugin."""
    body = request.get_json(silent=True) or {}
    plugin_name = body.get("plugin")
    enabled = body.get("enabled")
    if not plugin_name:
        return jsonify({"error": "Missing 'plugin' field"}), 400
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/plugins/toggle",
            headers=_hermes_headers(),
            json={"plugin": plugin_name, "enabled": enabled},
            timeout=10,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/plugins/install", methods=["POST"])
@login_required
def hermes_install_plugin():
    """Install a plugin from git URL."""
    body = request.get_json(silent=True) or {}
    git_url = body.get("git_url")
    force = body.get("force", False)
    enable = body.get("enable_after_install", True)
    if not git_url:
        return jsonify({"error": "Missing 'git_url' field"}), 400
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/plugins/install",
            headers=_hermes_headers(),
            json={"git_url": git_url, "force": force, "enable_after_install": enable},
            timeout=30,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Config ──────────────────────────────────────────────────────────────────

@hermes_bp.route("/config", methods=["GET"])
def hermes_config():
    """Proxy: get Hermes config."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/config",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/config/save", methods=["POST"])
@login_required
def hermes_save_config():
    """Save Hermes config."""
    body = request.get_json(silent=True) or {}
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/config/save",
            headers=_hermes_headers(),
            json=body,
            timeout=15,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Gateway Control ──────────────────────────────────────────────────────────

@hermes_bp.route("/gateway/restart", methods=["POST"])
@login_required
def hermes_restart_gateway():
    """Restart Hermes gateway."""
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/gateway/restart",
            headers=_hermes_headers(),
            timeout=15,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hermes_bp.route("/gateway/update", methods=["POST"])
@login_required
def hermes_update():
    """Update Hermes."""
    try:
        resp = requests.post(
            f"{HERMES_API_BASE}/gateway/update",
            headers=_hermes_headers(),
            timeout=30,
        )
        return jsonify(resp.json() if resp.text else {}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Profiles ─────────────────────────────────────────────────────────────────

@hermes_bp.route("/profiles", methods=["GET"])
def hermes_profiles():
    """Proxy: list Hermes profiles."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/profiles",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Keys ─────────────────────────────────────────────────────────────────────

@hermes_bp.route("/keys", methods=["GET"])
def hermes_keys():
    """Proxy: get Hermes API keys status."""
    try:
        resp = requests.get(
            f"{HERMES_API_BASE}/keys",
            headers=_hermes_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify(resp.json()), resp.status_code
        return jsonify({"error": f"HTTP {resp.status_code}"}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Hermes API not reachable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Socket Auth Decorator ─────────────────────────────────────────────────────
def socket_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return
        return f(*args, **kwargs)
    return wrapper


# ─── Socket.IO Events ────────────────────────────────────────────────────────

def init_hermes_bridge(socketio):
    """Initialize the Hermes bridge with Socket.IO reference."""
    global _socketio
    _socketio = socketio

    @socketio.on("hermes:join")
    @socket_login_required
    def on_hermes_join(data):
        """Client wants to subscribe to Hermes events."""
        emit("hermes:status", {"subscribed": True})

    @socketio.on("hermes:status_request")
    @socket_login_required
    def on_hermes_status_request():
        """Client requests current Hermes status."""
        try:
            resp = requests.get(
                f"{HERMES_API_BASE}/health/detailed",
                headers=_hermes_headers(),
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["connected"] = True
                emit("hermes:status", data)
            else:
                emit("hermes:status", {"connected": False})
        except Exception:
            emit("hermes:status", {"connected": False, "error": "unreachable"})
