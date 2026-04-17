// components/AgentCard/index.tsx — Thin orchestrator (decomposed from 631 lines → ~220 lines)
import { useState, useEffect, useRef, useCallback } from 'react';
import type { Agent, LogData, SubagentLog, LogTab, StdoutSubTab } from '../../types';
import { statusApi, gatewayApi, messageApi } from '../../utils/api';
import { useAgentShell } from '../../hooks/useAgentShell';

// Sub-components
import AgentHeader from './AgentHeader';
import GatewayConsole from './GatewayConsole';
import ShellAccess from './ShellAccess';
import ChatPanel from './ChatPanel';
import FileManager from './FileManager';
import SubagentMonitor from './SubagentMonitor';

interface AgentCardProps {
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
}

const AgentCard: React.FC<AgentCardProps> = ({
  gw, info, agent, logData, curLogTab,
  onSwitchTab, stdoutSubTab, onSwitchStdoutSubTab,
  onControl, onWatchLive, onSwitchAgent,
  chatMessages, setChatMessages,
  chatInput, setChatInput,
  subagentLogs = [],
  onRefreshStatus,
  allAgents = [],
}) => {
  const online = agent?.online || false;
  const logScrollRef = useRef<HTMLDivElement>(null);

  const [detailTab, setDetailTab] = useState<'console' | 'config'>('console');
  const [contentCollapsed, setContentCollapsed] = useState(!online);
  const contentExpandedByLogRef = useRef(false);
  const contentExpandedBySubagentRef = useRef(false);

  // ── Gateway Starting Animation State ──
  const [isStarting, setIsStarting] = useState(false);
  const [startFailed, setStartFailed] = useState(false);
  const startingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startingPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Model State ──
  const [selectedModel, setSelectedModel] = useState(agent?.primary_model || '');
  const [modelSaving, setModelSaving] = useState(false);
  const availableModels = agent?.available_models || [];

  // ── Shell (via extracted hook) ──
  const shell = useAgentShell(gw);

  // ── Auto-expand/collapse logic ──
  useEffect(() => {
    if (online && isStarting) {
      setIsStarting(false);
      setStartFailed(false);
      if (startingTimerRef.current) clearTimeout(startingTimerRef.current);
    }
  }, [online, isStarting]);

  useEffect(() => {
    return () => {
      if (startingTimerRef.current) clearTimeout(startingTimerRef.current);
      clearStartingPoll();
    };
  }, []);

  useEffect(() => {
    if (online && contentCollapsed && !contentExpandedByLogRef.current) {
      setContentCollapsed(false);
      contentExpandedByLogRef.current = true;
    }
  }, [online, contentCollapsed]);

  useEffect(() => {
    if (curLogTab === 'err' && subagentLogs.length > 0 && contentCollapsed && !contentExpandedBySubagentRef.current) {
      setContentCollapsed(false);
      contentExpandedBySubagentRef.current = true;
    }
  }, [curLogTab, subagentLogs.length, contentCollapsed]);

  // ── Log auto-scroll ──
  const prevLogSizeRef = useRef(0);
  useEffect(() => {
    const logSize = logData.log_size || 0;
    if (logSize > prevLogSizeRef.current && logScrollRef.current) {
      requestAnimationFrame(() => { if (logScrollRef.current) logScrollRef.current.scrollTop = logScrollRef.current.scrollHeight; });
    }
    prevLogSizeRef.current = logSize;
  }, [logData.log_size, curLogTab, stdoutSubTab]);

  // ── Starting poll helpers ──
  const clearStartingPoll = () => {
    if (startingPollRef.current) {
      clearInterval(startingPollRef.current);
      startingPollRef.current = null;
    }
  };

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
  }, [onControl, onRefreshStatus]);

  // ── Model change ──
  const changeModel = async (model: string) => {
    setSelectedModel(model);
    setModelSaving(true);
    try { await gatewayApi.changeModel(gw, model); } catch {}
    setModelSaving(false);
  };

  // ── Chat send ──
  const sendChat = async () => {
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
  };

  // ── Render ──
  return (
    <div className={`agent-detail-card glass animate-fade ${info.cls}`} data-testid={`agent-detail-${gw}`}>
      <AgentHeader
        gw={gw} info={info} agent={agent} online={online}
        allAgents={allAgents}
        selectedModel={selectedModel} modelSaving={modelSaving} availableModels={availableModels}
        isStarting={isStarting} startFailed={startFailed}
        onSwitchAgent={onSwitchAgent} onChangeModel={changeModel}
        onControlClick={handleControlClick} onWatchLive={onWatchLive}
      />

      <div className="agent-tabs">
        <button className={`tab-btn ${detailTab === 'console' ? 'active' : ''}`} onClick={() => setDetailTab('console')}>Console & Chat</button>
        <button className={`tab-btn ${detailTab === 'config' ? 'active' : ''}`} onClick={() => setDetailTab('config')}>Config & Files</button>
        <button className={`tab-btn tab-collapse ${contentCollapsed ? 'collapsed' : ''}`}
          onClick={() => setContentCollapsed(!contentCollapsed)}
          title={contentCollapsed ? 'Expand' : 'Collapse'}>
          {contentCollapsed ? '▼ Expand' : '▲ Collapse'}
        </button>
      </div>

      {!contentCollapsed && (
        <div className="agent-content">
          {detailTab === 'console' ? (
            <div className="console-wrapper">
              <div className="console-subtabs">
                <button className={`subtab ${curLogTab === 'log' ? 'active' : ''}`} onClick={() => onSwitchTab('log')}>
                  📄 stdout {logData.log.length > 0 && <span className="dot on" />}
                </button>
                <button className={`subtab ${curLogTab === 'err' ? 'active' : ''}`} onClick={() => onSwitchTab('err')}>
                  🤖 Subagents
                  {subagentLogs.length > 0 && <span className="sa-count-badge">{subagentLogs.length}</span>}
                </button>
                <button className={`subtab ${curLogTab === 'chat' ? 'active' : ''}`} onClick={() => onSwitchTab('chat')}>
                  💬 Chat {chatMessages.length > 0 && <span className="msg-count">{chatMessages.length}</span>}
                </button>
              </div>

              {curLogTab === 'log' && (
                <div className="stdout-subtabs">
                  <button className={`subtab-sm ${stdoutSubTab === 'gateway_logs' ? 'active' : ''}`} onClick={() => onSwitchStdoutSubTab('gateway_logs')}>
                    📄 GATEWAY LOGS
                  </button>
                  <button className={`subtab-sm ${stdoutSubTab === 'shell' ? 'active' : ''}`}
                    onClick={() => { onSwitchStdoutSubTab('shell'); if (!shell.shellSid) shell.initShell(); }}>
                    💻 SHELL ACCESS {shell.shellAlive && <span className="dot on" />}
                  </button>
                </div>
              )}

              {curLogTab === 'chat' ? (
                <ChatPanel
                  agentName={info.name}
                  chatMessages={chatMessages}
                  chatInput={chatInput}
                  setChatInput={setChatInput}
                  onSendChat={sendChat}
                />
              ) : curLogTab === 'err' ? (
                <SubagentMonitor logs={subagentLogs} agentName={info.name} agentId={gw} />
              ) : stdoutSubTab === 'shell' ? (
                <ShellAccess agentName={info.name} shell={shell} />
              ) : (
                <GatewayConsole
                  gw={gw} agentName={info.name} online={online}
                  isStarting={isStarting} startFailed={startFailed}
                  onControlClick={handleControlClick}
                />
              )}
            </div>
          ) : (
            <FileManager gw={gw} />
          )}
        </div>
      )}
    </div>
  );
};

export default AgentCard;
