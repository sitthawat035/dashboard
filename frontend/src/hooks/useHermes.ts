/**
 * useHermes — React hook for Hermes Agent Bridge Socket.IO events.
 *
 * Subscribes to hermes:* events and provides state + actions for:
 * - Gateway status monitoring
 * - Live agent run streaming (messages, tool calls)
 * - Run management (start, stop, list)
 */

import { useCallback, useEffect, useRef, useState } from "react";
import socketManager from "../utils/socket";
import { hermesApi } from "../utils/api";
import type { HermesStatus, HermesRunInfo } from "../utils/api";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface HermesMessage {
  runId: string;
  delta: string;
  timestamp: number;
}

export interface HermesToolEvent {
  runId: string;
  tool: string;
  preview?: string;
  duration?: number;
  error?: string;
  timestamp: number;
}

export interface HermesRunState {
  run_id: string;
  status: "running" | "completed" | "failed" | "stopped" | "ended";
  messages: string; // accumulated text
  tools: { name: string; startedAt: number; endedAt?: number; error?: string }[];
  startedAt: number;
  endedAt?: number;
}

export interface HermesLogEntry {
  runId: string;
  event: string;
  data: any;
  timestamp: number;
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useHermes() {
  const [status, setStatus] = useState<HermesStatus | null>(null);
  const [runs, setRuns] = useState<Record<string, HermesRunState>>({});
  const [logs, setLogs] = useState<HermesLogEntry[]>([]);
  const [subscribed, setSubscribed] = useState(false);

  // Refs to accumulate text without re-renders per character
  const runsRef = useRef<Record<string, HermesRunState>>({});
  const logsRef = useRef<HermesLogEntry[]>([]);

  // ── Socket.IO Event Handlers ─────────────────────────────────────────────

  useEffect(() => {
    // Subscribe
    socketManager.emit("hermes:join");

    const handleStatus = (data: HermesStatus) => {
      setStatus(data);
    };

    const handleRunStarted = (data: { run_id: string; status: string }) => {
      const runState: HermesRunState = {
        run_id: data.run_id,
        status: "running",
        messages: "",
        tools: [],
        startedAt: Date.now(),
      };
      runsRef.current = { ...runsRef.current, [data.run_id]: runState };
      setRuns({ ...runsRef.current });
      setSubscribed(true);
    };

    const handleMessage = (data: { run_id: string; delta: string }) => {
      const run = runsRef.current[data.run_id];
      if (run) {
        run.messages += data.delta;
        // Batch update every 50ms instead of per-character
        runsRef.current = { ...runsRef.current, [data.run_id]: run };
        setRuns({ ...runsRef.current });
      }
    };

    const handleToolStart = (data: HermesToolEvent) => {
      const run = runsRef.current[data.run_id];
      if (run) {
        run.tools.push({
          name: data.tool,
          startedAt: Date.now(),
        });
        runsRef.current = { ...runsRef.current, [data.run_id]: run };
        setRuns({ ...runsRef.current });
      }
    };

    const handleToolEnd = (data: HermesToolEvent) => {
      const run = runsRef.current[data.run_id];
      if (run) {
        const lastTool = [...run.tools].reverse().find((t) => t.name === data.tool && !t.endedAt);
        if (lastTool) {
          lastTool.endedAt = Date.now();
          if (data.error) lastTool.error = data.error;
        }
        runsRef.current = { ...runsRef.current, [data.run_id]: run };
        setRuns({ ...runsRef.current });
      }
    };

    const handleRunComplete = (data: { run_id: string; output?: string }) => {
      const run = runsRef.current[data.run_id];
      if (run) {
        run.status = "completed";
        run.endedAt = Date.now();
        if (data.output && !run.messages) {
          run.messages = data.output;
        }
        runsRef.current = { ...runsRef.current, [data.run_id]: run };
        setRuns({ ...runsRef.current });
      }
    };

    const handleRunFailed = (data: { run_id: string; error: string }) => {
      const run = runsRef.current[data.run_id];
      if (run) {
        run.status = "failed";
        run.endedAt = Date.now();
        runsRef.current = { ...runsRef.current, [data.run_id]: run };
        setRuns({ ...runsRef.current });
      }
    };

    const handleLog = (data: HermesLogEntry) => {
      logsRef.current = [...logsRef.current.slice(-200), data];
      setLogs([...logsRef.current]);
    };

    // Register listeners
    socketManager.on("hermes:status", handleStatus);
    socketManager.on("hermes:run:started", handleRunStarted);
    socketManager.on("hermes:run:message", handleMessage);
    socketManager.on("hermes:run:tool_start", handleToolStart);
    socketManager.on("hermes:run:tool_end", handleToolEnd);
    socketManager.on("hermes:run:complete", handleRunComplete);
    socketManager.on("hermes:run:failed", handleRunFailed);
    socketManager.on("hermes:run:log", handleLog);

    // Request initial status
    socketManager.emit("hermes:status_request");

    return () => {
      socketManager.off("hermes:status", handleStatus);
      socketManager.off("hermes:run:started", handleRunStarted);
      socketManager.off("hermes:run:message", handleMessage);
      socketManager.off("hermes:run:tool_start", handleToolStart);
      socketManager.off("hermes:run:tool_end", handleToolEnd);
      socketManager.off("hermes:run:complete", handleRunComplete);
      socketManager.off("hermes:run:failed", handleRunFailed);
      socketManager.off("hermes:run:log", handleLog);
    };
  }, []);

  // ── Actions ──────────────────────────────────────────────────────────────

  const startRun = useCallback(async (message: string, model?: string) => {
    try {
      const result = await hermesApi.startRun(message, model);
      return result;
    } catch (err) {
      console.error("[Hermes] Failed to start run:", err);
      return null;
    }
  }, []);

  const stopRun = useCallback(async (runId: string) => {
    try {
      await hermesApi.stopRun(runId);
      const run = runsRef.current[runId];
      if (run) {
        run.status = "stopped";
        run.endedAt = Date.now();
        runsRef.current = { ...runsRef.current, [runId]: run };
        setRuns({ ...runsRef.current });
      }
    } catch (err) {
      console.error("[Hermes] Failed to stop run:", err);
    }
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const s = await hermesApi.getStatus();
      setStatus(s);
    } catch {
      setStatus({ connected: false, error: "unreachable" });
    }
  }, []);

  const clearLogs = useCallback(() => {
    logsRef.current = [];
    setLogs([]);
  }, []);

  // ── Computed ─────────────────────────────────────────────────────────────

  const activeRuns = Object.values(runs).filter((r) => r.status === "running");
  const completedRuns = Object.values(runs).filter(
    (r) => r.status === "completed" || r.status === "failed"
  );
  const isConnected = status?.connected ?? false;

  return {
    status,
    runs,
    activeRuns,
    completedRuns,
    logs,
    isConnected,
    subscribed,
    startRun,
    stopRun,
    refreshStatus,
    clearLogs,
  };
}
