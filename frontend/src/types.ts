// src/types.ts

export interface Agent {
  name: string;
  emoji: string;
  port: number;
  online: boolean;
  color: string;
  subagents?: { id: string; name: string }[];
  primary_model?: string;
  available_models?: string[];
  token?: string;
  identity?: string;
  soul?: string;
  user_md?: string;
  memory_md?: string;
  heartbeat?: string;
}

export interface TermSession {
  id: string;
  lineCount: number;
  pollRef?: any;
}

export interface LogData {
  log: string[];
  err: string[];
  log_size?: number;
  err_size?: number;
}

export interface SubagentLog {
  id: string;
  agent: string;
  session_key: string;
  task: string;
  status: 'running' | 'complete' | 'error';
  timestamp: string;
  snippet?: string;
  mode?: string;
  model?: string;
}

export type LogTab = 'log' | 'err' | 'chat';
export type StdoutSubTab = 'gateway_logs' | 'shell';
export type TabId = 'dashboard' | 'agents' | 'terminal' | 'memory' | 'logs' | 'multi' | 'settings';
