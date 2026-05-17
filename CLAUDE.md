# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Patient Chart

```
Owner:       Sitthawat 035
Last visit:  2026-05-08 (Gemini CLI — 34/34 findings patched ✅)
Chief comp:  All P0/P1/P2 findings from QA Audit resolved.
Dashboard:   http://localhost:5050
Devices:     WSL (dev) ↔ Android/Termux (prod) via Syncthing
```

---

## Project Overview

OpenClaw Dashboard is a **Flask + Socket.IO backend** paired with a **React + Zustand frontend**.
It manages autonomous AI agent gateways (up to 7 profiles) and provides a Mission Control UI.

**WSL path:** `/home/usercivenz/dashboard/`
**Syncthing partner:** `C:\Users\User\Desktop\dashboard_android\` (Android/Termux)

---

## Development Commands

### Backend

```bash
cd /home/usercivenz/dashboard
source .venv/bin/activate
python server.py        # http://localhost:5050

# Test (pytest)
pytest
pytest tests/test_xxx.py -v

# Lint
ruff check api/ server.py
```

### Frontend

```bash
cd /home/usercivenz/dashboard/frontend

npm install
npm run dev       # Vite dev server (hot reload)
npm run build     # WSL only — builds to frontend/dist/ (Termux cannot build)
npm test          # Vitest unit tests
```

**Note:** On WSL, the backend starts via the `opdb` shell alias (runs `server.py` through cmd.exe). On Android/Termux, start directly with `python server.py`.

---

## Architecture

### Backend — Flask Blueprint Structure

`server.py` is thin — it wires blueprints and initializes Socket.IO only. All business logic lives in `api/` modules.

```
server.py                           ← Entry point
├── api/config.py                   ← AGENTS dict (scans .openclaw-* folders), path constants
├── api/__init__.py                ← Shared Limiter instance (flask-limiter)
├── api/auth.py                    ← @login_required, /api/login (rate-limited: 5/min)
├── api/status.py                  ← /api/status (parallel health checks)
├── api/gateway.py                 ← Start/stop/restart per agent
├── api/logs.py                   ← Gateway log read
├── api/socket_events.py           ← Socket.IO handlers (log tail, terminal)
│                                   ← Registers cleanup callback into gateway.py via
│                                      set_cleanup_callback() — cross-module dependency
├── api/mission_control.py         ← Mission Control routes + socket events
│                                   ← init_mission_control_socketio() called AFTER
│                                      init_socketio() in server.py — NOT in socket_events.py
├── api/hermes_bridge.py            ← SSE bridge to Hermes Agent (port 8642)
├── api/cron_manager.py            ← Persistent scheduler (daily/once/weekdays)
│                                   ← Jobs persist to data/schedule/jobs.json
├── api/schedule_api.py             ← /api/schedule CRUD
├── api/system.py                  ← /api/system/kill-all, scan-cli
├── api/engines_api.py             ← Engine Hub (trend-scan, veo-gen, shopee, etc.)
├── api/terminal.py                ← PowerShell bridge via subprocess
├── api/reports_api.py             ← Report generation
├── api/broadcast.py               ← Multi-agent broadcast
├── api/facebook.py / twitter.py / instagram.py / youtube.py
├── api/ai_caption.py             ← AI caption generation
└── api/helpers.py                ← Shared utilities
```

### Frontend — React + Zustand

State is centralized in Zustand (`stores/useAppStore.ts`). Components are pure — read from store, call API utilities.

```
frontend/src/
├── App.tsx                       ← Auth gate + routing
├── components/
│   ├── AppRouter.tsx             ← Route definitions
│   ├── Sidebar.tsx               ← Navigation
│   ├── LogViewerTerminal.tsx    ← Live log streaming via Socket.IO
│   └── TerminalModule.tsx        ← Interactive PowerShell terminal
├── hooks/
│   ├── useSocketEvents.ts       ← Centralized Socket.IO wiring (called from App.tsx)
│   ├── useAuth.ts / useGateway.ts / useLogStream.ts / useTerminal.ts
├── stores/useAppStore.ts         ← Single Zustand store
├── utils/api.ts                  ← REST client (axios)
└── utils/socket.ts               ← Socket.IO singleton
```

### Agent Profile System

Agents are discovered dynamically from `~/.openclaw-*` folders (via `OPENCLAW_ROOT` env var).

```
.openclaw-N/
├── openclaw.json                 ← Profile config (name, port, token)
├── gateway.cmd                   ← Windows startup script
├── gateway.log / gateway.err    ← Log files
└── workspace/
    ├── IDENTITY.md / SOUL.md    ← Agent identity
    └── memory/                  ← Persistent memory
```

`agent_key` is derived from `name.lower().replace(" ", "")` — Unicode names collapse to empty string, so config.py adds a `profile-N` fallback.

### Engine Hub

Engines run as subprocess scripts, registered in `api/engines_api.py` and `cron_manager.py`:

```
api/engines/
├── trend_scan/                  ← Daily trend analysis
├── veo_gen/                    ← Video generation (Google Veo)
├── shopee/                     ← Shopee scraping
├── lookforward/                ← Content pipeline
├── social/                     ← Facebook/social posting
├── image_gen/                  ← Image generation
└── common/                     ← Shared utilities (browser, ai_client)
```

### Hermes Agent Bridge

`api/hermes_bridge.py` bridges Hermes Agent (port 8642) into the dashboard's Socket.IO, streaming SSE as `hermes:run:*` events to the frontend.

---

## Key Patterns

**Adding a REST route:**
1. Add a `Blueprint("xxx", __name__)` in `api/xxx.py`
2. Use `@login_required` on all mutating/sensitive endpoints
3. Import and `app.register_blueprint()` in `server.py`

**Adding a Socket.IO event:**
- Gateway/log events → `api/socket_events.py`, registered in `init_socketio()`
- Mission Control events → `init_mission_control_socketio()` in `api/mission_control.py` (called after `init_socketio()`)

**Adding a scheduled job:**
Add engine to `ENGINE_SCRIPTS` dict in `api/cron_manager.py`. Jobs persist to `data/schedule/jobs.json`.

**Rate limiting:**
Use `@limiter.limit("N per minute")` on routes. The shared `limiter` instance lives in `api/__init__.py` (avoids circular import with server.py).

---

## Dependencies

All runtime deps are pinned in `requirements.txt`. New pip installs must be inside `.venv`:

```bash
/home/usercivenz/dashboard/.venv/bin/python3 -m pip install <package>
```

Required env vars (see `.env.example`):
- `SECRET_KEY` — Flask session signing key (no default, fails fast if missing)
- `DASHBOARD_PASSWORD` — Dashboard login password (no default, fails fast if missing)
- `OPENCLAW_ROOT` — Root dir where `.openclaw-*` folders live
- `DASHBOARD_ROOT` — Dashboard install dir

---

## Infrastructure

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI: pytest + ruff + frontend build |
| `Dockerfile` | Container build |
| `pytest.ini` | pytest config (`testpaths = tests`) |
| `.env.example` | Template for required env vars |
| `QA_AUDIT_REPORT.md` | All known issues (P0/P1/P2 findings) |

---

## Constraints

- **WSL-only frontend build** — Termux cannot run Node toolchain. Built `frontend/dist/` syncs to Android via Syncthing.
- **`.env` is device-specific** — excluded from Syncthing (`.stignore`). Each device has its own with different paths.
- **Syncthing exclusions** — `node_modules/`, `.venv/`, `.openclaw-*/`, `.env`, `data/`, `logs/`, `.chrome_shopee/` are all excluded.
- **Gateway spawn** — Agents spawn via `cmd /c` on Windows. Log output goes to `.openclaw-N/gateway.log`.
