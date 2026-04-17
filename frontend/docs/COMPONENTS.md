# Components Documentation

## Overview

The dashboard uses a component-based architecture with React. Components are organized by feature and responsibility.

## Component Hierarchy

```
App
├── Sidebar
├── AppHeader
├── AppRouter
│   ├── Dashboard
│   ├── MissionControl
│   ├── AgentPage
│   │   └── AgentCard
│   │       ├── AgentHeader
│   │       ├── GatewayConsole
│   │       │   └── LogViewerTerminal
│   │       ├── ChatPanel
│   │       ├── FileManager
│   │       ├── ShellAccess
│   │       └── SubagentMonitor
│   ├── TerminalModule
│   ├── CLIProviders
│   └── EngineHub
└── LoginScreen
```

## Common Components

### StatusBadge

Status indicator component.

**Props:**
- `status`: 'online' | 'offline' | 'starting' | 'error'
- `label?`: Custom label text
- `showDot?`: Show status dot (default: true)
- `size?`: 'sm' | 'md' | 'lg' (default: 'md')

**Usage:**
```tsx
<StatusBadge status="online" />
<StatusBadge status="offline" label="Disconnected" />
<StatusBadge status="starting" size="lg" />
```

### ControlButton

Action button component.

**Props:**
- `onClick`: Click handler
- `children`: Button content
- `variant?`: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'
- `size?`: 'sm' | 'md' | 'lg'
- `disabled?`: Disable button
- `loading?`: Show loading spinner
- `icon?`: Icon element
- `className?`: Custom CSS classes
- `title?`: Button title

**Usage:**
```tsx
<ControlButton onClick={handleClick}>Click me</ControlButton>
<ControlButton onClick={handleClick} variant="danger">Delete</ControlButton>
<ControlButton onClick={handleClick} loading>Saving...</ControlButton>
<ControlButton onClick={handleClick} icon={<Icon />}>With Icon</ControlButton>
```

## App Components

### AppHeader

Application header with title and actions.

**Props:**
- `isFullscreen`: Fullscreen state
- `onToggleFullscreen`: Toggle fullscreen handler

**Features:**
- Dynamic page title based on active tab
- Connection status indicator
- Fullscreen toggle button

### AppRouter

Tab-based routing component.

**Props:**
- Terminal props (termSessions, activeTermSid, etc.)
- CLI Providers props (cliScanState, detectedProviders, etc.)

**Features:**
- Renders correct page based on active tab
- Passes props to child components

## AgentCard Components

### AgentCardContext

Context provider for AgentCard components.

**Value:**
- Gateway and agent info
- Log data and tabs
- Control handlers
- Chat state
- Shell state
- Model state
- Starting state
- UI state

**Usage:**
```tsx
<AgentCardProvider {...props}>
  <AgentCardContent />
</AgentCardProvider>

// In child component:
const { gw, info, online } = useAgentCard();
```

### AgentHeader

Agent identity, model selector, and control buttons.

**Features:**
- Agent switcher dropdown
- Agent name and port
- Online/offline status
- Model selector
- Control buttons (Start/Stop/Restart/Watch Live)

### GatewayConsole

Gateway log viewer with overlays.

**Features:**
- Live log streaming
- Offline overlay
- Starting overlay
- Failed overlay
- Sync logs button

### ChatPanel

Chat interface with agent.

**Features:**
- Message history
- Auto-scroll to bottom
- Send message on Enter
- Role-based message display

### FileManager

File browser for agent workspace.

**Features:**
- File tree navigation
- File content preview
- File editing
- File creation/deletion

### ShellAccess

Terminal access to agent shell.

**Features:**
- Shell command execution
- Command history
- Output streaming
- Session management

### SubagentMonitor

Subagent log viewer.

**Features:**
- Subagent list
- Task status
- Log snippets
- Error display

## Page Components

### Dashboard

Overview page with agent fleet status.

**Features:**
- Agent count statistics
- Fleet status
- Quick actions (Start All/Stop All/Restart All)
- Agent grid with status

### MissionControl

Mission and task management.

**Features:**
- Agent performance metrics
- Task list
- Alerts
- Achievements

### AgentPage

Agent detail view.

**Features:**
- Agent selection
- Agent card display
- Tab navigation

### TerminalModule

PowerShell terminal interface.

**Features:**
- Multiple terminal sessions
- Command history
- Output display
- Session management

### CLIProviders

CLI provider management.

**Features:**
- Provider scanning
- Provider status
- Configuration

### EngineHub

Engine operations center.

**Features:**
- Engine list
- Engine status
- Engine control
- History and logs

## Styling

Components use CSS classes defined in:

- `styles/base.css`: Base styles and variables
- `styles/components.css`: Component styles
- `styles/agent.css`: Agent-specific styles
- `styles/mission-control.css`: Mission control styles
- `styles/engine-hub.css`: Engine hub styles

## Testing

Components are tested using Vitest and React Testing Library.

**Test files:**
- `__tests__/` directories
- `*.test.tsx` files

**Run tests:**
```bash
npm test
```

## Best Practices

### 1. Keep Components Small

Each component should have a single responsibility.

### 2. Use TypeScript

Define props interfaces for all components.

### 3. Use Context for Deep Nesting

Use React Context to avoid prop drilling.

### 4. Memoize Expensive Computations

Use `useMemo` for expensive computations.

### 5. Use Callbacks for Event Handlers

Use `useCallback` for event handlers passed to child components.

### 6. Test Components

Write tests for all components.

### 7. Document Components

Add JSDoc comments for complex components.
