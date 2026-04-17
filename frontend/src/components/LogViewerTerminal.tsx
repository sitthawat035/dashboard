import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import socketManager from '../utils/socket';
import 'xterm/css/xterm.css';

interface LogViewerTerminalProps {
  agentId: string;
}

/**
 * Unescape JSON-escaped ANSI sequences (e.g. \u001b → actual ESC byte).
 * xterm.js needs real escape codes, not JSON-stringified versions.
 */
function unescapeAnsi(str: string): string {
  // Handle double-escaped JSON sequences
  return str
    .replace(/\\\\u001b/g, '\u001b')  // \\u001b → ESC
    .replace(/\\u001b/g, '\u001b')    // \u001b → ESC
    .replace(/\\\\x1b/g, '\x1b')      // \\x1b → ESC
    .replace(/\\x1b/g, '\x1b');       // \x1b → ESC
}

const LogViewerTerminal: React.FC<LogViewerTerminalProps> = ({ agentId }) => {
  const xtermRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);

  // ── Use REFs for flags that must not trigger re-render ──────────────
  // If these were useState, any change would re-run useEffect → dispose terminal → wipe logs
  const isScrollLockedRef = useRef(false);
  const hasInitializedRef = useRef(false);

  // Only UI-visible state (safe to be useState — not in useEffect deps)
  const [isScrollLocked, setIsScrollLocked] = useState(false);
  const [socketConnected, setSocketConnected] = useState(socketManager.isConnected());
  const [isStreaming, setIsStreaming] = useState(false);

  const toggleScrollLock = () => {
    const next = !isScrollLockedRef.current;
    isScrollLockedRef.current = next;
    setIsScrollLocked(next);
  };

  const forceSync = () => {
    if (termRef.current) {
      termRef.current.clear();
      termRef.current.writeln('\x1b[1;33m🔄 Syncing logs from server...\x1b[0m');
    }
    // Reset ref (NOT setState) — avoids triggering useEffect re-run
    hasInitializedRef.current = false;
    setIsStreaming(false);
    socketManager.emit('leave_log_stream', { agent_id: agentId });
    setTimeout(() => {
      socketManager.emit('join_log_stream', { agent_id: agentId });
    }, 150);
  };

  // ── Terminal lifecycle — ONLY depends on agentId ────────────────────
  // Removing isScrollLocked / hasInitialized from deps was the critical fix.
  // Previously those state changes caused: dispose terminal → re-create → wipe all logs.
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
        green: '#00ff41', // Matrix/Vibrant Green
        yellow: '#ffcc00',
        blue: '#3b82f6',
        magenta: '#ff00ff',
        cyan: '#00fbff', // Neon Cyan
        white: '#f8fafc',
        brightBlack: '#4b5563',
        brightRed: '#ff6b6b',
        brightGreen: '#39ff14', // Neon Green
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

    // ── Socket event handlers ─────────────────────────────────────────
    const handleLogInit = (data: { agent_id: string; lines: string[] }) => {
      if (data.agent_id !== agentId || !termRef.current) return;
      // If live stream is already flowing, skip — don't wipe active content
      if (hasInitializedRef.current) return;

      console.log('[LogViewer] handleLogInit received:', {
        agent_id: data.agent_id,
        lineCount: data.lines?.length || 0,
        firstLine: data.lines?.[0]?.substring(0, 200),
      });

      termRef.current.clear();
      if (data.lines && data.lines.length > 0) {
        data.lines.forEach((line) => {
          const cleaned = unescapeAnsi(line);
          console.log('[LogViewer] Raw line:', line.substring(0, 100));
          console.log('[LogViewer] Cleaned line:', cleaned.substring(0, 100));
          termRef.current!.writeln(cleaned);
        });
      } else {
        termRef.current.writeln('\x1b[2mWaiting for gateway output...\x1b[0m');
      }
      console.log('[LogViewer] Streaming started for', agentId);
      hasInitializedRef.current = true;
      setIsStreaming(true); // Mark streaming as active
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
  }, [agentId]); // ← CRITICAL: only agentId, never scroll/init state

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
