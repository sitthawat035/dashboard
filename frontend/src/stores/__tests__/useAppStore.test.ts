// src/stores/__tests__/useAppStore.test.ts — Tests for useAppStore
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAppStore } from '../useAppStore';

// Mock API
vi.mock('../../utils/api', () => ({
  statusApi: {
    getAll: vi.fn(),
  },
  gatewayApi: {
    control: vi.fn(),
    startAll: vi.fn(),
  },
  systemApi: {
    killAll: vi.fn(),
  },
}));

describe('useAppStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAppStore.setState({
      activeTab: 'dashboard',
      sidebarOpen: true,
      agents: {},
      selectedAgent: null,
      logTab: {},
      stdoutSubTab: {},
      chatSessions: {},
      chatInputs: {},
      logData: {},
      subagentLogs: [],
      socketConnected: false,
      socketReconnecting: false,
      isLoggedIn: false,
    });
  });

  describe('Navigation', () => {
    it('should set active tab', () => {
      const { setActiveTab } = useAppStore.getState();
      setActiveTab('agents');
      expect(useAppStore.getState().activeTab).toBe('agents');
    });

    it('should set sidebar open', () => {
      const { setSidebarOpen } = useAppStore.getState();
      setSidebarOpen(false);
      expect(useAppStore.getState().sidebarOpen).toBe(false);
    });
  });

  describe('Agents', () => {
    it('should set agents', () => {
      const { setAgents } = useAppStore.getState();
      const agents = {
        'agent-1': {
          id: 'agent-1',
          name: 'Agent 1',
          emoji: '🤖',
          port: 10000,
          online: true,
          color: '#00ff00',
        },
      };
      setAgents(agents);
      expect(useAppStore.getState().agents).toEqual(agents);
    });

    it('should update agent', () => {
      const { setAgents, updateAgent } = useAppStore.getState();
      const agents = {
        'agent-1': {
          id: 'agent-1',
          name: 'Agent 1',
          emoji: '🤖',
          port: 10000,
          online: false,
          color: '#00ff00',
        },
      };
      setAgents(agents);
      updateAgent('agent-1', { online: true });
      expect(useAppStore.getState().agents['agent-1'].online).toBe(true);
    });

    it('should set selected agent', () => {
      const { setSelectedAgent } = useAppStore.getState();
      setSelectedAgent('agent-1');
      expect(useAppStore.getState().selectedAgent).toBe('agent-1');
    });
  });

  describe('Per-agent UI', () => {
    it('should set log tab for agent', () => {
      const { setLogTabForAgent } = useAppStore.getState();
      setLogTabForAgent('agent-1', 'err');
      expect(useAppStore.getState().logTab['agent-1']).toBe('err');
    });

    it('should set stdout subtab for agent', () => {
      const { setStdoutSubTabForAgent } = useAppStore.getState();
      setStdoutSubTabForAgent('agent-1', 'shell');
      expect(useAppStore.getState().stdoutSubTab['agent-1']).toBe('shell');
    });

    it('should set chat messages for agent', () => {
      const { setChatMessagesForAgent } = useAppStore.getState();
      const messages = [{ role: 'user' as const, text: 'Hello' }];
      setChatMessagesForAgent('agent-1', messages);
      expect(useAppStore.getState().chatSessions['agent-1']).toEqual(messages);
    });

    it('should set chat input for agent', () => {
      const { setChatInputForAgent } = useAppStore.getState();
      setChatInputForAgent('agent-1', 'Test input');
      expect(useAppStore.getState().chatInputs['agent-1']).toBe('Test input');
    });
  });

  describe('Log Data', () => {
    it('should set log data', () => {
      const { setLogData } = useAppStore.getState();
      const logData = {
        'agent-1': {
          log: ['Line 1'],
          err: [],
          log_size: 1,
          err_size: 0,
        },
      };
      setLogData(logData);
      expect(useAppStore.getState().logData).toEqual(logData);
    });

    it('should update log data', () => {
      const { setLogData, updateLogData } = useAppStore.getState();
      const logData = {
        'agent-1': {
          log: ['Line 1'],
          err: [],
          log_size: 1,
          err_size: 0,
        },
      };
      setLogData(logData);
      updateLogData('agent-1', { log: ['Line 1', 'Line 2'], log_size: 2 });
      expect(useAppStore.getState().logData['agent-1'].log_size).toBe(2);
    });
  });

  describe('Subagents', () => {
    it('should set subagent logs', () => {
      const { setSubagentLogs } = useAppStore.getState();
      const logs = [
        {
          id: 'subagent-1',
          agent: 'agent-1',
          session_key: 'session-1',
          task: 'Test task',
          status: 'running' as const,
          timestamp: '2024-01-01T00:00:00Z',
        },
      ];
      setSubagentLogs(logs);
      expect(useAppStore.getState().subagentLogs).toEqual(logs);
    });
  });

  describe('Socket', () => {
    it('should set socket connected', () => {
      const { setSocketConnected } = useAppStore.getState();
      setSocketConnected(true);
      expect(useAppStore.getState().socketConnected).toBe(true);
    });

    it('should set socket reconnecting', () => {
      const { setSocketReconnecting } = useAppStore.getState();
      setSocketReconnecting(true);
      expect(useAppStore.getState().socketReconnecting).toBe(true);
    });
  });

  describe('Auth', () => {
    it('should set is logged in', () => {
      const { setIsLoggedIn } = useAppStore.getState();
      setIsLoggedIn(true);
      expect(useAppStore.getState().isLoggedIn).toBe(true);
    });
  });
});
