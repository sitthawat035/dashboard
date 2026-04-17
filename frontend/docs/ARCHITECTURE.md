# Architecture Documentation

## Overview

This dashboard is a React application built with TypeScript, using Zustand for state management and Socket.IO for real-time updates.

## Project Structure

```
src/
├── components/           # React components
│   ├── common/          # Reusable UI components
│   ├── AgentCard/       # Agent-related components
│   ├── AppHeader.tsx    # Application header
│   ├── AppRouter.tsx    # Tab-based routing
│   ├── LogViewerTerminal.tsx  # Log viewer
│   ├── Sidebar.tsx      # Navigation sidebar
│   └── ...
├── contexts/            # React contexts
│   └── AgentCardContext.tsx  # Agent card context
├── hooks/               # Custom React hooks
│   ├── useAuth.ts       # Authentication
│   ├── useLogStream.ts  # Log streaming
│   ├── useSocketEvents.ts  # Socket events
│   ├── useTerminal.ts   # Terminal sessions
│   └── ...
├── pages/               # Page components
│   ├── DashboardPage.tsx
│   ├── AgentPage.tsx
│   ├── MissionControlPage.tsx
│   └── EngineHubPage.tsx
├── stores/              # Zustand stores
│   └── useAppStore.ts   # Global state store
├── types/               # TypeScript types
│   ├── agent.ts         # Agent types
│   ├── api.ts           # API types
│   ├── socket.ts        # Socket types
│   └── ui.ts            # UI types
├── utils/               # Utility functions
│   ├── api.ts           # API client
│   └── socket.ts        # Socket manager
└── test/                # Test utilities
    ├── setup.ts         # Test setup
    └── utils.tsx        # Test helpers
```

## State Management

### Zustand Store

The application uses Zustand for global state management. The main store is located in `stores/useAppStore.ts`.

**Key state:**
- `activeTab`: Current active tab
- `agents`: Record of agents
- `logData`: Record of log data per agent
- `subagentLogs`: Array of subagent logs
- `socketConnected`: Socket connection status
- `isLoggedIn`: Authentication status

**Actions:**
- `setActiveTab`: Set active tab
- `setAgents`: Set all agents
- `updateAgent`: Update single agent
- `setLogData`: Set log data
- `loadStatus`: Load agent status from API
- `control`: Control agent (start/stop/restart)

### Context API

AgentCard uses React Context to avoid prop drilling:

```tsx
<AgentCardProvider {...props}>
  <AgentCardContent />
</AgentCardProvider>
```

Components can access context using `useAgentCard()` hook.

## Socket Events

Socket events are managed centrally in `hooks/useSocketEvents.ts`.

**Events:**
- `connect`: Socket connected
- `disconnect`: Socket disconnected
- `agent:status`: Agent status changed
- `gateway_log_init`: Log stream initialized
- `gateway_log_line`: New log line received
- `terminal_created`: Terminal session created

## API Client

API calls are centralized in `utils/api.ts`.

**API modules:**
- `authApi`: Authentication
- `statusApi`: Agent status
- `gatewayApi`: Gateway control
- `terminalApi`: Terminal sessions
- `subagentApi`: Subagent logs
- `messageApi`: Agent messaging
- `missionApi`: Mission control
- `engineApi`: Engine operations
- `systemApi`: System operations

## Components

### Common Components

Reusable components in `components/common/`:

- `StatusBadge`: Status indicator
- `ControlButton`: Action button

### AgentCard Components

Agent-related components in `components/AgentCard/`:

- `AgentHeader`: Agent info and controls
- `GatewayConsole`: Log viewer
- `ChatPanel`: Chat interface
- `FileManager`: File browser
- `ShellAccess`: Terminal access
- `SubagentMonitor`: Subagent logs

## Testing

Tests use Vitest and React Testing Library.

**Run tests:**
```bash
npm test
```

**Run tests with coverage:**
```bash
npm test:coverage
```

**Test structure:**
- Unit tests: `__tests__/` directories
- Integration tests: `*.test.tsx` files
- Setup: `src/test/setup.ts`
- Utilities: `src/test/utils.tsx`

## Build

**Development:**
```bash
npm run dev
```

**Production:**
```bash
npm run build
```

**Preview:**
```bash
npm run preview
```
