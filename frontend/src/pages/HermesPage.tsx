/**
 * HermesPage — Hermes Agent Bridge monitoring & control.
 *
 * Features:
 * - Live gateway status (connected platforms, state)
 * - Start new agent runs with message input
 * - Live streaming of agent responses + tool calls
 * - Run history and management
 */

import { useState, useRef, useEffect } from "react";
import { useHermes } from "../hooks/useHermes";
import type { HermesRunState } from "../hooks/useHermes";

// ─── Status Indicator ────────────────────────────────────────────────────────

function StatusDot({ connected }: { connected: boolean }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 10,
        height: 10,
        borderRadius: "50%",
        backgroundColor: connected ? "#22c55e" : "#ef4444",
        marginRight: 8,
      }}
    />
  );
}

// ─── Run Card ────────────────────────────────────────────────────────────────

function RunCard({
  run,
  isActive,
  onStop,
}: {
  run: HermesRunState;
  isActive: boolean;
  onStop: (id: string) => void;
}) {
  const statusColors: Record<string, string> = {
    running: "#3b82f6",
    completed: "#22c55e",
    failed: "#ef4444",
    stopped: "#f59e0b",
    ended: "#6b7280",
  };

  const elapsed = run.endedAt
    ? ((run.endedAt - run.startedAt) / 1000).toFixed(1)
    : ((Date.now() - run.startedAt) / 1000).toFixed(1);

  return (
    <div
      style={{
        background: "#1e1e2e",
        border: `1px solid ${isActive ? statusColors[run.status] : "#333"}`,
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <div>
          <span
            style={{
              backgroundColor: statusColors[run.status],
              color: "#fff",
              padding: "2px 8px",
              borderRadius: 4,
              fontSize: 12,
              fontWeight: 600,
              textTransform: "uppercase",
              marginRight: 8,
            }}
          >
            {run.status}
          </span>
          <span style={{ color: "#888", fontSize: 13 }}>{elapsed}s</span>
        </div>
        {isActive && (
          <button
            onClick={() => onStop(run.run_id)}
            style={{
              background: "#ef4444",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              padding: "4px 12px",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            ⬛ Stop
          </button>
        )}
      </div>

      {/* Run ID */}
      <div style={{ color: "#888", fontSize: 11, marginBottom: 8 }}>
        {run.run_id}
      </div>

      {/* Messages (live stream) */}
      {run.messages && (
        <div
          style={{
            background: "#111",
            borderRadius: 6,
            padding: 12,
            maxHeight: 400,
            overflowY: "auto",
            fontFamily: "monospace",
            fontSize: 13,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            color: "#e0e0e0",
            marginBottom: 12,
          }}
        >
          {run.messages}
        </div>
      )}

      {/* Tool calls */}
      {run.tools.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ color: "#888", fontSize: 12, marginBottom: 4 }}>
            🔧 Tools ({run.tools.length})
          </div>
          {run.tools.map((tool, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "4px 0",
                fontSize: 12,
                color: tool.error ? "#ef4444" : "#a0a0a0",
              }}
            >
              <span>
                {tool.endedAt ? "✅" : "⏳"} {tool.name}
              </span>
              {tool.endedAt && (
                <span style={{ color: "#666" }}>
                  {((tool.endedAt - tool.startedAt) / 1000).toFixed(1)}s
                </span>
              )}
              {tool.error && (
                <span style={{ color: "#ef4444", fontSize: 11 }}>
                  Error: {tool.error}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function HermesPage() {
  const {
    status,
    activeRuns,
    completedRuns,
    logs,
    isConnected,
    startRun,
    stopRun,
    refreshStatus,
    clearLogs,
  } = useHermes();

  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeRuns.length, logs.length]);

  const handleSend = async () => {
    if (!message.trim() || sending) return;
    setSending(true);
    const result = await startRun(message.trim());
    if (result) {
      setMessage("");
    }
    setSending(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        padding: 24,
        maxWidth: 900,
        margin: "0 auto",
        color: "#e0e0e0",
      }}
    >
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>
        🤖 Hermes Agent Bridge
      </h1>
      <p style={{ color: "#888", marginBottom: 24 }}>
        Live streaming from Hermes Agent via SSE → Socket.IO
      </p>

      {/* Gateway Status */}
      <div
        style={{
          background: "#1e1e2e",
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
          border: "1px solid #333",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <StatusDot connected={isConnected} />
            <span style={{ fontWeight: 600 }}>
              {isConnected ? "Hermes Online" : "Hermes Offline"}
            </span>
            {status?.gateway_state && (
              <span style={{ color: "#888", marginLeft: 12, fontSize: 13 }}>
                State: {status.gateway_state}
              </span>
            )}
            {status?.pid && (
              <span style={{ color: "#666", marginLeft: 12, fontSize: 12 }}>
                PID: {status.pid}
              </span>
            )}
          </div>
          <button
            onClick={refreshStatus}
            style={{
              background: "#333",
              color: "#ccc",
              border: "none",
              borderRadius: 4,
              padding: "4px 12px",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            ↻ Refresh
          </button>
        </div>

        {/* Connected Platforms */}
        {status?.platforms && Object.keys(status.platforms).length > 0 && (
          <div style={{ marginTop: 12 }}>
            <span style={{ color: "#888", fontSize: 12 }}>Platforms: </span>
            {Object.entries(status.platforms).map(([name, online]) => (
              <span
                key={name}
                style={{
                  display: "inline-block",
                  backgroundColor: online ? "#166534" : "#451a1a",
                  color: online ? "#86efac" : "#fca5a5",
                  padding: "2px 8px",
                  borderRadius: 4,
                  fontSize: 11,
                  marginRight: 6,
                }}
              >
                {name} {online ? "✓" : "✗"}
              </span>
            ))}
          </div>
        )}

        {!isConnected && (
          <div
            style={{
              marginTop: 12,
              color: "#f59e0b",
              fontSize: 13,
              background: "#2a2010",
              padding: "8px 12px",
              borderRadius: 4,
            }}
          >
            ⚠️ Hermes API ไม่ได้เปิดอยู่ที่ port 8642 — รัน{" "}
            <code style={{ color: "#fbbf24" }}>hermes gateway run</code>{" "}
            หรือ{" "}
            <code style={{ color: "#fbbf24" }}>
              hermes dashboard
            </code>{" "}
            ก่อน
          </div>
        )}
      </div>

      {/* Message Input */}
      <div
        style={{
          background: "#1e1e2e",
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
          border: "1px solid #333",
        }}
      >
        <div style={{ color: "#888", fontSize: 13, marginBottom: 8 }}>
          💬 ส่ง task ให้ Alpha (Hermes Agent)
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="พิมพ์ task ที่ต้องการให้ Alpha ทำ..."
            disabled={!isConnected}
            style={{
              flex: 1,
              background: "#111",
              color: "#e0e0e0",
              border: "1px solid #444",
              borderRadius: 6,
              padding: "8px 12px",
              fontSize: 14,
              resize: "vertical",
              minHeight: 44,
              maxHeight: 120,
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={handleSend}
            disabled={!isConnected || !message.trim() || sending}
            style={{
              background: isConnected && message.trim() ? "#3b82f6" : "#333",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              padding: "8px 20px",
              cursor:
                isConnected && message.trim() ? "pointer" : "not-allowed",
              fontSize: 14,
              fontWeight: 600,
              alignSelf: "flex-end",
            }}
          >
            {sending ? "⏳" : "▶"} ส่ง
          </button>
        </div>
      </div>

      {/* Active Runs */}
      {activeRuns.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>
            ⚡ Active Runs ({activeRuns.length})
          </h2>
          {activeRuns.map((run) => (
            <RunCard
              key={run.run_id}
              run={run}
              isActive={true}
              onStop={stopRun}
            />
          ))}
        </div>
      )}

      {/* Completed Runs */}
      {completedRuns.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>
            📋 Completed Runs ({completedRuns.length})
          </h2>
          {completedRuns.map((run) => (
            <RunCard
              key={run.run_id}
              run={run}
              isActive={false}
              onStop={stopRun}
            />
          ))}
        </div>
      )}

      {/* Live Log Feed */}
      {logs.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 12,
            }}
          >
            <h2 style={{ fontSize: 18 }}>📜 Live Log Feed</h2>
            <button
              onClick={clearLogs}
              style={{
                background: "#333",
                color: "#ccc",
                border: "none",
                borderRadius: 4,
                padding: "4px 12px",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              Clear
            </button>
          </div>
          <div
            style={{
              background: "#111",
              borderRadius: 6,
              padding: 12,
              maxHeight: 300,
              overflowY: "auto",
              fontFamily: "monospace",
              fontSize: 12,
              lineHeight: 1.5,
            }}
          >
            {logs.map((log, i) => (
              <div key={i} style={{ marginBottom: 4, color: "#a0a0a0" }}>
                <span style={{ color: "#666" }}>
                  {new Date(log.timestamp * 1000).toLocaleTimeString()}
                </span>{" "}
                <span style={{ color: "#818cf8" }}>[{log.event}]</span>{" "}
                <span>
                  {typeof log.data === "string"
                    ? log.data
                    : JSON.stringify(log.data).substring(0, 200)}
                </span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Empty State */}
      {activeRuns.length === 0 && completedRuns.length === 0 && (
        <div
          style={{
            textAlign: "center",
            color: "#666",
            padding: 40,
            background: "#1a1a2e",
            borderRadius: 8,
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
          <div style={{ fontSize: 16, marginBottom: 8 }}>
            ยังไม่มี run ใดๆ
          </div>
          <div style={{ fontSize: 13 }}>
            {isConnected
              ? "พิมพ์ task ด้านบนเพื่อเริ่มใช้งาน Alpha ผ่าน Hermes"
              : "เชื่อมต่อ Hermes API ก่อนเพื่อเริ่มใช้งาน"}
          </div>
        </div>
      )}
    </div>
  );
}
