// hooks/useTerminal.ts — Terminal sessions: new, kill, send, command history
import { useState, useRef, useCallback } from 'react';
import type { TermSession } from '../types';
import socketManager from '../utils/socket';
import { terminalApi } from '../utils/api';

const MAX_HISTORY = 100;

export function useTerminal(socketConnected: boolean) {
  const [termSessions, setTermSessions] = useState<Record<string, TermSession>>({});
  const [activeTermSid, setActiveTermSid] = useState<string | null>(null);
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const histIdxRef = useRef(-1);
  const sessionsRef = useRef(termSessions);
  sessionsRef.current = termSessions;

  const pollTerm = useCallback(async (sid: string) => {
    if (socketConnected) return;
    const sess = sessionsRef.current[sid];
    if (!sess) return;
    const { ok, data } = await terminalApi.getOutput(sid, sess.lineCount);
    if (!ok || !data) return;
    if (data.lines?.length > 0) {
      const writeFn = (window as any).__termWriteOutput;
      if (typeof writeFn === 'function') writeFn(data.lines);
      setTermSessions(prev => ({ ...prev, [sid]: { ...prev[sid], lineCount: data.total } }));
    }
  }, [socketConnected]);

  const killTerm = useCallback(async (sid: string) => {
    const sess = sessionsRef.current[sid];
    if (sess?.pollRef) clearInterval(sess.pollRef);
    setTermSessions(prev => { const n = { ...prev }; delete n[sid]; return n; });
    setActiveTermSid(prev => prev === sid ? null : prev);
    socketManager.off(`terminal_output_${sid}`);
    try { await terminalApi.kill(sid); } catch {}
  }, []);

  const newSession = useCallback(async () => {
    const { ok, data } = await terminalApi.create();
    if (!ok || !data) return;
    const sid = data.session_id;
    let pollRef: ReturnType<typeof setInterval> | null = null;
    if (!socketConnected) {
      pollRef = setInterval(() => pollTerm(sid), 400);
    }
    setTermSessions(prev => ({ ...prev, [sid]: { id: sid, lineCount: 0, pollRef } }));
    setActiveTermSid(sid);
    socketManager.emit('terminal_created', { session_id: sid });
  }, [pollTerm, socketConnected]);

  const termSend = useCallback(async () => {
    const inp = document.getElementById('term-cmd-input') as HTMLInputElement;
    const cmd = inp?.value.trim();
    if (!cmd || !activeTermSid) return;
    inp.value = '';
    try { await terminalApi.send(activeTermSid, cmd); } catch {}
  }, [activeTermSid]);

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

  return {
    termSessions,
    activeTermSid,
    setActiveTermSid,
    cmdHistory,
    newSession,
    killTerm,
    termSend,
    pushHistory,
    historyUp,
    historyDown,
  };
}
