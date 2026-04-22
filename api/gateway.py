# ╔═══════════════════════════════════════════════════════╗
# ║  api/gateway.py — start/stop/restart/model routes     ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request, session

from api.config import AGENTS, ROOT_DIR
from api.auth import login_required
from api.helpers import gateway_health, read_file_safe, read_agent_config

gateway_bp = Blueprint("gateway", __name__)

# ── Forward reference for cleanup — will be set by socket_events on init ──────
# gateway.py calls cleanup_log_watchers_for_agent when stopping/restarting
_cleanup_log_watchers_for_agent = None


def set_cleanup_callback(fn):
    """Called from socket_events.init_socketio() to inject the cleanup function."""
    global _cleanup_log_watchers_for_agent
    _cleanup_log_watchers_for_agent = fn


def _do_start(agent_key: str, log_header: str = "Starting") -> dict:
    """Shared start logic used by gateway_start, gateway_restart, and gateway_start_all."""
    agent = AGENTS[agent_key]
    log_path = agent.get("log_file", "")

    # Write header to log (Python side) — do NOT pass file handle to subprocess
    # Windows child processes don't reliably inherit Python file handles.
    # Instead we pass the path and let cmd redirect itself.
    if log_path:
        try:
            with open(log_path, "w", encoding="utf-8") as f_hdr:
                f_hdr.write(f"--- {log_header} {agent['name']} Gateway ---\n")
        except Exception:
            pass

    env = dict(os.environ)
    env["OPENCLAW_ROOT"] = os.getenv("OPENCLAW_ROOT", str(ROOT_DIR))
    env["FORCE_COLOR"] = "1"
    env["TERM"] = "xterm-256color"
    env["OPENCLAW_WINDOWS_TASK_NAME"] = ""
    env["OPENCLAW_SERVICE_MARKER"] = ""

    # Build shell command that redirects stdout+stderr to log file (append)
    if log_path:
        safe_log = log_path.replace('"', '""')
        shell_cmd = f'cmd /c "{agent["gateway_cmd"]}" >> "{safe_log}" 2>&1'
    else:
        shell_cmd = f'cmd /c "{agent["gateway_cmd"]}"'

    subprocess.Popen(
        shell_cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000,
        cwd=agent.get("workspace", str(ROOT_DIR)),
        env=env,
    )


# ─── Routes ───────────────────────────────────────────────────────────────────


@gateway_bp.route("/api/gateway/<agent_key>/start", methods=["POST"])
@login_required
def gateway_start(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        # PRE-FLIGHT CLEANUP — use -NoProfile -NonInteractive to skip profile loading
        task_name = f"OpenClaw_Gateway_{agent.get('name', agent_key)}".replace(" ", "_")
        clean_cmd = (
            f"Get-NetTCPConnection -LocalPort {agent['port']} -ErrorAction SilentlyContinue "
            f"| ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}; "
            f"schtasks /delete /f /tn '{task_name}' 2>$null"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", clean_cmd],
                capture_output=True,
                timeout=15,
            )
        except Exception as stop_err:
            print(
                f"[GatewayStart] Warning during pre-flight cleanup for {agent_key}: {stop_err}"
            )

        # Brief pause so port is fully released before new process binds it
        time.sleep(0.5)

        log_path = agent.get("log_file", "")
        # Write header (Python-side only — do NOT pass file handle to subprocess)
        if log_path:
            try:
                with open(log_path, "w", encoding="utf-8") as f_hdr:
                    f_hdr.write(f"--- Starting {agent['name']} Gateway ---\n")
            except Exception:
                pass

        env = dict(os.environ)
        env["OPENCLAW_ROOT"] = os.getenv("OPENCLAW_ROOT", str(ROOT_DIR))
        env["OPENCLAW_WINDOWS_TASK_NAME"] = ""
        env["OPENCLAW_SERVICE_MARKER"] = ""
        env["FORCE_COLOR"] = "1"
        env["TERM"] = "xterm-256color"

        # Use shell=True with stdout/stderr redirected to log file via >> so the
        # child cmd process itself opens the file — avoids Windows handle inheritance issues
        if log_path:
            safe_log = log_path.replace('"', '""')
            shell_cmd = f'cmd /c "{agent["gateway_cmd"]}" >> "{safe_log}" 2>&1'
        else:
            shell_cmd = f'cmd /c "{agent["gateway_cmd"]}"'

        print(
            f"[GatewayStart] Starting {agent_key} | cmd: {agent['gateway_cmd']} | log: {log_path}"
        )
        agent_root = os.path.dirname(agent["config_file"])
        subprocess.Popen(
            shell_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000,
            cwd=agent_root,
            env=env,
        )
        print(f"[GatewayStart] Process spawned for {agent_key}")
        return jsonify(
            {"success": True, "message": f"Starting {agent['name']} gateway (clean)..."}
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@gateway_bp.route("/api/gateway/<agent_key>/stop", methods=["POST"])
@login_required
def gateway_stop(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        task_name = f"OpenClaw_Gateway_{agent.get('name', agent_key)}".replace(" ", "_")
        stop_cmd = (
            f"Get-NetTCPConnection -LocalPort {agent['port']} -ErrorAction SilentlyContinue "
            f"| ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}; "
            f"schtasks /delete /f /tn '{task_name}' 2>$null"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", stop_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if _cleanup_log_watchers_for_agent:
            _cleanup_log_watchers_for_agent(agent_key)

        return jsonify(
            {
                "success": True,
                "message": f"Stopped {agent['name']} gateway (Force)",
                "output": result.stdout,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@gateway_bp.route("/api/gateway/<agent_key>/restart", methods=["POST"])
@login_required
def gateway_restart(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        task_name = f"OpenClaw_Gateway_{agent.get('name', agent_key)}".replace(" ", "_")
        stop_cmd = (
            f"Get-NetTCPConnection -LocalPort {agent['port']} -ErrorAction SilentlyContinue "
            f"| ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}; "
            f"schtasks /delete /f /tn '{task_name}' 2>$null"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", stop_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if _cleanup_log_watchers_for_agent:
            _cleanup_log_watchers_for_agent(agent_key)

        time.sleep(1.5)
        _do_start(agent_key, log_header="Restarting")

        return jsonify(
            {
                "success": True,
                "message": f"Restarting {agent['name']} gateway (background)...",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@gateway_bp.route("/api/gateway/start-all", methods=["POST"])
@login_required
def gateway_start_all():
    """Start all agents in separate console windows."""
    try:
        results = {}
        for key, agent in AGENTS.items():
            health = gateway_health(key)
            if health["online"]:
                results[key] = {
                    "success": True,
                    "message": f"{agent['name']} already running",
                }
                continue
            _do_start(key, log_header="Starting (All)")
            results[key] = {
                "success": True,
                "message": f"Starting {agent['name']} (background)...",
            }

        return jsonify(
            {"success": True, "message": "Starting all agents...", "results": results}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@gateway_bp.route("/api/gateway/<agent_key>/model", methods=["POST"])
@login_required
def gateway_model(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404

    data = request.json or {}
    new_model = data.get("model")
    if not new_model:
        return jsonify({"error": "No model provided"}), 400

    agent = AGENTS[agent_key]
    cfg_path = agent["config_file"]

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if "agents" not in cfg:
            cfg["agents"] = {}
        if "defaults" not in cfg["agents"]:
            cfg["agents"]["defaults"] = {}
        if "model" not in cfg["agents"]["defaults"]:
            cfg["agents"]["defaults"]["model"] = {}

        cfg["agents"]["defaults"]["model"]["primary"] = new_model

        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

        return jsonify(
            {"success": True, "message": "Model updated. Please restart gateway."}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@gateway_bp.route("/api/gateway/<gw>/files", methods=["GET"])
def api_gateway_files(gw):
    if gw not in AGENTS:
        return jsonify({"error": "Not found"}), 404
    agent = AGENTS[gw]

    # Use agent root directory (parent of workspace)
    config_path = agent.get("config_file", "")
    base_dir = (
        os.path.dirname(config_path) if config_path else agent.get("workspace", "")
    )

    files = []
    try:
        for root, dirs, filenames in os.walk(base_dir):
            rel_root = os.path.relpath(root, base_dir)
            depth = 0 if rel_root == "." else len(rel_root.split(os.sep))
            if depth > 4:
                continue
            for f in filenames:
                # Only show JSON and Markdown files
                if f.endswith(".json") or f.endswith(".md"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, base_dir)
                    file_name = rel_path.replace("\\", "/")
                    files.append(
                        {
                            "name": file_name,
                            "size": os.path.getsize(full_path),
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(full_path)
                            ).isoformat(),
                            "is_workspace": "workspace" in rel_path.lower(),
                        }
                    )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"success": True, "files": sorted(files, key=lambda x: x["name"])})


@gateway_bp.route("/api/gateway/<gw>/file", methods=["GET", "POST"])
def api_gateway_file(gw):
    if gw not in AGENTS:
        return jsonify({"error": "Not found"}), 404

    if request.method == "POST" and not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    filename = (
        request.args.get("name")
        if request.method == "GET"
        else request.json.get("name")
    )

    if not filename or ".." in filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Use same base_dir as files API
    agent = AGENTS[gw]
    config_path = agent.get("config_file", "")
    base_dir = (
        os.path.dirname(config_path) if config_path else agent.get("workspace", "")
    )
    filepath = os.path.join(base_dir, filename)

    if request.method == "GET":
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        content = read_file_safe(filepath)
        # Include file metadata with content
        file_stat = os.stat(filepath)
        metadata = {
            "name": filename,
            "size": file_stat.st_size,
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }
        return jsonify({"success": True, "content": content, "metadata": metadata})

    if request.method == "POST":
        content = request.json.get("content", "")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
