// src/App.tsx — Thin orchestrator: routing + socket wiring only
// All state now lives in Zustand → components read directly from store
import { useState, useEffect, useRef } from 'react';
import { systemApi } from './utils/api';
import './App.css';
import socketManager from './utils/socket';

// Hooks (still needed for socket-aware logic)
import { useAuth } from './hooks/useAuth';
import { useLogStream } from './hooks/useLogStream';
import { useSubagents } from './hooks/useSubagents';
import { useTerminal } from './hooks/useTerminal';

// Zustand store
import { useAppStore } from './stores/useAppStore';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './pages/DashboardPage';
import AgentPage from './pages/AgentPage';
import TerminalModule from './components/TerminalModule';
import LoginScreen from './components/LoginScreen';
import CLIProviders from './components/CLIProviders';
import MissionControl from './pages/MissionControlPage';
import EngineHub from './pages/EngineHubPage';
import { Maximize, Minimize } from 'lucide-react';

export default function App() {
  // ── Store selectors ──
  const activeTab = useAppStore(s => s.activeTab);
  const agents = useAppStore(s => s.agents);
  const updateAgent = useAppStore(s => s.updateAgent);
  const socketConnected = useAppStore(s => s.socketConnected);
  const setSocketConnected = useAppStore(s => s.setSocketConnected);
  const socketReconnecting = useAppStore(s => s.socketReconnecting);
  const setSocketReconnecting = useAppStore(s => s.setSocketReconnecting);
  const loadStatus = useAppStore(s => s.loadStatus);

  // ── Local state (UI-only, not shared) ──
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [cliScanState, setCliScanState] = useState<'idle' | 'scanning' | 'done'>('idle');
  const [detectedProviders, setDetectedProviders] = useState<any[]>([]);

  const statusPollerRef = useRef<any>(null);
  const logPollerRef = useRef<any>(null);
  const FALLBACK_POLL_INTERVAL = 3000;

  // ── Hooks ──
  const auth = useAuth();
  const { isLoggedIn, isLoading, password, setPassword, loginError, handleLogin } = auth;
  const { loadAllLogs, handleGatewayLogInit, handleGatewayLogLine } = useLogStream();
  const { loadSubagentLogs } = useSubagents();
  const {
    termSessions, activeTermSid, setActiveTermSid,
    cmdHistory, newSession, killTerm, termSend,
    pushHistory, historyUp, historyDown,
  } = useTerminal(socketConnected);

  // ── Utility ──
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const executeCliScan = async () => {
    setCliScanState('scanning');
    const { ok, data } = await systemApi.scanCli();
    if (ok && data) setDetectedProviders(data.detected || []);
    setCliScanState('done');
  };

  // ── Effects ──
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(console.error);
    }
  }, []);

  // Socket.IO setup
  useEffect(() => {
    if (!isLoggedIn && isLoading) return;

    socketManager.connect();

    const handleConnect = () => {
      setSocketConnected(true);
      setSocketReconnecting(false);
    };

    const handleDisconnect = (reason: string) => {
      setSocketConnected(false);
      setSocketReconnecting(reason === 'io server disconnect' || reason === 'io client disconnect');
    };

    const handleConnectError = () => setSocketConnected(false);
    const handleReconnect = () => { setSocketConnected(true); setSocketReconnecting(false); };
    const handleReconnectError = () => setSocketReconnecting(true);
    const handleReconnectFailed = () => { setSocketConnected(false); setSocketReconnecting(false); };

    const handleAgentStatus = (data: { agentId: string; status: string }) => {
      updateAgent(data.agentId, { online: data.status === 'online' });
    };

    const handleTerminalOutput = (_sid: string, output: string) => {
      const writeFn = (window as any).__termWriteOutput;
      if (typeof writeFn === 'function') writeFn(output);
    };

    socketManager.on('connect', handleConnect);
    socketManager.on('disconnect', handleDisconnect);
    socketManager.on('connect_error', handleConnectError);
    socketManager.on('reconnect', handleReconnect);
    socketManager.on('reconnect_error', handleReconnectError);
    socketManager.on('reconnect_failed', handleReconnectFailed);
    socketManager.on('agent:status', handleAgentStatus);
    socketManager.on('gateway_log_init', handleGatewayLogInit);
    socketManager.on('gateway_log_line', handleGatewayLogLine);

    if (socketManager.isConnected()) handleConnect();

    const terminalListeners: { [key: string]: Function } = {};
    const setupTerminalListener = (sid: string) => {
      if (terminalListeners[sid]) return;
      terminalListeners[sid] = (output: string) => handleTerminalOutput(sid, output);
      socketManager.on(`terminal_output_${sid}`, terminalListeners[sid]);
    };

    socketManager.on('terminal_created', (data: { session_id: string }) => {
      setupTerminalListener(data.session_id);
    });

    return () => {
      socketManager.off('connect', handleConnect);
      socketManager.off('disconnect', handleDisconnect);
      socketManager.off('connect_error', handleConnectError);
      socketManager.off('reconnect', handleReconnect);
      socketManager.off('reconnect_error', handleReconnectError);
      socketManager.off('reconnect_failed', handleReconnectFailed);
      socketManager.off('agent:status', handleAgentStatus);
      socketManager.off('gateway_log_init', handleGatewayLogInit);
      socketManager.off('gateway_log_line', handleGatewayLogLine);
      socketManager.off('terminal_created');
      Object.keys(terminalListeners).forEach(sid => {
        socketManager.off(`terminal_output_${sid}`, terminalListeners[sid]);
      });
    };
  }, [isLoggedIn, isLoading, handleGatewayLogInit, handleGatewayLogLine, setSocketConnected, setSocketReconnecting, updateAgent]);

  // Dynamic log subscriptions
  useEffect(() => {
    if (!socketConnected || Object.keys(agents).length === 0) return;
    Object.keys(agents).forEach(agentId => {
      socketManager.emit('join_log_stream', { agent_id: agentId });
    });
  }, [socketConnected, agents]);

  // Polling fallback
  useEffect(() => {
    if (isLoading) return;

    loadStatus();
    const agentIds = Object.keys(agents);
    if (agentIds.length > 0) {
      loadAllLogs(agentIds);
      loadSubagentLogs();
    }

    const startFallbackPolling = () => {
      if (statusPollerRef.current) clearInterval(statusPollerRef.current);
      if (logPollerRef.current) clearInterval(logPollerRef.current);
      statusPollerRef.current = setInterval(loadStatus, FALLBACK_POLL_INTERVAL);
      logPollerRef.current = setInterval(() => loadAllLogs(Object.keys(agents)), FALLBACK_POLL_INTERVAL);
    };

    const stopFallbackPolling = () => {
      if (statusPollerRef.current) { clearInterval(statusPollerRef.current); statusPollerRef.current = null; }
      if (logPollerRef.current) { clearInterval(logPollerRef.current); logPollerRef.current = null; }
    };

    const subagentPollerRef = setInterval(loadSubagentLogs, FALLBACK_POLL_INTERVAL);

    if (!socketConnected && !socketReconnecting) startFallbackPolling();

    const onConnect = () => stopFallbackPolling();
    const onDisconnect = () => startFallbackPolling();

    socketManager.on('connect', onConnect);
    socketManager.on('disconnect', onDisconnect);

    return () => {
      socketManager.off('connect', onConnect);
      socketManager.off('disconnect', onDisconnect);
      stopFallbackPolling();
      clearInterval(subagentPollerRef);
    };
  }, [isLoading, loadStatus, loadAllLogs, loadSubagentLogs, socketConnected, socketReconnecting]);

  // ── Render ──
  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="multi-spinner" />
        <p>Verifying session...</p>
      </div>
    );
  }

  if (!isLoggedIn && loginError !== undefined) {
    return <LoginScreen password={password} setPassword={setPassword} onLogin={handleLogin} loginError={loginError} />;
  }

  const PAGE_TITLES: Record<string, string> = {
    dashboard: 'Dashboard Overview',
    mission: '🎮 Mission Control',
    agents: 'Agent Manager',
    terminal: 'PowerShell Console',
    settings: 'CLI OAuth Providers',
    memory: 'Knowledge Base',
    logs: 'System Logs',
    multi: 'Engine Operations Center',
  };

  return (
    <div className="app-container">
      <div className="noise-overlay" />
      <Sidebar />
      <main className="main-content glass">
        <header className="main-header">
          <h2>{PAGE_TITLES[activeTab] || 'JOEPV Master'}</h2>
          <div className="header-actions">
            <div
              className="connection-status"
              title={socketConnected ? 'Real-time updates active' : socketReconnecting ? 'Reconnecting...' : 'Using polling fallback'}
            >
              <div className={`connection-dot ${socketConnected ? 'connected' : socketReconnecting ? 'reconnecting' : 'disconnected'}`} />
              <span className="connection-text">
                {socketConnected ? 'Live' : socketReconnecting ? 'Reconnecting' : 'Polling'}
              </span>
            </div>
            <button className="btn-header" onClick={toggleFullscreen} title="Toggle Fullscreen">
              {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
            </button>
          </div>
        </header>

        <section className="view-port">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'mission' && <MissionControl agents={agents} />}
          {activeTab === 'agents' && <AgentPage />}

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
            <CLIProviders
              cliScanState={cliScanState}
              detectedProviders={detectedProviders}
              onExecuteCliScan={executeCliScan}
            />
          )}

          {activeTab === 'multi' && <EngineHub />}
        </section>
      </main>
    </div>
  );
}
