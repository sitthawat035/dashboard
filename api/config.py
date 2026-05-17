# ╔═══════════════════════════════════════════════════════╗
# ║  api/config.py — Dynamic Agent Configuration          ║
# ║  Grand Refactor (v4 Clean Edition)                    ║
# ╚═══════════════════════════════════════════════════════╝

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# ─── Environment & Paths ────────────────────────────────────────────────────────
load_dotenv()
# Dashboard is in root/dashboard, so parent is root
DASHBOARD_DIR = Path(__file__).parent.parent.absolute()
ENV_PATH = DASHBOARD_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD")
if not DASHBOARD_PASSWORD:
    raise RuntimeError("DASHBOARD_PASSWORD env variable must be set")

# CENTRALIZED PATHS (สัมพันธ์กับ PowerShell Profile)
ROOT_DIR = Path(os.getenv('OPENCLAW_ROOT', DASHBOARD_DIR.parent.absolute()))

# ── Build THEMES from env vars ──
def _build_themes():
    themes = {}
    max_slots = int(os.getenv("AGENT_MAX_SLOTS", "7"))
    default_emoji = os.getenv("DEFAULT_AGENT_EMOJI", "🤖")
    default_color = os.getenv("DEFAULT_AGENT_COLOR", "#8b5ceb")
    for i in range(1, max_slots + 1):
        prefix = f"AGENT_{i}"
        name = os.getenv(f"{prefix}_NAME", "")
        if name:
            themes[str(i)] = {
                "name": name,
                "emoji": os.getenv(f"{prefix}_EMOJI", default_emoji),
                "color": os.getenv(f"{prefix}_COLOR", default_color),
            }
    return themes

THEMES = _build_themes()

# ─── Dynamic Discovery ──────────────────────────────────────────────────────────

def discover_agents():
    """Scans ROOT_DIR for .openclaw-* folders and builds the agent mapping."""
    agents = {}

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
                    if not agent_key:
                        agent_key = f"profile-{profile_id}"

                    agents[agent_key] = {
                        "id": agent_key,
                        "profile_id": profile_id,
                        "name": raw_name,
                        "emoji": theme.get("emoji", os.getenv("DEFAULT_AGENT_EMOJI", "🤖")),
                        "port": gateway_cfg.get("port", int(os.getenv("AGENT_BASE_PORT", "18888")) + int(profile_id) if profile_id.isdigit() else int(os.getenv("AGENT_BASE_PORT", "18888"))),
                        "token": auth_cfg.get("token", ""),
                        "workspace": str((p / "workspace").absolute()),
                        "gateway_cmd": str((p / "gateway.cmd").absolute()),
                        "config_file": str(config_path.absolute()),
                        "color": theme.get("color", os.getenv("DEFAULT_AGENT_COLOR", "#8b5ceb")),
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
    new_agents = discover_agents()
    AGENTS.clear()
    AGENTS.update(new_agents)
    return AGENTS

# Print summary to console for debugging
print(f"--- [v4 Discovery] Loaded {len(AGENTS)} agents from {ROOT_DIR} ---")
for k, v in AGENTS.items():
    print(f"  > {v['name']} ({v['id']}) on port {v['port']} at {v['profile_id']}")
