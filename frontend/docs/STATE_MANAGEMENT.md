# State Management Documentation

## Overview

The dashboard uses Zustand for global state management, replacing the previous prop drilling approach. All shared state is centralized in the Zustand store.

## Store Structure

### Navigation State

```typescript
{
  activeTab: TabId;
  sidebarOpen: boolean;
}
```

**Actions:**
- `setActiveTab(tab: TabId)`: Set active tab
- `setSidebarOpen(open: boolean)`: Set sidebar open state

### Agent State

```typescript
{
  agents: Record<string, Agent>;
  selectedAgent: string | null;
}
```

**Actions:**
- `setAgents(agents: Record<string, Agent>)`: Set all agents
- `updateAgent(id: string, patch: Partial<Agent>)`: Update single agent
- `setSelectedAgent(gw: string | null)`: Set selected agent

### Per-Agent UI State

```typescript
{
  logTab: Record<string, LogTab>;
  stdoutSubTab: Record<string, StdoutSubTab>;
  chatSessions: Record<string, ChatMessage[]>;
  chatInputs: Record<string, string>;
}
```

**Actions:**
- `setLogTabForAgent(gw: string, tab: LogTab)`: Set log tab for agent
- `setStdoutSubTabForAgent(gw: string, tab: StdoutSubTab)`: Set stdout subtab for agent
- `setChatMessagesForAgent(gw: string, updater: ChatMessage[] | Function)`: Set chat messages for agent
- `setChatInputForAgent(gw: string, val: string)`: Set chat input for agent

### Log Data State

```typescript
{
  logData: Record<string, LogData>;
}
```

**Actions:**
- `setLogData(data: Record<string, LogData>)`: Set all log data
- `updateLogData(gw: string, data: Partial<LogData>)`: Update log data for agent

### Subagent State

```typescript
{
  subagentLogs: SubagentLog[];
}
```

**Actions:**
- `setSubagentLogs(logs: SubagentLog[])`: Set subagent logs

### Socket State

```typescript
{
  socketConnected: boolean;
  socketReconnecting: boolean;
}
```

**Actions:**
- `setSocketConnected(val: boolean)`: Set socket connected state
- `setSocketReconnecting(val: boolean)`: Set socket reconnecting state

### Auth State

```typescript
{
  isLoggedIn: boolean;
}
```

**Actions:**
- `setIsLoggedIn(val: boolean)`: Set logged in state

## Usage Examples

### Reading State

```typescript
import { useAppStore } from '../stores/useAppStore';

function MyComponent() {
  const activeTab = useAppStore(s => s.activeTab);
  const agents = useAppStore(s => s.agents);
  
  return <div>Active tab: {activeTab}</div>;
}
```

### Writing State

```typescript
import { useAppStore } from '../stores/useAppStore';

function MyComponent() {
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const updateAgent = useAppStore(s => s.updateAgent);
  
  const handleClick = () => {
    setActiveTab('agents');
    updateAgent('agent-1', { online: true });
  };
  
  return <button onClick={handleClick}>Click me</button>;
}
```

### Async Actions

```typescript
import { useAppStore } from '../stores/useAppStore';

function MyComponent() {
  const loadStatus = useAppStore(s => s.loadStatus);
  const control = useAppStore(s => s.control);
  
  const handleStart = async () => {
    await control('agent-1', 'start');
    await loadStatus();
  };
  
  return <button onClick={handleStart}>Start Agent</button>;
}
```

## Migration from Props

### Before (Prop Drilling)

```typescript
<AgentCard
  gw={gw}
  info={info}
  agent={agent}
  logData={logData}
  curLogTab={curLogTab}
  onSwitchTab={onSwitchTab}
  // ... many more props
/>
```

### After (Context + Store)

```typescript
<AgentCardProvider {...props}>
  <AgentCardContent />
</AgentCardProvider>

// Inside AgentCardContent:
const { gw, info, agent } = useAgentCard();
const logData = useAppStore(s => s.logData[gw]);
```

## Best Practices

### 1. Use Selectors

Always use selectors to read state:

```typescript
// Good
const agents = useAppStore(s => s.agents);

// Bad
const { agents } = useAppStore.getState();
```

### 2. Avoid Derived State

Don't store derived state in the store:

```typescript
// Good
const activeAgents = Object.values(agents).filter(a => a.online);

// Bad
// Don't store activeAgents in the store
```

### 3. Use Functional Updates

Use functional updates for complex state changes:

```typescript
// Good
setChatMessagesForAgent('agent-1', prev => [...prev, newMessage]);

// Bad
setChatMessagesForAgent('agent-1', [...chatMessages, newMessage]);
```

### 4. Keep Actions Close to State

Define actions in the same store as the state they modify:

```typescript
// Good
const useAppStore = create((set) => ({
  count: 0,
  increment: () => set(state => ({ count: state.count + 1 })),
}));

// Bad
// Don't define increment in a separate store
```

## Performance

### Selectors

Zustand uses shallow comparison by default. For complex objects, use custom equality functions:

```typescript
import { shallow } from 'zustand/shallow';

const { agents, logData } = useAppStore(
  s => ({ agents: s.agents, logData: s.logData }),
  shallow
);
```

### Memoization

Memoize expensive computations:

```typescript
import { useMemo } from 'react';

function MyComponent() {
  const agents = useAppStore(s => s.agents);
  
  const onlineAgents = useMemo(
    () => Object.values(agents).filter(a => a.online),
    [agents]
  );
  
  return <div>Online: {onlineAgents.length}</div>;
}
```

## Debugging

### Redux DevTools

Zustand supports Redux DevTools:

```typescript
import { devtools } from 'zustand/middleware';

const useAppStore = create(
  devtools((set) => ({
    // ... store
  }))
);
```

### Logging

Log state changes in development:

```typescript
const useAppStore = create((set) => ({
  // ... store
  _log: (action: string, data: unknown) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Store] ${action}:`, data);
    }
  },
}));
```
