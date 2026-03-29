// src/components/AgentCard.tsx
import { useState, useEffect, useRef } from 'react';
import type { Agent, LogData, SubagentLog, LogTab, StdoutSubTab } from '../types';
import { highlightLog, classifyLog } from '../utils/ansi';
import { GW_KEYS, GW_INFO } from '../constants';
import { ExternalLink } from 'lucide-react';

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
}

// ── SubagentMonitor Component ─────────────────────────────────────────────────
const SubagentMonitor: React.FC<{ logs: SubagentLog[]; agentName: string }> = ({ logs, agentName }) => {
  const [filter, setFilter] = useState<'all' | 'running' | 'complete' | 'error'>('all');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const filtered = logs.filter(l => filter === 'all' || l.status === filter);
  const counts = {
    all: logs.length,
    running: logs.filter(l => l.status === 'running').length,
    complete: logs.filter(l => l.status === 'complete').length,
    error: logs.filter(l => l.status === 'error').length,
  };

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const toggle = (id: string) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const statusColors: Record<string, string> = {
    running: '#58a6ff',
    complete: '#3fb950',
    error: '#f85149',
  };

  const statusIcons: Record<string, string> = {
    running: '⚡',
    complete: '✅',
    error: '❌',
  };

  return (
    <div className="sa-monitor">
      {/* Stats bar */}
      <div className="sa-stats-bar">
        <div className="sa-stat">
          <span className="sa-stat-num">{counts.all}</span>
          <span className="sa-stat-label">Total</span>
        </div>
        <div className="sa-stat sa-stat-running">
          <span className="sa-stat-num">{counts.running}</span>
          <span className="sa-stat-label">Running</span>
        </div>
        <div className="sa-stat sa-stat-complete">
          <span className="sa-stat-num">{counts.complete}</span>
          <span className="sa-stat-label">Done</span>
        </div>
        <div className="sa-stat sa-stat-error">
          <span className="sa-stat-num">{counts.error}</span>
          <span className="sa-stat-label">Errors</span>
        </div>
        <div className="sa-autoscroll">
          <label className="sa-toggle-label">
            <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} />
            <span>Auto-scroll</span>
          </label>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="sa-filter-bar">
        {(['all', 'running', 'complete', 'error'] as const).map(f => (
          <button
            key={f}
            className={`sa-filter-btn ${filter === f ? 'active' : ''} sa-filter-${f}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? '🌐' : statusIcons[f]} {f.charAt(0).toUpperCase() + f.slice(1)}
            {counts[f] > 0 && <span className="sa-filter-count">{counts[f]}</span>}
          </button>
        ))}
      </div>

      {/* Session list */}
      <div className="sa-session-list" ref={scrollRef}>
        {filtered.length === 0 ? (
          <div className="sa-empty">
            {logs.length === 0 ? (
              <>
                <div className="sa-empty-icon">🤖</div>
                <div className="sa-empty-title">No Subagent Activity</div>
                <div className="sa-empty-sub">
                  Spawn a session task to see {agentName}'s subagents in action.<br />
                  Logs are parsed live from the gateway log file.
                </div>
              </>
            ) : (
              <>
                <div className="sa-empty-icon">🔍</div>
                <div className="sa-empty-title">No {filter} sessions</div>
              </>
            )}
          </div>
        ) : (
          filtered.map((log) => {
            const isExpanded = expanded[log.id];
            const color = statusColors[log.status] || '#8b949e';
            const modelShort = log.model
              ? (log.model.includes('/') ? log.model.split('/').pop()! : log.model)
              : '';

            return (
              <div
                key={log.id}
                className={`sa-session-card sa-status-${log.status}`}
                style={{ borderLeftColor: color }}
                onClick={() => toggle(log.id)}
              >
                <div className="sa-session-top">
                  <div className="sa-session-left">
                    {log.status === 'running' && <span className="sa-live-pulse" />}
                    <span className="sa-session-icon">{statusIcons[log.status]}</span>
                    <div className="sa-session-info">
                      <div className="sa-session-name">{log.session_key}</div>
                      <div className="sa-session-time">{log.timestamp}</div>
                    </div>
                  </div>
                  <div className="sa-session-right">
                    {modelShort && (
                      <span className="sa-model-badge">
                        🧠 {modelShort.length > 20 ? modelShort.substring(0, 20) + '…' : modelShort}
                      </span>
                    )}
                    <span className={`sa-status-badge sa-status-${log.status}`}>
                      {log.status.toUpperCase()}
                    </span>
                    <span className="sa-expand-icon">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                <div className="sa-session-task">
                  📋 {log.task.length > 100 ? log.task.substring(0, 100) + '…' : log.task}
                </div>

                {isExpanded && (
                  <div className="sa-session-detail">
                    <div className="sa-detail-row">
                      <span className="sa-detail-label">Run ID</span>
                      <span className="sa-detail-value mono">{log.id}</span>
                    </div>
                    {log.model && (
                      <div className="sa-detail-row">
                        <span className="sa-detail-label">Model</span>
                        <span className="sa-detail-value mono">{log.model}</span>
                      </div>
                    )}
                    {log.snippet && (
                      <div className="sa-detail-snippet">
                        <div className="sa-detail-label">Last Output</div>
                        <div className="sa-snippet-content">{log.snippet}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

// ── AgentCard ─────────────────────────────────────────────────────────────────
const AgentCard: React.FC<AgentCardProps> = ({
  gw, info, agent, logData, curLogTab,
  onSwitchTab, stdoutSubTab, onSwitchStdoutSubTab,
  onControl, onWatchLive, onSwitchAgent,
  chatMessages, setChatMessages,
  chatInput, setChatInput,
  subagentLogs = [],
}) => {
  const online = agent?.online || false;
  const logScrollRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  const [detailTab, setDetailTab] = useState<'console' | 'config'>('console');
  const [contentCollapsed, setContentCollapsed] = useState(!online);
  const [files, setFiles] = useState<{ name: string; size: number; is_workspace?: boolean }[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  const [fileSaving, setFileSaving] = useState(false);

  const [selectedModel, setSelectedModel] = useState(agent?.primary_model || '');
  const [modelSaving, setModelSaving] = useState(false);
  const availableModels = agent?.available_models || [];

  const [shellSid, setShellSid] = useState<string | null>(null);
  const [shellLines, setShellLines] = useState<string[]>([]);
  const [shellInput, setShellInput] = useState('');
  const [shellAlive, setShellAlive] = useState(false);
  const shellPollerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const shellLineCountRef = useRef(0);

  const changeModel = async (model: string) => {
    setSelectedModel(model);
    setModelSaving(true);
    try {
      await fetch(`/api/gateway/${gw}/model`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model }),
      });
    } catch {}
    setModelSaving(false);
  };

  useEffect(() => {
    if (detailTab === 'config') {
      fetch(`/api/gateway/${gw}/files`).then(r => r.json()).then(d => setFiles(d.files || [])).catch(console.error);
    }
  }, [detailTab, gw]);

  useEffect(() => {
    if (selectedFile) {
      setFileContent('Loading...');
      fetch(`/api/gateway/${gw}/file?name=${encodeURIComponent(selectedFile)}`)
        .then(r => r.json()).then(d => setFileContent(d.content || ''))
        .catch(e => setFileContent(`Error loading file: ${e}`));
    }
  }, [selectedFile, gw]);

  const saveFile = async () => {
    if (!selectedFile) return;
    setFileSaving(true);
    try {
      await fetch(`/api/gateway/${gw}/file`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: selectedFile, content: fileContent }),
      });
    } catch (e) { console.error(e); }
    setFileSaving(false);
  };

  const prevLogSizeRef = useRef(0);
  useEffect(() => {
    const logSize = logData.log_size || 0;
    if (logSize > prevLogSizeRef.current && logScrollRef.current) {
      requestAnimationFrame(() => { if (logScrollRef.current) logScrollRef.current.scrollTop = logScrollRef.current.scrollHeight; });
    }
    prevLogSizeRef.current = logSize;
  }, [logData.log_size, curLogTab, stdoutSubTab]);

  const initShell = async () => {
    try {
      const r = await fetch('/api/terminal/new', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: gw }),
      });
      const data = await r.json();
      if (data.session_id) {
        shellLineCountRef.current = 0;
        setShellSid(data.session_id);
        setShellAlive(data.alive);
        setShellLines([]);
        startShellPolling(data.session_id);
      }
    } catch (e) { console.error('Shell init failed:', e); }
  };

  const startShellPolling = (sid: string) => {
    if (shellPollerRef.current) clearInterval(shellPollerRef.current);
    shellPollerRef.current = setInterval(async () => {
      try {
        const r = await fetch(`/api/terminal/${sid}/output?since=${shellLineCountRef.current}`);
        const data = await r.json();
        if (data.lines?.length > 0) {
          shellLineCountRef.current = data.total;
          setShellLines(prev => { const n = [...prev, ...data.lines]; return n.length > 500 ? n.slice(-500) : n; });
        }
        setShellAlive(data.alive);
        if (!data.alive && shellPollerRef.current) clearInterval(shellPollerRef.current);
      } catch {}
    }, 500);
  };

  const sendShellCmd = async () => {
    if (!shellInput.trim() || !shellSid) return;
    const cmd = shellInput.trim();
    setShellInput('');
    try {
      await fetch(`/api/terminal/${shellSid}/send`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd }),
      });
    } catch {}
  };

  const killShell = async () => {
    if (shellPollerRef.current) { clearInterval(shellPollerRef.current); shellPollerRef.current = null; }
    if (shellSid) { try { await fetch(`/api/terminal/${shellSid}/kill`, { method: 'POST' }); } catch {} }
    shellLineCountRef.current = 0;
    setShellSid(null); setShellLines([]); setShellAlive(false);
  };

  useEffect(() => { return () => { if (shellPollerRef.current) clearInterval(shellPollerRef.current); }; }, []);
  useEffect(() => { if (shellRef.current) shellRef.current.scrollTop = shellRef.current.scrollHeight; }, [shellLines]);

  const lines = logData.log.slice(-100);

  const sendChat = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages((prev: any[]) => [...prev, { role: 'user', text: msg }]);
    try {
      const res = await fetch(`/api/message/${gw}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setChatMessages((prev: any[]) => [...prev, { role: 'assistant', text: data.response || 'No response' }]);
    } catch {
      setChatMessages((prev: any[]) => [...prev, { role: 'system', text: 'Error connecting to agent' }]);
    }
  };

  return (
    <div className={`agent-detail-card glass animate-fade ${info.cls}`}>
      <div className="agent-header">
        <div className="agent-switcher-row">
          <select title="Switch agent" className="agent-switcher-dropdown" value={gw} onChange={e => onSwitchAgent?.(e.target.value)}>
            {GW_KEYS.map(key => <option key={key} value={key}>{GW_INFO[key].emoji} {GW_INFO[key].name}</option>)}
          </select>
          {agent?.token && (
            <button className="btn-cli-link"
              onClick={() => window.open(`http://${window.location.hostname}:${info.port}/#token=${agent?.token}`, '_blank', 'noopener,noreferrer')}>
              <ExternalLink size={14} /> Open CLI UI
            </button>
          )}
        </div>

        <div className="agent-title-row">
          <span className="agent-emoji">{info.emoji}</span>
          <div className="agent-name-stack">
            <h3>{info.name}</h3>
            <span className="agent-port">PORT: {info.port}</span>
          </div>
          <div className={`status-badge ${online ? 'online' : 'offline'}`}>
            {online ? '● ONLINE' : '● OFFLINE'}
          </div>
        </div>

        <div className="model-selector-row">
          <label className="model-label">Model:</label>
          <select title="Select model" className="model-dropdown" value={selectedModel} onChange={e => changeModel(e.target.value)} disabled={modelSaving}>
            {availableModels.length === 0 && <option value="">No model info</option>}
            {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          {modelSaving && <span className="model-saving">Saving...</span>}
        </div>

        <div className="agent-controls">
          <button className={`btn-solid ${online ? 'btn-danger' : 'btn-green'}`} onClick={() => onControl(gw, online ? 'stop' : 'start')}>
            {online ? '■ STOP' : '▶ START'}
          </button>
          <button className="btn-solid" onClick={() => onControl(gw, 'restart')}>🔄 RESTART</button>
          <button className="btn-solid" onClick={() => onWatchLive(gw)}>📺 WATCH LIVE</button>
        </div>
      </div>

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
                    onClick={() => { onSwitchStdoutSubTab('shell'); if (!shellSid) initShell(); }}>
                    💻 SHELL ACCESS {shellAlive && <span className="dot on" />}
                  </button>
                </div>
              )}

              {curLogTab === 'chat' ? (
                <div className="chat-container">
                  <div className="chat-history">
                    {chatMessages.length === 0 && <div className="chat-placeholder">💬 Start a conversation with {info.name}...</div>}
                    {chatMessages.map((m, i) => (
                      <div key={i} className={`chat-msg ${m.role}`}>
                        <div className="msg-header">
                          <span className="msg-role">{m.role === 'user' ? 'YOU' : info.name}</span>
                          <span className="msg-time">{new Date().toLocaleTimeString()}</span>
                        </div>
                        <div className="msg-content">{m.text}</div>
                      </div>
                    ))}
                  </div>
                  <div className="chat-input-row">
                    <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder="Type a message to agent..." />
                    <button className="btn-send" onClick={sendChat} disabled={!chatInput.trim()}>SEND</button>
                  </div>
                </div>
              ) : curLogTab === 'err' ? (
                <SubagentMonitor logs={subagentLogs} agentName={info.name} />
              ) : stdoutSubTab === 'shell' ? (
                <div className="shell-container">
                  <div className="shell-header">
                    <span className="shell-status">
                      {shellAlive ? <span className="text-green-400">● LIVE</span> : <span className="text-gray-500">○ OFFLINE</span>}
                    </span>
                    {!shellSid ? (
                      <button className="btn-mini btn-start" onClick={initShell}>▶ START SHELL</button>
                    ) : (
                      <>
                        <button className="btn-mini btn-stop" onClick={killShell}>■ KILL</button>
                        <button className="btn-mini btn-restart" onClick={() => { killShell(); setTimeout(initShell, 500); }}>🔄 RESTART</button>
                      </>
                    )}
                  </div>
                  <div className="shell-viewer" ref={shellRef}>
                    {shellLines.map((line, i) => <div key={i} className="shell-line">{line}</div>)}
                    {shellLines.length === 0 && !shellAlive && (
                      <div className="shell-empty">Press START SHELL to begin a PowerShell session for {info.name}</div>
                    )}
                  </div>
                  <div className="shell-input-row">
                    <input value={shellInput} onChange={e => setShellInput(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') sendShellCmd(); }}
                      placeholder="Enter PowerShell command..." disabled={!shellSid || !shellAlive} />
                    <button className="btn-send" onClick={sendShellCmd} disabled={!shellInput.trim() || !shellSid || !shellAlive}>SEND</button>
                  </div>
                </div>
              ) : (
                <div className="log-viewer" ref={logScrollRef}>
                  {lines.map((l, i) => (
                    <div key={i} className={`log-line ${classifyLog(l)}`} dangerouslySetInnerHTML={{ __html: highlightLog(l) }} />
                  ))}
                  {lines.length === 0 && (
                    <div className="log-empty">No gateway logs for {info.name}. {online ? 'Waiting for output...' : 'Gateway is offline.'}</div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="config-wrapper">
              <div className="file-list">
                <div className="file-list-header">WORKSPACE FILES</div>
                {files.map(f => {
                  const isWorkspace = f.name.includes('/') || f.name.includes('\\');
                  return (
                    <div key={f.name} className={`file-item ${selectedFile === f.name ? 'active' : ''} ${f.is_workspace ? 'workspace-file' : ''}`}
                      onClick={() => setSelectedFile(f.name)}>
                      <span className="file-icon">{isWorkspace ? '📁' : '⚙️'}</span>
                      <div className="file-info-mini">
                        <span className="file-name">{f.name}</span>
                        <span className="file-meta">{(f.size / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="file-editor">
                {selectedFile ? (
                  <>
                    <div className="editor-hdr">
                      <div className="editor-title">
                        <span className="tag">EDITING</span>
                        <strong>{selectedFile}</strong>
                      </div>
                      <button className="btn-save" onClick={saveFile} disabled={fileSaving}>
                        {fileSaving ? '⌛ Saving...' : '💾 Save File'}
                      </button>
                    </div>
                    <textarea value={fileContent} onChange={e => setFileContent(e.target.value)} spellCheck={false} placeholder="File content..." />
                  </>
                ) : (
                  <div className="editor-placeholder">
                    <div className="placeholder-icon">📄</div>
                    <p>Select an agent configuration or workspace file to view and edit</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentCard;
