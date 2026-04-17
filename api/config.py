# ╔═══════════════════════════════════════════════════════╗
# ║  api/config.py — Dynamic Agent Configuration          ║
# ║  Grand Refactor (v4 Clean Edition)                    ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
from pathlib import Path

# ─── Environment & Paths ────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DASHBOARD_PASSWORD = "1234"
# Dashboard is in root/dashboard, so parent is root
DASHBOARD_DIR = Path(__file__).parent.parent.absolute()
ENV_PATH = DASHBOARD_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# CENTRALIZED PATHS (สัมพันธ์กับ PowerShell Profile)
ROOT_DIR = Path(os.getenv('OPENCLAW_ROOT', DASHBOARD_DIR.parent.absolute()))

# ─── Dynamic Discovery ──────────────────────────────────────────────────────────

def discover_agents():
    """Scans ROOT_DIR for .openclaw-* folders and builds the agent mapping."""
    agents = {}
    
    # Color/Emoji mapping fallback for known indices
    THEMES = {
        "1": {"name": "Ace", "emoji": "🚀", "color": "#00d4ff"},
        "2": {"name": "Ameri", "emoji": "🧠", "color": "#ff6b9d"},
        "3": {"name": "Pudding", "emoji": "🍮", "color": "#f97316"},
        "4": {"name": "Alpha", "emoji": "⚙️", "color": "#9E9E9E"},
        "5": {"name": "Fah", "emoji": "💖", "color": "#ff6b9d"},
        "6": {"name": "Pudding G2", "emoji": "🔮", "color": "#f97316"},
        "7": {"name": "BOQ G2", "emoji": "🏗️", "color": "#3b82f6"},
    }

    try:
        # Sort to keep the list consistent (1, 2, 3...)
        items = sorted(list(ROOT_DIR.iterdir()), key=lambda x: x.name)
        
        for p in items:
            if p.is_dir() and p.name.startswith(".openclaw-"):
                try:
                    profile_id = p.name.replace(".openclaw-", "")
                    config_path = p / "openclaw.json"
                    
                    # If openclaw.json doesn't exist, we skip or use defaults
                    cfg_data = {}
                    if config_path.exists():
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg_data = json.load(f)
                    
                    # Resolve key data from JSON or defaults
                    gateway_cfg = cfg_data.get("gateway", {})
                    # Correct token path: gateway.auth.token
                    auth_cfg = gateway_cfg.get("auth", {}) if isinstance(gateway_cfg.get("auth"), dict) else {}
                    
                    # Key name for the dictionary (e.g., 'ameri' or 'profile-2')
                    # We'll use the name from JSON if available, otherwise lowercase theme name
                    theme = THEMES.get(profile_id, {})
                    raw_name = cfg_data.get("name", theme.get("name", f"Profile-{profile_id}"))
                    agent_key = raw_name.lower().replace(" ", "")

                    agents[agent_key] = {
                        "id": agent_key,
                        "profile_id": profile_id,
                        "name": raw_name,
                        "emoji": theme.get("emoji", "🤖"),
                        "port": gateway_cfg.get("port", 18888 + int(profile_id) if profile_id.isdigit() else 18888),
                        "token": auth_cfg.get("token", ""),
                        "workspace": str((p / "workspace").absolute()),
                        "gateway_cmd": str((p / "gateway.cmd").absolute()),
                        "config_file": str(config_path.absolute()),
                        "color": theme.get("color", "#8b5ceb"),
                        # Absolute paths for logs to ensure Windows finds them
                        "log_file": str((p / "gateway.log").absolute()),
                        "err_file": str((p / "gateway.err").absolute()),
                    }
                except Exception as e:
                    print(f"[Discovery] Error reading {p.name}: {e}")
                    
    except Exception as e:
        print(f"[Discovery] Critical error scanning root: {e}")
    
    return agents

# Initial registration
AGENTS = discover_agents()

def reload_agents():
    global AGENTS
    AGENTS = discover_agents()
    return AGENTS

# Print summary to console for debugging
print(f"--- [v4 Discovery] Loaded {len(AGENTS)} agents from {ROOT_DIR} ---")
for k, v in AGENTS.items():
    print(f"  > {v['name']} ({v['id']}) on port {v['port']} at {v['profile_id']}")
