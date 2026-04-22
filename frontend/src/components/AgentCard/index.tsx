// components/AgentCard/index.tsx — Thin orchestrator using Context
import { useEffect } from 'react';
import type { Agent, LogData, SubagentLog, LogTab, StdoutSubTab } from '../../types';
import { AgentCardProvider, useAgentCard } from '../../contexts/AgentCardContext';

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

// Inner component that uses context
function AgentCardContent() {
  const {
    gw, info, online,
    logData, curLogTab, onSwitchTab, stdoutSubTab, onSwitchStdoutSubTab,
    subagentLogs,
    shell,
    isStarting,
    contentCollapsed, setContentCollapsed,
    detailTab, setDetailTab,
    logScrollRef,
    handleControlClick,
  } = useAgentCard();

  // Auto-expand/collapse logic
  const contentExpandedByLogRef = { current: false };
  const contentExpandedBySubagentRef = { current: false };

  useEffect(() => {
    if (online && contentCollapsed && !contentExpandedByLogRef.current) {
      setContentCollapsed(false);
      contentExpandedByLogRef.current = true;
    }
  }, [online, contentCollapsed, setContentCollapsed]);

  useEffect(() => {
    if (curLogTab === 'err' && subagentLogs.length > 0 && contentCollapsed && !contentExpandedBySubagentRef.current) {
      setContentCollapsed(false);
      contentExpandedBySubagentRef.current = true;
    }
  }, [curLogTab, subagentLogs.length, contentCollapsed, setContentCollapsed]);

  // Log auto-scroll
  const prevLogSizeRef = { current: 0 };
  useEffect(() => {
    const logSize = logData.log_size || 0;
    if (logSize > prevLogSizeRef.current && logScrollRef.current) {
      requestAnimationFrame(() => { if (logScrollRef.current) logScrollRef.current.scrollTop = logScrollRef.current.scrollHeight; });
    }
    prevLogSizeRef.current = logSize;
  }, [logData.log_size, curLogTab, stdoutSubTab, logScrollRef]);

  // Auto-clear starting state when online
  useEffect(() => {
    if (online && isStarting) {
      handleControlClick(gw, 'stop');
    }
  }, [online, isStarting, gw, handleControlClick]);

  return (
    <div className={`agent-detail-card glass animate-fade ${info.cls}`} data-testid={`agent-detail-${gw}`}>
      <AgentHeader />

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
                  💬 Chat
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
                <ChatPanel />
              ) : curLogTab === 'err' ? (
                <SubagentMonitor logs={subagentLogs} agentName={info.name} agentId={gw} />
              ) : stdoutSubTab === 'shell' ? (
                <ShellAccess agentName={info.name} shell={shell} />
              ) : (
                <GatewayConsole />
              )}
            </div>
          ) : (
            <FileManager gw={gw} />
          )}
        </div>
      )}
    </div>
  );
}

// Main component that provides context
const AgentCard: React.FC<AgentCardProps> = (props) => {
  return (
    <AgentCardProvider {...props}>
      <AgentCardContent />
    </AgentCardProvider>
  );
};

export default AgentCard;
