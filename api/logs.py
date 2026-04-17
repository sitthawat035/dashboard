# ╔═══════════════════════════════════════════════════════╗
# ║  api/logs.py — /api/gateway/<key>/log route           ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

from datetime import datetime
from flask import Blueprint, jsonify, request

from api.config import AGENTS
from api.auth import login_required
from api.helpers import resolve_active_log_file, read_file_tail

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/api/gateway/<agent_key>/log")
@login_required
def gateway_log(agent_key):
    """Return last N lines of gateway log + err for an agent."""
    if agent_key not in AGENTS:
        return jsonify({"error": "Unknown agent"}), 404

    agent = AGENTS[agent_key]
    max_lines = int(request.args.get("lines", 100))

    active_log_path = resolve_active_log_file(agent_key)
    log_lines, log_size = read_file_tail(active_log_path, max_lines)
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
