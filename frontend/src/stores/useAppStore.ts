// stores/useAppStore.ts — Zustand global store (replaces prop drilling)
import { create } from 'zustand';
import type { Agent, TabId, LogTab, StdoutSubTab, LogData, SubagentLog } from '../types';
import { statusApi, systemApi, gatewayApi } from '../utils/api';

interface AppState {
  // Navigation
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // Agents
  agents: Record<string, Agent>;
  setAgents: (agents: Record<string, Agent>) => void;
  updateAgent: (id: string, patch: Partial<Agent>) => void;
  selectedAgent: string | null;
  setSelectedAgent: (gw: string | null) => void;

  // Per-agent UI state
  logTab: Record<string, LogTab>;
  setLogTabForAgent: (gw: string, tab: LogTab) => void;
  stdoutSubTab: Record<string, StdoutSubTab>;
  setStdoutSubTabForAgent: (gw: string, tab: StdoutSubTab) => void;
  chatSessions: Record<string, ChatMessage[]>;
  setChatMessagesForAgent: (gw: string, updater: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  chatInputs: Record<string, string>;
  setChatInputForAgent: (gw: string, val: string) => void;

  // Log Data
  logData: Record<string, LogData>;
  setLogData: (data: Record<string, LogData>) => void;
  updateLogData: (gw: string, data: Partial<LogData>) => void;

  // Subagents
  subagentLogs: SubagentLog[];
  setSubagentLogs: (logs: SubagentLog[]) => void;

  // Socket
  socketConnected: boolean;
  setSocketConnected: (val: boolean) => void;
  socketReconnecting: boolean;
  setSocketReconnecting: (val: boolean) => void;

  // Auth
  isLoggedIn: boolean;
  setIsLoggedIn: (val: boolean) => void;

  // Actions
  loadStatus: () => Promise<void>;
  control: (gw: string, action: string) => Promise<void>;
  startAll: () => Promise<void>;
  restartAll: () => Promise<void>;
  killAll: () => Promise<void>;
}

// Import ChatMessage type
import type { ChatMessage } from '../types';

export const useAppStore = create<AppState>((set, get) => ({
  // Navigation
  activeTab: 'dashboard',
  setActiveTab: (tab) => set({ activeTab: tab }),
  sidebarOpen: typeof window !== 'undefined' ? window.innerWidth > 768 : true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Agents
  agents: {},
  setAgents: (agents) => set({ agents }),
  updateAgent: (id, patch) => set(state => ({
    agents: { ...state.agents, [id]: { ...state.agents[id], ...patch } }
  })),
  selectedAgent: null,
  setSelectedAgent: (gw) => set({ selectedAgent: gw }),

  // Per-agent UI
  logTab: {},
  setLogTabForAgent: (gw, tab) => set(state => ({ logTab: { ...state.logTab, [gw]: tab } })),
  stdoutSubTab: {},
  setStdoutSubTabForAgent: (gw, tab) => set(state => ({ stdoutSubTab: { ...state.stdoutSubTab, [gw]: tab } })),
  chatSessions: {},
  setChatMessagesForAgent: (gw, updater) => set(state => {
    const prev = state.chatSessions[gw] || [];
    const next = typeof updater === 'function' ? updater(prev) : updater;
    return { chatSessions: { ...state.chatSessions, [gw]: next } };
  }),
  chatInputs: {},
  setChatInputForAgent: (gw, val) => set(state => ({ chatInputs: { ...state.chatInputs, [gw]: val } })),

  // Log Data
  logData: {},
  setLogData: (data) => set({ logData: data }),
  updateLogData: (gw, data) => set(state => ({
    logData: { ...state.logData, [gw]: { ...state.logData[gw], ...data } as LogData }
  })),

  // Subagents
  subagentLogs: [],
  setSubagentLogs: (logs) => set({ subagentLogs: logs }),

  // Socket
  socketConnected: false,
  setSocketConnected: (val) => set({ socketConnected: val }),
  socketReconnecting: false,
  setSocketReconnecting: (val) => set({ socketReconnecting: val }),

  // Auth
  isLoggedIn: false,
  setIsLoggedIn: (val) => set({ isLoggedIn: val }),

  // Actions
  loadStatus: async () => {
    const { ok, status, data } = await statusApi.getAll();
    if (status === 401) { set({ isLoggedIn: false }); return; }
    if (ok && data) set({ agents: data });
  },

  control: async (gw, action) => {
    const { status } = await gatewayApi.control(gw, action);
    if (status === 401) { set({ isLoggedIn: false }); return; }
    setTimeout(() => get().loadStatus(), 2500);
  },

  startAll: async () => {
    const { status } = await gatewayApi.startAll();
    if (status === 401) { set({ isLoggedIn: false }); return; }
    setTimeout(() => get().loadStatus(), 3000);
  },

  restartAll: async () => {
    const agents = get().agents;
    for (const gw of Object.keys(agents)) {
      const { status } = await gatewayApi.control(gw, 'restart');
      if (status === 401) { set({ isLoggedIn: false }); return; }
      await new Promise(r => setTimeout(r, 1800));
    }
    setTimeout(() => get().loadStatus(), 2500);
  },

  killAll: async () => {
    try {
      const { status, data } = await systemApi.killAll();
      if (status === 401) { set({ isLoggedIn: false }); return; }
      if (data?.success) {
        alert('GLOBAL WIPE COMPLETED: ' + data.message);
        get().loadStatus();
      }
    } catch (e) {
      alert('Error during sweep: ' + e);
    }
  },
}));
