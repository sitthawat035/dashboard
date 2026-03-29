// src/components/TerminalModule.tsx
import React, { useEffect, useRef, useCallback, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import type { TermSession } from '../types';

interface TerminalModuleProps {
  termSessions: Record<string, TermSession>;
  activeTermSid: string | null;
  setActiveTermSid: (sid: string) => void;
  onKillTerm: (sid: string) => void;
  onNewSession: () => void;
  onTermSend: () => void;
  cmdHistory?: string[];
  onHistoryUp?: () => string | null;
  onHistoryDown?: () => string | null;
  onPushHistory?: (cmd: string) => void;
}

const TerminalModule: React.FC<TerminalModuleProps> = ({
  termSessions,
  activeTermSid,
  setActiveTermSid,
  onKillTerm,
  onNewSession,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onTermSend: _onTermSend,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  cmdHistory: _cmdHistory = [],
  onHistoryUp,
  onHistoryDown,
  onPushHistory,
}) => {
  const xtermRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const cmdBufRef = useRef('');
  const histIdxRef = useRef(-1);
  const cursorPosRef = useRef(0);
  const [theme, setTheme] = useState<'dark' | 'matrix' | 'ocean'>('dark');
  const prevSidRef = useRef<string | null>(null);
  const pollCountRef = useRef(0);

  const THEMES = {
    dark: { background: '#010409', foreground: '#e6edf3', cursor: '#58a6ff', selectionBackground: '#264f78' },
    matrix: { background: '#0a0a0a', foreground: '#00ff41', cursor: '#00ff41', selectionBackground: '#003b00' },
    ocean: { background: '#0d1b2a', foreground: '#a8dadc', cursor: '#457b9d', selectionBackground: '#1d3557' },
  };

  const PROMPT = 'PS> ';

  // ── Write output from backend to xterm ──
  const writeOutput = useCallback((lines: string[]) => {
    const term = termRef.current;
    if (!term || lines.length === 0) return;
    // Clear current input line before writing output
    term.write('\r\x1b[K');
    lines.forEach((l, i) => {
      term.write(l);
      if (i < lines.length - 1) term.write('\r\n');
    });
    // If last line doesn't end with newline, add one
    const lastLine = lines[lines.length - 1];
    if (lastLine && !lastLine.endsWith('\n')) {
      term.write('\r\n');
    }
    // Re-show prompt with any buffered input
    term.write(PROMPT + cmdBufRef.current);
  }, []);

  // ── Show prompt ──
  const showPrompt = useCallback(() => {
    const term = termRef.current;
    if (!term) return;
    term.write('\r\x1b[K' + PROMPT + cmdBufRef.current);
  }, []);

  // ── Send command via xterm ──
  const sendCmdViaXterm = useCallback(async (cmd: string) => {
    if (!activeTermSid || !cmd.trim()) return;
    const term = termRef.current;
    // Echo command to terminal
    term?.write('\r\n');
    // Send to backend
    try {
      await fetch(`/api/terminal/${activeTermSid}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: cmd.trim() }),
      });
    } catch {}
    // Push to history
    onPushHistory?.(cmd.trim());
    histIdxRef.current = -1;
    cmdBufRef.current = '';
    cursorPosRef.current = 0;
  }, [activeTermSid, onPushHistory]);

  // ── Clear screen ──
  const clearScreen = useCallback(() => {
    const term = termRef.current;
    if (!term) return;
    term.clear();
    cmdBufRef.current = '';
    cursorPosRef.current = 0;
    showPrompt();
  }, [showPrompt]);

  // ── Copy output ──
  const copyOutput = useCallback(() => {
    const term = termRef.current;
    if (!term) return;
    // Get visible buffer content
    const buffer = term.buffer.active;
    let text = '';
    for (let i = 0; i < buffer.length; i++) {
      text += buffer.getLine(i)?.translateToString(true) + '\n';
    }
    navigator.clipboard.writeText(text.trim()).catch(() => {});
  }, []);

  // ── Quick command ──
  const quickCmd = useCallback((cmd: string) => {
    cmdBufRef.current = cmd;
    cursorPosRef.current = cmd.length;
    const term = termRef.current;
    term?.write('\r\x1b[K' + PROMPT + cmd);
    sendCmdViaXterm(cmd);
  }, [sendCmdViaXterm]);

  // ── Init xterm.js ──
  useEffect(() => {
    if (!xtermRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
      theme: THEMES[theme],
      scrollback: 5000,
      allowTransparency: true,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(xtermRef.current);

    // Delay fit to let DOM settle
    const fitTimer = setTimeout(() => {
      try { fitAddon.fit(); } catch {}
    }, 100);

    const resizeObs = new ResizeObserver(() => {
      try { fitAddon.fit(); } catch {}
    });
    resizeObs.observe(xtermRef.current);

    termRef.current = term;
    fitRef.current = fitAddon;

    // ── Keyboard handler (Mobile-friendly via onData) ──
    const { dispose: keyDispose } = term.onData((data) => {
      // Enter
      if (data === '\r') {
        sendCmdViaXterm(cmdBufRef.current);
        return;
      }

      // Backspace (127 or 8)
      if (data === '\x7F' || data === '\b') {
        if (cursorPosRef.current > 0) {
          const buf = cmdBufRef.current;
          cmdBufRef.current = buf.slice(0, cursorPosRef.current - 1) + buf.slice(cursorPosRef.current);
          cursorPosRef.current--;
          term.write('\r\x1b[K' + PROMPT + cmdBufRef.current);
          const moveBack = cmdBufRef.current.length - cursorPosRef.current;
          if (moveBack > 0) term.write('\b'.repeat(moveBack));
        }
        return;
      }

      // Arrow Up
      if (data === '\x1b[A') {
        if (onHistoryUp) {
          const cmd = onHistoryUp();
          if (cmd !== null) {
            cmdBufRef.current = cmd;
            cursorPosRef.current = cmd.length;
            term.write('\r\x1b[K' + PROMPT + cmd);
          }
        }
        return;
      }

      // Arrow Down
      if (data === '\x1b[B') {
        if (onHistoryDown) {
          const cmd = onHistoryDown();
          cmdBufRef.current = cmd ?? '';
          cursorPosRef.current = cmdBufRef.current.length;
          term.write('\r\x1b[K' + PROMPT + cmdBufRef.current);
        }
        return;
      }

      // Arrow Right
      if (data === '\x1b[C') {
        if (cursorPosRef.current < cmdBufRef.current.length) {
          cursorPosRef.current++;
          term.write('\x1b[C');
        }
        return;
      }

      // Arrow Left
      if (data === '\x1b[D') {
        if (cursorPosRef.current > 0) {
          cursorPosRef.current--;
          term.write('\x1b[D');
        }
        return;
      }

      // Ctrl+C (Interrupt)
      if (data === '\x03') {
        term.write('^C\r\n');
        cmdBufRef.current = '';
        cursorPosRef.current = 0;
        showPrompt();
        return;
      }

      // Ctrl+L (Clear screen)
      if (data === '\x0C') {
        clearScreen();
        return;
      }

      // Home
      if (data === '\x1b[H' || data === '\x1b[1~') {
        const move = cursorPosRef.current;
        cursorPosRef.current = 0;
        if (move > 0) term.write(`\x1b[${move}D`);
        return;
      }

      // End
      if (data === '\x1b[F' || data === '\x1b[4~') {
        const move = cmdBufRef.current.length - cursorPosRef.current;
        cursorPosRef.current = cmdBufRef.current.length;
        if (move > 0) term.write(`\x1b[${move}C`);
        return;
      }

      // Any other printable character
      if (data >= String.fromCharCode(32) && data !== '\x7F') {
        const buf = cmdBufRef.current;
        cmdBufRef.current = buf.slice(0, cursorPosRef.current) + data + buf.slice(cursorPosRef.current);
        cursorPosRef.current += data.length;
        const rest = cmdBufRef.current.slice(cursorPosRef.current);
        term.write(data + rest + '\b'.repeat(rest.length));
        return;
      }
    });

    // Welcome message
    term.writeln('\x1b[36m╔══════════════════════════════════════════════╗\x1b[0m');
    term.writeln('\x1b[36m║\x1b[0m  \x1b[1;33m⚡ JOEPV PowerShell Terminal v2.0\x1b[0m          \x1b[36m║\x1b[0m');
    term.writeln('\x1b[36m║\x1b[0m  \x1b[90mPowered by xterm.js\x1b[0m                       \x1b[36m║\x1b[0m');
    term.writeln('\x1b[36m╚══════════════════════════════════════════════╝\x1b[0m');
    term.writeln('');
    term.write(PROMPT);

    return () => {
      clearTimeout(fitTimer);
      resizeObs.disconnect();
      keyDispose();
      term.dispose();
      termRef.current = null;
      fitRef.current = null;
    };
  }, [theme]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Handle session switch ──
  useEffect(() => {
    if (activeTermSid !== prevSidRef.current) {
      prevSidRef.current = activeTermSid;
      cmdBufRef.current = '';
      cursorPosRef.current = 0;
      histIdxRef.current = -1;
      pollCountRef.current = 0;
      if (termRef.current && activeTermSid) {
        termRef.current.clear();
        termRef.current.write(PROMPT);
      }
    }
  }, [activeTermSid]);

  // ── Fit on tab/session change ──
  useEffect(() => {
    const timer = setTimeout(() => {
      try { fitRef.current?.fit(); } catch {}
    }, 200);
    return () => clearTimeout(timer);
  }, [activeTermSid, Object.keys(termSessions).length]);

  // ── Public method: write output from polling ──
  useEffect(() => {
    // This effect is called when termSessions changes (polling updates lineCount)
    // We expose writeOutput via a ref so App.tsx can call it
    (window as any).__termWriteOutput = writeOutput;
    (window as any).__termShowPrompt = showPrompt;
    return () => {
      delete (window as any).__termWriteOutput;
      delete (window as any).__termShowPrompt;
    };
  }, [writeOutput, showPrompt]);

  return (
    <div className="terminal-v2 animate-fade">
      {/* ── Top Bar (outside flex flow, absolute positioned) ── */}
      <div className="t2-topbar">
        <div className="t2-tab-list">
          {Object.values(termSessions).map((s) => (
            <div
              key={s.id}
              className={`t2-tab ${activeTermSid === s.id ? 'active' : ''}`}
              onClick={() => setActiveTermSid(s.id)}
            >
              <span className="t2-tab-dot" />
              <span className="t2-tab-label">PS {s.id.substring(0, 6)}</span>
              <button
                className="t2-tab-close"
                onClick={(e) => { e.stopPropagation(); onKillTerm(s.id); }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
        <button className="t2-btn-new" onClick={onNewSession}>
          + New Session
        </button>
      </div>

      {/* ── Toolbar ── */}
      <div className="t2-toolbar">
        <div className="t2-quick-cmds">
          <button className="t2-qcmd" onClick={() => quickCmd('cls')} title="Clear screen">cls</button>
          <button className="t2-qcmd" onClick={() => quickCmd('dir')} title="List files">dir</button>
          <button className="t2-qcmd" onClick={() => quickCmd('ls')} title="List files (short)">ls</button>
          <button className="t2-qcmd" onClick={() => quickCmd('cd ..')} title="Go up">cd ..</button>
          <button className="t2-qcmd" onClick={() => quickCmd('pwd')} title="Print working dir">pwd</button>
          <button className="t2-qcmd" onClick={() => quickCmd('Get-Process | Select -First 10')} title="Top processes">procs</button>
        </div>
        <div className="t2-toolbar-right">
          <div className="t2-theme-switcher">
            {(['dark', 'matrix', 'ocean'] as const).map((t) => (
              <button
                key={t}
                className={`t2-theme-btn ${theme === t ? 'active' : ''}`}
                onClick={() => setTheme(t)}
                title={t.charAt(0).toUpperCase() + t.slice(1)}
              >
                {t === 'dark' ? '🌙' : t === 'matrix' ? '💚' : '🌊'}
              </button>
            ))}
          </div>
          <button className="t2-action-btn" onClick={copyOutput} title="Copy output">📋</button>
          <button className="t2-action-btn" onClick={clearScreen} title="Clear (Ctrl+L)">🧹</button>
        </div>
      </div>

      {/* ── Terminal Body ── */}
      <div className="t2-body">
        {Object.keys(termSessions).length === 0 ? (
          <div className="t2-empty">
            <div className="t2-empty-icon">💻</div>
            <h3>No Active Sessions</h3>
            <p>Create a new PowerShell terminal to get started.</p>
            <button className="t2-btn-launch" onClick={onNewSession}>
              ⚡ Launch Terminal
            </button>
            <div className="t2-shortcuts-hint">
              <span>↑↓ History</span>
              <span>Ctrl+C Cancel</span>
              <span>Ctrl+L Clear</span>
            </div>
          </div>
        ) : (
          <div
            ref={xtermRef}
            className="t2-xterm-wrap"
            style={{ display: activeTermSid ? 'block' : 'none' }}
          />
        )}
      </div>

      {/* ── Status Bar ── */}
      <div className="t2-statusbar">
        <span className="t2-status-left">
          {activeTermSid ? (
            <>
              <span className="t2-status-dot online" />
              <span>Session {activeTermSid.substring(0, 8)}</span>
              <span className="t2-status-sep">|</span>
              <span>PowerShell</span>
            </>
          ) : (
            <>
              <span className="t2-status-dot offline" />
              <span>Disconnected</span>
            </>
          )}
        </span>
        <span className="t2-status-right">
          <span className="t2-status-hint">↑↓ History</span>
          <span className="t2-status-sep">|</span>
          <span className="t2-status-hint">Ctrl+C Interrupt</span>
          <span className="t2-status-sep">|</span>
          <span className="t2-status-hint">Ctrl+L Clear</span>
        </span>
      </div>
    </div>
  );
};

export default TerminalModule;
