"""
Cron Manager — Dynamic Job Scheduler with Persistence
Supports: once | daily | weekdays repeat modes
Jobs are persisted to data/schedule/jobs.json and reload on server restart.
"""

import threading
import time
import uuid
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# ── Paths ─────────────────────────────────────────────────────────────────────
script_dir    = Path(__file__).resolve().parent
dashboard_dir = script_dir.parent
JOBS_FILE     = dashboard_dir / "data" / "schedule" / "jobs.json"
JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Engine script map (kept in sync with engines_api.py ENGINES)
ENGINE_SCRIPTS: Dict[str, str] = {
    "trend-scan":    "api/engines/trend_scan/daily_trend_scan.py",
    "lookforward":   "api/engines/lookforward/scripts/run_pipeline_gemini.py",
    "shopee-scraper":"api/engines/shopee/tools/shopee_search_scraper.py",
    "fb-poster":     "api/engines/social/facebook_poster.py",
    "veo-gen":       "api/engines/veo_gen/manual_veo.py",
    "social-poster": "api/engines/social/facebook_poster.py",
    "image-gen":     "api/engines/image_gen/gen_from_prompt.py",
}


def _build_cmd(engine_id: str, options: Dict[str, Any]) -> List[str] | None:
    """Build subprocess command for a given engine + options."""
    script_rel = ENGINE_SCRIPTS.get(engine_id)
    if not script_rel:
        return None
    script = dashboard_dir / script_rel
    if not script.exists():
        return None

    cmd = [sys.executable, str(script)]

    if engine_id == "lookforward":
        topic = options.get("topic", "")
        if topic:
            cmd.append(topic)
        if options.get("tone"):
            cmd.extend(["--tone", options["tone"]])
        if options.get("content_type"):
            cmd.extend(["--mode", options["content_type"]])

    elif engine_id == "image-gen":
        if options.get("package_path"):
            cmd.extend(["--package-path", options["package_path"]])
        if options.get("model"):
            cmd.extend(["--model", options["model"]])
        if options.get("num_images"):
            cmd.extend(["--num-images", str(options["num_images"])])

    elif engine_id == "fb-poster" or engine_id == "social-poster":
        # Facebook poster takes no CLI args currently — content auto-detected
        pass

    elif engine_id == "shopee-scraper":
        if options.get("keyword"):
            cmd.append(options["keyword"])

    return cmd


class CronManager:
    def __init__(self):
        self.running   = False
        self.thread    = None
        self._lock     = threading.Lock()
        self._jobs: Dict[str, Dict[str, Any]] = {}   # {job_id: job_dict}
        self._last_ran: Dict[str, str] = {}           # {job_id: "YYYY-MM-DD HH:MM"}
        self._load_jobs()

    # ──────────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────────

    def _load_jobs(self):
        """Load persisted jobs from disk on startup."""
        try:
            if JOBS_FILE.exists():
                with open(JOBS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._jobs = data.get("jobs", {})
                print(f"[CronManager] Loaded {len(self._jobs)} persisted job(s).")
        except Exception as e:
            print(f"[CronManager] Failed to load jobs: {e}")
            self._jobs = {}

    def _save_jobs(self):
        """Persist current job list to disk (call inside _lock)."""
        try:
            with open(JOBS_FILE, "w", encoding="utf-8") as f:
                json.dump({"jobs": self._jobs}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CronManager] Failed to save jobs: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def add_job(self, engine_id: str, run_time: str, repeat: str = "daily",
                options: Dict[str, Any] = None) -> str:
        """Add a new scheduled job. Returns job_id."""
        job_id = str(uuid.uuid4())[:8]
        job = {
            "id":        job_id,
            "engine_id": engine_id,
            "time":      run_time,   # "HH:MM"
            "repeat":    repeat,      # once | daily | weekdays
            "options":   options or {},
            "created_at": datetime.now().isoformat(),
            "last_run":  None,
            "run_count": 0,
            "active":    True,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._save_jobs()
        print(f"[CronManager] [+] Added job {job_id}: {engine_id} @ {run_time} ({repeat})")
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a job by ID. Returns True if found and removed."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self._save_jobs()
                print(f"[CronManager] [-] Removed job {job_id}")
                return True
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Return list of all active jobs."""
        with self._lock:
            return list(self._jobs.values())

    # ──────────────────────────────────────────────────────────────────────────
    # Scheduler Loop
    # ──────────────────────────────────────────────────────────────────────────

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread  = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        active = sum(1 for j in self._jobs.values() if j.get("active"))
        print(f"[CronManager] [OK] Scheduler started. Active jobs: {active}")

    def stop(self):
        self.running = False

    def _run_loop(self):
        while self.running:
            now          = datetime.now()
            current_hhmm = now.strftime("%H:%M")
            current_day  = now.strftime("%A")  # Monday, Tuesday…
            current_ts   = now.strftime("%Y-%m-%d %H:%M")

            with self._lock:
                jobs_snapshot = list(self._jobs.items())

            for job_id, job in jobs_snapshot:
                if not job.get("active"):
                    continue

                # Has this job already fired this minute?
                if self._last_ran.get(job_id) == current_ts:
                    continue

                # Check time match
                if job["time"] != current_hhmm:
                    continue

                # Check repeat/day constraints
                repeat = job.get("repeat", "daily")
                if repeat == "weekdays" and current_day in ("Saturday", "Sunday"):
                    continue

                # Fire!
                print(f"[CronManager] [!] Triggering job {job_id}: {job['engine_id']} @ {current_hhmm}")
                self._last_ran[job_id] = current_ts
                self._fire_job(job)

                # If once — deactivate after firing
                if repeat == "once":
                    with self._lock:
                        if job_id in self._jobs:
                            self._jobs[job_id]["active"] = False
                            self._jobs[job_id]["last_run"] = current_ts
                            self._jobs[job_id]["run_count"] += 1
                            self._save_jobs()
                else:
                    with self._lock:
                        if job_id in self._jobs:
                            self._jobs[job_id]["last_run"] = current_ts
                            self._jobs[job_id]["run_count"] += 1
                            self._save_jobs()

            time.sleep(30)   # Check every 30s

    def _fire_job(self, job: Dict[str, Any]):
        """Spawn the engine subprocess in a daemon thread (non-blocking)."""
        cmd = _build_cmd(job["engine_id"], job.get("options", {}))
        if not cmd:
            print(f"[CronManager] [ERR] Cannot build command for engine: {job['engine_id']}")
            return

        def _spawn():
            try:
                env = __import__("os").environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(dashboard_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                # Log output to file
                log_dir  = dashboard_dir / "data" / "logs" / "history" / job["engine_id"]
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / f"cron_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file, "w", encoding="utf-8") as lf:
                    for line in proc.stdout:
                        lf.write(line)
                        lf.flush()
                proc.wait(timeout=900)
                print(f"[CronManager] [OK] Job {job['id']} finished (exit {proc.returncode})")
            except Exception as e:
                print(f"[CronManager] [ERR] Job {job['id']} error: {e}")

        threading.Thread(target=_spawn, daemon=True).start()


# ── Global instance ───────────────────────────────────────────────────────────
scheduler = CronManager()


def start_scheduler():
    scheduler.start()
