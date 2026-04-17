// src/App.tsx — Thin orchestrator: routing + socket wiring only
// All state now lives in Zustand → components read directly from store
import { useState, useEffect } from 'react';
import { systemApi } from './utils/api';
import './App.css';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useTerminal } from './hooks/useTerminal';
import { useSocketEvents } from './hooks/useSocketEvents';

// Zustand store
import { useAppStore } from './stores/useAppStore';

// Components
import Sidebar from './components/Sidebar';
import LoginScreen from './components/LoginScreen';
import AppHeader from './components/AppHeader';
import AppRouter from './components/AppRouter';

export default function App() {
  // ── Store selectors ──
  const socketConnected = useAppStore(s => s.socketConnected);

  // ── Local state (UI-only, not shared) ──
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [cliScanState, setCliScanState] = useState<'idle' | 'scanning' | 'done'>('idle');
  const [detectedProviders, setDetectedProviders] = useState<any[]>([]);

  // ── Hooks ──
  const auth = useAuth();
  const { isLoggedIn, isLoading, password, setPassword, loginError, handleLogin } = auth;
  const {
    termSessions, activeTermSid, setActiveTermSid,
    cmdHistory, newSession, killTerm, termSend,
    pushHistory, historyUp, historyDown,
  } = useTerminal(socketConnected);

  // ── Socket Events (centralized) ──
  useSocketEvents({});

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

  return (
    <div className="app-container">
      <div className="noise-overlay" />
      <Sidebar />
      <main className="main-content glass">
        <AppHeader isFullscreen={isFullscreen} onToggleFullscreen={toggleFullscreen} />
        <AppRouter
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
          cliScanState={cliScanState}
          detectedProviders={detectedProviders}
          onExecuteCliScan={executeCliScan}
        />
      </main>
    </div>
  );
}
