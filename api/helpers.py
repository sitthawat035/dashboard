# ╔═══════════════════════════════════════════════════════╗
# ║  api/helpers.py — Shared utility functions            ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import re
import json
import time
from typing import Optional
from pathlib import Path
from datetime import datetime, date, timedelta as _td

from api.config import AGENTS

# ─── File Utilities ───────────────────────────────────────────────────────────

def read_file_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None


_TS_RE = re.compile(r'(\d{4}-\d{2}-\d{2}T)(\d{2}:\d{2}:\d{2})\.\d+([+\-]\d{2}:\d{2})')

def shorten_ts(line: str) -> str:
    """Trim full ISO timestamp to HH:MM:SS+TZ.
    e.g. 2026-04-05T02:48:30.123+07:00 → 02:48:30+07:00
    """
    return _TS_RE.sub(lambda m: m.group(2) + m.group(3), line, count=1)


def read_file_tail(path: str, max_lines: int = 200):
    """Read last N lines of a file (handles large files efficiently via seek)."""
    try:
        p = Path(str(path))
        if not p.exists():
            return [], 0
        size = p.stat().st_size
        with open(str(p), "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(max(0, file_size - 32768))  # ~32KB for 200 lines
            data = f.read().decode("utf-8", errors="replace")
        tail_lines = data.splitlines()[-max_lines:]
        return [shorten_ts(line) for line in tail_lines], size
    except Exception as e:
        return [f"[Error reading log: {e}]"], 0


# ─── Agent Config / Subagents ─────────────────────────────────────────────────

def read_agent_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


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
                excluded = os.getenv('EXCLUDED_SUBAGENTS', 'fah').split(',')
                if ag_id in excluded:
                    continue
                name = a.get("name", ag_id)
                subagents.append({"id": ag_id, "name": name})
    except Exception as e:
        print(f"Error reading subagents from {config_path}: {e}")
    return subagents


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


# ─── Log Resolution ───────────────────────────────────────────────────────────

def resolve_active_log_file(agent_key: str) -> str:
    """Return the log file for an agent.
    Priority:
      1) Dashboard-managed gateway.log (FORCE_COLOR=1, written by dashboard start)
      2) Dated log in the agent state dir  (openclaw-YYYY-MM-DD.log)
      3) Generic openclaw.log in state dir
      4) /tmp/openclaw-{port}.log  (written when openclaw started externally)
      5) Return configured path so watcher waits for file creation
    """
    agent = AGENTS.get(agent_key, {})
    configured = agent.get("log_file", "")
    state_dir = os.path.dirname(agent.get("config_file", ""))
    port = agent.get("port", 0)

    # 1) Dashboard-managed log (most reliable, has ANSI color)
    try:
        p = Path(configured)
        if p.exists() and p.stat().st_size > 0:
            return str(p.absolute())
    except Exception:
        pass

    # 2) Scan agent state dir for dated / generic logs
    if state_dir and os.path.exists(state_dir):
        sd = Path(state_dir)
        for delta in (0, 1):
            d = date.today() - _td(days=delta)
            cand = sd / f"openclaw-{d.strftime('%Y-%m-%d')}.log"
            if cand.exists() and cand.stat().st_size > 0:
                return str(cand.absolute())
        cand = sd / "openclaw.log"
        if cand.exists() and cand.stat().st_size > 0:
            return str(cand.absolute())

    # 3) /tmp/openclaw-{port}.log — written when openclaw is started externally
    if port:
        tmp_cand = Path(f"/tmp/openclaw-{port}.log")
        if tmp_cand.exists() and tmp_cand.stat().st_size > 0:
            return str(tmp_cand.absolute())

    # 4) Any /tmp/openclaw*.log newer than 5 min (external run without port in name)
    try:
        import glob, time as _time
        now = _time.time()
        for tmp_f in sorted(glob.glob("/tmp/openclaw*.log"), key=os.path.getmtime, reverse=True):
            if now - os.path.getmtime(tmp_f) < 300:  # newer than 5 min
                return tmp_f
    except Exception:
        pass

    # 5) Last resort: return configured path so watcher waits for creation
    try:
        p = Path(configured)
        if p.exists():
            return str(p.absolute())
    except Exception:
        pass
    return configured


def detect_running_port(agent_key: str) -> Optional[int]:
    """Scan last 50 lines of log for 'listening on ws://...:PORT' using seek."""
    log_path = resolve_active_log_file(agent_key)
    if not log_path or not Path(log_path).exists():
        return None

    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(max(0, file_size - 8192))
            lines = f.read().splitlines()[-50:]
            for line in lines:
                decoded = line.decode("utf-8", errors="replace")
                m = re.search(r"listening on ws://[^:]+:(\d+)", decoded)
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    return None


# ─── Gateway Health ───────────────────────────────────────────────────────────

def gateway_health(agent_key, override_port=None):
    """Check gateway by HTTP against OpenClaw __canvas__ endpoint."""
    import requests as _requests

    if agent_key not in AGENTS:
        return {"online": False, "error": "Unknown agent"}

    agent = AGENTS[agent_key]
    try:
        cfg = read_agent_config(agent["config_file"])
        gw_cfg = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}

        # Try to detect actual running port from log first
        live_port = detect_running_port(agent_key)
        port = override_port if override_port else (live_port if live_port else gw_cfg.get("port", agent["port"]))

        try:
            import socket as _socket
            with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
                s.settimeout(0.5)  # 0.5s is plenty for localhost check
                online = (s.connect_ex(("127.0.0.1", port)) == 0)
        except Exception:
            online = False

        return {
            "online": online,
            "port": port, # Return the port we actually found
            "status_code": 200 if online else 503,
            "data": "OK" if online else "Offline",
        }
    except Exception as e:
        return {"online": False, "error": str(e)}
