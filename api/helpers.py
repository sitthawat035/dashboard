# ╔═══════════════════════════════════════════════════════╗
# ║  api/helpers.py — Shared utility functions            ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import re
import json
import time
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
    """Read last N lines of a file (handles large files efficiently)."""
    try:
        p = Path(str(path))
        if not p.exists():
            return [], 0
        size = p.stat().st_size
        with open(str(p), "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-max_lines:] if len(lines) > max_lines else lines
        return [shorten_ts(line.rstrip("\n")) for line in tail], size
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
                if ag_id == "fah":
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
    """Return the configured log file for an agent.
    Always prefer the dashboard-managed log file (has ANSI color)
    over any system-wide /tmp/openclaw logs (which are stripped of color).
    """
    agent = AGENTS.get(agent_key, {})
    configured = agent.get("log_file", "")
    state_dir = os.path.dirname(agent.get("config_file", ""))

    # 1) Always use configured log_file — written with FORCE_COLOR=1
    try:
        p = Path(configured)
        if p.exists():
            return str(p.absolute())
    except Exception:
        pass

    # 2) Fallback: scan agent state dir for dated logs (no /tmp fallback)
    if state_dir and os.path.exists(state_dir):
        sd = Path(state_dir)
        for delta in (0, 1):
            d = date.today() - _td(days=delta)
            cand = sd / f"openclaw-{d.strftime('%Y-%m-%d')}.log"
            if cand.exists() and cand.stat().st_size > 0:
                return str(cand.absolute())
        cand = sd / "openclaw.log"
        if cand.exists():
            return str(cand.absolute())

    # 3) Last resort: return configured path (watcher will wait for file)
    return configured


def detect_running_port(agent_key: str) -> int | None:
    """Scan latest log lines for 'listening on ws://...:PORT'."""
    log_path = resolve_active_log_file(agent_key)
    if not log_path or not Path(log_path).exists():
        return None

    # Check if log exists
    if not log_path or not Path(log_path).exists():
        return None

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-50:]
            for line in reversed(lines):
                m = re.search(r"listening on ws://[^:]+:(\d+)", line)
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
