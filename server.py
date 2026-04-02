from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    session,
    redirect,
    url_for,
    Response,
    stream_with_context,
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
import subprocess
import threading
import uuid
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

# Try to load environment variables safely
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)
CORS(app) 
# ─── Config ───────────────────────────────────────────────────────────────────
DASHBOARD_PASSWORD = os.getenv(
    "DASHBOARD_PASSWORD", "0"
)  # Default to '0' if not set in .env
DASHBOARD_DIR = Path(__file__).parent

AGENTS = {
    "ace": {
        "name": "Ace",
        "emoji": "🚀",
        "port": 18889,
        "token": "94396b98ba5d8ec5a42739905e1b55083667c25680ad7539",
        "workspace": r"C:\Users\User\openclaw\.openclaw\workspace",
        "gateway_cmd": r"C:\Users\User\openclaw\.openclaw\gateway.cmd",
        "config_file": r"C:\Users\User\openclaw\.openclaw\openclaw.json",
        "color": "#00d4ff",
        "log_file": str(DASHBOARD_DIR / "cf_ace_new.log"),
        "err_file": str(DASHBOARD_DIR / "cf_ace_new.err"),
    },
    "ameri": {
        "name": "Fah",
        "emoji": "🧠",
        "port": 18890,
        "token": "bfc5ba9fafd053ee8c034469eba2f8ba759ae4bf39ae5aac",
        "workspace": r"C:\Users\User\openclaw\.openclaw-2\workspace",
        "gateway_cmd": r"C:\Users\User\openclaw\.openclaw-2\gateway.cmd",
        "config_file": r"C:\Users\User\openclaw\.openclaw-2\openclaw.json",
        "color": "#ff6b9d",
        "log_file": str(DASHBOARD_DIR / "cf_ameri_new.log"),
        "err_file": str(DASHBOARD_DIR / "cf_ameri_new.err"),
    },
    "pudding": {
        "name": "Pudding",
        "emoji": "🍮",
        "port": 18891,
        "token": "e48a1de7c7d47651cd6846b45c7d4023c7167c735bbe407b",
        "workspace": r"C:\Users\User\openclaw\.openclaw-3\workspace",
        "gateway_cmd": r"C:\Users\User\openclaw\.openclaw-3\gateway.cmd",
        "config_file": r"C:\Users\User\openclaw\.openclaw-3\openclaw.json",
        "color": "#f97316",
        "log_file": str(DASHBOARD_DIR / "cf_pudding_new.log"),
        "err_file": str(DASHBOARD_DIR / "cf_pudding_new.err"),
    },
    "alpha": {
        "name": "Alpha",
        "emoji": "⚙️",
        "port": 10000,
        "token": "2c97b1fd8ba7a8808b2e4226e72753cd13cfc7ad17f310b6",
        "workspace": r"C:\Users\User\Joepv\.openclaw-4",
        "gateway_cmd": r"C:\Users\User\Joepv\.openclaw-4\gateway.cmd",
        "config_file": r"C:\Users\User\Joepv\.openclaw-4\openclaw.json",
        "color": "#9E9E9E",
        "log_file": str(DASHBOARD_DIR / "cf_alpha_new.log"),
        "err_file": str(DASHBOARD_DIR / "cf_alpha_new.err"),
    },
    "fah": {
        "name": "Fah",
        "emoji": "💖",
        "port": 20000,
        "token": "bede44f85f58ebcf4ee54b6bf8b78b09a6df67605fd06f64",
        "workspace": r"C:\Users\User\Joepv\Fah\workspace",
        "gateway_cmd": r"C:\Users\User\Joepv\Fah\gateway.cmd",
        "config_file": r"C:\Users\User\Joepv\Fah\openclaw.json",
        "color": "#ff6b9d",
        "log_file": str(DASHBOARD_DIR / "cf_fah_new.log"),
        "err_file": str(DASHBOARD_DIR / "cf_fah_new.err"),
    },
}

# ─── PowerShell Session Store ─────────────────────────────────────────────────
ps_sessions = {}  # session_id -> { process, output_queue, lock }
ps_sessions_lock = threading.Lock()

MAX_OUTPUT_LINES = 500  # keep last N lines per session


class PsSession:
    def __init__(self, session_id: str, cwd: str | None = None):
        self.session_id = session_id
        self.lines: list[str] = []
        self.lock = threading.Lock()
        self.alive = True

        import ctypes

        # STARTUPINFO is Windows-only; use ctypes to avoid pyright stub errors
        try:
            si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
            si.wShowWindow = 0  # SW_HIDE = 0
            _si = si
        except Exception:
            _si = None

        self.process = subprocess.Popen(
            ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=0,
            startupinfo=_si,
            cwd=cwd or "C:\\Users\\User",
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        try:
            stdout = self.process.stdout
            if stdout is None:
                return
            buf = ""
            while True:
                char = stdout.read(1)
                if not char:
                    if buf.strip():
                        with self.lock:
                            self.lines.append(buf.rstrip("\r\n"))
                    break
                buf += char
                # Flush on newline or PowerShell prompt (ends with "> ")
                if char == "\n" or buf.endswith("> "):
                    with self.lock:
                        line = buf.rstrip("\r\n")
                        if line:
                            self.lines.append(line)
                            if len(self.lines) > MAX_OUTPUT_LINES:
                                self.lines = list(self.lines[-MAX_OUTPUT_LINES:])
                    buf = ""
        except Exception:
            pass
        finally:
            self.alive = False

    def send(self, cmd: str):
        if self.process.poll() is not None:
            self.alive = False
            return False
        try:
            stdin = self.process.stdin
            if stdin is None:
                self.alive = False
                return False
            # Strip \r to prevent line ending issues on Termux/SSH
            clean_cmd = cmd.replace('\r', '') + '\n'
            stdin.write(clean_cmd)
            stdin.flush()
            return True
        except Exception:
            self.alive = False
            return False

    def get_output(self, since_line: int = 0):
        with self.lock:
            lines = list(self.lines[since_line:])
            total = len(self.lines)
        return lines, total

    def kill(self):
        self.alive = False
        try:
            self.process.kill()
        except Exception:
            pass


# ─── Helpers ──────────────────────────────────────────────────────────────────
def read_file_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None


def read_file_tail(path: str, max_lines: int = 200):
    """Read last N lines of a file (handles large files efficiently)."""
    try:
        p = Path(str(path))
        if not p.exists():
            return [], 0
        size = p.stat().st_size
        with open(str(p), "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-max_lines:] if len(lines) > max_lines else lines
        return [line.rstrip("\n") for line in tail], size
    except Exception as e:
        return [f"[Error reading log: {e}]"], 0


def get_subagents(config_path):
    subagents = []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            agents_list = cfg.get("agents", {}).get("list", [])
            for a in agents_list:
                ag_id = a.get("id")
                if not ag_id:
                    continue
                if ag_id == "fah":
                    continue
                name = a.get("name", ag_id)
                subagents.append({"id": ag_id, "name": name})
    except Exception as e:
        print(f"Error reading subagents from {config_path}: {e}")
    return subagents


def read_agent_config(config_path):
    try:
        import json

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def gateway_health(agent_key):
    agent = AGENTS[agent_key]
    try:
        cfg = read_agent_config(agent["config_file"])
        gw_cfg = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}
        port = gw_cfg.get("port", agent["port"])

        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            result = s.connect_ex(("127.0.0.1", int(port)))
            online = result == 0

        return {
            "online": online,
            "status_code": 200 if online else 503,
            "data": "OK" if online else "Offline",
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


def get_memory_files(workspace):
    memory_dir = Path(workspace) / "memory"
    files = []
    if memory_dir.exists():
        for f in sorted(memory_dir.iterdir(), reverse=True):
            if f.suffix == ".md":
                content = read_file_safe(f)
                files.append(
                    {
                        "filename": f.name,
                        "content": content,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                )
    return files


# ─── Auth Decorator ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    if data.get("password") == DASHBOARD_PASSWORD:
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("logged_in", None)
    return jsonify({"success": True})


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/status")
@login_required
def api_status():
    result = {}
    for key, agent in AGENTS.items():
        health = gateway_health(key)
        workspace = agent["workspace"]

        cfg = read_agent_config(agent["config_file"])

        agents_cfg = cfg.get("agents") if isinstance(cfg.get("agents"), dict) else {}
        defaults_cfg = (
            agents_cfg.get("defaults")
            if isinstance(agents_cfg.get("defaults"), dict)
            else {}
        )
        model_defaults = (
            defaults_cfg.get("model")
            if isinstance(defaults_cfg.get("model"), dict)
            else {}
        )

        primary_model = model_defaults.get("primary", "")
        fallbacks = model_defaults.get("fallbacks", [])
        if not isinstance(fallbacks, list):
            fallbacks = []

        available_models = [primary_model] if primary_model else []
        for m in fallbacks:
            if m not in available_models:
                available_models.append(m)

        gw_cfg = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}
        port = gw_cfg.get("port", agent["port"])

        result[key] = {
            "name": agent["name"],
            "emoji": agent["emoji"],
            "port": port,
            "token": agent.get("token", ""),
            "color": agent["color"],
            "subagents": get_subagents(agent["config_file"]),
            "online": health["online"],
            "health": health,
            "primary_model": primary_model,
            "available_models": available_models,
            "identity": read_file_safe(os.path.join(workspace, "IDENTITY.md")),
            "soul": read_file_safe(os.path.join(workspace, "SOUL.md")),
            "user_md": read_file_safe(os.path.join(workspace, "USER.md")),
            "memory_md": read_file_safe(os.path.join(workspace, "MEMORY.md")),
            "heartbeat": read_file_safe(os.path.join(workspace, "HEARTBEAT.md")),
        }
    return jsonify(result)


@app.route("/api/memory/<agent_key>")
@login_required
def api_memory(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    workspace = AGENTS[agent_key]["workspace"]
    files = get_memory_files(workspace)
    return jsonify(files)


@app.route("/api/memory/<agent_key>/<filename>")
@login_required
def api_memory_file(agent_key, filename):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    workspace = AGENTS[agent_key]["workspace"]
    path = Path(workspace) / "memory" / filename
    content = read_file_safe(path)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"filename": filename, "content": content})


# ─── Gateway Log API ──────────────────────────────────────────────────────────
@app.route("/api/gateway/<agent_key>/log")
@login_required
def gateway_log(agent_key):
    """Return last N lines of gateway log + err for an agent."""
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    max_lines = int(request.args.get("lines", 100))

    log_lines, log_size = read_file_tail(agent.get("log_file", ""), max_lines)
    err_lines, err_size = read_file_tail(agent.get("err_file", ""), max_lines)

    # Filter for Pudding Logs if requested
    if agent_key == "pudding":
        err_lines = [line for line in err_lines if "pudding" in line.lower()]

    return jsonify(
        {
            "agent": agent_key,
            "log": log_lines or [],
            "err": err_lines or [],
            "log_size": log_size,
            "err_size": err_size,
            "timestamp": datetime.now().isoformat(),
        }
    )


# ─── Subagent Stream API ──────────────────────────────────────────────────────
@app.route("/api/subagents/stream")
@login_required
def subagent_stream():
    """Parse real OpenClaw gateway logs for embedded subagent activity."""
    import re

    result = {
        "subagents": [],
        "timestamp": datetime.now().isoformat(),
    }

    # Regex patterns matching real log format
    # e.g.: 2026-03-26T21:08:24.237+07:00 [agent/embedded] embedded run failover decision: runId=... lane=session:agent:pudding-review:main ...
    # e.g.: 2026-03-26T21:09:00.789+07:00 [agent/embedded] embedded run agent end: runId=... isError=true model=... error=...
    # e.g.: 2026-03-26T21:02:12.403+07:00 สร้างไว้แล้วทั้งหมด ...  (agent reply - no bracket prefix)

    TS_PATTERN    = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+\-]\d{2}:\d{2})"
    EMBEDDED_MARK = r"\[agent/embedded\]"
    LANE_PATTERN  = r"lane=session:agent:([^:]+):main"
    RUNID_PATTERN = r"runId=([a-f0-9\-]{36})"
    MODEL_PATTERN = r"model=([^\s]+)"
    ERROR_PATTERN = r"error=(.+)$"
    DIAG_PATTERN  = r"\[diagnostic\].*lane=session:agent:([^:]+):main.*error=\"(.+?)\""

    for agent_key, agent in AGENTS.items():
        log_path = agent.get("log_file", "")
        if not log_path or not Path(log_path).exists():
            continue

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue

        # Track sessions: runId → session info
        sessions: dict = {}
        # Track last message per agent session (non-system lines = agent reply)
        session_last_reply: dict = {}

        for raw_line in lines:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue

            # Extract ISO timestamp
            ts_match = re.match(TS_PATTERN, line)
            if not ts_match:
                continue
            ts_str = ts_match.group(1)
            # Normalise: 2026-03-26T21:08:24.237+07:00 → "2026-03-26 21:08:24"
            ts_display = ts_str[:19].replace("T", " ")

            rest = line[len(ts_str):].strip()

            # ── Detect [agent/embedded] events ──────────────────────────
            if re.search(EMBEDDED_MARK, rest):
                runid_m = re.search(RUNID_PATTERN, rest)
                lane_m  = re.search(LANE_PATTERN, rest)
                runid   = runid_m.group(1) if runid_m else None
                subagent_name = lane_m.group(1) if lane_m else None

                if not runid:
                    continue

                # Spawn / start detection
                if "embedded run" in rest and runid not in sessions:
                    sessions[runid] = {
                        "id": f"{agent_key}-{runid[:8]}",
                        "agent": agent_key,
                        "session_key": subagent_name or "subagent",
                        "task": subagent_name or "Embedded run",
                        "status": "running",
                        "timestamp": ts_display,
                        "model": "",
                        "snippet": "",
                        "errors": [],
                        "runId": runid,
                    }

                sess = sessions.get(runid)
                if not sess:
                    continue

                # Update subagent name if found later
                if subagent_name and sess["session_key"] == "subagent":
                    sess["session_key"] = subagent_name
                    sess["task"] = subagent_name

                # Detect model
                model_m = re.search(MODEL_PATTERN, rest)
                if model_m:
                    sess["model"] = model_m.group(1)

                # Detect end / error
                if "embedded run agent end" in rest:
                    error_m = re.search(r"error=(.+)$", rest)
                    if error_m:
                        err_text = error_m.group(1).strip()
                        sess["errors"].append(err_text[:120])
                        sess["status"] = "error"
                    else:
                        # successful end — keep running until failover confirmed
                        pass

                elif "failover decision" in rest:
                    decision_m = re.search(r"decision=(\w+)", rest)
                    reason_m   = re.search(r"reason=(\w+)", rest)
                    if decision_m and decision_m.group(1) == "candidate_succeeded":
                        sess["status"] = "complete"
                    elif reason_m:
                        sess["status"] = "error"

            # ── Detect [diagnostic] errors (session-level) ───────────────
            elif re.search(r"\[diagnostic\]", rest):
                lane_m = re.search(LANE_PATTERN, rest)
                if lane_m:
                    subagent_name = lane_m.group(1)
                    err_m = re.search(r'error="(.+?)"', rest)
                    # Link to matching session by subagent name
                    for sess in sessions.values():
                        if sess["session_key"] == subagent_name:
                            if err_m:
                                err_short = err_m.group(1)[:120]
                                if err_short not in sess["errors"]:
                                    sess["errors"].append(err_short)
                            sess["status"] = "error"
                            break

            # ── Detect agent reply lines (no [module] prefix, not empty) ─
            else:
                # Lines that look like agent output (Thai or English natural language)
                bracket_m = re.match(r"^\[[\w/\-]+\]", rest)
                if not bracket_m and len(rest) > 10:
                    # Assign to most recent running session for this agent
                    for sess in reversed(list(sessions.values())):
                        if sess["agent"] == agent_key and sess["status"] == "running":
                            sess["snippet"] = rest[:200]
                            if not sess["task"] or sess["task"] == sess["session_key"]:
                                # Use first reply as task description
                                sess["task"] = rest[:80]
                            break

        # Finalise sessions into result
        for sess in sessions.values():
            errors = sess.pop("errors", [])
            sess.pop("runId", None)
            if not sess["snippet"] and errors:
                sess["snippet"] = errors[-1]
            elif errors and sess["status"] == "error":
                sess["snippet"] = errors[-1]

            result["subagents"].append(sess)

    # Sort newest first
    result["subagents"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    result["subagents"] = result["subagents"][:100]

    return jsonify(result)


# ─── Gateway Model API ────────────────────────────────────────────────────────
@app.route("/api/gateway/<agent_key>/model", methods=["POST"])
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
        import json

        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Ensure nested structure exists
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


# ─── Gateway Control Routes ───────────────────────────────────────────────────
@app.route("/api/gateway/<agent_key>/start", methods=["POST"])
@login_required
def gateway_start(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        log_path = agent.get("log_file", "")
        if log_path:
            f_log = open(log_path, "w", encoding="utf-8")
            f_log.write(f"--- Starting {agent['name']} Gateway ---\n")
            f_log.flush()
            out_pipe = f_log
        else:
            out_pipe = subprocess.DEVNULL

        env = dict(os.environ)
        env["FORCE_COLOR"] = "1"

        subprocess.Popen(
            ["cmd", "/c", agent["gateway_cmd"]],
            stdout=out_pipe,
            stderr=subprocess.STDOUT,
            creationflags=0x08000000,
            cwd=agent.get("workspace", r"C:\Users\User"),
            env=env,
        )
        return jsonify(
            {
                "success": True,
                "message": f"Starting {agent['name']} gateway (background)...",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/gateway/<agent_key>/stop", methods=["POST"])
@login_required
def gateway_stop(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                f"Get-NetTCPConnection -LocalPort {agent['port']} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return jsonify(
            {
                "success": True,
                "message": f"Stopped {agent['name']} gateway",
                "output": result.stdout,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/gateway/<agent_key>/restart", methods=["POST"])
@login_required
def gateway_restart(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    agent = AGENTS[agent_key]
    try:
        subprocess.run(
            [
                "powershell",
                "-Command",
                f"Get-NetTCPConnection -LocalPort {agent['port']} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        import time

        time.sleep(1.5)

        # Consistent background start with correct CWD and no window
        log_path = agent.get("log_file", "")
        if log_path:
            f_log = open(log_path, "w", encoding="utf-8")
            f_log.write(f"--- Restarting {agent['name']} Gateway ---\n")
            f_log.flush()
            out_pipe = f_log
        else:
            out_pipe = subprocess.DEVNULL

        env = dict(os.environ)
        env["FORCE_COLOR"] = "1"

        subprocess.Popen(
            ["cmd", "/c", agent["gateway_cmd"]],
            stdout=out_pipe,
            stderr=subprocess.STDOUT,
            creationflags=0x08000000,
            cwd=agent.get("workspace", r"C:\Users\User"),
            env=env,
        )
        return jsonify(
            {
                "success": True,
                "message": f"Restarting {agent['name']} gateway (background)...",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/gateway/start-all", methods=["POST"])
@login_required
def gateway_start_all():
    """Start all 3 agents in separate console windows"""
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
            log_path = agent.get("log_file", "")
            if log_path:
                f_log = open(log_path, "w", encoding="utf-8")
                f_log.write(f"--- Starting {agent['name']} (All) ---\n")
                f_log.flush()
                out_pipe = f_log
            else:
                out_pipe = subprocess.DEVNULL

            env = dict(os.environ)
            env["FORCE_COLOR"] = "1"

            subprocess.Popen(
                ["cmd", "/c", agent["gateway_cmd"]],
                stdout=out_pipe,
                stderr=subprocess.STDOUT,
                creationflags=0x08000000,
                cwd=agent.get("workspace", r"C:\Users\User"),
                env=env,
            )
            results[key] = {
                "success": True,
                "message": f"Starting {agent['name']} (background)...",
            }

        return jsonify(
            {
                "success": True,
                "message": "Starting all agents...",
                "results": results,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/message/<agent_key>", methods=["POST"])
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
    port = agent["port"]
    token = agent["token"]

    # OpenClaw typically uses /v1/chat/completions for direct chat
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


# ─── Global System Control ───────────────────────────────────────────────────
@app.route("/api/system/kill-all", methods=["POST"])
@login_required
def system_kill_all():
    """Nuclear option: Kill all agents, MultiContentApp, and dangling processes."""
    try:
        # Ports to clear: 5000 (MultiContent), 10000 (Alpha), 18890-18893 (OpenClaw Agents)
        target_ports = ["5000", "10000", "18890", "18891", "18892", "18893"]
        port_filter = " -or ".join([f"$_.LocalPort -eq {p}" for p in target_ports])

        powershell_script = f"""
        # 1. Kill everything on target ports
        Get-NetTCPConnection | Where-Object {{ {port_filter} }} -ErrorAction SilentlyContinue | ForEach-Object {{ 
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
        }}
        
        # 2. Kill all node.exe (OpenClaw engines)
        Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        
        # 3. Kill dangling powershell.exe NOT belonging to the host dashboard
        # (This is tricky, we just kill common ones)
        Get-Process powershell -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        """

        subprocess.run(
            ["powershell", "-Command", powershell_script],
            capture_output=True,
            timeout=15,
        )

        # Also clear our internal PS sessions
        with ps_sessions_lock:
            for sid, sess in ps_sessions.items():
                sess.kill()
            ps_sessions.clear()

        return jsonify(
            {
                "success": True,
                "message": "Global sweep completed. All subsystems terminated.",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/multicontent/start", methods=["POST"])
@login_required
def start_multicontent():
    """Start MultiContentApp on-demand."""
    try:
        # Check if already running
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", 5000)) == 0:
                return jsonify(
                    {"success": True, "message": "MultiContentApp already running"}
                )

        # Start it
        target_dir = r"C:\DriveD_MultiContentApp"
        if not os.path.exists(target_dir):
            return jsonify(
                {"success": False, "error": f"Directory not found: {target_dir}"}
            ), 404

        env = dict(os.environ)
        env["FORCE_COLOR"] = "1"

        # Use our standard background start with dedicated .venv
        venv_python = os.path.join(
            target_dir, "dashboard", ".venv", "Scripts", "python.exe"
        )
        if not os.path.exists(venv_python):
            # Fallback to system python if venv not found (though it should be there)
            venv_python = "python"

        subprocess.Popen(
            [venv_python, "dashboard/server.py"],
            creationflags=0x08000000,
            cwd=target_dir,
            env=env,
        )
        return jsonify(
            {"success": True, "message": "MultiContentApp starting in background..."}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/multicontent/status", methods=["GET"])
@login_required
def status_multicontent():
    """Check if MultiContentApp is reachable."""
    import socket

    online = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", 5000)) == 0:
                online = True
    except:
        pass
    return jsonify({"online": online})


# ─── PowerShell Terminal API ──────────────────────────────────────────────────
@app.route("/api/terminal/new", methods=["POST"])
@login_required
def terminal_new():
    """Create a new persistent PowerShell session."""
    data = request.get_json(silent=True) or {}
    cwd = data.get("cwd", None)
    agent_id = data.get("agent_id", None)

    if agent_id and agent_id.lower() in AGENTS:
        cwd = AGENTS[agent_id.lower()]["workspace"]

    pid_dir = cwd if (cwd and os.path.exists(cwd)) else "C:\\Users\\User"
    sid = str(uuid.uuid4())[:8]
    try:
        sess = PsSession(sid, cwd=pid_dir)
        with ps_sessions_lock:
            ps_sessions[sid] = sess
        print(f"[Terminal] Created session {sid} (alive={sess.alive}) cwd={pid_dir}")
        return jsonify({"session_id": sid, "alive": sess.alive})
    except Exception as e:
        print(f"[Terminal] Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/terminal/<sid>/send", methods=["POST"])
@login_required
def terminal_send(sid):
    """Send a command to an existing PowerShell session."""
    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        print(f"[Terminal] Session {sid} not found")
        return jsonify({"error": "Session not found"}), 404
    if not sess.alive:
        print(f"[Terminal] Session {sid} is dead")
        return jsonify({"error": "Session is dead"}), 410

    data = request.get_json(silent=True) or {}
    cmd = data.get("cmd", "")
    if not cmd:
        return jsonify({"error": "No command"}), 400

    ok = sess.send(cmd)
    print(f"[Terminal] Session {sid} send '{cmd}' -> ok={ok} alive={sess.alive}")
    return jsonify({"ok": ok, "alive": sess.alive})


# ── Agent Files API ───────────────────────────────────────────────────────────
@app.route("/api/gateway/<gw>/files", methods=["GET"])
@login_required
def api_gateway_files(gw):
    if gw not in AGENTS:
        return jsonify({"error": "Not found"}), 404
    agent = AGENTS[gw]
    base_dir = os.path.dirname(agent["config_file"])

    files = []
    try:
        # Recursive scan for .md and .json in base_dir and subdirectories
        for root, dirs, filenames in os.walk(base_dir):
            # Only go 2 levels deep to keep it fast
            rel_root = os.path.relpath(root, base_dir)
            depth = 0 if rel_root == "." else len(rel_root.split(os.sep))
            if depth > 2:
                continue

            for f in filenames:
                if f.endswith(".md") or f.endswith(".json"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, base_dir)
                    files.append(
                        {
                            "name": rel_path,
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


@app.route("/api/gateway/<gw>/file", methods=["GET", "POST"])
@login_required
def api_gateway_file(gw):
    if gw not in AGENTS:
        return jsonify({"error": "Not found"}), 404
    filename = (
        request.args.get("name")
        if request.method == "GET"
        else request.json.get("name")
    )

    # Path Traversal Protection
    if not filename or ".." in filename:
        return jsonify({"error": "Invalid filename"}), 400

    base_dir = os.path.dirname(AGENTS[gw]["config_file"])
    filepath = os.path.join(base_dir, filename)

    if request.method == "GET":
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        content = read_file_safe(filepath)
        return jsonify({"success": True, "content": content})

    if request.method == "POST":
        content = request.json.get("content", "")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# (Note: Overwritten by unified route above, safe to remove if code becomes too long)


# ── Settings API ──────────────────────────────────────────────────────────────
@app.route("/api/settings/scan-cli", methods=["GET"])
@login_required
def scan_cli():
    """Scan local file system for recognized AI CLI credentials/configs"""
    import os

    user_home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", os.path.join(user_home, "AppData", "Roaming"))
    localappdata = os.environ.get(
        "LOCALAPPDATA", os.path.join(user_home, "AppData", "Local")
    )

    results = []

    # 1. Gemini CLI
    gemini_path = os.path.join(user_home, ".gemini", "credentials")
    gemini_npm = os.path.join(appdata, "npm", "gemini")
    if (
        os.path.exists(gemini_path)
        or os.path.exists(gemini_npm)
        or os.path.exists(os.path.join(user_home, ".gemini"))
    ):
        results.append(
            {
                "id": "gemini",
                "name": "Gemini CLI",
                "badge": "gemini",
                "status": "registered",
                "path": gemini_path if os.path.exists(gemini_path) else gemini_npm,
                "default_model": "gemini-2.5-flash",
                "models_count": 3,
            }
        )

    # 2. Claude Code CLI
    claude_path = os.path.join(user_home, ".claude")
    if os.path.exists(claude_path) or os.path.exists(
        os.path.join(localappdata, "claude")
    ):
        results.append(
            {
                "id": "claude",
                "name": "Claude Code CLI",
                "badge": "claude",
                "status": "registered",
                "path": claude_path,
                "default_model": "claude-3-7-sonnet",
                "models_count": 2,
            }
        )

    # 3. Kilo Code
    kilo_path = os.path.join(appdata, "npm", "kilo")
    if os.path.exists(kilo_path) or os.path.exists(os.path.join(user_home, ".kilo")):
        results.append(
            {
                "id": "kilo",
                "name": "Kilo Code CLI",
                "badge": "kilo",
                "status": "registered",
                "path": kilo_path,
                "default_model": "kilo/kilo-auto/free",
                "models_count": 6,
            }
        )

    # 4. OpenAI
    openai_path = os.path.join(user_home, ".openai")
    if os.path.exists(openai_path):
        results.append(
            {
                "id": "openai",
                "name": "OpenAI CLI",
                "badge": "openai",
                "status": "registered",
                "path": openai_path,
                "default_model": "gpt-4o",
                "models_count": 4,
            }
        )

    # 5. Opencode CLI
    opencode_path = os.path.join(user_home, ".opencode")
    opencode_npm = os.path.join(appdata, "npm", "opencode")
    if os.path.exists(opencode_path) or os.path.exists(opencode_npm):
        results.append(
            {
                "id": "opencode",
                "name": "Opencode CLI",
                "badge": "opencode",
                "status": "registered",
                "path": opencode_path
                if os.path.exists(opencode_path)
                else opencode_npm,
                "default_model": "opencode-auto",
                "models_count": 2,
            }
        )

    # 6. Ollama (Just check if running port 11434 exists)
    import socket

    ollama_running = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", 11434)) == 0:
            ollama_running = True

    if ollama_running:
        results.append(
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "badge": "ollama",
                "status": "active",
                "path": "localhost:11434",
                "default_model": "llama3",
                "models_count": 0,
            }
        )
    else:
        results.append(
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "badge": "ollama",
                "status": "offline",
                "path": "Ollama not running. Start with: ollama serve",
                "default_model": "-",
                "models_count": 0,
            }
        )

    import time

    time.sleep(1.2)  # Fake processing time for UI effect
    return jsonify({"success": True, "detected": results})


@app.route("/api/terminal/<sid>/output")
@login_required
def terminal_output(sid):
    """Poll for output lines since a given line index."""
    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        print(f"[Terminal] Output: session {sid} not found")
        return jsonify({"error": "Session not found"}), 404

    since = int(request.args.get("since", 0))
    lines, total = sess.get_output(since)
    if lines:
        print(
            f"[Terminal] Session {sid} output: {len(lines)} new lines (since={since}, total={total})"
        )
    return jsonify({"lines": lines, "total": total, "alive": sess.alive})


@app.route("/api/terminal/<sid>/kill", methods=["POST"])
@login_required
def terminal_kill(sid):
    """Kill a PowerShell session."""
    with ps_sessions_lock:
        sess = ps_sessions.pop(sid, None)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404
    sess.kill()
    return jsonify({"ok": True})


@app.route("/api/terminal/list")
@login_required
def terminal_list():
    """List all active sessions."""
    with ps_sessions_lock:
        result = [
            {"session_id": sid, "alive": s.alive} for sid, s in ps_sessions.items()
        ]
    return jsonify(result)


# ─── Socket.IO Terminal Handlers ─────────────────────────────────────────────
terminal_processes = {}  # sid -> subprocess.Popen


@socketio.on("terminal_specific_create")
def handle_specific_terminal(data):
    sid = data.get("id")
    agent_id = data.get("agent_id")
    print(f"DEBUG: Creating specific terminal for {agent_id} (session {sid})")
    if not sid:
        return

    # Determine the directory for this agent
    agent_dir = "C:\\Users\\User"  # Default
    if agent_id in AGENTS:
        # Assuming the agent directory is relative to current dashboard
        agent_dir = os.path.abspath(os.path.join(os.getcwd(), "..", agent_id))

    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        _si = si
    except:
        _si = None

    p = subprocess.Popen(
        ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=0,
        startupinfo=_si,
        cwd=agent_dir if os.path.exists(agent_dir) else "C:\\Users\\User",
    )
    terminal_processes[sid] = p

    def reader():
        buffer = []
        last_emit = time.time()
        try:
            while True:
                char = p.stdout.read(1)
                if not char:
                    break
                buffer.append(char)

                # Emit if buffer is large or 10ms have passed
                now = time.time()
                if len(buffer) > 100 or (now - last_emit > 0.01 and buffer):
                    socketio.emit(f"terminal_output_{sid}", "".join(buffer))
                    buffer = []
                    last_emit = now
        except:
            pass
        finally:
            if buffer:
                socketio.emit(f"terminal_output_{sid}", "".join(buffer))
            socketio.emit(f"terminal_output_{sid}", "\r\n[Process terminated]\r\n")

    threading.Thread(target=reader, daemon=True).start()


@socketio.on("terminal_create")
def handle_terminal_create(data):
    sid = data.get("id")
    print(f"DEBUG: Creating terminal for session {sid}")
    if not sid:
        return

    # Start a PowerShell process for this terminal
    import ctypes

    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        _si = si
    except:
        _si = None

    p = subprocess.Popen(
        ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=0,
        startupinfo=_si,
        cwd="C:\\Users\\User",
    )
    terminal_processes[sid] = p

    def reader():
        buffer = []
        last_emit = time.time()
        try:
            while True:
                char = p.stdout.read(1)
                if not char:
                    break
                buffer.append(char)

                now = time.time()
                if len(buffer) > 100 or (now - last_emit > 0.01 and buffer):
                    socketio.emit(f"terminal_output_{sid}", "".join(buffer))
                    buffer = []
                    last_emit = now
        except Exception as e:
            print(f"DEBUG: Reader error for sid {sid}: {e}")
        finally:
            if buffer:
                socketio.emit(f"terminal_output_{sid}", "".join(buffer))
            socketio.emit(f"terminal_output_{sid}", "\r\n[Process terminated]\r\n")

    threading.Thread(target=reader, daemon=True).start()


@socketio.on("terminal_input")
def handle_terminal_input(data):
    sid = data.get("id")
    input_data = data.get("data")
    if sid in terminal_processes and input_data:
        p = terminal_processes[sid]
        try:
            # Strip \r to prevent line ending issues on Termux/SSH
            clean_data = input_data.replace('\r', '')
            p.stdin.write(clean_data)
            p.stdin.flush()
        except:
            pass


@socketio.on("disconnect")
def handle_disconnect():
    """Cleanup terminal processes when user leaves or disconnects."""
    from flask import request

    # With socketio, we identify the session by request.sid
    sid = getattr(request, "sid", None)
    if sid:
        print(f"DEBUG: Client disconnected (sid: {sid}). Cleaning up resources...")
        if sid in terminal_processes:
            p = terminal_processes.pop(sid, None)
            if p:
                try:
                    p.kill()
                    print(f"DEBUG: Killed terminal process for sid: {sid}")
                except Exception as e:
                    print(f"DEBUG: Error killing process for sid {sid}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# ─── Mission Control API ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# ── Mock Data Store ───────────────────────────────────────────────────────────
# In-memory store for Mission Control data (will be replaced with real gateway logs later)

MISSION_CONTROL_AGENTS = {
    "ace": {
        "id": "ace",
        "name": "Ace",
        "emoji": "🎯",
        "status": "online",
        "currentTask": "Building dashboard",
        "taskProgress": 75,
        "connections": ["pudding", "ameri"],
        "stats": {
            "tasksCompleted": 42,
            "errorsToday": 0,
            "uptimeSeconds": 3600,
        },
    },
    "pudding": {
        "id": "pudding",
        "name": "Pudding",
        "emoji": "🍮",
        "status": "online",
        "currentTask": "Coordinating team",
        "taskProgress": 90,
        "connections": ["ace", "ameri", "fah", "alpha", "j1"],
        "stats": {
            "tasksCompleted": 128,
            "errorsToday": 1,
            "uptimeSeconds": 7200,
        },
    },
    "ameri": {
        "id": "ameri",
        "name": "Ameri",
        "emoji": "🌸",
        "status": "busy",
        "currentTask": "Processing API requests",
        "taskProgress": 45,
        "connections": ["pudding", "ace"],
        "stats": {
            "tasksCompleted": 67,
            "errorsToday": 2,
            "uptimeSeconds": 5400,
        },
    },
    "fah": {
        "id": "fah",
        "name": "Fah",
        "emoji": "📊",
        "status": "idle",
        "currentTask": None,
        "taskProgress": None,
        "connections": ["pudding"],
        "stats": {
            "tasksCompleted": 35,
            "errorsToday": 0,
            "uptimeSeconds": 1800,
        },
    },
    "alpha": {
        "id": "alpha",
        "name": "Alpha",
        "emoji": "🔷",
        "status": "online",
        "currentTask": "Running diagnostics",
        "taskProgress": 60,
        "connections": ["pudding"],
        "stats": {
            "tasksCompleted": 19,
            "errorsToday": 0,
            "uptimeSeconds": 900,
        },
    },
    "j1": {
        "id": "j1",
        "name": "J1",
        "emoji": "📱",
        "status": "online",
        "currentTask": "WhatsApp relay active",
        "taskProgress": 100,
        "connections": ["pudding"],
        "stats": {
            "tasksCompleted": 53,
            "errorsToday": 0,
            "uptimeSeconds": 4320,
        },
        "specialStyle": {
            "borderColor": "#25D366",
            "badgeColor": "#25D366",
            "glow": True,
        },
    },
}

MISSION_CONTROL_TASKS = [
    {
        "id": "task-001",
        "agentId": "ace",
        "title": "Building dashboard component",
        "status": "running",
        "progress": 75,
        "startedAt": "2026-03-31T01:00:00Z",
    },
    {
        "id": "task-002",
        "agentId": "pudding",
        "title": "Coordinating subagent pipeline",
        "status": "running",
        "progress": 90,
        "startedAt": "2026-03-31T00:45:00Z",
    },
    {
        "id": "task-003",
        "agentId": "ameri",
        "title": "Processing API endpoints",
        "status": "running",
        "progress": 45,
        "startedAt": "2026-03-31T01:10:00Z",
    },
    {
        "id": "task-004",
        "agentId": "alpha",
        "title": "Running system diagnostics",
        "status": "running",
        "progress": 60,
        "startedAt": "2026-03-31T01:15:00Z",
    },
    {
        "id": "task-005",
        "agentId": "j1",
        "title": "WhatsApp message relay",
        "status": "running",
        "progress": 100,
        "startedAt": "2026-03-31T00:30:00Z",
    },
    {
        "id": "task-006",
        "agentId": "fah",
        "title": "Market analysis report",
        "status": "waiting",
        "progress": 0,
        "startedAt": "2026-03-31T01:20:00Z",
    },
]

MISSION_CONTROL_ALERTS = [
    {
        "id": "alert-001",
        "type": "success",
        "message": "All agents online and healthy",
        "timestamp": "2026-03-31T01:30:00Z",
        "agentId": None,
        "dismissed": False,
    },
    {
        "id": "alert-002",
        "type": "warning",
        "message": "Ameri: High memory usage detected",
        "timestamp": "2026-03-31T01:25:00Z",
        "agentId": "ameri",
        "dismissed": False,
    },
    {
        "id": "alert-003",
        "type": "info",
        "message": "Fah is idle and available for tasks",
        "timestamp": "2026-03-31T01:20:00Z",
        "agentId": "fah",
        "dismissed": False,
    },
    {
        "id": "alert-004",
        "type": "info",
        "message": "J1 WhatsApp relay connected",
        "timestamp": "2026-03-31T01:00:00Z",
        "agentId": "j1",
        "dismissed": False,
    },
    {
        "id": "alert-005",
        "type": "error",
        "message": "Task task-007 failed: timeout on external API",
        "timestamp": "2026-03-31T00:50:00Z",
        "agentId": "ameri",
        "dismissed": True,
    },
]

MISSION_CONTROL_ACHIEVEMENTS = [
    {
        "id": "ach-001",
        "name": "First Task Complete",
        "emoji": "🏆",
        "description": "Complete your first task",
        "unlocked": True,
        "progress": 1,
        "target": 1,
    },
    {
        "id": "ach-002",
        "name": "Team Player",
        "emoji": "🤝",
        "description": "Coordinate 10 subagent sessions",
        "unlocked": True,
        "progress": 10,
        "target": 10,
    },
    {
        "id": "ach-003",
        "name": "Centurion",
        "emoji": "💯",
        "description": "Complete 100 tasks across all agents",
        "unlocked": True,
        "progress": 100,
        "target": 100,
    },
    {
        "id": "ach-004",
        "name": "Uptime Champion",
        "emoji": "⏱️",
        "description": "Maintain 99% uptime for 24 hours",
        "unlocked": False,
        "progress": 18,
        "target": 24,
    },
    {
        "id": "ach-005",
        "name": "Error Free",
        "emoji": "✨",
        "description": "Zero errors for 48 hours",
        "unlocked": False,
        "progress": 12,
        "target": 48,
    },
    {
        "id": "ach-006",
        "name": "Full House",
        "emoji": "🏠",
        "description": "All 6 agents online simultaneously",
        "unlocked": False,
        "progress": 5,
        "target": 6,
    },
]


# ── GET /api/mission-control/agents ──────────────────────────────────────────
@app.route("/api/mission-control/agents")
@login_required
def mission_control_agents():
    """Return all agents with current status for Mission Control dashboard."""
    # TODO: Replace with real gateway health checks
    agents_list = list(MISSION_CONTROL_AGENTS.values())

    # Update online status from real gateway health where possible
    for agent_data in agents_list:
        agent_key = agent_data["id"]
        if agent_key in AGENTS:
            health = gateway_health(agent_key)
            agent_data["status"] = "online" if health["online"] else "offline"
            # Emit agent:status for real-time dashboard updates
            socketio.emit('agent:status', {'agentId': agent_data['id'], 'status': agent_data['status']})

    return jsonify(agents_list)


# ── GET /api/mission-control/tasks ───────────────────────────────────────────
@app.route("/api/mission-control/tasks")
@login_required
def mission_control_tasks():
    """Return current task queue with progress."""
    # TODO: Parse real gateway logs for task data
    # Emit task:complete for any tasks that reached 100%
    for task in MISSION_CONTROL_TASKS:
        if task.get("progress", 0) >= 100 and task.get("status") != "complete":
            task["status"] = "complete"
            socketio.emit('task:complete', {'taskId': task['id']})
    return jsonify(MISSION_CONTROL_TASKS)


# ── GET /api/mission-control/alerts ──────────────────────────────────────────
@app.route("/api/mission-control/alerts", methods=["GET", "POST"])
@login_required
def mission_control_alerts():
    """Return recent alerts (last 50) or create a new alert."""
    if request.method == "POST":
        data = request.json or {}
        alert_type = data.get("type", "info")
        message = data.get("message", "")
        agent_id = data.get("agentId")

        if not message:
            return jsonify({"success": False, "error": "message is required"}), 400

        alert_id = f"alert-{str(len(MISSION_CONTROL_ALERTS) + 1).zfill(3)}"
        new_alert = {
            "id": alert_id,
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "agentId": agent_id,
            "dismissed": False,
        }
        MISSION_CONTROL_ALERTS.append(new_alert)

        # Emit alert:new for real-time dashboard updates
        socketio.emit('alert:new', {
            'id': alert_id,
            'type': alert_type,
            'message': message,
            'timestamp': new_alert['timestamp'],
            'dismissed': False
        })

        return jsonify({"success": True, "alert": new_alert})

    # GET: Return alerts list
    # Filter out dismissed alerts, return most recent first
    active_alerts = [a for a in MISSION_CONTROL_ALERTS if not a["dismissed"]]
    dismissed_alerts = [a for a in MISSION_CONTROL_ALERTS if a["dismissed"]]
    # Active first, then dismissed, sorted by timestamp desc
    all_sorted = sorted(
        active_alerts + dismissed_alerts,
        key=lambda x: x["timestamp"],
        reverse=True,
    )
    return jsonify(all_sorted[:50])


# ── GET /api/mission-control/achievements ────────────────────────────────────
@app.route("/api/mission-control/achievements")
@login_required
def mission_control_achievements():
    """Return achievement status."""
    # Emit achievement:unlock for any newly unlocked achievements
    for ach in MISSION_CONTROL_ACHIEVEMENTS:
        if ach.get("unlocked") and ach.get("progress", 0) >= ach.get("target", 1):
            socketio.emit('achievement:unlock', {
                'id': ach['id'],
                'name': ach['name'],
                'emoji': ach['emoji'],
                'description': ach['description'],
                'unlocked': True
            })
    return jsonify(MISSION_CONTROL_ACHIEVEMENTS)


# ── POST /api/mission-control/tasks/<task_id>/reassign ───────────────────────
@app.route("/api/mission-control/tasks/<task_id>/reassign", methods=["POST"])
@login_required
def mission_control_task_reassign(task_id):
    """Reassign a task to a different agent."""
    data = request.json or {}
    new_agent_id = data.get("agentId")

    if not new_agent_id:
        return jsonify({"success": False, "error": "agentId is required"}), 400

    if new_agent_id not in MISSION_CONTROL_AGENTS:
        return jsonify({"success": False, "error": f"Unknown agent: {new_agent_id}"}), 404

    # Find the task
    task = None
    for t in MISSION_CONTROL_TASKS:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404

    old_agent = task["agentId"]

    # Emit task:complete if task was already at 100% before reassignment
    if task.get("progress", 0) >= 100 or task.get("status") == "complete":
        socketio.emit('task:complete', {'taskId': task_id})

    task["agentId"] = new_agent_id
    task["progress"] = 0  # Reset progress for new agent

    # Emit WebSocket event for real-time dashboard update
    socketio.emit(
        "task:progress",
        {
            "taskId": task_id,
            "agentId": new_agent_id,
            "progress": 0,
            "status": "running",
            "reassignedFrom": old_agent,
        },
    )

    return jsonify(
        {
            "success": True,
            "message": f"Task {task_id} reassigned from {old_agent} to {new_agent_id}",
            "task": task,
        }
    )


# ── POST /api/mission-control/alerts/<alert_id>/dismiss ──────────────────────
@app.route("/api/mission-control/alerts/<alert_id>/dismiss", methods=["POST"])
@login_required
def mission_control_alert_dismiss(alert_id):
    """Dismiss an alert."""
    alert = None
    for a in MISSION_CONTROL_ALERTS:
        if a["id"] == alert_id:
            alert = a
            break

    if not alert:
        return jsonify({"success": False, "error": f"Alert not found: {alert_id}"}), 404

    alert["dismissed"] = True

    # Emit WebSocket event
    socketio.emit("alert:dismiss", {"alertId": alert_id})

    return jsonify({"success": True, "message": f"Alert {alert_id} dismissed"})


# ── Socket.IO: Mission Control Events ────────────────────────────────────────
@socketio.on("task:reassign")
def handle_socket_task_reassign(data):
    """Handle WebSocket task reassignment requests."""
    task_id = data.get("taskId")
    agent_id = data.get("agentId")
    if not task_id or not agent_id:
        return

    for task in MISSION_CONTROL_TASKS:
        if task["id"] == task_id:
            old_agent = task["agentId"]
            task["agentId"] = agent_id
            task["progress"] = 0
            socketio.emit(
                "task:progress",
                {
                    "taskId": task_id,
                    "agentId": agent_id,
                    "progress": 0,
                    "status": "running",
                    "reassignedFrom": old_agent,
                },
            )
            break


@socketio.on("alert:dismiss")
def handle_socket_alert_dismiss(data):
    """Handle WebSocket alert dismissal."""
    alert_id = data.get("alertId")
    if not alert_id:
        return

    for alert in MISSION_CONTROL_ALERTS:
        if alert["id"] == alert_id:
            alert["dismissed"] = True
            socketio.emit("alert:dismiss", {"alertId": alert_id})
            break


# ═══════════════════════════════════════════════════════════════════════════════
# ─── End Mission Control API ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    print("Agent Dashboard (React/SocketIO) running at http://localhost:5050")
    socketio.run(
        app, host="0.0.0.0", port=5050, debug=False, allow_unsafe_werkzeug=True
    )
