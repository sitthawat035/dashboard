# Mission Control Integration — Review Report

**Reviewer:** pudding-review  
**Date:** 2026-03-31  
**Files reviewed:**
- `server.py` (backend)
- `frontend/src/components/MissionControl.tsx` (frontend)
- `API_CONTRACT.md` (spec)

---

## ✅ What's Working

### Backend (server.py)

1. **All 6 Mission Control endpoints present and correct:**
   - `GET /api/mission-control/agents` (line ~488) ✅
   - `GET /api/mission-control/tasks` (line ~503) ✅
   - `GET /api/mission-control/alerts` (line ~511) ✅
   - `GET /api/mission-control/achievements` (line ~527) ✅
   - `POST /api/mission-control/tasks/<task_id>/reassign` (line ~534) ✅
   - `POST /api/mission-control/alerts/<alert_id>/dismiss` (line ~569) ✅

2. **Python syntax valid** — `py_compile` passes with no errors ✅

3. **JSON response structure matches API contract** — all 4 GET endpoints return data in the correct shape (arrays of objects with expected fields) ✅

4. **Socket.IO setup correct** — `socketio` initialized with CORS, threading mode, proper timeouts ✅

5. **Socket.IO server events implemented:**
   - `task:progress` emitted on reassign (line ~562) ✅
   - `alert:dismiss` emitted on dismiss (line ~586) ✅
   - `task:reassign` handler (line ~594) ✅
   - `alert:dismiss` handler (line ~610) ✅

6. **All `@login_required` decorators applied** to all 6 MC endpoints ✅

7. **Real-time health integration** — `/api/mission-control/agents` calls `gateway_health()` to update `status` dynamically ✅

8. **Mock data well-structured** — agents, tasks, alerts, achievements all have complete, realistic data ✅

### Frontend (MissionControl.tsx)

1. **All 4 GET endpoints called** via `Promise.all` (line ~99) ✅
2. **Loading state exists** — full loading screen with `mc-loading` class (line ~130) ✅
3. **Error state exists** — error display with retry button (line ~141) ✅
4. **Stale data handling** — shows error as warning indicator while still displaying cached data (line ~167) ✅
5. **TypeScript interfaces match API contract exactly:**
   - `AgentNode` ✅
   - `Task` ✅
   - `Alert` ✅
   - `Achievement` ✅
6. **`mc-*` CSS classes preserved** — 20+ classes verified in `App.css` ✅
7. **Auto-refresh polling** — 5-second interval for data updates ✅
8. **Agent map with SVG connections** renders dynamically from data ✅
9. **Task progress bars** render correctly with percentage display ✅
10. **Agent detail popup** with stats, task info, and close button ✅
11. **Achievement progress bars** for locked achievements ✅
12. **Alert panel** shows active (non-dismissed) alerts ✅

### Integration (Frontend ↔ Backend)

1. **Endpoint URLs match** — all 4 frontend URLs (`/api/mission-control/...`) match backend routes ✅
2. **Data types match** — TS interfaces align with JSON response shapes ✅
3. **Field names consistent** — `agentId`, `tasksCompleted`, `errorsToday`, `uptimeSeconds`, etc. all match ✅

---

## ❌ What Needs Fixing

### Issue 1: Frontend doesn't listen to WebSocket events
**File:** `MissionControl.tsx`  
**Impact:** Medium — real-time updates are lost

The API contract defines 6 WebSocket events, and the backend emits `task:progress` and `alert:dismiss`, but the **frontend never connects to Socket.IO** or listens for any events. All updates rely solely on 5-second polling.

**Missing:**
- No `import` of `socket.io-client`
- No `socket.on("task:progress", ...)` listener
- No `socket.on("alert:dismiss", ...)` listener
- No `socket.on("agent:status", ...)` listener
- No `socket.on("task:complete", ...)` listener
- No `socket.on("alert:new", ...)` listener
- No `socket.on("achievement:unlock", ...)` listener

**Fix:** Add a `useEffect` that initializes a Socket.IO client connection and listens for all server events to update state in real-time, reducing reliance on polling.

---

### Issue 2: `fetchJSON` doesn't send credentials/cookies
**File:** `MissionControl.tsx`, line ~88  
**Impact:** High — API calls will fail with 401 Unauthorized

```typescript
async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);  // ← no credentials
```

The backend uses Flask session auth (`@login_required` checks `session.get("logged_in")`). Flask session cookies require `credentials: 'include'` to be sent cross-origin or even same-origin in some setups.

**Fix:** Change to:
```typescript
const res = await fetch(url, { credentials: 'include' });
```

---

### Issue 3: `specialStyle` field in mock data not in TypeScript interface
**File:** `server.py` line ~439 (mock data) vs `MissionControl.tsx` line ~14  
**Impact:** Low — TS won't complain because it's extra data, but it's never used in the frontend

The `j1` agent has `specialStyle: { borderColor, badgeColor, glow }` in the backend mock data, but:
- The `AgentNode` interface doesn't include this field
- The frontend never reads or applies it

**Verdict:** Not a bug (extra fields are ignored by TypeScript), but it's dead data. Either add the field to the TS interface and use it for visual styling, or remove it from the mock data to avoid confusion.

---

### Issue 4: Socket.IO events `task:complete` and `agent:status` not emitted
**File:** `server.py`  
**Impact:** Low — these events are in the API contract but not implemented

The API contract promises these server→client events:
- `agent:status` — ❌ never emitted
- `task:complete` — ❌ never emitted
- `alert:new` — ❌ never emitted
- `achievement:unlock` — ❌ never emitted

Only `task:progress` and `alert:dismiss` are actually emitted.

**Fix:** Either implement the missing emissions or update the API contract to reflect what's actually supported.

---

### Issue 5: No disconnect cleanup for polling interval on unmount edge case
**File:** `MissionControl.tsx`, line ~110  
**Impact:** Low

The `useEffect` cleanup does `clearInterval`, which is correct. However, if the component unmounts while a `fetchData` call is in-flight, the `setAgents` / `setError` calls on the unmounted component could cause a React warning. A simple `isMounted` flag or `AbortController` would fix this.

---

## 💡 Suggestions for Improvement

1. **Add Socket.IO client integration** — This was clearly planned (backend events exist) but not wired up. This is the biggest missing piece. Route to `pudding-frontend`.

2. **Add `credentials: 'include'` to fetch calls** — Critical for auth to work. This should be fixed ASAP. Route to `pudding-frontend`.

3. **Consider real data for achievements** — Currently all achievement data is hardcoded mock data. Once real task tracking is in place, achievements could be computed dynamically from actual agent stats.

4. **Add a POST endpoint for achievements** — If you want manual admin unlock capability, add `POST /api/mission-control/achievements/<ach_id>/unlock`.

5. **Add connection line hover/tooltip** — When hovering a line on the agent map, show which agents are connected. Nice UX touch.

6. **Add timestamp display on alerts** — The alert panel shows messages but not timestamps. Add a relative time display (e.g., "5m ago").

7. **Update API contract to match reality** — Remove or mark as "planned" the WebSocket events that aren't implemented yet (`agent:status`, `task:complete`, `alert:new`, `achievement:unlock`).

---

## 📊 Summary

| Area | Status | Issues |
|------|--------|--------|
| Backend endpoints | ✅ Pass | 0 bugs |
| Backend Socket.IO | ⚠️ Partial | 4 events not emitted |
| Frontend API calls | ❌ Fix needed | Missing credentials |
| Frontend Socket.IO | ❌ Missing | No client listener |
| TypeScript types | ✅ Pass | 1 unused field |
| CSS classes | ✅ Pass | All preserved |
| Data integration | ✅ Pass | URLs & types match |

### Priority Fixes (route to correct agent):
1. **`pudding-frontend`** — Add `credentials: 'include'` to fetch + Socket.IO client integration
2. **`pudding-backend`** — Implement missing WebSocket event emissions OR update API contract
