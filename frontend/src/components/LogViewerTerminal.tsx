// components/LogViewerTerminal.tsx — Log viewer using centralized socket events
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import socketManager from '../utils/socket';
import 'xterm/css/xterm.css';

interface LogViewerTerminalProps {
  agentId: string;
}

function unescapeAnsi(str: string): string {
  return str
    .replace(/\\\\u001b/g, '\u001b')
    .replace(/\\u001b/g, '\u001b')
    .replace(/\\\\x1b/g, '\x1b')
    .replace(/\\x1b/g, '\x1b');
}

const LogViewerTerminal: React.FC<LogViewerTerminalProps> = ({ agentId }) => {
  const xtermRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const isScrollLockedRef = useRef(false);
  const hasInitializedRef = useRef(false);

  const [isScrollLocked, setIsScrollLocked] = useState(false);
  const [socketConnected, setSocketConnected] = useState(socketManager.isConnected());
  const [isStreaming, setIsStreaming] = useState(false);

  const toggleScrollLock = () => {
    const next = !isScrollLockedRef.current;
    isScrollLockedRef.current = next;
    setIsScrollLocked(next);
  };

  const forceSync = useCallback(() => {
    if (termRef.current) {
      termRef.current.clear();
      termRef.current.writeln('\x1b[1;33m🔄 Syncing logs from server...\x1b[0m');
    }
    hasInitializedRef.current = false;
    setIsStreaming(false);
    socketManager.emit('leave_log_stream', { agent_id: agentId });
    setTimeout(() => {
      socketManager.emit('join_log_stream', { agent_id: agentId });
    }, 150);
  }, [agentId]);

  // Terminal lifecycle
  useEffect(() => {
    if (!xtermRef.current) return;

    hasInitializedRef.current = false;

    const term = new Terminal({
      cursorBlink: false,
      disableStdin: true,
      fontSize: 13,
      lineHeight: 1.4,
      letterSpacing: 0.5,
      fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
      theme: {
        background: '#000000',
        foreground: '#ffffff',
        black: '#1f2937',
        red: '#ff4a4a',
        green: '#00ff41',
        yellow: '#ffcc00',
        blue: '#3b82f6',
        magenta: '#ff00ff',
        cyan: '#00fbff',
        white: '#f8fafc',
        brightBlack: '#4b5563',
        brightRed: '#ff6b6b',
        brightGreen: '#39ff14',
        brightYellow: '#ffff00',
        brightBlue: '#60a5fa',
        brightMagenta: '#ff79c6',
        brightCyan: '#00ffff',
        brightWhite: '#ffffff',
      },
      scrollback: 10000,
      allowTransparency: true,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(xtermRef.current);
    setTimeout(() => { try { fitAddon.fit(); } catch { /* ignore */ } }, 300);

    let resizeTimer: ReturnType<typeof setTimeout> | null = null;
    const resizeObs = new ResizeObserver(() => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => { try { fitAddon.fit(); } catch { /* ignore */ } }, 200);
    });
    resizeObs.observe(xtermRef.current);

    termRef.current = term;

    // Socket event handlers
    const handleLogInit = (data: { agent_id: string; lines: string[] }) => {
      if (data.agent_id !== agentId || !termRef.current) return;
      if (hasInitializedRef.current) return;

      termRef.current.clear();
      if (data.lines && data.lines.length > 0) {
        data.lines.forEach((line) => {
          const cleaned = unescapeAnsi(line);
          termRef.current!.writeln(cleaned);
        });
      } else {
        termRef.current.writeln('\x1b[2mWaiting for gateway output...\x1b[0m');
      }
      hasInitializedRef.current = true;
      setIsStreaming(true);
      setTimeout(() => { try { termRef.current?.scrollToBottom(); } catch { /* ignore */ } }, 50);
    };

    const handleLogLines = (data: { agent_id: string; lines: string[] }) => {
      if (data.agent_id !== agentId || !termRef.current) return;
      hasInitializedRef.current = true;
      data.lines.forEach((line) => {
        const cleaned = unescapeAnsi(line);
        termRef.current!.writeln(cleaned);
      });
      if (!isScrollLockedRef.current) termRef.current.scrollToBottom();
    };

    const handleLogLine = (data: { agent_id: string; line: string }) => {
      if (data.agent_id !== agentId || !termRef.current) return;
      hasInitializedRef.current = true;
      const cleaned = unescapeAnsi(data.line);
      termRef.current.writeln(cleaned);
      if (!isScrollLockedRef.current) termRef.current.scrollToBottom();
    };

    const handleConnect = () => {
      setSocketConnected(true);
      hasInitializedRef.current = false;
      socketManager.emit('join_log_stream', { agent_id: agentId });
    };
    const handleDisconnect = () => setSocketConnected(false);

    // Register event handlers
    socketManager.on('gateway_log_init', handleLogInit);
    socketManager.on('gateway_log_line', handleLogLine);
    socketManager.on('gateway_log_lines', handleLogLines);
    socketManager.on('connect', handleConnect);
    socketManager.on('disconnect', handleDisconnect);

    socketManager.emit('join_log_stream', { agent_id: agentId });

    return () => {
      resizeObs.disconnect();
      if (resizeTimer) clearTimeout(resizeTimer);
      socketManager.off('gateway_log_init', handleLogInit);
      socketManager.off('gateway_log_line', handleLogLine);
      socketManager.off('gateway_log_lines', handleLogLines);
      socketManager.off('connect', handleConnect);
      socketManager.off('disconnect', handleDisconnect);
      socketManager.emit('leave_log_stream', { agent_id: agentId });
      term.dispose();
    };
  }, [agentId]);

  return (
    <div className="gw-terminal-outer">
      <div className="gw-term-header">
        <div className="gw-term-status">
          <span className={socketConnected ? 'gw-live-dot connected' : 'gw-live-dot disconnected'}>
            {socketConnected ? '● Live' : '● Reconnecting...'}
          </span>
        </div>

        <button
          className={`gw-term-btn gw-scroll-btn${isScrollLocked ? ' active' : ''}`}
          onClick={toggleScrollLock}
          title={isScrollLocked ? 'Resume auto-scroll' : 'Pause auto-scroll'}
        >
          {isScrollLocked ? '⏸ LOCK' : '📍 LIVE'}
        </button>

        <button
          className="gw-term-btn gw-sync-btn"
          onClick={forceSync}
          title={isStreaming ? 'Log stream is active' : 'Re-fetch last 100 lines from server'}
        >
          {isStreaming ? '📡 STREAMING' : '🔄 SYNC'}
        </button>
      </div>

      <div ref={xtermRef} className="gw-xterm-mount" />
    </div>
  );
};

export default LogViewerTerminal;
