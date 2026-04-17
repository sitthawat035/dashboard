# ╔═══════════════════════════════════════════════════════╗
# ║  api/subagents.py — subagent stream + conversation    ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import re
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request

from api.config import AGENTS
from api.helpers import resolve_active_log_file

subagents_bp = Blueprint("subagents", __name__)


@subagents_bp.route("/api/subagents/stream")
def subagent_stream():
    """Parse real OpenClaw gateway logs for embedded subagent activity (Public for UI)."""
    result = {
        "subagents": [],
        "timestamp": datetime.now().isoformat(),
    }

    TS_PATTERN = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+\-]\d{2}:\d{2})"
    EMBEDDED_MARK = r"\[agent/embedded\]"
    LANE_PATTERN = r"lane=session:agent:([^:]+):main"
    RUNID_PATTERN = r"runId=([a-f0-9\-]{36})"
    MODEL_PATTERN = r"model=([^\s]+)"

    for agent_key, agent in AGENTS.items():
        log_path = resolve_active_log_file(agent_key)
        if not log_path or not Path(log_path).exists():
            continue

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue

        sessions: dict = {}

        for raw_line in lines:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue

            ts_match = re.match(TS_PATTERN, line)
            if not ts_match:
                continue
            ts_str = ts_match.group(1)
            ts_display = ts_str[:19].replace("T", " ")
            rest = line[len(ts_str):].strip()

            if re.search(EMBEDDED_MARK, rest):
                runid_m = re.search(RUNID_PATTERN, rest)
                lane_m = re.search(LANE_PATTERN, rest)
                runid = runid_m.group(1) if runid_m else None
                subagent_name = lane_m.group(1) if lane_m else None

                if not runid:
                    continue

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

                if subagent_name and sess["session_key"] == "subagent":
                    sess["session_key"] = subagent_name
                    sess["task"] = subagent_name

                model_m = re.search(MODEL_PATTERN, rest)
                if model_m:
                    sess["model"] = model_m.group(1)

                if "embedded run agent end" in rest:
                    error_m = re.search(r"error=(.+)$", rest)
                    if error_m:
                        err_text = error_m.group(1).strip()
                        sess["errors"].append(err_text[:120])
                        sess["status"] = "error"

                elif "failover decision" in rest:
                    decision_m = re.search(r"decision=(\w+)", rest)
                    reason_m = re.search(r"reason=(\w+)", rest)
                    if decision_m and decision_m.group(1) == "candidate_succeeded":
                        sess["status"] = "complete"
                    elif reason_m:
                        sess["status"] = "error"

            elif re.search(r"\[diagnostic\]", rest):
                lane_m = re.search(LANE_PATTERN, rest)
                if lane_m:
                    subagent_name = lane_m.group(1)
                    err_m = re.search(r'error="(.+?)"', rest)
                    for sess in sessions.values():
                        if sess["session_key"] == subagent_name:
                            if err_m:
                                err_short = err_m.group(1)[:120]
                                if err_short not in sess["errors"]:
                                    sess["errors"].append(err_short)
                            sess["status"] = "error"
                            break

            else:
                bracket_m = re.match(r"^\[[\w/\-]+\]", rest)
                if not bracket_m and len(rest) > 10:
                    for sess in reversed(list(sessions.values())):
                        if sess["agent"] == agent_key and sess["status"] == "running":
                            sess["snippet"] = rest[:200]
                            if not sess["task"] or sess["task"] == sess["session_key"]:
                                sess["task"] = rest[:80]
                            break

        for sess in sessions.values():
            errors = sess.pop("errors", [])
            sess.pop("runId", None)
            if not sess["snippet"] and errors:
                sess["snippet"] = errors[-1]
            elif errors and sess["status"] == "error":
                sess["snippet"] = errors[-1]
            result["subagents"].append(sess)

    result["subagents"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    result["subagents"] = result["subagents"][:100]

    return jsonify(result)


@subagents_bp.route("/api/subagents/conversation/<agent_key>")
def subagent_conversation(agent_key):
    """Extract real agent conversation lines from gateway log."""
    import unicodedata

    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404

    agent = AGENTS[agent_key]
    log_path = resolve_active_log_file(agent_key)
    max_messages = int(request.args.get("limit", 200))

    if not log_path or not Path(log_path).exists():
        return jsonify({"messages": [], "agent": agent_key})

    ANSI_RE = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    TS_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+\-]\d{2}:\d{2})')
    MODULE_RE = re.compile(r'^\[[a-zA-Z0-9_/\-\.]+\]')

    messages = []
    current_msg = None
    current_ts = ""

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return jsonify({"messages": [], "error": str(e)})

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        line = ANSI_RE.sub("", line)
        line_stripped = line.strip().replace("\x00", "")
        if not line_stripped:
            if current_msg:
                messages.append(current_msg)
                current_msg = None
            continue

        if all(c == '\x00' or c == ' ' for c in line_stripped):
            continue

        ts_match = TS_PATTERN.match(line)
        if ts_match:
            ts_str = ts_match.group(1)
            ts_display = ts_str[:19].replace("T", " ")
            rest = line[len(ts_str):].strip()
            rest = ANSI_RE.sub("", rest).strip()

            if MODULE_RE.match(rest) or not rest or len(rest) < 3:
                if current_msg:
                    messages.append(current_msg)
                    current_msg = None
                continue

            if any(skip in rest for skip in [
                "Gateway failed to start", "Port ", "gateway already running",
                "Stop it", "schtasks", "openclaw gateway", "pid "
            ]):
                if current_msg:
                    messages.append(current_msg)
                    current_msg = None
                continue

            if current_msg:
                messages.append(current_msg)

            current_msg = {"ts": ts_display, "text": rest}
            current_ts = ts_display

        else:
            clean_line = ANSI_RE.sub("", line).strip()
            if not clean_line or all(c == '\x00' for c in clean_line):
                continue

            if current_msg:
                current_msg["text"] += "\n" + clean_line
            else:
                if clean_line and not MODULE_RE.match(clean_line):
                    current_msg = {"ts": current_ts, "text": clean_line}

    if current_msg:
        messages.append(current_msg)

    messages = messages[-max_messages:]

    return jsonify({
        "messages": messages,
        "agent": agent_key,
        "total": len(messages),
        "timestamp": datetime.now().isoformat(),
    })
