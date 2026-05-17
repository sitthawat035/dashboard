# Shell Access Replacement: Quick Command Runner

## Executive Summary

**Task:** Replace the incomplete "Shell Access" tab with a more practical, safer, and dashboard-appropriate feature.

**Recommendation:** **Quick Command Runner** - a curated panel of pre-approved commands that users can execute with one click.

---

## 1. Current Shell Access Analysis

### What Exists

| Component | Location | Status |
|-----------|----------|--------|
| Backend Shell API | `api/terminal.py` | ✅ Functional |
| Frontend Hook | `frontend/src/hooks/useAgentShell.ts` | ✅ Functional |
| Context Integration | `frontend/src/contexts/AgentCardContext.tsx` | ✅ Wired but unused |
| UI Tab | `frontend/src/components/AgentCard/index.tsx` | ❌ Not implemented |
| Type Definition | `frontend/src/types/ui.ts` | ⚠️ Only `'gateway_logs'` allowed |
| CSS Styles | `frontend/src/styles/components.css` | ✅ `.shell-*` exist but unused |

### Why Shell Access Was Never Completed

1. **Security Concerns** - Direct shell access is dangerous in a multi-agent dashboard
2. **UX Complexity** - Requires shell/terminal knowledge to be useful
3. **Backend Inefficiency** - Character-by-character reading is CPU-intensive
4. **Polling Overhead** - 500ms intervals cause lag and wasted API calls
5. **Low Utility** - Most dashboard users don't need raw shell access

---

## 2. Proposed Replacement: Quick Command Runner

### Concept

A panel of pre-approved, safe commands organized by category that users can execute with a single click. Output is displayed in a clean, scrollable view.

### Design Principles

1. **Safe** - Only allowlisted commands; no arbitrary shell injection
2. **Fast** - Real-time output via existing Socket.IO infrastructure
3. **Simple** - One-click execution, no typing required
4. **Informative** - Commands designed for agent management, not general computing
5. **Consistent** - Fits the existing dashboard aesthetic

### Command Categories

#### 📊 Agent Status
- `status` - Full agent health check (gateway, subagents, models)
- `uptime` - How long agent has been running

#### 📁 File Operations
- `ls` - List workspace root
- `ls -la` - Detailed listing with hidden files
- `tree` - Directory tree view

#### 📝 Logs
- `tail -30` - Last 30 lines of gateway log
- `tail -100` - Last 100 lines
- `grep -i error *.log` - Find errors

#### 💻 System Info
- `ps aux` / `Get-Process` - Running processes
- `free -h` / `systeminfo` - Memory info
- `df -h` - Disk usage

#### ⚙️ Control
- `sync` - Force config reload
- `restart` - Restart agent gateway

---

## 3. Implementation Plan

### Phase 1: Type & Infrastructure (Low Risk)

**File:** `frontend/src/types/ui.ts`
```typescript
// Add new tab type
export type StdoutSubTab = 'gateway_logs' | 'quick_commands';
```

**File:** `frontend/src/stores/useAppStore.ts`
```typescript
// Default new agents to 'gateway_logs' for backward compat
stdoutSubTab: {},

// setStdoutSubTabForAgent already polymorphic - no changes needed
```

### Phase 2: Quick Commands Component (Medium Risk)

**New File:** `frontend/src/components/AgentCard/QuickCommands.tsx`

```typescript
// Pseudocode structure
interface QuickCommandsProps {
  agentId: string;
  onOutput: (line: string) => void;
}

// Commands definition (could come from API or hardcoded)
const COMMAND_CATEGORIES = [
  { category: 'Status', commands: [
    { id: 'status', label: 'Status', cmd: 'status', icon: '📊' },
    { id: 'uptime', label: 'Uptime', cmd: 'uptime', icon: '⏱️' },
  ]},
  // ...
];
```

### Phase 3: UI Integration (Low Risk)

**File:** `frontend/src/components/AgentCard/index.tsx`

```typescript
// Add button for quick_commands tab
{curLogTab === 'log' && (
  <div className="stdout-subtabs">
    <button 
      className={`subtab-sm ${stdoutSubTab === 'gateway_logs' ? 'active' : ''}`}
      onClick={() => onSwitchStdoutSubTab('gateway_logs')}
    >
      📄 GATEWAY LOGS
    </button>
    <button 
      className={`subtab-sm ${stdoutSubTab === 'quick_commands' ? 'active' : ''}`}
      onClick={() => onSwitchStdoutSubTab('quick_commands')}
    >
      ⚡ QUICK COMMANDS
    </button>
  </div>
)}

// Render QuickCommands or GatewayConsole based on tab
{curLogTab === 'log' && (
  stdoutSubTab === 'quick_commands' 
    ? <QuickCommands agentId={gw} />
    : <GatewayConsole />
)}
```

### Phase 4: Backend Enhancement (Optional)

**Option A:** Use existing `terminalApi` but with pre-approved commands only

**Option B:** Create new `/api/agents/{id}/quick-command` endpoint that:
- Accepts command ID (not raw command string)
- Maps ID to actual command
- Returns structured output

**Recommendation:** Option B for security

---

## 4. UI Wireframe

```
┌────────────────────────────────────────────────────────────────┐
│ [Console & Chat] [Config & Files]                    [▼ Expand]│
├────────────────────────────────────────────────────────────────┤
│  [📄 stdout ●] [🤖 Subagents] [💬 Chat]                         │
├────────────────────────────────────────────────────────────────┤
│  [📄 GATEWAY LOGS]  [⚡ QUICK COMMANDS]                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─ Command Palette ────────────────────────────────────────┐  │
│  │ 📊 Status    📁 Files    📝 Logs    💻 System    ⚙️ Ctrl │  │
│  │                                                        │  │
│  │  [Status] [Uptime]                                     │  │
│  │  [ls]      [ls -la]  [tree]                           │  │
│  │  [logs]    [errors]  [search]                        │  │
│  │  [ps]      [memory]  [disk]                          │  │
│  │  [sync]    [restart]                                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ Output ─────────────────────────────────────────────────┐  │
│  │ > Running 'status' on agent...                          │  │
│  │ ✓ Gateway: Online (PID 1234)                            │  │
│  │ ✓ Model: claude-3-sonnet                                │  │
│  │ ✓ Subagents: 3 running                                  │  │
│  │ ✓ Memory: 2.1GB / 8GB                                   │  │
│  │ ✓ Uptime: 4h 23m                                       │  │
│  │                                                        │  │
│  │                              [Copy] [Clear] [Export]   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. CSS Requirements (Reuse Existing)

The `.shell-*` CSS classes in `components.css` can be adapted:

```css
/* Rename/reuse from shell-* to quick-commands-* */
.quick-commands-container { /* reuse .shell-container */ }
.quick-commands-header { /* reuse .shell-header */ }
.quick-commands-viewer { /* reuse .shell-viewer */ }
.quick-commands-input-row { /* reuse .shell-input-row */ }
```

---

## 6. Security Considerations

1. **Command Allowlist Only** - Never accept raw command strings from frontend
2. **Command Mapping** - Frontend sends `command_id`, backend maps to actual command
3. **Timeout** - Commands should timeout after 30 seconds
4. **Output Limit** - Truncate output at 1000 lines to prevent DoS
5. **Rate Limiting** - Max 10 commands per minute per user

---

## 7. Migration Path

1. Add `'quick_commands'` to `StdoutSubTab` type
2. Create `QuickCommands.tsx` component
3. Add second subtab button to `AgentCard/index.tsx`
4. Conditionally render `QuickCommands` vs `GatewayConsole`
5. (Optional) Create backend quick-command API endpoint
6. Deprecate `useAgentShell.ts` and `terminalApi.create(agentId)` in favor of new approach

---

## 8. Alternative Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Quick Command Runner** (recommended) | Safe, user-friendly, dashboard-appropriate | Limited to predefined commands |
| Agent Config Editor | Great for power users | Too complex for casual users |
| Process Monitor | Useful for debugging | Duplicates some existing functionality |
| Notification Center | Nice for activity feed | Not related to Shell Access purpose |
| Keep Shell Access | Full power | Security risk, incomplete, poor UX |

---

## 9. Files to Create/Modify

### Create
- `frontend/src/components/AgentCard/QuickCommands.tsx`
- `frontend/src/hooks/useQuickCommands.ts`

### Modify
- `frontend/src/types/ui.ts` - Add `'quick_commands'` to StdoutSubTab
- `frontend/src/components/AgentCard/index.tsx` - Add tab button + conditional render
- `frontend/src/styles/components.css` - Add `.quick-commands-*` styles

### Optional Backend
- `api/agents.py` - New `/api/agents/<id>/quick-command` endpoint
- `api/config.py` - Add `QUICK_COMMANDS` config per agent

---

## 10. Success Metrics

- [ ] Quick Commands tab is visible and clickable in AgentCard
- [ ] At least 5 commands functional across different categories
- [ ] Output displays within 1 second of command execution
- [ ] No security vulnerabilities (command injection blocked)
- [ ] CSS matches existing dashboard styling
- [ ] Shell Access code can be removed/deprecated afterward
