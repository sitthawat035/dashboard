// types/agent.ts — Agent-related types

export interface Agent {
  id: string;
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

export interface AgentInfo {
  name: string;
  emoji: string;
  port: number;
  cls: string;
}

export interface AgentStatus {
  agentId: string;
  status: 'online' | 'offline';
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
  workspace?: string;
  error?: string;
}
