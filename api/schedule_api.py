# api/schedule_api.py
"""
Schedule API Blueprint
Manages persistent scheduled jobs for engine automation.

Routes:
  GET  /api/schedule           — list all jobs
  POST /api/schedule           — add a job
  DELETE /api/schedule/<id>    — cancel a job
  GET  /api/schedule/status    — scheduler health
"""

from flask import Blueprint, jsonify, request
from api.auth import login_required
from api.cron_manager import scheduler

schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/api/schedule", methods=["GET"])
@login_required
def list_jobs():
    jobs = scheduler.list_jobs()
    return jsonify({"success": True, "jobs": jobs})


@schedule_bp.route("/api/schedule", methods=["POST"])
@login_required
def add_job():
    body = request.get_json(force=True, silent=True) or {}

    engine_id = body.get("engine_id")
    run_time  = body.get("time")        # "HH:MM"
    repeat    = body.get("repeat", "daily")   # once | daily | weekdays
    options   = body.get("options", {})

    if not engine_id or not run_time:
        return jsonify({"success": False, "error": "engine_id and time are required"}), 400

    # Validate time format
    import re
    if not re.match(r"^\d{2}:\d{2}$", run_time):
        return jsonify({"success": False, "error": "time must be HH:MM format"}), 400

    if repeat not in ("once", "daily", "weekdays"):
        return jsonify({"success": False, "error": "repeat must be: once | daily | weekdays"}), 400

    job_id = scheduler.add_job(engine_id=engine_id, run_time=run_time, repeat=repeat, options=options)
    return jsonify({"success": True, "job_id": job_id})


@schedule_bp.route("/api/schedule/<job_id>", methods=["DELETE"])
@login_required
def remove_job(job_id):
    removed = scheduler.remove_job(job_id)
    if removed:
        return jsonify({"success": True, "message": f"Job {job_id} removed."})
    return jsonify({"success": False, "error": "Job not found"}), 404


@schedule_bp.route("/api/schedule/status", methods=["GET"])
@login_required
def scheduler_status():
    jobs = scheduler.list_jobs()
    return jsonify({
        "success": True,
        "running": scheduler.running,
        "job_count": len(jobs),
        "jobs": jobs,
    })
