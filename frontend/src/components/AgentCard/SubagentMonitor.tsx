import React, { useState, useRef } from 'react';
import type { SubagentLog } from '../../types';
import ConversationLog from './ConversationLog';

interface SubagentMonitorProps {
  logs: SubagentLog[];
  agentName: string;
  agentId: string;
}

const SubagentMonitor: React.FC<SubagentMonitorProps> = ({ logs, agentName, agentId }) => {
  const [filter, setFilter] = useState<'all' | 'running' | 'complete' | 'error'>('all');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [view, setView] = useState<'sessions' | 'conversation'>('conversation');
  const scrollRef = useRef<HTMLDivElement>(null);

  const filtered = logs.filter(l => filter === 'all' || l.status === filter);
  const counts = {
    all: logs.length,
    running: logs.filter(l => l.status === 'running').length,
    complete: logs.filter(l => l.status === 'complete').length,
    error: logs.filter(l => l.status === 'error').length,
  };

  const toggle = (id: string) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const statusColors: Record<string, string> = {
    running: '#58a6ff',
    complete: '#3fb950',
    error: '#f85149',
  };

  const statusIcons: Record<string, string> = {
    running: '⚡',
    complete: '✅',
    error: '❌',
  };

  return (
    <div className="sa-monitor">
      {/* Top nav: Sessions / Conversation */}
      <div className="sa-view-tabs">
        <button
          className={`sa-view-tab ${view === 'conversation' ? 'active' : ''}`}
          onClick={() => setView('conversation')}
        >
          💬 Conversation Log
        </button>
        <button
          className={`sa-view-tab ${view === 'sessions' ? 'active' : ''}`}
          onClick={() => setView('sessions')}
        >
          🤖 Sessions {counts.all > 0 && <span className="sa-filter-count">{counts.all}</span>}
        </button>
      </div>

      {view === 'conversation' ? (
        <ConversationLog agentId={agentId} agentName={agentName} />
      ) : (
        <>
          {/* Stats bar */}
          <div className="sa-stats-bar">
            <div className="sa-stat">
              <span className="sa-stat-num">{counts.all}</span>
              <span className="sa-stat-label">Total</span>
            </div>
            <div className="sa-stat sa-stat-running">
              <span className="sa-stat-num">{counts.running}</span>
              <span className="sa-stat-label">Running</span>
            </div>
            <div className="sa-stat sa-stat-complete">
              <span className="sa-stat-num">{counts.complete}</span>
              <span className="sa-stat-label">Done</span>
            </div>
            <div className="sa-stat sa-stat-error">
              <span className="sa-stat-num">{counts.error}</span>
              <span className="sa-stat-label">Errors</span>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="sa-filter-bar">
            {(['all', 'running', 'complete', 'error'] as const).map(f => (
              <button
                key={f}
                className={`sa-filter-btn ${filter === f ? 'active' : ''} sa-filter-${f}`}
                onClick={() => setFilter(f)}
              >
                {f === 'all' ? '🌐' : statusIcons[f]} {f.charAt(0).toUpperCase() + f.slice(1)}
                {counts[f] > 0 && <span className="sa-filter-count">{counts[f]}</span>}
              </button>
            ))}
          </div>

          {/* Session list */}
          <div className="sa-session-list" ref={scrollRef}>
            {filtered.length === 0 ? (
              <div className="sa-empty">
                {logs.length === 0 ? (
                  <>
                    <div className="sa-empty-icon">🤖</div>
                    <div className="sa-empty-title">No Embedded Sessions</div>
                    <div className="sa-empty-sub">
                      No [agent/embedded] events found in gateway log.<br />
                      Switch to "Conversation Log" to see agent output.
                    </div>
                  </>
                ) : (
                  <>
                    <div className="sa-empty-icon">🔍</div>
                    <div className="sa-empty-title">No {filter} sessions</div>
                  </>
                )}
              </div>
            ) : (
              filtered.map((log) => {
                const isExpanded = expanded[log.id];
                const color = statusColors[log.status] || '#8b949e';
                const modelShort = log.model
                  ? (log.model.includes('/') ? log.model.split('/').pop()! : log.model)
                  : '';

                return (
                  <div
                    key={log.id}
                    className={`sa-session-card sa-status-${log.status}`}
                    style={{ borderLeftColor: color }}
                    onClick={() => toggle(log.id)}
                  >
                    <div className="sa-session-top">
                      <div className="sa-session-left">
                        {log.status === 'running' && <span className="sa-live-pulse" />}
                        <span className="sa-session-icon">{statusIcons[log.status]}</span>
                        <div className="sa-session-info">
                          <div className="sa-session-name">{log.session_key}</div>
                          <div className="sa-session-time">{log.timestamp}</div>
                        </div>
                      </div>
                      <div className="sa-session-right">
                        {modelShort && (
                          <span className="sa-model-badge">
                            🧠 {modelShort.length > 20 ? modelShort.substring(0, 20) + '…' : modelShort}
                          </span>
                        )}
                        <span className={`sa-status-badge sa-status-${log.status}`}>
                          {log.status.toUpperCase()}
                        </span>
                        <span className="sa-expand-icon">{isExpanded ? '▲' : '▼'}</span>
                      </div>
                    </div>

                    <div className="sa-session-task">
                      📋 {log.task.length > 100 ? log.task.substring(0, 100) + '…' : log.task}
                    </div>

                    {isExpanded && (
                      <div className="sa-session-detail">
                        <div className="sa-detail-row">
                          <span className="sa-d-label">Workspace:</span>
                          <span className="sa-d-val">{log.workspace || 'N/A'}</span>
                        </div>
                        {log.error && (
                          <div className="sa-detail-error">
                            <span className="sa-d-label">Error:</span> {log.error}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default SubagentMonitor;
