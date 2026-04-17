# api/system.py — System-level routes (extracted from server.py)
from flask import Blueprint, jsonify
import subprocess
import os
import time
import socket as _socket
from api.config import AGENTS
from api.auth import login_required
from api.terminal import ps_sessions, ps_sessions_lock

system_bp = Blueprint("system", __name__)


@system_bp.route("/api/system/kill-all", methods=["POST"])
@login_required
def system_kill_all():
    """Nuclear option: Kill all agents, MultiContentApp, and dangling processes."""
    try:
        # Dynamic ports from discovered agents
        target_ports = ["5000", "10000"] + [str(a["port"]) for a in AGENTS.values()]
        port_filter = " -or ".join([f"$_.LocalPort -eq {p}" for p in target_ports])

        powershell_script = f"""
        Get-NetTCPConnection | Where-Object {{ {port_filter} }} -ErrorAction SilentlyContinue | ForEach-Object {{
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }}
        Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Get-Process powershell -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        """

        subprocess.run(
            ["powershell", "-Command", powershell_script],
            capture_output=True,
            timeout=15,
        )

        # Clear internal PS sessions
        with ps_sessions_lock:
            for sid, sess in ps_sessions.items():
                sess.kill()
            ps_sessions.clear()

        return jsonify({"success": True, "message": "Global sweep completed. All subsystems terminated."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/api/settings/scan-cli", methods=["GET"])
@login_required
def scan_cli():
    """Scan local file system for recognized AI CLI credentials/configs."""
    user_home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", os.path.join(user_home, "AppData", "Roaming"))
    localappdata = os.environ.get("LOCALAPPDATA", os.path.join(user_home, "AppData", "Local"))

    results = []

    gemini_path = os.path.join(user_home, ".gemini", "credentials")
    gemini_npm = os.path.join(appdata, "npm", "gemini")
    if os.path.exists(gemini_path) or os.path.exists(gemini_npm) or os.path.exists(os.path.join(user_home, ".gemini")):
        results.append({"id": "gemini", "name": "Gemini CLI", "badge": "gemini", "status": "registered",
                         "path": gemini_path if os.path.exists(gemini_path) else gemini_npm,
                         "default_model": "gemini-2.5-flash", "models_count": 3})

    claude_path = os.path.join(user_home, ".claude")
    if os.path.exists(claude_path) or os.path.exists(os.path.join(localappdata, "claude")):
        results.append({"id": "claude", "name": "Claude Code CLI", "badge": "claude", "status": "registered",
                         "path": claude_path, "default_model": "claude-3-7-sonnet", "models_count": 2})

    kilo_path = os.path.join(appdata, "npm", "kilo")
    if os.path.exists(kilo_path) or os.path.exists(os.path.join(user_home, ".kilo")):
        results.append({"id": "kilo", "name": "Kilo Code CLI", "badge": "kilo", "status": "registered",
                         "path": kilo_path, "default_model": "kilo/kilo-auto/free", "models_count": 6})

    openai_path = os.path.join(user_home, ".openai")
    if os.path.exists(openai_path):
        results.append({"id": "openai", "name": "OpenAI CLI", "badge": "openai", "status": "registered",
                         "path": openai_path, "default_model": "gpt-4o", "models_count": 4})

    opencode_path = os.path.join(user_home, ".opencode")
    opencode_npm = os.path.join(appdata, "npm", "opencode")
    if os.path.exists(opencode_path) or os.path.exists(opencode_npm):
        results.append({"id": "opencode", "name": "Opencode CLI", "badge": "opencode", "status": "registered",
                         "path": opencode_path if os.path.exists(opencode_path) else opencode_npm,
                         "default_model": "opencode-auto", "models_count": 2})

    ollama_running = False
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", 11434)) == 0:
            ollama_running = True

    results.append({
        "id": "ollama", "name": "Ollama (Local)", "badge": "ollama",
        "status": "active" if ollama_running else "offline",
        "path": "localhost:11434" if ollama_running else "Ollama not running. Start with: ollama serve",
        "default_model": "llama3" if ollama_running else "-",
        "models_count": 0,
    })

    time.sleep(1.2)  # Fake processing time for UI effect
    return jsonify({"success": True, "detected": results})
