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

        import sys
        is_windows = sys.platform.startswith("win") or os.path.exists("/c/Windows")

        if is_windows:
            # Windows: use PowerShell
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
                cwd=cwd or os.path.expanduser("~"),
            )
        else:
            # Linux/WSL: use bash with pseudo-terminal for proper shell behavior
            import pty
            import select

            # Create master and slave pty
            master_fd, slave_fd = pty.openpty()
            slave_name = os.ttyname(slave_fd)

            self.process = subprocess.Popen(
                ["/bin/bash", "--norc", "--noprofile"],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=cwd or os.path.expanduser("~"),
                env=dict(os.environ, TERM="xterm-256color"),
                start_new_session=True,
                pass_fds=(slave_fd,),
            )
            # Close slave fd in parent - only process uses it
            os.close(slave_fd)
            self._master_fd = master_fd
            self._use_pty = True

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        try:
            if getattr(self, '_use_pty', False):
                # Use PTY master fd for reading
                import select as _select
                master_fd = self._master_fd
                buf = ""
                while True:
                    ready, _, _ = _select.select([master_fd], [], [], 0.5)
                    if ready:
                        try:
                            chunk = os.read(master_fd, 4096).decode('utf-8', errors='replace')
                            if not chunk:
                                break
                            buf += chunk
                            # Process complete lines
                            while "\n" in buf:
                                line, buf = buf.split("\n", 1)
                                line = line.strip("\r")
                                if line:
                                    with self.lock:
                                        self.lines.append(line)
                                        if len(self.lines) > MAX_OUTPUT_LINES:
                                            self.lines = self.lines[-MAX_OUTPUT_LINES:]
                        except OSError:
                            break
                    # Check if process is still alive
                    if self.process.poll() is not None:
                        break
            else:
                # Original non-PTY reading
                stdout = self.process.stdout
                if stdout is None:
                    return
                buf = ""
                while True:
                    try:
                        chunk = stdout.read(1024)
                        if not chunk:
                            break
                        buf += chunk
                        while "\n" in buf:
                            line, buf = buf.split("\n", 1)
                            line = line.strip("\r")
                            if line:
                                with self.lock:
                                    self.lines.append(line)
                                    if len(self.lines) > MAX_OUTPUT_LINES:
                                        self.lines = self.lines[-MAX_OUTPUT_LINES:]
                    except BlockingIOError:
                        continue
        except Exception as e:
            print(f"[Terminal] Read error: {e}")
        finally:
            self.alive = False
            if getattr(self, '_master_fd', None):
                try:
                    os.close(self._master_fd)
                except:
                    pass

    def send(self, cmd: str):
        if self.process.poll() is not None:
            self.alive = False
            return False
        try:
            if getattr(self, '_use_pty', False):
                # Write to PTY master fd
                master_fd = self._master_fd
                clean_cmd = cmd.replace("\r", "").strip() + "\n"
                os.write(master_fd, clean_cmd.encode('utf-8'))
            else:
                # Original stdin writing
                stdin = self.process.stdin
                if stdin is None:
                    self.alive = False
                    return False
                clean_cmd = cmd.replace("\r", "").strip() + "\n"
                stdin.write(clean_cmd)
                stdin.flush()
            return True
        except Exception as e:
            print(f"[Terminal] Send error: {e}")
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
        if getattr(self, '_master_fd', None):
            try:
                os.close(self._master_fd)
            except:
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
@login_required
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


# ── Alias routes for CLI Helper (Frontend) ──────────────────────────────────────

@terminal_bp.route("/api/terminal/create", methods=["POST"])
@login_required
def terminal_create():
    """Alias for /api/terminal/new - Create a new terminal session."""
    return terminal_new()


@terminal_bp.route("/api/terminal/input", methods=["POST"])
@login_required
def terminal_input():
    """Alias for /api/terminal/<sid>/send - Send command to terminal."""
    data = request.get_json(silent=True) or {}
    sid = data.get("id")
    if not sid:
        return jsonify({"error": "Missing session id"}), 400

    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404
    if not sess.alive:
        return jsonify({"error": "Session is dead"}), 410

    cmd = data.get("data", "")
    if not cmd:
        return jsonify({"output": ""}), 200

    ok = sess.send(cmd)

    # Get output after sending
    since = 0
    lines, total = sess.get_output(since)

    # Format output as a string
    output = "\n".join(lines[-20:]) if lines else ""

    return jsonify({"ok": ok, "output": output, "alive": sess.alive})


@terminal_bp.route("/api/terminal/<sid>/poll", methods=["GET"])
@login_required
def terminal_poll(sid):
    """Poll for new output lines."""
    with ps_sessions_lock:
        sess = ps_sessions.get(sid)
    if sess is None:
        return jsonify({"error": "Session not found"}), 404

    since = int(request.args.get("since", 0))
    lines, total = sess.get_output(since)
    return jsonify({"lines": lines, "total": total, "alive": sess.alive})
