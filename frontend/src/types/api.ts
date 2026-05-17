// types/api.ts — API-related types

export interface ApiResponse<T = unknown> {
  ok: boolean;
  status: number;
  data: T;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface LogData {
  log: string[];
  err: string[];
  log_size?: number;
  err_size?: number;
}

export interface GatewayStatus {
  online: boolean;
  port?: number;
  pid?: number;
  uptime?: number;
}

export interface TerminalSession {
  session_id: string;
  created_at?: string;
}

export interface TerminalOutput {
  lines: string[];
  total: number;
}

export interface LoginRequest {
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
}

export interface MessageRequest {
  message: string;
}

export interface MessageResponse {
  response: string;
  error?: string;
}

export interface ModelChangeRequest {
  model: string;
}

export interface FileContent {
  name: string;
  content: string;
  path?: string;
  size?: number;
  modified?: string;
}

export interface FileList {
  files: string[];
  directories?: string[];
}

export interface ScanCliResponse {
  detected: ProviderInfo[];
}

export interface ProviderInfo {
  name: string;
  version?: string;
  path?: string;
  available: boolean;
}

export interface KillAllResponse {
  success: boolean;
  message: string;
}

export interface MissionControlAgent {
  id: string;
  name: string;
  status: string;
  task?: string;
  performance?: number;
}

export interface MissionControlTask {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignedTo?: string;
  priority?: 'low' | 'medium' | 'high';
  createdAt?: string;
  updatedAt?: string;
}

export interface MissionControlAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
  dismissed?: boolean;
}

export interface MissionControlAchievement {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  unlockedAt?: string;
}

export interface EngineInfo {
  id: string;
  name: string;
  description?: string;
  version?: string;
  status: 'available' | 'running' | 'error';
}

export interface EngineStatus {
  id: string;
  running: boolean;
  pid?: number;
  uptime?: number;
  lastRun?: string;
}

export interface EngineHistory {
  id: string;
  timestamp: string;
  status: 'success' | 'failed';
  duration?: number;
  logFile?: string;
}

export interface EnginePreview {
  id: string;
  type: string;
  url?: string;
  content?: string;
}
