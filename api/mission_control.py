# api/mission_control.py — Mission Control routes + socket events (extracted from server.py)
from flask import Blueprint, jsonify, request
from datetime import datetime
from api.config import AGENTS
from api.auth import login_required
from api.helpers import gateway_health

mission_control_bp = Blueprint("mission_control", __name__)

# ── Shared socketio ref — injected by init_mission_control_socketio() ──
_socketio = None


def init_mission_control_socketio(socketio):
    """Call from server.py to inject socketio instance and register socket events."""
    global _socketio
    _socketio = socketio

    @socketio.on("task:reassign")
    def handle_socket_task_reassign(data):
        task_id = data.get("taskId")
        agent_id = data.get("agentId")
        if not task_id or not agent_id:
            return
        for task in MISSION_CONTROL_TASKS:
            if task["id"] == task_id:
                old_agent = task["agentId"]
                task["agentId"] = agent_id
                task["progress"] = 0
                socketio.emit("task:progress", {"taskId": task_id, "agentId": agent_id,
                                                 "progress": 0, "status": "running", "reassignedFrom": old_agent})
                break

    @socketio.on("alert:dismiss")
    def handle_socket_alert_dismiss(data):
        alert_id = data.get("alertId")
        if not alert_id:
            return
        for alert in MISSION_CONTROL_ALERTS:
            if alert["id"] == alert_id:
                alert["dismissed"] = True
                socketio.emit("alert:dismiss", {"alertId": alert_id})
                break


# ── Data helpers ──
def get_mission_control_agents():
    mc_agents = {}
    for key, agent in AGENTS.items():
        mc_agents[key] = {
            "id": key,
            "name": agent.get("name", key),
            "emoji": agent.get("emoji", "🤖"),
            "status": "online" if gateway_health(key)["online"] else "offline",
            "currentTask": "Monitoring" if gateway_health(key)["online"] else None,
            "taskProgress": 100 if gateway_health(key)["online"] else None,
            "connections": [k for k in AGENTS.keys() if k != key],
            "stats": {"tasksCompleted": 0, "errorsToday": 0, "uptimeSeconds": 0}
        }
        if key == "j1":
            mc_agents[key]["specialStyle"] = {"borderColor": "#25D366", "badgeColor": "#25D366", "glow": True}
    return mc_agents


# ── Static data ──
MISSION_CONTROL_TASKS = [
    {"id": "task-001", "agentId": "ace", "title": "Building dashboard component",
     "status": "running", "progress": 75, "startedAt": "2026-03-31T01:00:00Z"},
    {"id": "task-002", "agentId": "pudding", "title": "Coordinating subagent pipeline",
     "status": "running", "progress": 90, "startedAt": "2026-03-31T00:45:00Z"},
    {"id": "task-003", "agentId": "ameri", "title": "Processing API endpoints",
     "status": "running", "progress": 45, "startedAt": "2026-03-31T01:10:00Z"},
    {"id": "task-004", "agentId": "alpha", "title": "Running system diagnostics",
     "status": "running", "progress": 60, "startedAt": "2026-03-31T01:15:00Z"},
    {"id": "task-005", "agentId": "j1", "title": "WhatsApp message relay",
     "status": "running", "progress": 100, "startedAt": "2026-03-31T00:30:00Z"},
    {"id": "task-006", "agentId": "fah", "title": "Market analysis report",
     "status": "waiting", "progress": 0, "startedAt": "2026-03-31T01:20:00Z"},
]

MISSION_CONTROL_ALERTS = [
    {"id": "alert-001", "type": "success", "message": "All agents online and healthy",
     "timestamp": "2026-03-31T01:30:00Z", "agentId": None, "dismissed": False},
    {"id": "alert-002", "type": "warning", "message": "Ameri: High memory usage detected",
     "timestamp": "2026-03-31T01:25:00Z", "agentId": "ameri", "dismissed": False},
    {"id": "alert-003", "type": "info", "message": "Fah is idle and available for tasks",
     "timestamp": "2026-03-31T01:20:00Z", "agentId": "fah", "dismissed": False},
    {"id": "alert-004", "type": "info", "message": "J1 WhatsApp relay connected",
     "timestamp": "2026-03-31T01:00:00Z", "agentId": "j1", "dismissed": False},
    {"id": "alert-005", "type": "error", "message": "Task task-007 failed: timeout on external API",
     "timestamp": "2026-03-31T00:50:00Z", "agentId": "ameri", "dismissed": True},
]

MISSION_CONTROL_ACHIEVEMENTS = [
    {"id": "ach-001", "name": "First Task Complete", "emoji": "🏆",
     "description": "Complete your first task", "unlocked": True, "progress": 1, "target": 1},
    {"id": "ach-002", "name": "Team Player", "emoji": "🤝",
     "description": "Coordinate 10 subagent sessions", "unlocked": True, "progress": 10, "target": 10},
    {"id": "ach-003", "name": "Centurion", "emoji": "💯",
     "description": "Complete 100 tasks across all agents", "unlocked": True, "progress": 100, "target": 100},
    {"id": "ach-004", "name": "Uptime Champion", "emoji": "⏱️",
     "description": "Maintain 99% uptime for 24 hours", "unlocked": False, "progress": 18, "target": 24},
    {"id": "ach-005", "name": "Error Free", "emoji": "✨",
     "description": "Zero errors for 48 hours", "unlocked": False, "progress": 12, "target": 48},
    {"id": "ach-006", "name": "Full House", "emoji": "🏠",
     "description": "All 6 agents online simultaneously", "unlocked": False, "progress": 5, "target": 6},
]


# ── Routes ──
@mission_control_bp.route("/api/mission-control/agents")
@login_required
def mission_control_agents():
    mc_agents = get_mission_control_agents()
    agents_list = list(mc_agents.values())
    for agent_data in agents_list:
        agent_key = agent_data["id"]
        if agent_key in AGENTS:
            health = gateway_health(agent_key)
            agent_data["status"] = "online" if health["online"] else "offline"
            if _socketio:
                _socketio.emit("agent:status", {"agentId": agent_data["id"], "status": agent_data["status"]})
    return jsonify(agents_list)


@mission_control_bp.route("/api/mission-control/tasks")
@login_required
def mission_control_tasks():
    for task in MISSION_CONTROL_TASKS:
        if task.get("progress", 0) >= 100 and task.get("status") != "complete":
            task["status"] = "complete"
            if _socketio:
                _socketio.emit("task:complete", {"taskId": task["id"]})
    return jsonify(MISSION_CONTROL_TASKS)


@mission_control_bp.route("/api/mission-control/alerts", methods=["GET", "POST"])
@login_required
def mission_control_alerts():
    if request.method == "POST":
        data = request.json or {}
        alert_type = data.get("type", "info")
        message = data.get("message", "")
        agent_id = data.get("agentId")
        if not message:
            return jsonify({"success": False, "error": "message is required"}), 400
        alert_id = f"alert-{str(len(MISSION_CONTROL_ALERTS) + 1).zfill(3)}"
        new_alert = {"id": alert_id, "type": alert_type, "message": message,
                     "timestamp": datetime.now().isoformat(), "agentId": agent_id, "dismissed": False}
        MISSION_CONTROL_ALERTS.append(new_alert)
        if _socketio:
            _socketio.emit("alert:new", {"id": alert_id, "type": alert_type, "message": message,
                                         "timestamp": new_alert["timestamp"], "dismissed": False})
        return jsonify({"success": True, "alert": new_alert})

    active_alerts = [a for a in MISSION_CONTROL_ALERTS if not a["dismissed"]]
    dismissed_alerts = [a for a in MISSION_CONTROL_ALERTS if a["dismissed"]]
    all_sorted = sorted(active_alerts + dismissed_alerts, key=lambda x: x["timestamp"], reverse=True)
    return jsonify(all_sorted[:50])


@mission_control_bp.route("/api/mission-control/achievements")
@login_required
def mission_control_achievements():
    for ach in MISSION_CONTROL_ACHIEVEMENTS:
        if ach.get("unlocked") and ach.get("progress", 0) >= ach.get("target", 1):
            if _socketio:
                _socketio.emit("achievement:unlock", {"id": ach["id"], "name": ach["name"],
                                                       "emoji": ach["emoji"], "description": ach["description"],
                                                       "unlocked": True})
    return jsonify(MISSION_CONTROL_ACHIEVEMENTS)


@mission_control_bp.route("/api/mission-control/tasks/<task_id>/reassign", methods=["POST"])
@login_required
def mission_control_task_reassign(task_id):
    data = request.json or {}
    new_agent_id = data.get("agentId")
    if not new_agent_id:
        return jsonify({"success": False, "error": "agentId is required"}), 400
    if new_agent_id not in AGENTS:
        return jsonify({"success": False, "error": f"Unknown agent: {new_agent_id}"}), 404
    task = next((t for t in MISSION_CONTROL_TASKS if t["id"] == task_id), None)
    if not task:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404
    old_agent = task["agentId"]
    if task.get("progress", 0) >= 100 or task.get("status") == "complete":
        if _socketio:
            _socketio.emit("task:complete", {"taskId": task_id})
    task["agentId"] = new_agent_id
    task["progress"] = 0
    if _socketio:
        _socketio.emit("task:progress", {"taskId": task_id, "agentId": new_agent_id,
                                         "progress": 0, "status": "running", "reassignedFrom": old_agent})
    return jsonify({"success": True, "message": f"Task {task_id} reassigned from {old_agent} to {new_agent_id}", "task": task})


@mission_control_bp.route("/api/mission-control/alerts/<alert_id>/dismiss", methods=["POST"])
@login_required
def mission_control_alert_dismiss(alert_id):
    alert = next((a for a in MISSION_CONTROL_ALERTS if a["id"] == alert_id), None)
    if not alert:
        return jsonify({"success": False, "error": f"Alert not found: {alert_id}"}), 404
    alert["dismissed"] = True
    if _socketio:
        _socketio.emit("alert:dismiss", {"alertId": alert_id})
    return jsonify({"success": True, "message": f"Alert {alert_id} dismissed"})
