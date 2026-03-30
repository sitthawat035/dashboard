// src/components/MissionControl.tsx
import React, { useState, useEffect, useRef } from 'react';
import type { Agent } from '../types';
import { GW_KEYS, GW_INFO } from '../constants';

interface MissionControlProps {
  agents: Record<string, Agent>;
}

interface AgentNode {
  id: string;
  name: string;
  emoji: string;
  status: 'online' | 'offline' | 'busy' | 'idle';
  platform: 'openclaw' | 'whatsapp';
  currentTask?: string;
  taskProgress?: number;
  x: number;
  y: number;
  connections: string[];
  stats: {
    tasksCompleted: number;
    messagesHandled: number;
    uptimeMinutes: number;
  };
}

interface Task {
  id: string;
  agentId: string;
  title: string;
  status: 'running' | 'waiting' | 'complete' | 'error';
  progress: number;
  startedAt: string;
}

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  message: string;
  timestamp: string;
  agentId?: string;
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

const MissionControl: React.FC<MissionControlProps> = ({ agents }) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([
    { id: '1', name: 'First Contact', emoji: '🥇', description: 'Connect to first agent', unlocked: true },
    { id: '2', name: 'Squad Goals', emoji: '🥈', description: 'Have 3 agents online', unlocked: false, progress: 0, target: 3 },
    { id: '3', name: 'WhatsApp Warrior', emoji: '🥉', description: 'J1 handles 100 messages', unlocked: false, progress: 0, target: 100 },
    { id: '4', name: 'Full House', emoji: '🏅', description: 'All agents online simultaneously', unlocked: false },
    { id: '5', name: 'Zero Hour', emoji: '💎', description: '24h with no errors', unlocked: false },
  ]);

  // Build agent nodes from real data
  const agentNodes: AgentNode[] = [
    ...GW_KEYS.map((gw, i) => {
      const info = GW_INFO[gw];
      const agent = agents[gw];
      const online = agent?.online || false;
      const angle = (i / GW_KEYS.length) * Math.PI * 2 - Math.PI / 2;
      const radius = 140;
      const node: AgentNode = {
        id: gw,
        name: info.name,
        emoji: info.emoji,
        status: online ? 'online' : 'offline',
        platform: 'openclaw',
        x: 200 + Math.cos(angle) * radius,
        y: 180 + Math.sin(angle) * radius,
        connections: GW_KEYS.filter(g => g !== gw && agents[g]?.online),
        stats: {
          tasksCompleted: Math.floor(Math.random() * 50),
          messagesHandled: Math.floor(Math.random() * 200),
          uptimeMinutes: online ? Math.floor(Math.random() * 300) : 0,
        },
      };
      return node;
    }),
    // J1 WhatsApp agent
    ({
      id: 'j1',
      name: 'J1',
      emoji: '📱',
      status: 'online',
      platform: 'whatsapp',
      currentTask: 'Managing WhatsApp community',
      x: 200,
      y: 180,
      connections: ['pudding', 'alpha'],
      stats: {
        tasksCompleted: 0,
        messagesHandled: Math.floor(Math.random() * 500),
        uptimeMinutes: Math.floor(Math.random() * 600),
      },
    } as AgentNode),
  ];

  // Generate mock tasks
  const tasks: Task[] = agentNodes
    .filter(n => n.status === 'online')
    .map((n, i) => ({
      id: `task-${i}`,
      agentId: n.id,
      title: n.platform === 'whatsapp' ? 'Replying to community...' : 'Processing task...',
      status: (['running', 'waiting', 'complete'] as const)[i % 3],
      progress: Math.floor(Math.random() * 100),
      startedAt: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    }));

  // Stats
  const onlineCount = agentNodes.filter(n => n.status !== 'offline').length;
  const totalTasks = tasks.filter(t => t.status === 'running').length;
  const totalMessages = agentNodes.reduce((sum, n) => sum + n.stats.messagesHandled, 0);

  // Update achievements
  useEffect(() => {
    setAchievements(prev => prev.map(a => {
      if (a.id === '2') return { ...a, progress: onlineCount, unlocked: onlineCount >= 3 };
      if (a.id === '4') return { ...a, unlocked: onlineCount >= agentNodes.length };
      return a;
    }));
  }, [onlineCount]);

  // Auto-clear old alerts
  useEffect(() => {
    const timer = setInterval(() => {
      setAlerts(prev => prev.filter(a => {
        const age = Date.now() - new Date(`2026-01-01 ${a.timestamp}`).getTime();
        return age < 30000 || a.type === 'error';
      }));
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mission-control animate-fade">
      {/* Header Stats */}
      <div className="mc-stats-bar">
        <div className="mc-stat glass">
          <div className="mc-stat-icon">🤖</div>
          <div className="mc-stat-info">
            <div className="mc-stat-value">{onlineCount}</div>
            <div className="mc-stat-label">Agents Online</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <div className="mc-stat-icon">⚡</div>
          <div className="mc-stat-info">
            <div className="mc-stat-value">{totalTasks}</div>
            <div className="mc-stat-label">Tasks Running</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <div className="mc-stat-icon">💬</div>
          <div className="mc-stat-info">
            <div className="mc-stat-value">{totalMessages}</div>
            <div className="mc-stat-label">Messages Handled</div>
          </div>
        </div>
        <div className="mc-stat glass">
          <div className="mc-stat-icon">🏆</div>
          <div className="mc-stat-info">
            <div className="mc-stat-value">{achievements.filter(a => a.unlocked).length}/{achievements.length}</div>
            <div className="mc-stat-label">Achievements</div>
          </div>
        </div>
      </div>

      <div className="mc-main-grid">
        {/* Agent Map */}
        <div className="mc-map-panel glass">
          <div className="mc-panel-hdr">
            <span>🗺️ AGENT MAP</span>
            <span className="mc-live-badge">● LIVE</span>
          </div>
          <div className="mc-map" ref={canvasRef}>
            {/* Connection lines (SVG) */}
            <svg className="mc-connections" viewBox="0 0 400 360">
              {agentNodes.flatMap(node =>
                node.connections
                  .filter(targetId => agentNodes.find(n => n.id === targetId)?.status !== 'offline')
                  .map(targetId => {
                    const target = agentNodes.find(n => n.id === targetId);
                    if (!target) return null;
                    return (
                      <line
                        key={`${node.id}-${targetId}`}
                        x1={node.x}
                        y1={node.y}
                        x2={target.x}
                        y2={target.y}
                        className="mc-connection-line"
                      />
                    );
                  })
              )}
            </svg>

            {/* Agent nodes */}
            {agentNodes.map(node => (
              <div
                key={node.id}
                className={`mc-node mc-node-${node.status} ${node.platform === 'whatsapp' ? 'mc-node-whatsapp' : ''} ${selectedAgent === node.id ? 'selected' : ''}`}
                style={{ left: node.x - 24, top: node.y - 24 }}
                onClick={() => setSelectedAgent(selectedAgent === node.id ? null : node.id)}
                title={`${node.name} - ${node.status}`}
              >
                <span className="mc-node-emoji">{node.emoji}</span>
                <span className="mc-node-name">{node.name}</span>
                {node.status === 'online' && <span className="mc-pulse" />}
                {node.platform === 'whatsapp' && <span className="mc-whatsapp-badge">WA</span>}
              </div>
            ))}

            {/* Center label */}
            <div className="mc-map-center">
              <span className="mc-center-icon">🦀</span>
              <span className="mc-center-label">HUB</span>
            </div>
          </div>
        </div>

        {/* Right Panel: Tasks + Alerts + Achievements */}
        <div className="mc-side-panels">
          {/* Task Queue */}
          <div className="mc-task-panel glass">
            <div className="mc-panel-hdr">📋 TASK QUEUE</div>
            <div className="mc-task-list">
              {tasks.map(task => {
                const agent = agentNodes.find(n => n.id === task.agentId);
                return (
                  <div key={task.id} className={`mc-task mc-task-${task.status}`}>
                    <div className="mc-task-header">
                      <span className="mc-task-agent">{agent?.emoji} {agent?.name}</span>
                      <span className={`mc-task-status mc-status-${task.status}`}>
                        {task.status === 'running' ? '⚡' : task.status === 'complete' ? '✅' : task.status === 'error' ? '❌' : '⏳'}
                        {task.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="mc-task-title">{task.title}</div>
                    {task.status === 'running' && (
                      <div className="mc-progress-bar">
                        <div className="mc-progress-fill" style={{ width: `${task.progress}%` }} />
                        <span className="mc-progress-text">{task.progress}%</span>
                      </div>
                    )}
                  </div>
                );
              })}
              {tasks.length === 0 && (
                <div className="mc-empty">No active tasks. Agents are resting 😴</div>
              )}
            </div>
          </div>

          {/* Alerts */}
          <div className="mc-alert-panel glass">
            <div className="mc-panel-hdr">🔔 ALERTS</div>
            <div className="mc-alert-list">
              {alerts.length === 0 ? (
                <div className="mc-empty">All quiet. No alerts! 🎉</div>
              ) : (
                alerts.map(alert => (
                  <div key={alert.id} className={`mc-alert mc-alert-${alert.type}`}>
                    <span className="mc-alert-icon">
                      {alert.type === 'error' ? '🚨' : alert.type === 'warning' ? '⚠️' : alert.type === 'success' ? '✅' : 'ℹ️'}
                    </span>
                    <span className="mc-alert-msg">{alert.message}</span>
                    <span className="mc-alert-time">{alert.timestamp}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Achievements */}
          <div className="mc-achievement-panel glass">
            <div className="mc-panel-hdr">🏆 ACHIEVEMENTS</div>
            <div className="mc-achievement-list">
              {achievements.map(ach => (
                <div key={ach.id} className={`mc-achievement ${ach.unlocked ? 'unlocked' : 'locked'}`}>
                  <span className="mc-ach-emoji">{ach.unlocked ? ach.emoji : '🔒'}</span>
                  <div className="mc-ach-info">
                    <div className="mc-ach-name">{ach.name}</div>
                    <div className="mc-ach-desc">{ach.description}</div>
                    {!ach.unlocked && ach.target && (
                      <div className="mc-ach-progress">
                        <div className="mc-ach-progress-bar">
                          <div className="mc-ach-progress-fill" style={{ width: `${((ach.progress || 0) / ach.target) * 100}%` }} />
                        </div>
                        <span className="mc-ach-progress-text">{ach.progress || 0}/{ach.target}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Agent Detail */}
      {selectedAgent && (() => {
        const node = agentNodes.find(n => n.id === selectedAgent);
        if (!node) return null;
        return (
          <div className="mc-agent-detail glass">
            <div className="mc-detail-hdr">
              <span className="mc-detail-emoji">{node.emoji}</span>
              <div className="mc-detail-info">
                <h3>{node.name}</h3>
                <span className={`mc-detail-status mc-status-${node.status}`}>{node.status.toUpperCase()}</span>
                <span className="mc-detail-platform">{node.platform === 'whatsapp' ? '📱 WhatsApp' : '🦀 OpenClaw'}</span>
              </div>
              <button className="mc-close-btn" onClick={() => setSelectedAgent(null)}>✕</button>
            </div>
            <div className="mc-detail-stats">
              <div className="mc-detail-stat">
                <span className="mc-detail-stat-val">{node.stats.tasksCompleted}</span>
                <span className="mc-detail-stat-label">Tasks Done</span>
              </div>
              <div className="mc-detail-stat">
                <span className="mc-detail-stat-val">{node.stats.messagesHandled}</span>
                <span className="mc-detail-stat-label">Messages</span>
              </div>
              <div className="mc-detail-stat">
                <span className="mc-detail-stat-val">{node.stats.uptimeMinutes}m</span>
                <span className="mc-detail-stat-label">Uptime</span>
              </div>
              <div className="mc-detail-stat">
                <span className="mc-detail-stat-val">{node.connections.length}</span>
                <span className="mc-detail-stat-label">Connections</span>
              </div>
            </div>
            {node.currentTask && (
              <div className="mc-detail-task">
                <span className="mc-detail-task-label">Current Task:</span>
                <span className="mc-detail-task-value">{node.currentTask}</span>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
};

export default MissionControl;
