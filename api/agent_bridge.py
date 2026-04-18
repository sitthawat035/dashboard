# dashboard/api/agent_bridge.py
import sys
import os
import subprocess
import argparse
import json
from pathlib import Path

# --- Configuration & Paths ---
PYTHON_EXE = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
DASHBOARD_DIR = Path(__file__).parent.parent.absolute()
CONFIG_FILE = DASHBOARD_DIR / "data" / "config" / "ameri_settings.json"

# Default fallback settings
DEFAULT_CONFIG = {
    "ameri_status": "active",
    "content_strategy": {
        "niche": "Tech & Engineering",
        "tone": "Formal"
    },
    "dashboard_bridge": {
        "enabled_engines": ["trend-scan", "lookforward", "image-gen", "fb-poster"]
    }
}

ENGINES = {
    "trend-scan": "api/engines/trend_scan/daily_trend_scan.py",
    "lookforward": "api/engines/lookforward/scripts/run_pipeline_gemini.py",
    "image-gen": "api/engines/image_gen/gen_from_prompt.py",
    "fb-poster": "api/engines/social/facebook_poster.py",
}

def load_settings():
    """Safely load user settings from JSON or return defaults."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config ({e}). Using defaults.")
        return DEFAULT_CONFIG

def run_engine(engine_id, extra_args=None):
    settings = load_settings()
    
    # Check if Ameri is paused
    if settings.get("ameri_status") != "active":
        print(f"Agent Bridge: Ameri is currently paused (Status: {settings.get('ameri_status')}). Execution skipped.")
        return False

    if engine_id not in ENGINES:
        print(f"Error: Unknown engine '{engine_id}'")
        return False
    
    script_abs_path = DASHBOARD_DIR / ENGINES[engine_id]
    if not script_abs_path.exists():
        print(f"Error: Script not found at {script_abs_path}")
        return False
    
    cmd = [PYTHON_EXE, str(script_abs_path)]
    
    # Append smart arguments from config if they are not provided via CLI
    if not extra_args:
        extra_args = []
        if engine_id == "lookforward":
            niche = settings.get("content_strategy", {}).get("niche")
            tone = settings.get("persona", {}).get("tone")
            if niche: extra_args.append(niche)
            if tone: extra_args.extend(["--tone", tone])

    if extra_args:
        cmd.extend(extra_args)
        
    print(f"Agent Bridge: Launching {engine_id}...")
    print(f"  Final Command: {' '.join(cmd)}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["OPENCLAW_ROOT"] = str(DASHBOARD_DIR.parent.absolute())
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=str(DASHBOARD_DIR), 
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.stdout: print(result.stdout)
        if result.stderr: print(f"STDERR: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        print(f"💥 Bridge Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw Agent-to-Dashboard Bridge")
    parser.add_argument("--run", type=str, help="Engine ID to run")
    parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional arguments")
    
    args = parser.parse_args()
    if args.run:
        success = run_engine(args.run, args.args)
        sys.exit(0 if success else 1)
    else:
        # If run without args, print current settings summary
        cfg = load_settings()
        print(f"Ameri Bridge Status: {cfg.get('ameri_status')}")
        print(f"Current Niche: {cfg.get('content_strategy', {}).get('niche')}")
        print(f"Enabled Engines: {', '.join(cfg.get('dashboard_bridge', {}).get('enabled_engines', []))}")
