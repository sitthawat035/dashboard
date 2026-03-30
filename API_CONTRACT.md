# Mission Control API Contract

## REST API Endpoints

### GET /api/mission-control/agents
Returns all agents with current status.

Response:
```json
[
  {
    "id": "ace",
    "name": "Ace",
    "emoji": "🎯",
    "status": "online",
    "currentTask": "Building dashboard",
    "taskProgress": 75,
    "connections": ["pudding", "ameri"],
    "stats": {
      "tasksCompleted": 42,
      "errorsToday": 0,
      "uptimeSeconds": 3600
    }
  }
]
```

### GET /api/mission-control/tasks
Returns current task queue with progress.

Response:
```json
[
  {
    "id": "task-001",
    "agentId": "ace",
    "title": "Building dashboard component",
    "status": "running",
    "progress": 75,
    "startedAt": "2026-03-31T01:00:00Z"
  }
]
```

### GET /api/mission-control/alerts
Returns recent alerts (last 50).

### GET /api/mission-control/achievements
Returns achievement status.

### POST /api/mission-control/tasks/{task_id}/reassign
Reassigns a task to a different agent.

### POST /api/mission-control/alerts/{alert_id}/dismiss
Dismisses an alert.

## WebSocket Events (Socket.IO)

### Server → Client
- `agent:status` - Agent status changed
- `task:progress` - Task progress updated  
- `task:complete` - Task completed
- `alert:new` - New alert
- `achievement:unlock` - Achievement unlocked

### Client → Server
- `task:reassign` - Request task reassignment
- `alert:dismiss` - Dismiss alert

## Data Models

### AgentNode
```typescript
interface AgentNode {
  id: string;
  name: string;
  emoji: string;
  status: 'online' | 'offline' | 'busy' | 'idle';
  currentTask?: string;
  taskProgress?: number;
  connections: string[];
  stats: {
    tasksCompleted: number;
    errorsToday: number;
    uptimeSeconds: number;
  };
}
```

### Task
```typescript
interface Task {
  id: string;
  agentId: string;
  title: string;
  status: 'running' | 'waiting' | 'complete' | 'error';
  progress: number;
  startedAt: string;
  error?: string;
}
```

### Alert
```typescript
interface Alert {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  message: string;
  timestamp: string;
  agentId?: string;
  dismissed: boolean;
}
```

### Achievement
```typescript
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

## Python Pydantic Models (Backend)

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"

class TaskStatus(str, Enum):
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETE = "complete"
    ERROR = "error"

class AlertType(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"

class AgentStats(BaseModel):
    tasksCompleted: int = 0
    errorsToday: int = 0
    uptimeSeconds: int = 0

class AgentNode(BaseModel):
    id: str
    name: str
    emoji: str
    status: AgentStatus
    currentTask: Optional[str] = None
    taskProgress: Optional[int] = None
    connections: List[str] = []
    stats: AgentStats = AgentStats()

class Task(BaseModel):
    id: str
    agentId: str
    title: str
    status: TaskStatus
    progress: int = 0
    startedAt: datetime
    error: Optional[str] = None

class Alert(BaseModel):
    id: str
    type: AlertType
    message: str
    timestamp: datetime
    agentId: Optional[str] = None
    dismissed: bool = False

class Achievement(BaseModel):
    id: str
    name: str
    emoji: str
    description: str
    unlocked: bool = False
    progress: Optional[int] = None
    target: Optional[int] = None
```

## Implementation Notes
- Parse gateway logs to detect agent activity
- Track subagent spawns as task events
- Achievement unlocks trigger on milestone completion
- WebSocket broadcasts for real-time dashboard updates
