# Mission Control Dashboard - Specification

## Overview
A game-like command center for monitoring and controlling AI agents.
Think "SimCity meets AI orchestration" 🎮🤖

## UI Components

### 1. MissionControl.tsx (Main Tab)
```tsx
// New tab in sidebar: "🎮 Mission Control"
// Shows the command center view
```

### 2. AgentMapView.tsx
```
┌─────────────────────────────────────┐
│         AGENT COMMAND CENTER        │
├─────────────────────────────────────┤
│                                     │
│    🟢 ──── 🔵 ──── 🟡              │
│    Ace     Pudding  Ameri           │
│     │        │       │              │
│     └──── 🔴 ───────┘              │
│          Fah (busy)                 │
│                                     │
│    🟢 ──── ⚪                       │
│    Alpha   (offline)                │
│                                     │
└─────────────────────────────────────┘

- Each agent = glowing node
- Lines = active connections/conversations
- Colors: 🟢 online, 🔴 busy, 🟡 idle, ⚪ offline
- Click node → zoom into agent details
- Nodes pulse when working
```

### 3. StatsPanel.tsx
```
┌──────────────────────────────┐
│ 📊 LIVE STATS                │
├──────────────────────────────┤
│ Tasks Running:    3  ⚡      │
│ Tasks Completed: 47  ✅      │
│ Errors Today:     2  ❌      │
│ Uptime:      4h 23m  🟢      │
│                              │
│ Agent Health:                │
│ ████████████░░░░  78%        │
└──────────────────────────────┘
```

### 4. TaskQueue.tsx
```
┌──────────────────────────────────────┐
│ 📋 TASK QUEUE                        │
├──────────────────────────────────────┤
│ ⚡ [Ace]      Building dashboard... │ 87%
│ 🔄 [Pudding]  Reviewing code...    │ 54%
│ ⏳ [Ameri]    Waiting for input     │  0%
│ ✅ [Fah]      Analysis complete     │ 100%
│ ❌ [Alpha]    Error: timeout        │  --
└──────────────────────────────────────┘

- Real-time progress bars
- Drag tasks between agents
- Click to see task details
```

### 5. AlertPanel.tsx
```
┌──────────────────────────────────────┐
│ 🔔 ALERTS                            │
├──────────────────────────────────────┤
│ 🚨 [16:32] Fah stuck on task        │
│ ✅ [16:28] Dashboard build complete  │
│ ⚠️ [16:15] API rate limit warning    │
│ ℹ️ [16:00] New agent connected       │
└──────────────────────────────────────┘

- Color coded by severity
- Auto-dismiss after 30s (except errors)
- Sound notification option
```

### 6. AchievementBadges.tsx
```
┌──────────────────────────────────────┐
│ 🏆 ACHIEVEMENTS                      │
├──────────────────────────────────────┤
│ 🥇 First 100 Tasks    ✅ Unlocked   │
│ 🥈 Zero Errors 24h    ✅ Unlocked   │
│ 🥉 Agent Collaboration ✅ Unlocked  │
│ 🏅 Speed Demon         🔒 10 more   │
│ 💎 Perfectionist       🔒 50 more   │
└──────────────────────────────────────┘
```

## Data Models (TypeScript)

```typescript
interface AgentNode {
  id: string;
  name: string;
  emoji: string;
  status: 'online' | 'offline' | 'busy' | 'idle';
  currentTask?: string;
  taskProgress?: number; // 0-100
  connections: string[]; // connected agent IDs
  stats: {
    tasksCompleted: number;
    errorsToday: number;
    uptimeSeconds: number;
  };
}

interface Task {
  id: string;
  agentId: string;
  title: string;
  status: 'running' | 'waiting' | 'complete' | 'error';
  progress: number; // 0-100
  startedAt: string;
  error?: string;
}

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  message: string;
  timestamp: string;
  agentId?: string;
  dismissed: boolean;
}

interface Achievement {
  id: string;
  name: string;
  emoji: string;
  description: string;
  unlocked: boolean;
  progress?: number;
  target?: number;
}
```

## Backend API Endpoints

```python
# FastAPI routes for Mission Control

@router.get("/api/mission-control/agents")
async def get_agent_nodes() -> list[AgentNode]:
    """Get all agents with their current status and connections"""

@router.get("/api/mission-control/tasks")
async def get_task_queue() -> list[Task]:
    """Get current task queue with progress"""

@router.post("/api/mission-control/tasks/{task_id}/reassign")
async def reassign_task(task_id: str, new_agent_id: str):
    """Move a task to a different agent"""

@router.get("/api/mission-control/alerts")
async def get_alerts() -> list[Alert]:
    """Get recent alerts"""

@router.post("/api/mission-control/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    """Dismiss an alert"""

@router.get("/api/mission-control/achievements")
async def get_achievements() -> list[Achievement]:
    """Get achievement status"""
```

## WebSocket Events

```typescript
// Real-time updates via Socket.IO

// Server → Client
socket.on('agent:status', (data: { agentId: string, status: string }) => {});
socket.on('task:progress', (data: { taskId: string, progress: number }) => {});
socket.on('task:complete', (data: { taskId: string }) => {});
socket.on('alert:new', (data: Alert) => {});
socket.on('achievement:unlock', (data: Achievement) => {});
socket.on('connection:update', (data: { from: string, to: string, active: boolean }) => {});

// Client → Server
socket.emit('task:reassign', { taskId: string, newAgentId: string });
socket.emit('alert:dismiss', { alertId: string });
```

## Integration with Existing Dashboard

### Sidebar Update
Add new tab: `🎮 Mission Control`

### App.tsx Update
```tsx
{activeTab === 'mission' && (
  <MissionControl 
    agents={agents}
    tasks={tasks}
    alerts={alerts}
    achievements={achievements}
  />
)}
```

### CSS Styles
- Dark theme with neon accents (game-like)
- Animated nodes and connections
- Glow effects for active agents
- Smooth progress bar animations

## Implementation Order

1. **Phase 1**: Basic MissionControl.tsx with static layout
2. **Phase 2**: AgentMapView with real status from API
3. **Phase 3**: TaskQueue with progress bars
4. **Phase 4**: AlertPanel with WebSocket events
5. **Phase 5**: Achievement system with persistence

## Agents to Include

| Agent | Role | Platform | Emoji |
|-------|------|----------|-------|
| Ace | Dashboard agent | OpenClaw | 🟢 |
| Ameri | Dashboard agent | OpenClaw | 🟡 |
| Fah | Dashboard agent | OpenClaw | 🔴 |
| Pudding | Dashboard agent | OpenClaw | 🔵 |
| Alpha | Dashboard agent | OpenClaw | 🟢 |
| J1 | WhatsApp community | WhatsApp | 📱 |

> J1 gets special "📱 WhatsApp" badge and shows message activity

## Notes
- Keep it fun! This should feel like a game, not enterprise software
- Use animations and sound effects sparingly
- Mobile responsive (stack panels vertically)
- Dark theme only (matches existing dashboard)
