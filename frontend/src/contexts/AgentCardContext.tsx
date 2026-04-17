// contexts/AgentCardContext.tsx — Context for AgentCard to reduce prop drilling
import { createContext, useContext, useState, useRef, useCallback, type ReactNode } from 'react';
import type { Agent, LogData, SubagentLog, LogTab, StdoutSubTab } from '../types';
import { statusApi, gatewayApi, messageApi } from '../utils/api';
import { useAgentShell } from '../hooks/useAgentShell';

interface AgentCardContextValue {
  gw: string;
  info: { name: string; emoji: string; port: number; cls: string };
  agent?: Agent;
  online: boolean;
  allAgents: Agent[];
  logData: LogData;
  curLogTab: LogTab;
  onSwitchTab: (tab: LogTab) => void;
  stdoutSubTab: StdoutSubTab;
  onSwitchStdoutSubTab: (tab: StdoutSubTab) => void;
  onControl: (gw: string, action: string) => void;
  onWatchLive: (gw: string) => void;
  onSwitchAgent?: (gw: string) => void;
  onRefreshStatus?: () => void;
  chatMessages: any[];
  setChatMessages: (updater: any) => void;
  chatInput: string;
  setChatInput: (val: string) => void;
  subagentLogs: SubagentLog[];
  shell: ReturnType<typeof useAgentShell>;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  modelSaving: boolean;
  setModelSaving: (saving: boolean) => void;
  availableModels: string[];
  isStarting: boolean;
  setIsStarting: (starting: boolean) => void;
  startFailed: boolean;
  setStartFailed: (failed: boolean) => void;
  contentCollapsed: boolean;
  setContentCollapsed: (collapsed: boolean) => void;
  detailTab: 'console' | 'config';
  setDetailTab: (tab: 'console' | 'config') => void;
  logScrollRef: React.RefObject<HTMLDivElement | null>;
  handleControlClick: (gwKey: string, action: string) => void;
  changeModel: (model: string) => void;
  sendChat: () => void;
}

const AgentCardContext = createContext<AgentCardContextValue | null>(null);

export function useAgentCard() {
  const context = useContext(AgentCardContext);
  if (!context) {
    throw new Error('useAgentCard must be used within AgentCardProvider');
  }
  return context;
}

interface AgentCardProviderProps {
  gw: string;
  info: { name: string; emoji: string; port: number; cls: string };
  agent?: Agent;
  logData: LogData;
  curLogTab: LogTab;
  onSwitchTab: (tab: LogTab) => void;
  stdoutSubTab: StdoutSubTab;
  onSwitchStdoutSubTab: (tab: StdoutSubTab) => void;
  onControl: (gw: string, action: string) => void;
  onWatchLive: (gw: string) => void;
  onSwitchAgent?: (gw: string) => void;
  chatMessages: any[];
  setChatMessages: (updater: any) => void;
  chatInput: string;
  setChatInput: (val: string) => void;
  subagentLogs?: SubagentLog[];
  onRefreshStatus?: () => void;
  allAgents?: Agent[];
  children: ReactNode;
}

export function AgentCardProvider({
  gw, info, agent, logData, curLogTab,
  onSwitchTab, stdoutSubTab, onSwitchStdoutSubTab,
  onControl, onWatchLive, onSwitchAgent,
  chatMessages, setChatMessages,
  chatInput, setChatInput,
  subagentLogs = [],
  onRefreshStatus,
  allAgents = [],
  children,
}: AgentCardProviderProps) {
  const online = agent?.online || false;
  const logScrollRef = useRef<HTMLDivElement>(null);

  const [detailTab, setDetailTab] = useState<'console' | 'config'>('console');
  const [contentCollapsed, setContentCollapsed] = useState(!online);

  const [isStarting, setIsStarting] = useState(false);
  const [startFailed, setStartFailed] = useState(false);
  const startingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startingPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [selectedModel, setSelectedModel] = useState(agent?.primary_model || '');
  const [modelSaving, setModelSaving] = useState(false);
  const availableModels = agent?.available_models || [];

  const shell = useAgentShell(gw);

  const clearStartingPoll = useCallback(() => {
    if (startingPollRef.current) {
      clearInterval(startingPollRef.current);
      startingPollRef.current = null;
    }
  }, []);

  const handleControlClick = useCallback((gwKey: string, action: string) => {
    if (action === 'start') {
      setIsStarting(true);
      setStartFailed(false);
      clearStartingPoll();
      if (startingTimerRef.current) clearTimeout(startingTimerRef.current);
      startingTimerRef.current = setTimeout(() => {
        setIsStarting(false);
        setStartFailed(true);
        clearStartingPoll();
      }, 180000);

      const pollStatus = async () => {
        try {
          const { ok, status, data } = await statusApi.getHealth(gwKey);
          if (status === 401) { startingPollRef.current = setTimeout(pollStatus, 1500) as any; return; }
          if (!ok) { startingPollRef.current = setTimeout(pollStatus, 1500) as any; return; }
          if (data?.online) {
            setIsStarting(false);
            setStartFailed(false);
            clearStartingPoll();
            if (startingTimerRef.current) clearTimeout(startingTimerRef.current);
            onRefreshStatus?.();
            return;
          }
        } catch {}
        startingPollRef.current = setTimeout(pollStatus, 1500) as any;
      };
      startingPollRef.current = setTimeout(pollStatus, 1500) as any;
    } else if (action === 'stop') {
      setIsStarting(false);
      setStartFailed(false);
      clearStartingPoll();
      if (startingTimerRef.current) clearTimeout(startingTimerRef.current);
    } else if (action === 'restart') {
      setStartFailed(false);
      clearStartingPoll();
    }
    onControl(gwKey, action);
  }, [onControl, onRefreshStatus, clearStartingPoll]);

  const changeModel = useCallback(async (model: string) => {
    setSelectedModel(model);
    setModelSaving(true);
    try { await gatewayApi.changeModel(gw, model); } catch {}
    setModelSaving(false);
  }, [gw]);

  const sendChat = useCallback(async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages((prev: any[]) => [...prev, { role: 'user', text: msg }]);
    try {
      const { ok, data } = await messageApi.send(gw, msg);
      if (ok && data) {
        setChatMessages((prev: any[]) => [...prev, { role: 'assistant', text: data.response || 'No response' }]);
      } else {
        setChatMessages((prev: any[]) => [...prev, { role: 'system', text: 'Error connecting to agent' }]);
      }
    } catch {
      setChatMessages((prev: any[]) => [...prev, { role: 'system', text: 'Error connecting to agent' }]);
    }
  }, [gw, chatInput, setChatInput, setChatMessages]);

  const value: AgentCardContextValue = {
    gw, info, agent, online, allAgents,
    logData, curLogTab, onSwitchTab, stdoutSubTab, onSwitchStdoutSubTab,
    onControl, onWatchLive, onSwitchAgent, onRefreshStatus,
    chatMessages, setChatMessages, chatInput, setChatInput,
    subagentLogs, shell,
    selectedModel, setSelectedModel, modelSaving, setModelSaving, availableModels,
    isStarting, setIsStarting, startFailed, setStartFailed,
    contentCollapsed, setContentCollapsed,
    detailTab, setDetailTab,
    logScrollRef,
    handleControlClick, changeModel, sendChat,
  };

  return (
    <AgentCardContext.Provider value={value}>
      {children}
    </AgentCardContext.Provider>
  );
}
