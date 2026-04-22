# ╔══════════════════════════════════════════════════════════════════╗
# ║  AGENT DASHBOARD - server.py  (Phase 6 — Final Clean)          ║
# ║  Flask + Socket.IO entry point — ~60 lines                     ║
# ║                                                                ║
# ║  ALL business logic lives in api/ modules:                     ║
# ║    api/config.py            — AGENTS dict, constants           ║
# ║    api/auth.py              — login_required, /api/login       ║
# ║    api/helpers.py           — read_file_*, gateway_health      ║
# ║    api/status.py            — /api/status, /api/memory         ║
# ║    api/logs.py              — /api/gateway/<key>/log           ║
# ║    api/gateway.py           — start/stop/restart/model routes  ║
# ║    api/subagents.py         — /api/subagents/*                 ║
# ║    api/terminal.py          — PsSession + terminal routes      ║
# ║    api/socket_events.py     — log streaming + socketio         ║
# ║    api/engines_api.py       — Engine Hub routes                ║
# ║    api/message.py           — /api/message/<key>      [NEW P6] ║
# ║    api/system.py            — kill-all, scan-cli       [NEW P6]║
# ║    api/mission_control.py   — Mission Control routes   [NEW P6]║
# ╚══════════════════════════════════════════════════════════════════╝

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import time
from datetime import timedelta

# ─── Import all Blueprints ────────────────────────────────────────────────────
from api.config import AGENTS, DASHBOARD_PASSWORD, DASHBOARD_DIR, ROOT_DIR
from api.auth import auth_bp
from api.status import status_bp
from api.logs import logs_bp
from api.gateway import gateway_bp
from api.subagents import subagents_bp
from api.terminal import terminal_bp
from api.engines_api import engines_bp
from api.message import message_bp
from api.system import system_bp
from api.mission_control import mission_control_bp, init_mission_control_socketio
from api.socket_events import init_socketio, cleanup_zombie_threads
from api.cron_manager import start_scheduler
from api.schedule_api import schedule_bp
from api.hermes_bridge import hermes_bp, init_hermes_bridge
from api.reports_api import reports_bp

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
app.secret_key = "joepv_dashboard_v4_dynamic_key"
app.permanent_session_lifetime = timedelta(days=7)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)
CORS(app, supports_credentials=True)

# ─── Register ALL Blueprints ─────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(status_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(gateway_bp)
app.register_blueprint(subagents_bp)
app.register_blueprint(terminal_bp)
app.register_blueprint(engines_bp)
app.register_blueprint(message_bp)
app.register_blueprint(system_bp)
app.register_blueprint(mission_control_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(hermes_bp)
app.register_blueprint(reports_bp)

# ─── Init Socket.IO Events ───────────────────────────────────────────────────
init_socketio(socketio)
init_mission_control_socketio(socketio)
init_hermes_bridge(socketio)


# ─── Static ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ─── Periodic Cleanup ─────────────────────────────────────────────────────────
def periodic_cleanup():
    """Run periodic cleanup of zombie threads every 5 minutes."""
    while True:
        try:
            cleanup_zombie_threads()
        except Exception as e:
            print(f"[Cleanup] Error during periodic cleanup: {e}")
        time.sleep(300)


cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

# Start Engine Scheduler (Cron)
start_scheduler()


# ─── Startup ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Agent Dashboard (React/SocketIO) running at http://localhost:5050")
    socketio.run(app, host="0.0.0.0", port=5050, debug=False, allow_unsafe_werkzeug=True)
