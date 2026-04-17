# ╔═══════════════════════════════════════════════════════╗
# ║  api/status.py — /api/status + /api/memory routes     ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, jsonify, request

from api.config import AGENTS
from api.auth import login_required
from api.helpers import (
    gateway_health,
    detect_running_port,
    resolve_active_log_file,
    read_agent_config,
    get_subagents,
    get_memory_files,
    read_file_safe,
)

status_bp = Blueprint("status", __name__)


def _check_single_agent(key, agent, active_owners):
    """Build status dict for one agent — designed for parallel execution."""
    cfg = read_agent_config(agent["config_file"])

    # Determine Name: Config > Hardcoded
    agent_name = cfg.get("ui", {}).get("assistant", {}).get("name")
    if not agent_name:
        agent_name = agent["name"]

    # Determine Port: Log Detection > Config File > Hardcoded
    gw_cfg = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}
    config_port = gw_cfg.get("port", agent["port"])

    owner_key = active_owners.get(config_port, (None, 0))[0]

    detected_port = None
    for p, (okey, omt) in active_owners.items():
        if okey == key:
            detected_port = p
            break

    port_to_check = detected_port if detected_port else config_port

    if owner_key and owner_key != key and not detected_port:
        health = {"online": False, "data": "Occupied by other agent"}
    else:
        health = gateway_health(key, override_port=port_to_check)

    # Workspace resolution
    workspace = cfg.get("agents", {}).get("defaults", {}).get("workspace")
    if not workspace:
        workspace = agent["workspace"]
    workspace = workspace.strip()

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

    port = gw_cfg.get("port", agent["port"])

    return key, {
        "id": key,
        "name": agent_name,
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


@status_bp.route("/api/status")
def api_status():
    """Public endpoint — no authentication required for gateway health check."""
    from api.config import reload_agents
    agents_map = reload_agents()
    result = {}

    # Group 1: Identify "Real" Running Ports from logs for all agents
    active_owners = {}  # { port: (agent_key, mtime) }
    for k, a in agents_map.items():
        lp = resolve_active_log_file(k)
        if lp and os.path.exists(lp):
            mt = os.path.getmtime(lp)
            rp = detect_running_port(k)
            if rp and (time.time() - mt < 45):
                if rp not in active_owners or mt > active_owners[rp][1]:
                    active_owners[rp] = (k, mt)

    # Parallel health checks — all agents checked concurrently (~0.5s total)
    with ThreadPoolExecutor(max_workers=min(len(agents_map), 8)) as executor:
        futures = {
            executor.submit(_check_single_agent, key, agent, active_owners): key
            for key, agent in agents_map.items()
        }
        for future in as_completed(futures):
            try:
                agent_key, agent_data = future.result()
                result[agent_key] = agent_data
            except Exception as e:
                agent_key = futures[future]
                print(f"[Status] Error checking {agent_key}: {e}")

    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


@status_bp.route("/api/status/<agent_key>/health")
def api_agent_health(agent_key):
    """Ultra-lightweight single-agent health check — ~5ms.
    Uses direct socket check only. No filesystem scanning.
    Called every 2s by frontend during gateway start polling.
    """
    import socket as _socket

    if agent_key not in AGENTS:
        return jsonify({"online": False, "error": "Unknown agent"}), 404

    agent = AGENTS[agent_key]
    port = agent.get("port", 0)
    online = False
    try:
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            online = (s.connect_ex(("127.0.0.1", port)) == 0)
    except Exception:
        pass

    response = jsonify({"online": online, "port": port})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@status_bp.route("/api/memory/<agent_key>")
@login_required
def api_memory(agent_key):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    workspace = AGENTS[agent_key]["workspace"]
    files = get_memory_files(workspace)
    return jsonify(files)


@status_bp.route("/api/memory/<agent_key>/<filename>")
@login_required
def api_memory_file(agent_key, filename):
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404
    from pathlib import Path
    workspace = AGENTS[agent_key]["workspace"]
    path = Path(workspace) / "memory" / filename
    content = read_file_safe(path)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"filename": filename, "content": content})
