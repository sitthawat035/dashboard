# OpenClaw Dashboard — Technical Documentation
**Last Updated: 2026-04-29**

---

## 1. System Overview

OpenClaw Dashboard is a **Flask + Socket.IO web dashboard** for managing autonomous AI agents (gateways). It runs on two platforms that stay in sync:

| Platform | Location | Role |
|----------|----------|------|
| **WSL (PC)** | `~/openclaw/dashboard/` | Development + Build (Vite/Rolldown) |
| **Termux (Android)** | `/storage/emulated/0/syncthing/dashboard_android/` | Primary Agent Runtime |

Both dashboards share the **same git repository** (`dashboard` folder), synced via **Syncthing** P2P. Source code is identical; only generated artifacts and secrets differ per device.

---

## 2. Two Dashboard Versions

### 2.1 WSL Dashboard (PC Build)
```
~/openclaw/dashboard/          ← Linux paths (WSL)
```

- **Source code**: Python API + React frontend (`frontend/src/`)
- **Built frontend**: `frontend/dist/` (Vite build output, built on Windows PC only)
- **Python venv**: `.venv/` (Linux virtualenv)
- **Flask runs**: `python server.py` (or `python server.py` in `.venv`)
- **Port**: `5050`
- **Access**: http://100.69.181.45:5050 (Windows portproxy) or http://localhost:5050 (WSL direct)
- **Profile folders**: `~/.openclaw-1` through `~/.openclaw-7` (Linux paths)
- **Git repo**: Inside `~/openclaw/dashboard/.git`

### 2.2 Android Dashboard (Termux)
```
/storage/emulated/0/syncthing/dashboard_android/    ← Android paths
```

- **Source code**: Identical to WSL version (Synced)
- **Built frontend**: `frontend/dist/` (Synced from WSL)
- **Python venv**: `.venv/` (Termux virtualenv at `/data/data/com.termux/files/home/usr/` or similar)
- **Flask runs**: `python server.py`
- **Port**: `5050`
- **Access**: http://localhost:5050 (Termux) or via Tailscale
- **Profile folders**: `/data/data/com.termux/files/home/.openclaw-*` (Termux home)
- **Git repo**: Inside `/storage/emulated/0/syncthing/dashboard_android/.git`

---

## 3. Syncthing Sync Architecture

### 3.1 Syncthing Folder Configuration

Both devices share a Syncthing folder labeled **"dashboard_android"** (historic name, syncs both ways):

| Setting | WSL (PC) | Android |
|---------|----------|---------|
| **Folder Path** | `/home/usercivenz/openclaw/dashboard/` | `/storage/emulated/0/syncthing/dashboard_android/` |
| **Device** | `JOE-MSI` (PC) | `ANDROID` (Termux) |
| **Share Type** | Sender + Receiver | Sender + Receiver |

> **Note**: Despite the name "dashboard_android", the WSL `~/openclaw/dashboard/` IS included in this sync — meaning Android is the **primary** but PC also receives updates.

### 3.2 What SYNCs (Allowed)

```
dashboard/
├── api/                      ← All Python API modules (synced)
├── frontend/src/             ← React source code (synced)
├── frontend/public/          ← Static assets source (synced)
├── frontend/package.json     ← Dependencies manifest (synced)
├── common/                   ← Shared libraries (synced)
├── extensions/               ← Browser extensions (synced)
├── data/                     ← Schedules, logs, uploads (synced)
├── .agents/                  ← Agent configurations & workflows (synced)
├── scripts/                  ← PowerShell helper scripts (synced)
├── server.py                 ← Flask entry point (synced)
├── config.yml                ← Dashboard config (synced)
├── requirements.txt          ← Python deps (synced)
├── Dockerfile                ← Docker build file (synced)
├── frontend/dist/            ← Built frontend (synced from WSL)
└── .gitignore                ← Git ignore rules (synced)
```

### 3.3 What DOES NOT Sync (.stignore)

```
# Android .stignore
frontend/node_modules         ← npm packages (device-specific)
frontend/.vite                 ← Vite cache
frontend/.swc                  ← SWC cache
frontend/build                 ← Vite build dir
frontend/dist                  ← Built output (WSL-only build)
frontend/package-lock.json     ← Lock file (build-specific)
.venv                          ← Python venv (device-specific)
venv                           ← Alternative venv name
.pytest_cache                 ← Test cache
.ruff_cache                   ← Linter cache
*.pyc / *.pyo                 ← Compiled Python
dist / dist.tar / *.egg-info   ← Build artifacts
.chrome_shopee                 ← Browser profile (contains auth)
screenshots                    ← Debug screenshots
*.png / *.jpg / *.gif / *.mp4 ← Media files
*.log / logs/                  ← Log files
.env / .env.*                  ← API keys & secrets (LOCAL ONLY)
cookies.txt                    ← Session cookies
.openclaw-*                    ← Agent profile folders
.stfolder / .stversions        ← Syncthing internals
.stignore                      ← This file
.git / .github                 ← Git history
.vscode / .idea                ← IDE settings
*.pem / *.key                  ← Private keys
*.lnk                          ← Windows shortcuts
.DS_Store / Thumbs.db           ← OS junk
```

### 3.4 Critical: .env is Device-Specific

The `.env` file contains **API keys** and **device-specific paths**. It is explicitly excluded from Syncthing sync.

```
# WSL .env paths
ROOT_DIR=/home/usercivenz
OPENCLAW_ROOT=/home/usercivenz
DASHBOARD_ROOT=/home/usercivenz/openclaw/dashboard
USER_DATA_DIR=/home/usercivenz/openclaw/dashboard/.chrome_shopee

# Android .env paths
ROOT_DIR=/data/data/com.termux/files/home
OPENCLAW_ROOT=/data/data/com.termux/files/home
DASHBOARD_ROOT=/data/data/com.termux/files/home/dashboard
USER_DATA_DIR=/data/data/com.termux/files/home/dashboard/.chrome_shopee
```

> **Rule**: After any `git pull` or sync that overwrites `.env`, verify paths are correct for the current device.

### 3.5 Version Conflict Resolution

Syncthing creates `.sync-conflict-*` files when the same file is modified on both devices simultaneously. These should be **deleted manually**:
```bash
find ~/openclaw/dashboard -name "*.sync-conflict*" -delete
```

---

## 4. Network Architecture

### 4.1 Device Addresses

| Device | IP Address | Type | SSH Port | Notes |
|--------|-----------|------|---------|-------|
| **Windows (Host)** | `100.69.181.45` | Tailscale | — | Run `ipconfig` on Windows to verify |
| **WSL (PC)** | `192.168.80.98` | WSL Internal | — | Not directly accessible from Android |
| **Termux (Android)** | `100.110.26.16` | Tailscale | `8022` | SSH daemon in Termux |

### 4.2 WSL Network Isolation

WSL has its own network namespace. External devices (including Android via Tailscale) **cannot reach WSL directly** at `192.168.80.98`.

**Solution: Windows Port Proxy**

On Windows (PowerShell as Admin), a port proxy forwards port 5050:
```powershell
netsh interface portproxy add v4tov4 listenport=5050 listenaddress=100.69.181.45 connectport=5050 connectaddress=192.168.80.98
netsh interface portproxy show all
```

This makes the dashboard accessible at **http://100.69.181.45:5050** from any device on the Tailscale network.

### 4.3 SSH Access

**From WSL → Android (via Tailscale)**:
```bash
ssh -p 8022 u0_a331@100.110.26.16
# or using tm alias:
tm
```

**From Windows → Android**:
```bash
ssh -p 8022 u0_a331@100.110.26.16
```

**SSH Key**: Passwordless key-based auth is configured. Keys are at:
- WSL: `~/.ssh/id_ed25519` or `~/.ssh/id_rsa`
- Android Termux: `~/.ssh/authorized_keys` (configured with user's key)

### 4.4 Tailscale

Both Windows and Android run Tailscale for VPN access:

| Device | Tailscale IP |
|--------|-------------|
| Windows | `100.69.181.45` |
| Android | `100.110.26.16` |

Check online status from WSL:
```bash
check-tm     # ping $IP_TERMUX
```

---

## 5. File Sync: Android ↔ WSL

### 5.1 Primary Sync Path: Syncthing

Syncthing runs on both Android and WSL/PC, keeping `dashboard/` folders in sync automatically.

**Android → WSL**: Source code, configs, Python files  
**WSL → Android**: Built `frontend/dist/`, Vite output

### 5.2 Manual File Transfer

**Android → WSL** (via `scp` through Tailscale):
```bash
# Copy single file
scp -P 8022 u0_a331@100.110.26.16:/path/to/file .

# Copy entire workspace
get-oc       # shorthand: scp -r -P 8022 u0_a331@100.110.26.16:~/openclaw-main/ ~/openclaw/
```

**WSL → Android** (via `scp`):
```bash
scp -P 8022 ~/openclaw/dashboard/somefile.py u0_a331@100.110.26.16:/storage/emulated/0/syncthing/dashboard_android/
```

### 5.3 Why Two Dashboard Locations?

- **Windows PC**: `/mnt/c/Users/User/openclaw/dashboard/` — Does NOT exist (or is empty/legacy). The WSL dashboard at `~/openclaw/dashboard/` is the canonical "PC" version.
- **WSL**: `~/openclaw/dashboard/` — Linux development environment
- **Android**: `/storage/emulated/0/syncthing/dashboard_android/` — Synced via Syncthing

The `dashboard_android` folder name is historical; it effectively means "the OpenClaw Dashboard folder that Android also uses."

---

## 6. Startup Procedures

### 6.1 Starting the Dashboard (WSL)

```bash
# Via opdb function (runs server.py in Background via cmd.exe)
opdb

# Or manually:
cd ~/openclaw/dashboard
source .venv/bin/activate    # Activate Linux venv
python server.py             # or: python server.py &

# Check if running:
curl http://localhost:5050
```

### 6.2 Starting the Dashboard (Android/Termux)

```bash
cd /storage/emulated/0/syncthing/dashboard_android
source .venv/bin/activate
python server.py
```

### 6.3 Frontend Build (WSL Only)

Vite/Rolldown builds **must** be done on Windows PC (WSL), as Android's Termux lacks required toolchain:

```bash
cd ~/openclaw/dashboard/frontend
npm install
npm run build              # Builds to frontend/dist/
# Then Syncthing syncs frontend/dist/ to Android
```

> **Note**: `npm run build` fails on Android Termux (ARM64, missing native toolchain for `rolldown`).

---

## 7. Profile System (openclaw-*)

OpenClaw uses profile folders for isolation. Each profile has its own gateway instance.

| Profile | Folder (WSL) | Folder (Android) | Agent Name |
|---------|-------------|-----------------|------------|
| 1 | `~/.openclaw-1/` | `/data/data/com.termux/files/home/.openclaw-1/` | Ace |
| 2 | `~/.openclaw-2/` | Same | Ameri |
| 3 | `~/.openclaw-3/` | Same | Pudding |
| 4 | `~/.openclaw-4/` | Same | Alpha |
| 5 | `~/.openclaw-5/` | Same | Fah (Synced) |
| 6 | `~/.openclaw-6/` | Same | Pudding G2 |
| 7 | `~/.openclaw-7/` | Same | BOQ G2 (Synced) |

Each profile folder contains:
```
.openclaw-N/
├── workspace/              ← Agent working files
├── openclaw.json           ← Profile configuration (name, port, token)
├── gateway.cmd             ← Windows startup script
├── gateway.log             ← Gateway stdout
├── gateway.err             ← Gateway stderr
└── (other agent data)
```

Profile folders are **NOT synced** (excluded in `.stignore`).

**Switch profiles via aliases** (defined in `~/.bashrc`):
```bash
op1    # Switch to Profile 1 (Ace)
op5    # Switch to Profile 5 (Fah)
opstatus   # Show current profile
opreset    # Clear profile
```

---

## 8. API & Architecture

### 8.1 Flask Blueprint Structure

```
server.py                 ← Entry point, registers all blueprints
├── api/auth.py           ← Login (/api/login)
├── api/status.py         ← Dashboard & agent status
├── api/gateway.py        ← Start/stop/restart gateways
├── api/logs.py           ← Read gateway logs
├── api/subagents.py      ← Subagent management
├── api/terminal.py       ← PowerShell/SSH terminal bridge
├── api/engines_api.py    ← Engine Hub routes
├── api/message.py        ← Message/chat routes
├── api/system.py         ← System operations (kill-all)
├── api/mission_control.py← Mission Control UI
├── api/schedule_api.py   ← Scheduled jobs
├── api/hermes_bridge.py  ← Hermes Agent integration
├── api/reports_api.py    ← Report generation
├── api/socket_events.py  ← Socket.IO event handlers
└── api/cron_manager.py   ← Background scheduler
```

### 8.2 Key Config (api/config.py)

```python
DASHBOARD_DIR = Path(__file__).parent.parent    # ~/openclaw/dashboard
ROOT_DIR      = Path(os.getenv('OPENCLAW_ROOT', DASHBOARD_DIR.parent))
AGENTS        = discover_agents()               # Auto-discovers .openclaw-* folders
```

`discover_agents()` scans `ROOT_DIR` for `.openclaw-*` folders and reads `openclaw.json` for each.

### 8.3 Port Usage

| Port | Service | Notes |
|------|---------|-------|
| 5050 | Flask Dashboard | Main web UI |
| 18888+N | Gateway (Profile N) | Agent gateway per profile |

---

## 9. Shell Aliases & Functions (~/.bashrc)

These are defined in `~/.bashrc` on WSL:

```bash
# Profile Switchers
op1, op2, op3, op4, op5, op6, op7   # Switch OpenClaw profile
opstatus                             # Show current profile
opreset                              # Clear profile

# Dashboard
opdb       # Launch Flask dashboard (Background)
tsc        # Run daily trend scan (venv mode)

# Gateway
opgate     # Start gateway (port 10000 default)
opkill     # Kill process on port (Windows side)

# Mobile Bridge
tm         # SSH to Termux Android
check-tm   # Ping Android to check online
get-oc     # Pull workspace from Termux

# Utilities
kall / kkk  # NUCLEAR KILL (Python/Node/CMD)
recon       # ADB connect + scrcpy
adb         # Call Windows adb.exe

# Windows SSH
tw          # SSH to Windows, open PowerShell
wsl         # SSH to Windows, jump to WSL
pc          # SSH to Windows as User (key-based)
```

---

## 10. Git Workflow

### 10.1 Repository

- **Location**: `~/openclaw/dashboard/.git` (WSL) and `/storage/emulated/0/syncthing/dashboard_android/.git` (Android)
- **Remote**: Assumed to be on GitHub (not verified in current session)
- **Syncing**: Git commits are NOT synced via Syncthing. Use `git push/pull` separately on each device.

### 10.2 Commit & Push (WSL)

```bash
cd ~/openclaw/dashboard
git add .
git commit -m "description"
git push
```

### 10.3 Pull Updates (Android)

```bash
cd /storage/emulated/0/syncthing/dashboard_android
git pull
```

---

## 11. Hermes Agent Integration

- **Hermes** runs in WSL at `~/.hermes/` (symlinked to `/mnt/c/Users/User/.hermes`)
- **Hermes Sync**: `~/.hermes-sync` → `/mnt/c/Users/User/hermes-sync` (Windows path)
- **Hermes Dashboard**: `hermes dashboard` (starts at http://127.0.0.1:9119)

Alpha (this agent) can:
- Start/stop OpenClaw gateways via the Dashboard API
- Read/write files on both WSL and Android via SSH
- Trigger trend scans, manage schedules, view logs

---

## 12. Fresh Reset Procedure

If Alpha needs to rebuild everything from scratch:

### Step 1: Clone Repository
```bash
# On WSL
git clone <repo-url> ~/openclaw/dashboard

# On Android (via SSH from WSL)
ssh -p 8022 u0_a331@100.110.26.16
git clone <repo-url> /storage/emulated/0/syncthing/dashboard_android
exit
```

### Step 2: Create Device-Specific .env
```bash
# WSL
cat > ~/openclaw/dashboard/.env << 'EOF'
ROOT_DIR=/home/usercivenz
OPENCLAW_ROOT=/home/usercivenz
DASHBOARD_ROOT=/home/usercival/dashboard
USER_DATA_DIR=/home/usercivenz/openclaw/dashboard/.chrome_shopee
# ... add all API keys
EOF

# Android
cat > /storage/emulated/0/syncthing/dashboard_android/.env << 'EOF'
ROOT_DIR=/data/data/com.termux/files/home
OPENCLAW_ROOT=/data/data/com.termux/files/home
DASHBOARD_ROOT=/data/data/com.termux/files/home/dashboard
USER_DATA_DIR=/data/data/com.termux/files/home/dashboard/.chrome_shopee
# ... add all API keys
EOF
```

### Step 3: Install Dependencies
```bash
# WSL
cd ~/openclaw/dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Android
cd /storage/emulated/0/syncthing/dashboard_android
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Build Frontend (WSL Only)
```bash
cd ~/openclaw/dashboard/frontend
npm install
npm run build
# Syncthing will push frontend/dist/ to Android
```

### Step 5: Start Dashboard
```bash
# WSL
opdb

# Android
cd /storage/emulated/0/syncthing/dashboard_android
python server.py
```

### Step 6: Verify
```bash
check-tm        # Ping Android
curl localhost:5050   # WSL dashboard
ssh -p 8022 u0_a331@100.110.26.16 "curl localhost:5050"  # Android dashboard
```

---

## 13. Troubleshooting

### Dashboard won't start
```bash
cd ~/openclaw/dashboard
source .venv/bin/activate
python -c "from api.config import AGENTS; print(len(AGENTS))"
python server.py
```

### Paths wrong after sync
Check `.env` on the device — `ROOT_DIR` and `DASHBOARD_ROOT` must match the device's filesystem.

### Android offline / can't SSH
```bash
check-tm   # ping 100.110.26.16
# If offline, check Termux is running and Tailscale is connected
```

### frontend/dist missing on Android
Run `npm run build` on WSL. Android cannot build frontend.

### Sync conflicts
```bash
find ~/openclaw/dashboard -name "*.sync-conflict*" -delete
```

---

## 14. Quick Reference

| Task | Command |
|------|---------|
| Launch dashboard | `opdb` |
| SSH to Android | `tm` |
| Switch to profile 1 | `op1` |
| Check profile | `opstatus` |
| Build frontend | `cd frontend && npm run build` |
| View logs | Dashboard → Logs tab |
| Restart gateway | Dashboard → Gateway → Restart |
| Trend scan | `tsc` |
| Kill all Python | `kall` |

---

*This document is the single source of truth for the OpenClaw Dashboard multi-device architecture. Update this file after any structural changes.*
