// hooks/useAgentShell.ts — Extracted shell session logic from AgentCard
import { useState, useRef, useCallback, useEffect } from 'react';
import { terminalApi } from '../utils/api';

export interface UseAgentShellReturn {
  shellSid: string | null;
  shellLines: string[];
  shellInput: string;
  setShellInput: (val: string) => void;
  shellAlive: boolean;
  shellRef: React.RefObject<HTMLDivElement | null>;
  initShell: () => Promise<void>;
  sendShellCmd: () => Promise<void>;
  killShell: () => Promise<void>;
}

export function useAgentShell(agentId: string): UseAgentShellReturn {
  const [shellSid, setShellSid] = useState<string | null>(null);
  const [shellLines, setShellLines] = useState<string[]>([]);
  const [shellInput, setShellInput] = useState('');
  const [shellAlive, setShellAlive] = useState(false);
  const shellPollerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const shellLineCountRef = useRef(0);
  const shellRef = useRef<HTMLDivElement>(null);

  const startShellPolling = useCallback((sid: string) => {
    if (shellPollerRef.current) clearInterval(shellPollerRef.current);
    shellPollerRef.current = setInterval(async () => {
      try {
        const { ok, data } = await terminalApi.getOutput(sid, shellLineCountRef.current);
        if (ok && data) {
          if (data.lines?.length > 0) {
            shellLineCountRef.current = data.total;
            setShellLines(prev => {
              const n = [...prev, ...data.lines];
              return n.length > 500 ? n.slice(-500) : n;
            });
          }
          setShellAlive(data.alive);
          if (!data.alive && shellPollerRef.current) clearInterval(shellPollerRef.current);
        }
      } catch {}
    }, 500);
  }, []);

  const initShell = useCallback(async () => {
    try {
      const { ok, data } = await terminalApi.create(agentId);
      if (ok && data?.session_id) {
        shellLineCountRef.current = 0;
        setShellSid(data.session_id);
        setShellAlive(data.alive);
        setShellLines([]);
        startShellPolling(data.session_id);
      }
    } catch (e) {
      console.error('Shell init failed:', e);
    }
  }, [agentId, startShellPolling]);

  const killShell = useCallback(async () => {
    if (shellPollerRef.current) {
      clearInterval(shellPollerRef.current);
      shellPollerRef.current = null;
    }
    if (shellSid) {
      try { await terminalApi.kill(shellSid); } catch {}
    }
    shellLineCountRef.current = 0;
    setShellSid(null);
    setShellLines([]);
    setShellAlive(false);
  }, [shellSid]);

  const sendShellCmd = useCallback(async () => {
    if (!shellInput.trim() || !shellSid) return;
    const cmd = shellInput.trim();
    setShellInput('');
    try {
      await terminalApi.send(shellSid, cmd);
    } catch {}
  }, [shellInput, shellSid]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (shellPollerRef.current) clearInterval(shellPollerRef.current);
    };
  }, []);

  // Auto-scroll shell output
  useEffect(() => {
    if (shellRef.current) shellRef.current.scrollTop = shellRef.current.scrollHeight;
  }, [shellLines]);

  return {
    shellSid,
    shellLines,
    shellInput,
    setShellInput,
    shellAlive,
    shellRef,
    initShell,
    sendShellCmd,
    killShell,
  };
}
