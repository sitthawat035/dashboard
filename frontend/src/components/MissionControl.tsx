import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';

interface MissionControlProps {
  gatewayStatus?: any;
  agents?: any;
}

// ── API data types ──────────────────────────────────────────────
interface AgentNode {
  id: string;
  name: string;
  emoji: string;
  status: 'online' | 'offline' | 'busy' | 'idle';
  currentTask?: string;
  taskProgress?: number;
  connections: string[];
  stats: {
    tasksCompleted: number;
    errorsToday: number;
    uptimeSeconds: number;
  };
}

interface Task {
  id: string;
  agentId: string;
  title: string;
  status: 'running' | 'waiting' | 'complete' | 'error';
  progress: number;
  startedAt: string;
  error?: string;
}

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  message: string;
  timestamp: string;
  agentId?: string;
  dismissed: boolean;
}

interface Achievement {
  id: string;
  name: string;
  emoji: string;
  description: string;
  unlocked: boolean;
  progress?: number;
  target?: number;
}

// ── Layout constants ────────────────────────────────────────────
// Fixed node positions for the agent map (radial + center hub)
const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  pudding: { x: 200, y: 180 }, // center hub
};

function getPositions(ids: string[]): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = { ...NODE_POSITIONS };
  const rimIds = ids.filter((id) => id !== 'pudding');
  rimIds.forEach((id, i, arr) => {
    const angle = (i / arr.length) * Math.PI * 2 - Math.PI / 2;
    positions[id] = {
      x: 200 + Math.cos(angle) * 140,
      y: 180 + Math.sin(angle) * 140,
    };
  });
  return positions;
}

// ── Helpers ─────────────────────────────────────────────────────
async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function statusColor(status: string): string {
  switch (status) {
    case 'online': return '#00ff88';
    case 'busy': return '#ffaa00';
    case 'idle': return '#00bbff';
    case 'offline':
    default: return '#ff4444';
  }
}

function alertIcon(type: Alert['type']): string {
  switch (type) {
    case 'error': return '🔴';
    case 'warning': return '🟡';
    case 'success': return '🟢';
    case 'info':
    default: return '🔵';
  }
}

// ── Component ───────────────────────────────────────────────────
const MissionControl = ({ gatewayStatus: _gatewayStatus }: MissionControlProps) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const [agents, setAgents] = useState<AgentNode[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Fetch all endpoints ──────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const [agentsData, tasksData, alertsData, achievementsData] = await Promise.all([
        fetchJSON<AgentNode[]>('/api/mission-control/agents'),
        fetchJSON<Task[]>('/api/mission-control/tasks'),
        fetchJSON<Alert[]>('/api/mission-control/alerts'),
        fetchJSON<Achievement[]>('/api/mission-control/achievements'),
      ]);
      setAgents(agentsData);
      setTasks(tasksData);
      setAlerts(alertsData);
      setAchievements(achievementsData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch mission control data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ── Socket.IO real-time updates ─────────────────────────────
  useEffect(() => {
    const socket = io();

    socket.on('agent:status', (data) => {
      setAgents(prev => prev.map(a =>
        a.id === data.agentId ? { ...a, status: data.status } : a
      ));
    });

    socket.on('task:progress', (data) => {
      setTasks(prev => prev.map(t =>
        t.id === data.taskId ? { ...t, progress: data.progress } : t
      ));
    });

    socket.on('task:complete', (data) => {
      setTasks(prev => prev.map(t =>
        t.id === data.taskId ? { ...t, status: 'complete', progress: 100 } : t
      ));
    });

    socket.on('alert:new', (data) => {
      setAlerts(prev => [data, ...prev].slice(0, 50));
    });

    socket.on('achievement:unlock', (data) => {
      setAchievements(prev => prev.map(a =>
        a.id === data.id ? { ...a, unlocked: true } : a
      ));
    });

    return () => { socket.disconnect(); };
  }, []);

  // ── Derived data ─────────────────────────────────────────────
  const agentIds = agents.map((a) => a.id);
  const positions = getPositions(agentIds);

  const onlineCount = agents.filter((n) => n.status !== 'offline').length;
  const busyCount = agents.filter((n) => n.status === 'busy').length;
  const completedCount = tasks.filter((t) => t.status === 'complete').length;
  const unlockedAchievements = achievements.filter((a) => a.unlocked).length;

  const selectedNode = selectedAgent ? agents.find((n) => n.id === selectedAgent) : null;
  const activeAlerts = alerts.filter((a) => !a.dismissed);

  // ── Loading state ────────────────────────────────────────────
  if (loading && agents.length === 0) {
    return (
      <div className="mission-control">
        <div className="mc-loading">
          <span className="mc-loading-icon">⏳</span>
          <span>Loading Mission Control…</span>
        </div>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────
  if (error && agents.length === 0) {
    return (
      <div className="mission-control">
        <div className="mc-error">
          <span className="mc-error-icon">⚠️</span>
          <span>Connection error: {error}</span>
          <button className="mc-retry-btn" onClick={fetchData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="mission-control">
      {/* ── Stats bar ─────────────────────────────────────────── */}
      <div className="mc-stats-bar">
        <div className="mc-stat glass">
          <span className="mc-stat-icon">🤖</span>
          <div>
            <div className="mc-stat-value">{onlineCount}</div>
            <div className="mc-stat-label">Online</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <span className="mc-stat-icon">⚡</span>
          <div>
            <div className="mc-stat-value">{busyCount}</div>
            <div className="mc-stat-label">Busy</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <span className="mc-stat-icon">✅</span>
          <div>
            <div className="mc-stat-value">{completedCount}</div>
            <div className="mc-stat-label">Done</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <span className="mc-stat-icon">🏆</span>
          <div>
            <div className="mc-stat-value">{unlockedAchievements}/{achievements.length || '–'}</div>
            <div className="mc-stat-label">Achievements</div>
          </div>
        </div>
        {/* Error flash indicator */}
        {error && (
          <div className="mc-stat glass mc-stat-warning">
            <span className="mc-stat-icon">⚠️</span>
            <div>
              <div className="mc-stat-value" style={{ fontSize: '0.75rem' }}>Stale data</div>
              <div className="mc-stat-label">{error}</div>
            </div>
          </div>
        )}
      </div>

      {/* ── Main grid ─────────────────────────────────────────── */}
      <div className="mc-main-grid">
        {/* Agent map */}
        <div className="mc-map-panel glass">
          <div className="mc-panel-hdr">
            <span>🗺️ AGENT MAP</span>
            <span className="mc-live-badge">● LIVE</span>
          </div>
          <div className="mc-map">
            <svg className="mc-connections" viewBox="0 0 400 360">
              {agents.flatMap((node) =>
                node.connections.map((targetId) => {
                  const from = positions[node.id];
                  const to = positions[targetId];
                  if (!from || !to) return null;
                  return (
                    <line
                      key={`${node.id}-${targetId}`}
                      x1={from.x}
                      y1={from.y}
                      x2={to.x}
                      y2={to.y}
                      className="mc-connection-line"
                    />
                  );
                })
              )}
            </svg>

            {agents.map((node) => {
              const pos = positions[node.id];
              if (!pos) return null;
              return (
                <div
                  key={node.id}
                  className={`mc-node mc-node-${node.status} ${selectedAgent === node.id ? 'selected' : ''}`}
                  style={{ left: pos.x - 24, top: pos.y - 24 }}
                  onClick={() => setSelectedAgent(selectedAgent === node.id ? null : node.id)}
                >
                  <span className="mc-node-emoji">{node.emoji}</span>
                  <span className="mc-node-name">{node.name}</span>
                  {node.status === 'online' && <span className="mc-pulse" />}
                  <span
                    className="mc-node-indicator"
                    style={{ backgroundColor: statusColor(node.status) }}
                  />
                </div>
              );
            })}

            <div className="mc-map-center">
              <span className="mc-center-icon">🦀</span>
              <span className="mc-center-label">HUB</span>
            </div>
          </div>
        </div>

        {/* Side panels */}
        <div className="mc-side-panels">
          {/* Task queue */}
          <div className="mc-task-panel glass">
            <div className="mc-panel-hdr">📋 TASKS</div>
            <div className="mc-task-list">
              {tasks.slice(0, 6).map((task) => {
                const agent = agents.find((n) => n.id === task.agentId);
                return (
                  <div key={task.id} className={`mc-task mc-task-${task.status}`}>
                    <div className="mc-task-header">
                      <span>{agent?.emoji ?? '🤖'} {agent?.name ?? task.agentId}</span>
                      <span className={`mc-task-status mc-status-${task.status}`}>
                        {task.status === 'running' && '⚡ RUNNING'}
                        {task.status === 'waiting' && '⏳ WAITING'}
                        {task.status === 'complete' && '✅ COMPLETE'}
                        {task.status === 'error' && '❌ ERROR'}
                      </span>
                    </div>
                    <div className="mc-task-title">{task.title}</div>
                    {task.status === 'running' && (
                      <div className="mc-progress-bar">
                        <div className="mc-progress-fill" style={{ width: `${task.progress}%` }} />
                        <span className="mc-progress-text">{task.progress}%</span>
                      </div>
                    )}
                    {task.error && <div className="mc-task-error">{task.error}</div>}
                  </div>
                );
              })}
              {tasks.length === 0 && <div className="mc-empty">No active tasks</div>}
            </div>
          </div>

          {/* Achievements */}
          <div className="mc-achievement-panel glass">
            <div className="mc-panel-hdr">🏆 ACHIEVEMENTS</div>
            <div className="mc-achievement-list">
              {achievements.map((ach) => (
                <div key={ach.id} className={`mc-achievement ${ach.unlocked ? 'unlocked' : 'locked'}`}>
                  <span className="mc-ach-emoji">{ach.unlocked ? ach.emoji : '🔒'}</span>
                  <div className="mc-ach-info">
                    <div className="mc-ach-name">{ach.name}</div>
                    <div className="mc-ach-desc">{ach.description}</div>
                    {!ach.unlocked && ach.progress !== undefined && ach.target !== undefined && (
                      <div className="mc-progress-bar" style={{ marginTop: 4 }}>
                        <div className="mc-progress-fill" style={{ width: `${(ach.progress / ach.target) * 100}%` }} />
                        <span className="mc-progress-text">{ach.progress}/{ach.target}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {achievements.length === 0 && <div className="mc-empty">No achievements loaded</div>}
            </div>
          </div>

          {/* Alerts (new panel) */}
          {activeAlerts.length > 0 && (
            <div className="mc-alert-panel glass">
              <div className="mc-panel-hdr">🔔 ALERTS</div>
              <div className="mc-alert-list">
                {activeAlerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className={`mc-alert mc-alert-${alert.type}`}>
                    <span>{alertIcon(alert.type)}</span>
                    <span className="mc-alert-msg">{alert.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Agent detail popup ─────────────────────────────────── */}
      {selectedNode && (
        <div className="mc-agent-detail glass">
          <div className="mc-detail-hdr">
            <span className="mc-detail-emoji">{selectedNode.emoji}</span>
            <div className="mc-detail-info">
              <h3>{selectedNode.name}</h3>
              <span className={`mc-detail-status mc-status-${selectedNode.status}`}>
                {selectedNode.status.toUpperCase()}
              </span>
            </div>
            <button className="mc-close-btn" onClick={() => setSelectedAgent(null)}>✕</button>
          </div>
          <div className="mc-detail-stats">
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.stats.tasksCompleted}</span>
              <span className="mc-detail-stat-label">Tasks</span>
            </div>
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.stats.errorsToday}</span>
              <span className="mc-detail-stat-label">Errors</span>
            </div>
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{Math.floor(selectedNode.stats.uptimeSeconds / 60)}m</span>
              <span className="mc-detail-stat-label">Uptime</span>
            </div>
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.connections.length}</span>
              <span className="mc-detail-stat-label">Links</span>
            </div>
          </div>
          {selectedNode.currentTask && (
            <div className="mc-detail-task">
              <span className="mc-detail-task-label">Task:</span>
              <span className="mc-detail-task-value">{selectedNode.currentTask}</span>
              {selectedNode.taskProgress !== undefined && (
                <div className="mc-progress-bar" style={{ marginTop: 6 }}>
                  <div className="mc-progress-fill" style={{ width: `${selectedNode.taskProgress}%` }} />
                  <span className="mc-progress-text">{selectedNode.taskProgress}%</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MissionControl;
