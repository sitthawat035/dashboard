import { useState, useEffect, useCallback } from 'react';
import type { Agent } from '../types';
import { GW_KEYS, GW_INFO } from '../constants';

interface MissionControlProps {
  agents: Record<string, Agent>;
}

interface AgentNode {
  id: string;
  name: string;
  emoji: string;
  status: 'online' | 'offline' | 'busy';
  platform: 'openclaw' | 'whatsapp';
  currentTask?: string;
  x: number;
  y: number;
  connections: string[];
  stats: { tasksCompleted: number; messagesHandled: number; uptimeMinutes: number };
}

interface Task {
  id: string;
  agentId: string;
  title: string;
  status: 'running' | 'complete' | 'error';
  progress: number;
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

const MissionControl = ({ agents }: MissionControlProps) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [subagentData, setSubagentData] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const r = await fetch('/api/subagents/stream');
      if (r.ok) {
        const d = await r.json();
        setSubagentData(d.subagents || []);
      }
    } catch {}
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const agentNodes: AgentNode[] = GW_KEYS.map((gw, i) => {
    const info = GW_INFO[gw];
    const agent = agents[gw];
    const online = agent?.online || false;
    const tasks = subagentData.filter((t) => t.agent === gw);
    const hasRunning = tasks.some((t) => t.status === 'running');
    const angle = (i / GW_KEYS.length) * Math.PI * 2 - Math.PI / 2;
    return {
      id: gw,
      name: info.name,
      emoji: info.emoji,
      status: online ? (hasRunning ? 'busy' : 'online') : 'offline',
      platform: 'openclaw',
      currentTask: tasks.find((t) => t.status === 'running')?.task?.substring(0, 40),
      x: 200 + Math.cos(angle) * 140,
      y: 180 + Math.sin(angle) * 140,
      connections: (agent?.subagents || []).map((s) => s.id).filter((c) => GW_KEYS.includes(c)),
      stats: {
        tasksCompleted: tasks.filter((t) => t.status === 'complete').length,
        messagesHandled: tasks.length * 10,
        uptimeMinutes: online ? Math.floor(Math.random() * 300) : 0,
      },
    };
  });

  const j1Node: AgentNode = {
    id: 'j1',
    name: 'J1',
    emoji: '📱',
    status: 'online',
    platform: 'whatsapp',
    currentTask: 'WhatsApp community...',
    x: 200,
    y: 180,
    connections: ['pudding', 'alpha'],
    stats: { tasksCompleted: subagentData.length * 5, messagesHandled: subagentData.length * 50, uptimeMinutes: 120 },
  };

  const allNodes = [...agentNodes, j1Node];
  const tasks: Task[] = subagentData.slice(0, 6).map((t, i) => ({
    id: t.id || `task-${i}`,
    agentId: t.agent || 'unknown',
    title: t.task ? t.task.substring(0, 45) : 'Processing...',
    status: t.status === 'complete' ? 'complete' : t.status === 'error' ? 'error' : 'running',
    progress: t.status === 'complete' ? 100 : t.status === 'running' ? 50 : 0,
  }));

  const onlineCount = allNodes.filter((n) => n.status !== 'offline').length;
  const busyCount = allNodes.filter((n) => n.status === 'busy').length;
  const completedCount = tasks.filter((t) => t.status === 'complete').length;

  const [achievements, setAchievements] = useState<Achievement[]>([
    { id: '1', name: 'First Contact', emoji: '🥇', description: 'Connect to first agent', unlocked: true },
    { id: '2', name: 'Squad Goals', emoji: '🥈', description: 'Have 3 agents online', unlocked: false, progress: 0, target: 3 },
    { id: '3', name: 'WhatsApp Warrior', emoji: '🥉', description: 'J1 handles 100 messages', unlocked: false, progress: 0, target: 100 },
    { id: '4', name: 'Full House', emoji: '🏅', description: 'All agents online', unlocked: false },
    { id: '5', name: 'Zero Hour', emoji: '💎', description: 'No errors', unlocked: false },
  ]);

  useEffect(() => {
    setAchievements((prev) =>
      prev.map((a) => {
        if (a.id === '2') return { ...a, progress: onlineCount, unlocked: onlineCount >= 3 };
        if (a.id === '3') return { ...a, progress: j1Node.stats.messagesHandled, unlocked: j1Node.stats.messagesHandled >= 100 };
        if (a.id === '4') return { ...a, unlocked: onlineCount >= GW_KEYS.length };
        if (a.id === '5') return { ...a, unlocked: !tasks.some((t) => t.status === 'error') };
        return a;
      })
    );
  }, [onlineCount, tasks]);

  const selectedNode = selectedAgent ? allNodes.find((n) => n.id === selectedAgent) : null;

  return (
    <div className="mission-control">
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
            <div className="mc-stat-value">{achievements.filter((a) => a.unlocked).length}/{achievements.length}</div>
            <div className="mc-stat-label">Achievements</div>
          </div>
        </div>
      </div>

      <div className="mc-main-grid">
        <div className="mc-map-panel glass">
          <div className="mc-panel-hdr">
            <span>🗺️ AGENT MAP</span>
            <span className="mc-live-badge">● LIVE</span>
          </div>
          <div className="mc-map">
            <svg className="mc-connections" viewBox="0 0 400 360">
              {allNodes.flatMap((node) =>
                node.connections.map((targetId) => {
                  const target = allNodes.find((n) => n.id === targetId);
                  return target ? <line key={node.id + targetId} x1={node.x} y1={node.y} x2={target.x} y2={target.y} className="mc-connection-line" /> : null;
                })
              )}
            </svg>
            {allNodes.map((node) => (
              <div
                key={node.id}
                className={`mc-node mc-node-${node.status} ${node.platform === 'whatsapp' ? 'mc-node-whatsapp' : ''} ${selectedAgent === node.id ? 'selected' : ''}`}
                style={{ left: node.x - 24, top: node.y - 24 }}
                onClick={() => setSelectedAgent(selectedAgent === node.id ? null : node.id)}
              >
                <span className="mc-node-emoji">{node.emoji}</span>
                <span className="mc-node-name">{node.name}</span>
                {node.status === 'online' && <span className="mc-pulse" />}
                {node.platform === 'whatsapp' && <span className="mc-whatsapp-badge">WA</span>}
              </div>
            ))}
            <div className="mc-map-center">
              <span className="mc-center-icon">🦀</span>
              <span className="mc-center-label">HUB</span>
            </div>
          </div>
        </div>

        <div className="mc-side-panels">
          <div className="mc-task-panel glass">
            <div className="mc-panel-hdr">📋 TASKS</div>
            <div className="mc-task-list">
              {tasks.map((task) => {
                const agent = allNodes.find((n) => n.id === task.agentId);
                return (
                  <div key={task.id} className={`mc-task mc-task-${task.status}`}>
                    <div className="mc-task-header">
                      <span>{agent?.emoji} {agent?.name}</span>
                      <span className={`mc-task-status mc-status-${task.status}`}>
                        {task.status === 'running' ? '⚡' : task.status === 'complete' ? '✅' : '❌'} {task.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="mc-task-title">{task.title}</div>
                    {task.status === 'running' && (
                      <div className="mc-progress-bar">
                        <div className="mc-progress-fill" style={{ width: '50%' }} />
                        <span className="mc-progress-text">50%</span>
                      </div>
                    )}
                  </div>
                );
              })}
              {tasks.length === 0 && <div className="mc-empty">No active tasks</div>}
            </div>
          </div>

          <div className="mc-achievement-panel glass">
            <div className="mc-panel-hdr">🏆 ACHIEVEMENTS</div>
            <div className="mc-achievement-list">
              {achievements.map((ach) => (
                <div key={ach.id} className={`mc-achievement ${ach.unlocked ? 'unlocked' : 'locked'}`}>
                  <span className="mc-ach-emoji">{ach.unlocked ? ach.emoji : '🔒'}</span>
                  <div className="mc-ach-info">
                    <div className="mc-ach-name">{ach.name}</div>
                    <div className="mc-ach-desc">{ach.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {selectedNode && (
        <div className="mc-agent-detail glass">
          <div className="mc-detail-hdr">
            <span className="mc-detail-emoji">{selectedNode.emoji}</span>
            <div className="mc-detail-info">
              <h3>{selectedNode.name}</h3>
              <span className={`mc-detail-status mc-status-${selectedNode.status}`}>{selectedNode.status.toUpperCase()}</span>
              <span className="mc-detail-platform">{selectedNode.platform === 'whatsapp' ? '📱 WhatsApp' : '🦀 OpenClaw'}</span>
            </div>
            <button className="mc-close-btn" onClick={() => setSelectedAgent(null)}>✕</button>
          </div>
          <div className="mc-detail-stats">
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.stats.tasksCompleted}</span>
              <span className="mc-detail-stat-label">Tasks</span>
            </div>
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.stats.messagesHandled}</span>
              <span className="mc-detail-stat-label">Msgs</span>
            </div>
            <div className="mc-detail-stat">
              <span className="mc-detail-stat-val">{selectedNode.stats.uptimeMinutes}m</span>
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
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MissionControl;