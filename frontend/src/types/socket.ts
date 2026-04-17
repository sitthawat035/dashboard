// types/socket.ts — Socket-related types

export interface SocketEvent {
  type: string;
  payload: unknown;
  timestamp?: string;
}

export interface GatewayLogInitEvent {
  agent_id: string;
  lines: string[];
}

export interface GatewayLogLineEvent {
  agent_id: string;
  line: string;
}

export interface GatewayLogLinesEvent {
  agent_id: string;
  lines: string[];
}

export interface TerminalCreatedEvent {
  session_id: string;
}

export interface TerminalOutputEvent {
  session_id: string;
  output: string;
}

export interface AgentStatusEvent {
  agentId: string;
  status: 'online' | 'offline';
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastConnected?: string;
  reconnectAttempts?: number;
}

export type SocketEventType =
  | 'connect'
  | 'disconnect'
  | 'connect_error'
  | 'reconnect'
  | 'reconnect_error'
  | 'reconnect_failed'
  | 'agent:status'
  | 'gateway_log_init'
  | 'gateway_log_line'
  | 'gateway_log_lines'
  | 'terminal_created'
  | 'terminal_output'
  | 'terminal_killed';

export interface SocketEventMap {
  connect: () => void;
  disconnect: (reason: string) => void;
  connect_error: (error: Error) => void;
  reconnect: (attemptNumber: number) => void;
  reconnect_error: (error: Error) => void;
  reconnect_failed: () => void;
  'agent:status': (data: AgentStatusEvent) => void;
  gateway_log_init: (data: GatewayLogInitEvent) => void;
  gateway_log_line: (data: GatewayLogLineEvent) => void;
  gateway_log_lines: (data: GatewayLogLinesEvent) => void;
  terminal_created: (data: TerminalCreatedEvent) => void;
  terminal_output: (data: TerminalOutputEvent) => void;
  terminal_killed: (data: { session_id: string }) => void;
}
