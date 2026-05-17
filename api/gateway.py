# ╔═══════════════════════════════════════════════════════╗
# ║  api/gateway.py — start/stop/restart/model routes     ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import sys
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
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

def _safe_log_path(log_path: str) -> str:
    """Return a safe log file path. If the path is a directory (edge case),
    remove it so a file can be created there instead."""
    if not log_path:
        return log_path
    import shutil
    p = __import__('pathlib').Path(log_path)
    if p.is_dir():
        try:
            shutil.rmtree(str(p))
            print(f"[GatewayStart] Removed stale directory at log_path: {log_path}")
        except Exception as e:
            print(f"[GatewayStart] Warning: could not remove dir {log_path}: {e}")
            return ""  # give up on this log path
    # Ensure parent directory exists
    p.parent.mkdir(parents=True, exist_ok=True)
    return log_path




def is_windows():
    """Detect if running on Windows."""
    return sys.platform.startswith("win") or os.path.exists("/c/Windows")


def _stop_on_linux(agent_key: str, agent: dict) -> bool:
    """Stop gateway process on Linux/WSL using the port."""
    try:
        port = agent.get("port", 0)
        # Find and kill process using the port
        result = subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print(f"[GatewayStop] Stopped process on port {port}")
        return True
    except FileNotFoundError:
        # fuser not available, try lsof
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{agent.get('port', 0)}"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                print(f"[GatewayStop] Killed processes: {pids}")
                return True
        except Exception as e:
            print(f"[GatewayStop] lsof failed: {e}")
    except Exception as e:
        print(f"[GatewayStop] Failed: {e}")
    return False


def _do_start(agent_key: str, log_header: str = "Starting") -> dict:
    """Shared start logic used by gateway_start, gateway_restart, and gateway_start_all."""
    agent = AGENTS[agent_key]
    log_path = _safe_log_path(agent.get("log_file", ""))
    workspace = agent.get("workspace", str(ROOT_DIR))

    # Write header to log
    if log_path:
        try:
            with open(log_path, "w", encoding="utf-8") as f_hdr:
                f_hdr.write(f"--- {log_header} {agent['name']} Gateway ---\n")
        except Exception:
            pass

    env = dict(os.environ)
    # Per-agent OPENCLAW_ROOT: point to the agent's config directory
    _cfg_file = agent.get("config_file", "")
    if _cfg_file and os.path.exists(os.path.dirname(_cfg_file)):
        env["OPENCLAW_ROOT"] = str(Path(_cfg_file).parent)
        env["OPENCLAW_STATE_DIR"] = env["OPENCLAW_ROOT"]
    else:
        env["OPENCLAW_ROOT"] = os.getenv("OPENCLAW_ROOT", str(ROOT_DIR))
        env["OPENCLAW_STATE_DIR"] = env["OPENCLAW_ROOT"]
    env["FORCE_COLOR"] = "1"
    env["TERM"] = "xterm-256color"

    if is_windows():
        # Windows: use cmd /c with PowerShell for cleanup
        env["OPENCLAW_WINDOWS_TASK_NAME"] = ""
        env["OPENCLAW_SERVICE_MARKER"] = ""

        if log_path:
            safe_log = log_path.replace('"', '""')
            shell_cmd = f'cmd /c "{agent["gateway_cmd"]}" >> "{safe_log}" 2>&1'
        else:
            shell_cmd = f'cmd /c "{agent["gateway_cmd"]}"'

        proc = subprocess.Popen(
            shell_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000,
            cwd=workspace,
            env=env,
        )
    else:
        # Linux/WSL: use openclaw command directly with log redirect
        port = agent.get("port", 1111)

        if log_path:
            # Open log file for append
            log_file = open(log_path, "a")
            proc = subprocess.Popen(
                ["openclaw", "gateway", "--port", str(port)],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=workspace,
                env=env,
                start_new_session=True,
            )
        else:
            proc = subprocess.Popen(
                ["openclaw", "gateway", "--port", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=workspace,
                env=env,
                start_new_session=True,
            )

    # Small delay for process to settle
    time.sleep(0.3)

    print(
        f"[GatewayStart] Started {agent_key} | pid={proc.pid} | port={agent.get('port')}"
    )


# ─── Routes ───────────────────────────────────────────────────────────────────


@gateway_bp.route("/api/gateway/<agent_key>/start", methods=["POST"])
@login_required
def gateway_start(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        # PRE-FLIGHT CLEANUP
        if is_windows():
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
                print(f"[GatewayStart] Warning during pre-flight cleanup: {stop_err}")
        else:
            # Linux/WSL: kill process on port
            _stop_on_linux(agent_key, agent)

        time.sleep(0.5)

        log_path = agent.get("log_file", "")
        workspace = agent.get("workspace", str(ROOT_DIR))

        if log_path:
            try:
                with open(log_path, "w", encoding="utf-8") as f_hdr:
                    f_hdr.write(f"--- Starting {agent['name']} Gateway ---\n")
            except Exception:
                pass

        env = dict(os.environ)
        # Per-agent OPENCLAW_ROOT: point to the agent's config directory
        # so openclaw finds the correct openclaw.json (e.g. ~/.openclaw-1/)
        _cfg_file = agent.get("config_file", "")
        if _cfg_file and os.path.exists(os.path.dirname(_cfg_file)):
            env["OPENCLAW_ROOT"] = str(Path(_cfg_file).parent)
            env["OPENCLAW_STATE_DIR"] = env["OPENCLAW_ROOT"]
        else:
            env["OPENCLAW_ROOT"] = os.getenv("OPENCLAW_ROOT", str(ROOT_DIR))
            env["OPENCLAW_STATE_DIR"] = env["OPENCLAW_ROOT"]
        env["FORCE_COLOR"] = "1"
        env["TERM"] = "xterm-256color"

        if is_windows():
            env["OPENCLAW_WINDOWS_TASK_NAME"] = ""
            env["OPENCLAW_SERVICE_MARKER"] = ""

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
                cwd=workspace,
                env=env,
            )
        else:
            # Linux/WSL: use openclaw directly
            port = agent.get("port", 1111)
            if log_path:
                log_file_handle = open(log_path, "a")
                proc = subprocess.Popen(
                    ["openclaw", "gateway", "--port", str(port)],
                    stdout=log_file_handle,
                    stderr=subprocess.STDOUT,
                    cwd=workspace,
                    env=env,
                    start_new_session=True,
                )
            else:
                proc = subprocess.Popen(
                    ["openclaw", "gateway", "--port", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=workspace,
                    env=env,
                    start_new_session=True,
                )

        print(f"[GatewayStart] Starting {agent_key} on port {agent.get('port')} (pid={proc.pid})")

        # ── Early-exit / error detection: poll for up to 8s ─────────────────
        # openclaw with missing config may take a few seconds before exiting.
        # We also scan the log content for known fatal error patterns so we
        # can fail-fast even if the process is technically still alive.
        FATAL_LOG_PATTERNS = [
            "Missing config",
            "missing config",
            "Run `openclaw setup`",
            "gateway.mode=local",
            "--allow-unconfigured",
            "Error: Cannot find",
            "ENOENT",
            "EACCES",
            "fatal error",
            "SyntaxError",
            "ModuleNotFoundError",
            "ImportError",
        ]

        def _read_log_tail(n=20):
            if log_path and os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                        lines = lf.readlines()
                        return "".join(lines[-n:]).strip()
                except Exception:
                    pass
            return ""

        def _log_has_fatal_error():
            tail = _read_log_tail(30)
            return any(p in tail for p in FATAL_LOG_PATTERNS), tail

        exit_code = None
        fatal_from_log = False
        log_tail = ""

        for i in range(450):  # 45 seconds total (Termux takes ~33s)
            time.sleep(0.1)
            exit_code = proc.poll()
            if exit_code is not None:
                log_tail = _read_log_tail(20)
                break
            # Every 1s after the first 0.5s, scan log for fatal patterns
            if i >= 5 and i % 10 == 0:
                fatal_from_log, log_tail = _log_has_fatal_error()
                if fatal_from_log:
                    # Process still running but log shows config error — kill it
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    time.sleep(0.3)
                    exit_code = proc.poll() or -1
                    break

        if exit_code is not None or fatal_from_log:
            if not log_tail:
                log_tail = _read_log_tail(20)
            reason = "config error detected in log" if fatal_from_log else f"process exited (code {exit_code})"
            print(f"[GatewayStart] Fast-fail: {reason} for {agent_key}")
            return jsonify({
                "success": False,
                "immediate_exit": True,
                "exit_code": exit_code,
                "error": f"Gateway failed to start: {reason}. Check Gateway Logs for details.",
                "log_tail": log_tail,
            }), 500

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
        if is_windows():
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
            output = result.stdout
        else:
            # Linux/WSL: use openclaw gateway stop or kill port
            try:
                result = subprocess.run(
                    ["openclaw", "gateway", "stop"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=agent.get("workspace", str(ROOT_DIR)),
                )
                output = result.stdout
            except Exception:
                _stop_on_linux(agent_key, agent)
                output = f"Killed process on port {agent.get('port')}"

        if _cleanup_log_watchers_for_agent:
            _cleanup_log_watchers_for_agent(agent_key)

        return jsonify(
            {
                "success": True,
                "message": f"Stopped {agent['name']} gateway (Force)",
                "output": output,
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
        if is_windows():
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
        else:
            # Linux/WSL: kill process on port
            _stop_on_linux(agent_key, agent)

        if _cleanup_log_watchers_for_agent:
            _cleanup_log_watchers_for_agent(agent_key)

        # PERF-009: Wait for port to be released before starting (up to 3s)
        import socket
        port = agent.get("port")
        if port:
            for _ in range(30):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.1)
                        if s.connect_ex(("127.0.0.1", port)) != 0:
                            break
                except Exception:
                    break
                time.sleep(0.1)

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
    """Start all agents in parallel using ThreadPoolExecutor."""
    try:
        def start_one(key):
            agent = AGENTS[key]
            health = gateway_health(key)
            if health["online"]:
                return key, {"success": True, "message": f"{agent['name']} already running"}
            try:
                _do_start(key, log_header="Starting (All)")
                return key, {"success": True, "message": f"Starting {agent['name']} (background)..."}
            except Exception as start_err:
                return key, {"success": False, "message": f"Failed to start {agent['name']}: {start_err}"}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(start_one, key): key for key in AGENTS}
            results = {}
            for future in futures:
                key, result = future.result()
                results[key] = result

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
@login_required
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
    except FileNotFoundError:
        return jsonify({"error": "Base directory not found"}), 404
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"success": True, "files": sorted(files, key=lambda x: x["name"])})


@gateway_bp.route("/api/gateway/<gw>/file", methods=["GET", "POST"])
@login_required
def api_gateway_file(gw):
    if gw not in AGENTS:
        return jsonify({"error": "Not found"}), 404

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

    # SEC-003: Proper path traversal protection using resolve()
    base = Path(base_dir).resolve()
    target = (Path(base_dir) / filename).resolve()
    if not str(target).startswith(str(base) + os.sep):
        return jsonify({"error": "Access denied"}), 403

    filepath = str(target)

    if request.method == "GET":
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        try:
            content = read_file_safe(filepath)
            # Include file metadata with content
            file_stat = os.stat(filepath)
            metadata = {
                "name": filename,
                "size": file_stat.st_size,
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            }
            return jsonify({"success": True, "content": content, "metadata": metadata})
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == "POST":
        content = request.json.get("content", "")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return jsonify({"success": True})
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            return jsonify({"error": str(e)}), 500
