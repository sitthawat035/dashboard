// src/types.ts — Legacy types file (deprecated)
// Import from types/index.ts instead

// Re-export all types from new structure
export * from './types/index';

// Legacy types for backward compatibility
export type { Agent, AgentInfo, AgentStatus, SubagentLog } from './types/agent';
export type { LogData, ApiResponse } from './types/api';
export type { LogTab, StdoutSubTab, TabId, TermSession, ChatMessage } from './types/ui';
