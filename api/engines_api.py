# dashboard/api/engines_api.py
from flask import Blueprint, jsonify, request
import subprocess
import sys
import threading
import time
import os
from pathlib import Path
from api.config import DASHBOARD_DIR
from api.auth import login_required

# Load environment variables from both dashboard and lookforward .env files
from dotenv import load_dotenv
load_dotenv(DASHBOARD_DIR / '.env')





engines_bp = Blueprint("engines", __name__)

# Track running processes and their status
engine_status = {}  # {engine_id: {status, started_at, finished_at, exit_code, log_tail}}
engine_processes = {}  # {engine_id: Popen} â€” live process refs
engine_status_lock = threading.Lock()

ENGINES = {
    "trend-scan": {
        "name": "Daily Trend Scan",
        "path": "api/engines/trend_scan/daily_trend_scan.py",
        "description": "Scans tech trends and Shopee viral keywords.",
    },
    "lookforward": {
        "name": "Lookforward Content Gen",
        "path": "api/engines/lookforward/scripts/run_pipeline_gemini.py",
        "description": "Generates high-authority tech analysis and visuals.",
    },
    "shopee-scraper": {
        "name": "Shopee Search Scraper",
        "path": "api/engines/shopee/tools/shopee_search_scraper.py",
        "description": "Scrapes product data from Shopee stealthily.",
    },
    "fb-poster": {
        "name": "Facebook Auto-Poster",
        "path": "api/engines/social/facebook_poster.py",
        "description": "Publishes latest ready-to-post content to Facebook Page automatically.",
    },
    "veo-gen": {
        "name": "VEO Video Prompt Gen",
        "path": "api/engines/veo_gen/manual_veo.py",
        "description": "Analyzes products and generates locked prompts for Google Flow.",
    },
    "social-poster": {
        "name": "Social Media Poster",
        "path": "api/engines/social/facebook_poster.py",
        "description": "Automated Facebook page publishing via Playwright.",
    },
    "image-gen": {
        "name": "Image Gen (FLUX)",
        "path": "api/engines/image_gen/gen_from_prompt.py",
        "description": "Generates images from Lookforward image prompts via HuggingFace FLUX.1.",
    },
}


@engines_bp.route("/api/engines/list", methods=["GET"])
@login_required
def list_engines():
    # Merge ENGINES definition with live status
    result = {}
    for eid, engine in ENGINES.items():
        entry = {**engine}
        with engine_status_lock:
            if eid in engine_status:
                entry["_status"] = engine_status[eid]
        result[eid] = entry
    return jsonify(result)


@engines_bp.route("/api/engines/status", methods=["GET"])
@login_required
def get_all_engine_status():
    """Return live status of all engines."""
    with engine_status_lock:
        return jsonify(dict(engine_status))


@engines_bp.route("/api/engines/status/<engine_id>", methods=["GET"])
@login_required
def get_engine_status(engine_id):
    """Return live status of a specific engine."""
    with engine_status_lock:
        if engine_id in engine_status:
            return jsonify(engine_status[engine_id])
    return jsonify({"status": "idle"}), 200


@engines_bp.route("/api/engines/run/<engine_id>", methods=["POST"])
@login_required
def run_engine(engine_id):
    if engine_id not in ENGINES:
        return jsonify({"success": False, "error": "Unknown engine"}), 404

    # Check if already running
    with engine_status_lock:
        if (
            engine_id in engine_status
            and engine_status[engine_id].get("status") == "running"
        ):
            return jsonify({"success": False, "error": "Engine already running"}), 409

    engine = ENGINES[engine_id]
    script_path = DASHBOARD_DIR / engine["path"]

    if not script_path.exists():
        return jsonify(
            {
                "success": False,
                "error": f"Script not found: {engine['path']} (resolved: {script_path})",
            }
        ), 404

    # Get options from request body â€” silent=True prevents 400 on missing/bad JSON
    options = request.get_json(force=True, silent=True) or {}

    # Build command with sys.executable (same Python as server)
    cmd = [sys.executable, str(script_path)]
    if engine_id == "lookforward" and options.get("topic"):
        cmd.append(options["topic"])
        if options.get("tone"):
            cmd.extend(["--tone", options["tone"]])
        if options.get("content_type"):
            cmd.extend(["--mode", options["content_type"]])
        if options.get("word_count"):
            cmd.extend(["--max-words", str(options["word_count"])])
        if not options.get("include_images", True):
            cmd.append("--no-images")
            
    elif engine_id == "shopee-scraper" and options.get("keyword"):
        cmd.extend([options["keyword"]])
        if options.get("limit"):
            cmd.extend(["--count", str(options["limit"])])
            
    elif engine_id == "veo-gen":
        if options.get("aspect_ratio"):
            cmd.extend(["--aspect-ratio", options["aspect_ratio"]])
        if options.get("duration"):
            cmd.extend(["--duration", options["duration"]])
        if options.get("style"):
            cmd.extend(["--style", options["style"]])
        if options.get("image_path"):
            cmd.extend(["--image", options["image_path"]])

    elif engine_id == "image-gen":
        if options.get("package_path"):
            cmd.extend(["--package-path", options["package_path"]])
        if options.get("model"):
            cmd.extend(["--model", options["model"]])
        if options.get("num_images"):
            cmd.extend(["--num-images", str(options["num_images"])])

    elif engine_id == "fb-poster":
        # Schedule mode — hand off to cron manager instead of running now
        if options.get("mode") == "scheduled" and options.get("schedule_time"):
            from api.cron_manager import scheduler
            repeat = options.get("repeat", "daily")
            job_id = scheduler.add_job(
                engine_id="fb-poster",
                run_time=options["schedule_time"],
                repeat=repeat,
                options={k: v for k, v in options.items() if k not in ("mode", "schedule_time", "repeat")},
            )
            return jsonify({"success": True, "scheduled": True, "job_id": job_id,
                            "message": f"FB Auto-Post scheduled at {options['schedule_time']} ({repeat})"})

    elif engine_id == "trend-scan":
        if options.get("custom_niche"):
            cmd.extend(["--custom-niche", options["custom_niche"]])
        elif options.get("niche") and options["niche"] != "tech":
            cmd.extend(["--niche", options["niche"]])
    # Setup history directory
    history_dir = DASHBOARD_DIR / "data" / "logs" / "history" / engine_id
    history_dir.mkdir(parents=True, exist_ok=True)
    run_dt = time.strftime("%Y%m%d_%H%M%S")
    history_file_path = history_dir / f"{run_dt}.log"

    # Init status
    with engine_status_lock:
        engine_status[engine_id] = {
            "status": "running",
            "started_at": time.time(),
            "finished_at": None,
            "exit_code": None,
            "log_tail": ["[Engine starting...]"],
        }

    print(f"ðŸš€ Starting engine '{engine_id}': {' '.join(cmd)}")

    # Run in background with real-time output streaming via Popen
    def execute():
        log_lines = []
        exit_code = -1
        proc = None
        try:
            env = os.environ.copy()
            env["OPENCLAW_ROOT"] = os.getenv("OPENCLAW_ROOT", str(DASHBOARD_DIR.parent.absolute()))
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.Popen(
                cmd,
                cwd=str(DASHBOARD_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,  # Line-buffered
                env=env,
            )
            engine_processes[engine_id] = proc

            # Stream output line-by-line in real-time
            with open(history_file_path, "w", encoding="utf-8") as f_history:
                for line in proc.stdout:
                    line = line.rstrip("\n\r")
                    if line.strip():
                        log_lines.append(line)
                        f_history.write(line + "\n")
                        f_history.flush()
                        
                        # Keep last 200 lines in memory
                        if len(log_lines) > 200:
                            log_lines = log_lines[-200:]
                        # Update status with live log tail
                        with engine_status_lock:
                            engine_status[engine_id]["log_tail"] = log_lines[-50:]

            proc.wait(timeout=600)
            exit_code = proc.returncode

            if exit_code == 0:
                print(f"âœ… Engine {engine_id} completed successfully.")
            else:
                print(f"âš ï¸ Engine {engine_id} exited with code {exit_code}")
                if not log_lines:
                    log_lines = [f"Process exited with code {exit_code}"]

        except subprocess.TimeoutExpired:
            exit_code = -2
            log_lines.append("ERROR: Engine timed out after 600 seconds")
            print(f"â° Engine {engine_id} timed out.")
            if proc:
                proc.kill()
        except Exception as e:
            exit_code = -1
            log_lines.append(f"ERROR: {str(e)}")
            print(f"âŒ Engine {engine_id} failed: {e}")
        finally:
            engine_processes.pop(engine_id, None)
            with engine_status_lock:
                engine_status[engine_id] = {
                    "status": "success" if exit_code == 0 else "error",
                    "started_at": engine_status.get(engine_id, {}).get("started_at"),
                    "finished_at": time.time(),
                    "exit_code": exit_code,
                    "log_tail": log_lines[-50:],
                }

    thread = threading.Thread(target=execute, daemon=True)
    thread.start()

    return jsonify(
        {"success": True, "message": f"Engine {engine_id} started in background."}
    )


@engines_bp.route("/api/engines/upload", methods=["POST"])
@login_required
def upload_engine_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
        
    upload_dir = DASHBOARD_DIR / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = upload_dir / safe_name
    file.save(file_path)
    
    return jsonify({
        "success": True, 
        "path": str(file_path.absolute())
    })


@engines_bp.route("/api/engines/history/<engine_id>", methods=["GET"])
@login_required
def get_engine_history(engine_id):
    history_dir = DASHBOARD_DIR / "data" / "logs" / "history" / engine_id
    if not history_dir.exists():
        return jsonify({"success": True, "files": []})
        
    files = [f.name for f in history_dir.iterdir() if f.is_file() and f.name.endswith(".log")]
    files.sort(reverse=True) # Newest first
    return jsonify({"success": True, "files": files})


@engines_bp.route("/api/engines/history/log/<engine_id>/<filename>", methods=["GET"])
@login_required
def get_engine_history_log(engine_id, filename):
    history_file = DASHBOARD_DIR / "data" / "logs" / "history" / engine_id / filename
    if not history_file.exists():
        return jsonify({"success": False, "error": "File not found"}), 404
        
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@engines_bp.route("/api/engines/preview/<engine_id>", methods=["GET"])
@login_required
def get_engine_preview(engine_id):
    content_dir = DASHBOARD_DIR / "data" / "content"
    preview_data = {}
    
    if engine_id == "lookforward":
        # Find latest directory in lookforward
        lf_base = content_dir / "lookforward"
        # Since it uses dates like 2026-04-15, we find the newest folder
        if not lf_base.exists():
            return jsonify({"success": False, "error": "No lookforward output found."}), 404
            
        folders = [d for d in lf_base.iterdir() if d.is_dir() and d.name.startswith("20")]
        if not folders:
            return jsonify({"success": False, "error": "No recent runs found."}), 404
            
        folders.sort(reverse=True, key=lambda p: p.name)
        latest_date_folder = folders[0]
        
        # Inside date folder, find newest project folder
        projects = [d for d in latest_date_folder.iterdir() if d.is_dir()]
        if not projects:
            return jsonify({"success": False, "error": "No projects in latest folder."}), 404
            
        projects.sort(reverse=True, key=lambda p: p.stat().st_mtime)
        latest_project = projects[0]
        
        preview_data = {"project": latest_project.name}
        
        # Read text files
        for f_name in ["post.txt", "caption.txt", "hashtags.txt"]:
            file_path = latest_project / f_name
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    preview_data[f_name.replace(".txt", "")] = f.read()

        # Read prompts guide if exists
        prompts_file = latest_project / "media" / "prompts_guide.txt"
        if prompts_file.exists():
            with open(prompts_file, "r", encoding="utf-8") as f:
                preview_data["image_prompts"] = f.read()
                
        return jsonify({"success": True, "preview_type": "lookforward", "data": preview_data})
        
    elif engine_id == "shopee-scraper":
        import csv
        csv_path = content_dir / "shopee" / "scraped" / "items.csv"
        if not csv_path.exists():
            return jsonify({"success": False, "error": "No Shopee items.csv found."}), 404
            
        try:
            items = []
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 10: # Preview top 10
                        break
                    items.append(row)
            return jsonify({"success": True, "preview_type": "shopee", "data": {"items": items}})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    return jsonify({"success": False, "error": "Preview not supported for this engine."}), 400



