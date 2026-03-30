// src/App.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import './index.css';

// Types & Constants
import type { Agent, TermSession, LogData, TabId, SubagentLog, LogTab, StdoutSubTab } from './types';
import { GW_KEYS, GW_INFO } from './constants';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AgentCard from './components/AgentCard';
import TerminalModule from './components/TerminalModule';
import LoginScreen from './components/LoginScreen';
import CLIProviders from './components/CLIProviders';
import MissionControl from './components/MissionControl';
import { Maximize, Minimize } from 'lucide-react';

const MAX_HISTORY = 100;

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState(false);

  // State
  const [logData, setLogData] = useState<Record<string, LogData>>({});
  const [logTab, setLogTab] = useState<Record<string, LogTab>>({});
  const [stdoutSubTab, setStdoutSubTab] = useState<Record<string, StdoutSubTab>>({});
  const [chatSessions, setChatSessions] = useState<Record<string, any[]>>({});
  const [chatInputs, setChatInputs] = useState<Record<string, string>>({});
  const [termSessions, setTermSessions] = useState<Record<string, TermSession>>({});
  const [activeTermSid, setActiveTermSid] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [cliScanState, setCliScanState] = useState<'idle'|'scanning'|'done'>('idle');
  const [detectedProviders, setDetectedProviders] = useState<any[]>([]);
  const [subagentLogs, setSubagentLogs] = useState<SubagentLog[]>([]);

  // Terminal command history
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const histIdxRef = useRef(-1);

  const statusPollerRef = useRef<any>(null);
  const logPollerRef = useRef<any>(null);
  const sessionsRef = useRef(termSessions);
  sessionsRef.current = termSessions;

  const loadStatus = useCallback(async () => {
    try {
      const r = await fetch('/api/status');
      if (r.status === 401) { setIsLoggedIn(false); return; }
      if (r.ok) setAgents(await r.json());
    } catch {}
  }, []);

  const loadLog = useCallback(async (gw: string) => {
    try {
      const r = await fetch(`/api/gateway/${gw}/log?lines=100`);
      if (!r.ok) return;
      const d = await r.json();
      setLogData(prev => ({ ...prev, [gw]: { log: d.log || [], err: d.err || [], log_size: d.log_size, err_size: d.err_size } }));
    } catch {}
  }, []);

  const loadAllLogs = useCallback(async () => {
    await Promise.all(GW_KEYS.map(gw => loadLog(gw)));
  }, [loadLog]);

  const loadSubagentLogs = useCallback(async () => {
    try {
      const r = await fetch('/api/subagents/stream');
      if (r.ok) {
        const d = await r.json();
        setSubagentLogs(d.subagents || []);
      }
    } catch {}
  }, []);

  const handleLogin = async () => {
    try {
      const r = await fetch('/api/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (r.ok) { setIsLoggedIn(true); setLoginError(false); }
      else setLoginError(true);
    } catch { setLoginError(true); }
  };

  const control = async (gw: string, action: string) => {
    await fetch(`/api/gateway/${gw}/${action}`, { method: 'POST' });
    setTimeout(loadStatus, 2500);
  };

  const startAll = async () => {
    await fetch('/api/gateway/start-all', { method: 'POST' });
    setTimeout(loadStatus, 3000);
  };

  const restartAll = async () => {
    for (const gw of GW_KEYS) {
      await fetch(`/api/gateway/${gw}/restart`, { method: 'POST' });
      await new Promise(r => setTimeout(r, 1800));
    }
    setTimeout(loadStatus, 2500);
  };

  const executeCliScan = async () => {
    setCliScanState('scanning');
    try {
      const r = await fetch('/api/settings/scan-cli');
      if (r.ok) {
        const data = await r.json();
        setDetectedProviders(data.detected || []);
      }
    } catch {}
    setCliScanState('done');
  };

  // ── Terminal Polling (writes to xterm.js) ──
  const pollTerm = useCallback(async (sid: string) => {
    const sess = sessionsRef.current[sid];
    if (!sess) return;
    try {
      const r = await fetch(`/api/terminal/${sid}/output?since=${sess.lineCount}`);
      if (!r.ok) return;
      const d = await r.json();
      if (d.lines?.length > 0) {
        // Write to xterm.js via global function set by TerminalModule
        const writeFn = (window as any).__termWriteOutput;
        if (typeof writeFn === 'function') {
          writeFn(d.lines);
        }
        setTermSessions(prev => ({ ...prev, [sid]: { ...prev[sid], lineCount: d.total } }));
      }
    } catch {}
  }, []);

  const killTerm = useCallback(async (sid: string) => {
    const sess = sessionsRef.current[sid];
    if (sess?.pollRef) clearInterval(sess.pollRef);
    setTermSessions(prev => { const n = { ...prev }; delete n[sid]; return n; });
    setActiveTermSid(prev => prev === sid ? null : prev);
    try { await fetch('/api/terminal/' + sid + '/kill', { method: 'POST' }); } catch {}
  }, []);

  const newSession = useCallback(async () => {
    try {
      const r = await fetch('/api/terminal/new', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (!r.ok) return;
      const data = await r.json();
      const sid = data.session_id;
      const pollRef = setInterval(() => pollTerm(sid), 400);
      setTermSessions(prev => ({ ...prev, [sid]: { id: sid, lineCount: 0, pollRef } }));
      setActiveTermSid(sid);
    } catch {}
  }, [pollTerm]);

  const termSend = useCallback(async () => {
    // Fallback for legacy input field (if any)
    const inp = document.getElementById('term-cmd-input') as HTMLInputElement;
    const cmd = inp?.value.trim();
    if (!cmd || !activeTermSid) return;
    inp.value = '';
    try {
      await fetch(`/api/terminal/${activeTermSid}/send`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd }),
      });
    } catch {}
  }, [activeTermSid]);

  // ── Command History Callbacks ──
  const pushHistory = useCallback((cmd: string) => {
    if (!cmd.trim()) return;
    setCmdHistory(prev => {
      const next = [...prev, cmd.trim()];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
    histIdxRef.current = -1;
  }, []);

  const historyUp = useCallback((): string | null => {
    setCmdHistory(prev => {
      if (prev.length === 0) return prev;
      if (histIdxRef.current === -1) {
        histIdxRef.current = prev.length - 1;
      } else if (histIdxRef.current > 0) {
        histIdxRef.current--;
      }
      return prev;
    });
    // We need to return the value synchronously, so use the ref
    if (cmdHistory.length === 0) return null;
    const idx = histIdxRef.current === -1 ? cmdHistory.length - 1 : histIdxRef.current;
    return cmdHistory[idx] ?? null;
  }, [cmdHistory]);

  const historyDown = useCallback((): string | null => {
    if (histIdxRef.current === -1) return null;
    if (histIdxRef.current >= cmdHistory.length - 1) {
      histIdxRef.current = -1;
      return '';
    }
    histIdxRef.current++;
    return cmdHistory[histIdxRef.current] ?? '';
  }, [cmdHistory]);

  const watchGwLog = (_gw: string) => {
    setActiveTab('terminal');
    setTimeout(async () => {
        if (!activeTermSid) await newSession();
    }, 1000);
  };

  const killAll = async () => {
    try {
      const r = await fetch('/api/system/kill-all', { method: 'POST' });
      const data = await r.json();
      if (data.success) {
        alert('GLOBAL WIPE COMPLETED: ' + data.message);
        loadStatus();
      }
    } catch (e) {
      alert('Error during sweep: ' + e);
    }
  };

  const [multiStatus, setMultiStatus] = useState({ online: false, checking: false });
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };
  
  const checkMulti = async () => {
    try {
      const r = await fetch('/api/system/multicontent/status');
      const data = await r.json();
      setMultiStatus({ online: data.online, checking: false });
      if (!data.online && !multiStatus.checking) {
          console.log("Auto-starting MultiContentApp...");
          await fetch('/api/system/multicontent/start', { method: 'POST' });
          setMultiStatus(prev => ({ ...prev, checking: true }));
          setTimeout(checkMulti, 5000);
      }
    } catch { }
  };

  useEffect(() => {
    if (activeTab === 'multi') {
        checkMulti();
    }
  }, [activeTab]);

  useEffect(() => {
    fetch('/api/status').then(r => { if (r.ok) setIsLoggedIn(true); });
    
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(console.error);
    }
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    loadStatus();
    loadAllLogs();
    loadSubagentLogs();
    statusPollerRef.current = setInterval(loadStatus, 3000);
    logPollerRef.current = setInterval(loadAllLogs, 3000);
    const subagentPollerRef = setInterval(loadSubagentLogs, 3000);
    return () => {
      if (statusPollerRef.current) clearInterval(statusPollerRef.current);
      if (logPollerRef.current) clearInterval(logPollerRef.current);
      clearInterval(subagentPollerRef);
    };
  }, [isLoggedIn, loadStatus, loadAllLogs, loadSubagentLogs]);

  if (!isLoggedIn) {
    return <LoginScreen password={password} setPassword={setPassword} onLogin={handleLogin} loginError={loginError} />;
  }

  const activeCount = Object.values(agents).filter((a: any) => a.online).length;

  return (
    <div className="app-container">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        sidebarOpen={sidebarOpen} 
        setSidebarOpen={setSidebarOpen}
        onLogout={() => setIsLoggedIn(false)}
        onKillAll={killAll}
      />
      <main className="main-content glass">
        <header className="main-header">
            <h2>{(({ 
                dashboard: 'Dashboard Overview', 
                mission: '🎮 Mission Control',
                agents: 'Agent Manager', 
                terminal: 'PowerShell Console', settings: 'CLI OAuth Providers',
                memory: 'Knowledge Base', logs: 'System Logs', multicontent: 'MultiContent Hub'
            } as any)[activeTab]) || 'JOEPV Master'}</h2>
            <div className="header-actions">
              <button className="btn-header" onClick={toggleFullscreen} title="Toggle Fullscreen">
                {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
              </button>
            </div>
        </header>
        <section className="view-port">
            {activeTab === 'dashboard' && (
                <Dashboard agents={agents} activeCount={activeCount} onControl={control} onSetSelectedAgent={setSelectedAgent} onSetActiveTab={setActiveTab} onStartAll={startAll} onRestartAll={restartAll} onLoadStatus={loadStatus} onLoadAllLogs={loadAllLogs} />
            )}
            {activeTab === 'mission' && (
                <MissionControl agents={agents} />
            )}
            {activeTab === 'agents' && (
                selectedAgent ? (
                    <div className="agent-detail-view animate-fade">
                        <button className="back-btn" onClick={() => setSelectedAgent(null)}>← BACK TO FLEET</button>
                        <AgentCard 
                            gw={selectedAgent} info={GW_INFO[selectedAgent]} agent={agents[selectedAgent]} 
                            logData={logData[selectedAgent] || { log: [], err: [] }} 
                            curLogTab={logTab[selectedAgent] || 'log'} 
                            onSwitchTab={tab => { 
                              setLogTab(prev => ({ ...prev, [selectedAgent]: tab })); 
                              if (tab === 'log' && !stdoutSubTab[selectedAgent]) {
                                setStdoutSubTab(prev => ({ ...prev, [selectedAgent]: 'gateway_logs' }));
                              }
                            }} 
                            stdoutSubTab={stdoutSubTab[selectedAgent] || 'gateway_logs'}
                            onSwitchStdoutSubTab={tab => setStdoutSubTab(prev => ({ ...prev, [selectedAgent]: tab }))}
                            onControl={control} onWatchLive={watchGwLog}
                            onSwitchAgent={setSelectedAgent}
                            chatMessages={chatSessions[selectedAgent] || []} 
                            setChatMessages={(updater: any) => setChatSessions(prev => ({ ...prev, [selectedAgent]: typeof updater === 'function' ? updater(prev[selectedAgent] || []) : updater }))} 
                            chatInput={chatInputs[selectedAgent] || ''} 
                            setChatInput={(val: string) => setChatInputs(prev => ({ ...prev, [selectedAgent]: val }))}
                            subagentLogs={subagentLogs.filter(log => log.agent === selectedAgent)}
                        />
                    </div>
                ) : (
                    <div className="agents-grid animate-fade">
                        {GW_KEYS.map(gw => {
                          const info = GW_INFO[gw];
                          const agent = agents[gw];
                          const online = agent?.online || false;
                          const modelFull = agent?.primary_model || '-';
                          const model = modelFull.includes('/') ? modelFull.split('/').pop()! : modelFull;
                          const subCount = agent?.subagents?.length || 0;
                          return (
                            <div key={gw} className={`agent-mini-item glass ${info.cls}`} onClick={() => setSelectedAgent(gw)}>
                              <div className="agi-top">
                                <span className="agi-emoji">{info.emoji}</span>
                                <span className="agi-name">{info.name}</span>
                                <span className={`status-dot ${online ? 'online' : 'offline'}`}></span>
                              </div>
                              <div className="agi-details">
                                <div className="agi-row"><span className="agi-label">Port</span><span className="agi-val">{info.port}</span></div>
                                <div className="agi-row"><span className="agi-label">Status</span><span className={`agi-val ${online ? 'text-green' : 'text-red'}`}>{online ? 'Online' : 'Offline'}</span></div>
                                <div className="agi-row"><span className="agi-label">Model</span><span className="agi-val agi-model">{model.length > 18 ? model.substring(0,18)+'...' : model}</span></div>
                                {subCount > 0 && <div className="agi-row"><span className="agi-label">Subagents</span><span className="agi-val">{subCount}</span></div>}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                )
            )}
            {activeTab === 'terminal' && (
                <TerminalModule 
                  termSessions={termSessions} 
                  activeTermSid={activeTermSid} 
                  setActiveTermSid={setActiveTermSid} 
                  onKillTerm={killTerm} 
                  onNewSession={newSession} 
                  onTermSend={termSend}
                  cmdHistory={cmdHistory}
                  onHistoryUp={historyUp}
                  onHistoryDown={historyDown}
                  onPushHistory={pushHistory}
                />
            )}
            {activeTab === 'settings' && (
                <CLIProviders cliScanState={cliScanState} detectedProviders={detectedProviders} onExecuteCliScan={executeCliScan} />
            )}
            {activeTab === 'multi' && (
                <div className="multicontent-wrapper animate-fade">
                    {!multiStatus.online ? (
                        <div className="multi-loading">
                            <div className="multi-spinner"></div>
                            <p>Initializing MultiContent Server...</p>
                        </div>
                    ) : (
                        <iframe 
                            src="http://localhost:5000" 
                            className="multi-iframe"
                            title="MultiContentApp"
                        />
                    )}
                </div>
            )}
        </section>
      </main>
    </div>
  );
}
