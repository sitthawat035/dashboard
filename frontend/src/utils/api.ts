// src/utils/api.ts — Centralized API client
// Replaces 32+ scattered fetch() calls with typed, consistent helpers.

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

// Global auth-expired callback — set by useAuth hook
let onAuthExpired: (() => void) | null = null;

export function setAuthExpiredHandler(handler: () => void) {
  onAuthExpired = handler;
}

// ── Core request wrapper ─────────────────────────────────────────────────────
async function request<T = any>(
  url: string,
  method: HttpMethod = 'GET',
  body?: Record<string, any>,
): Promise<{ ok: boolean; status: number; data: T }> {
  const opts: RequestInit = {
    method,
    credentials: 'include',
  };

  if (body && method !== 'GET') {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(url, opts);

  // Central 401 handler
  if (res.status === 401) {
    onAuthExpired?.();
    return { ok: false, status: 401, data: null as any };
  }

  if (!res.ok) {
    return { ok: false, status: res.status, data: null as any };
  }

  // Try to parse JSON, fall back to null
  let data: T;
  try {
    data = await res.json();
  } catch {
    data = null as any;
  }

  return { ok: true, status: res.status, data };
}

// ── Convenience helpers ──────────────────────────────────────────────────────
export const api = {
  get: <T = any>(url: string) => request<T>(url, 'GET'),
  post: <T = any>(url: string, body?: Record<string, any>) => request<T>(url, 'POST', body),
  put: <T = any>(url: string, body?: Record<string, any>) => request<T>(url, 'PUT', body),
  del: <T = any>(url: string) => request<T>(url, 'DELETE'),
};

// ── Domain-specific API modules ──────────────────────────────────────────────

/** Auth & session */
export const authApi = {
  ping: () => api.get('/api/ping'),
  login: (password: string) => api.post('/api/login', { password }),
};

/** Agent status */
export const statusApi = {
  getAll: () => api.get<Record<string, any>>('/api/status'),
  getHealth: (agentId: string) => api.get<{ online: boolean }>(`/api/status/${agentId}/health`),
};

/** Gateway control & data */
export const gatewayApi = {
  control: (gw: string, action: string) => api.post(`/api/gateway/${gw}/${action}`),
  startAll: () => api.post('/api/gateway/start-all'),
  stop: (gw: string) => api.post(`/api/gateway/${gw}/stop`),
  getLog: (gw: string, lines = 100) => api.get(`/api/gateway/${gw}/log?lines=${lines}`),
  changeModel: (gw: string, model: string) => api.post(`/api/gateway/${gw}/model`, { model }),
  getFiles: (gw: string) => api.get(`/api/gateway/${gw}/files`),
  getFile: (gw: string, name: string) => api.get(`/api/gateway/${gw}/file?name=${encodeURIComponent(name)}`),
  saveFile: (gw: string, name: string, content: string) => api.post(`/api/gateway/${gw}/file`, { name, content }),
};

/** Terminal sessions */
export const terminalApi = {
  create: (agentId?: string) => api.post('/api/terminal/new', agentId ? { agent_id: agentId } : {}),
  getOutput: (sid: string, since: number) => api.get(`/api/terminal/${sid}/output?since=${since}`),
  send: (sid: string, cmd: string) => api.post(`/api/terminal/${sid}/send`, { cmd }),
  kill: (sid: string) => api.post(`/api/terminal/${sid}/kill`),
};

/** Subagents */
export const subagentApi = {
  stream: () => api.get('/api/subagents/stream'),
  conversation: (agentId: string, limit = 150) => api.get(`/api/subagents/conversation/${agentId}?limit=${limit}`),
};

/** Agent messaging */
export const messageApi = {
  send: (agentKey: string, message: string) => api.post(`/api/message/${agentKey}`, { message }),
};

/** Mission Control */
export const missionApi = {
  getAgents: () => api.get('/api/mission-control/agents'),
  getTasks: () => api.get('/api/mission-control/tasks'),
  getAlerts: () => api.get('/api/mission-control/alerts'),
  getAchievements: () => api.get('/api/mission-control/achievements'),
  reassignTask: (taskId: string, agentId: string) => api.post(`/api/mission-control/tasks/${taskId}/reassign`, { agentId }),
  dismissAlert: (alertId: string) => api.post(`/api/mission-control/alerts/${alertId}/dismiss`),
};

/** Engines */
export const engineApi = {
  list: () => api.get('/api/engines/list'),
  status: () => api.get('/api/engines/status'),
  run: (id: string, options?: Record<string, any>) => api.post(`/api/engines/run/${id}`, options),
  history: (id: string) => api.get(`/api/engines/history/${id}`),
  historyLog: (id: string, file: string) => api.get(`/api/engines/history/log/${id}/${file}`),
  preview: (id: string) => api.get(`/api/engines/preview/${id}`),
  upload: async (file: File): Promise<{success: boolean; path?: string; error?: string}> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/engines/upload', {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },
};

/** System & Settings */
export const systemApi = {
  killAll: () => api.post('/api/system/kill-all'),
  scanCli: () => api.get('/api/settings/scan-cli'),
};

// ─── Hermes Agent Bridge ──────────────────────────────────────────────────────

export interface HermesStatus {
  connected: boolean;
  status?: string;
  platform?: string;
  gateway_state?: string;
  platforms?: Record<string, boolean>;
  active_agents?: number;
  pid?: number;
  error?: string;
}

export interface HermesRun {
  run_id: string;
  status: "started" | "running" | "completed" | "failed" | "stopped" | "ended";
  mode?: "runs_api" | "chat_completions";
}

export interface HermesRunInfo {
  status: string;
  started_at?: number;
  ended_at?: number;
}

export const hermesApi = {
  getStatus: (): Promise<HermesStatus> =>
    api.get('/api/hermes/status').then((r) => r.data),

  startRun: (message: string, model?: string): Promise<HermesRun> =>
    api.post('/api/hermes/run', { message, model }).then((r) => r.data),

  listRuns: (): Promise<Record<string, HermesRunInfo>> =>
    api.get('/api/hermes/runs').then((r) => r.data),

  stopRun: (runId: string): Promise<{ stopped: boolean }> =>
    api.post(`/api/hermes/runs/${runId}/stop`).then((r) => r.data),

  getCronJobs: (): Promise<any> =>
    api.get('/api/hermes/cron').then((r) => r.data),

  triggerCronJob: (jobId: string): Promise<any> =>
    api.post(`/api/hermes/cron/${jobId}/run`).then((r) => r.data),
};
