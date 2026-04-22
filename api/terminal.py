# ╔═══════════════════════════════════════════════════════╗
# ║  api/terminal.py — PsSession class + terminal routes  ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import subprocess
import threading
import uuid
from flask import Blueprint, jsonify, request

from api.config import AGENTS
from api.auth import login_required

terminal_bp = Blueprint("terminal", __name__)

MAX_OUTPUT_LINES = 500

# ─── Session Store ────────────────────────────────────────────────────────────
ps_sessions: dict = {}
ps_sessions_lock = threading.Lock()


# ─── PsSession Class ──────────────────────────────────────────────────────────
class PsSession:
    def __init__(self, session_id: str, cwd: str | None = None):
        self.session_id = session_id
        self.lines: list[str] = []
        self.lock = threading.Lock()
        self.alive = True

        try:
            si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
            si.wShowWindow = 0
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
            cwd=cwd or r"C:\Users\User",
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
            clean_cmd = cmd.replace("\r", "") + "\n"
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


# ─── Routes ───────────────────────────────────────────────────────────────────

@terminal_bp.route("/api/terminal/new", methods=["POST"])
@login_required
def terminal_new():
    """Create a new persistent PowerShell session."""
    data = request.get_json(silent=True) or {}
    cwd = data.get("cwd", None)
    agent_id = data.get("agent_id", None)

    if agent_id and agent_id.lower() in AGENTS:
        agent = AGENTS[agent_id.lower()]
        cwd = agent.get("workspace")
        if not cwd or not os.path.exists(cwd):
            cwd = os.path.dirname(agent["config_file"])
    
    # Fallback to absolute root if all else fails
    if not cwd or not os.path.exists(cwd):
        from api.config import ROOT_DIR
        cwd = str(ROOT_DIR)

    sid = str(uuid.uuid4())[:8]
    try:
        sess = PsSession(sid, cwd=cwd)
        with ps_sessions_lock:
            ps_sessions[sid] = sess
        print(f"[Terminal] Created session {sid} (alive={sess.alive}) | CWD: {cwd}")
        return jsonify({"session_id": sid, "alive": sess.alive})
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Terminal] Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@terminal_bp.route("/api/terminal/<sid>/send", methods=["POST"])
@login_required
def terminal_send(sid):
    """Send a command to an existing PowerShell session."""
    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404
    if not sess.alive:
        return jsonify({"error": "Session is dead"}), 410

    data = request.get_json(silent=True) or {}
    cmd = data.get("cmd", "")
    if not cmd:
        return jsonify({"error": "No command"}), 400

    ok = sess.send(cmd)
    print(f"[Terminal] Session {sid} send '{cmd}' -> ok={ok} alive={sess.alive}")
    return jsonify({"ok": ok, "alive": sess.alive})


@terminal_bp.route("/api/terminal/<sid>/output")
def terminal_output(sid):
    """Poll for output lines since a given line index."""
    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404

    since = int(request.args.get("since", 0))
    lines, total = sess.get_output(since)
    return jsonify({"lines": lines, "total": total, "alive": sess.alive})


@terminal_bp.route("/api/terminal/<sid>/kill", methods=["POST"])
@login_required
def terminal_kill(sid):
    """Kill a PowerShell session."""
    with ps_sessions_lock:
        sess = ps_sessions.pop(sid, None)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404
    sess.kill()
    return jsonify({"ok": True})


@terminal_bp.route("/api/terminal/list")
@login_required
def terminal_list():
    """List all active sessions."""
    with ps_sessions_lock:
        result = [
            {"session_id": sid, "alive": s.alive} for sid, s in ps_sessions.items()
        ]
    return jsonify(result)
