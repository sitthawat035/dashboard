// src/components/Dashboard.tsx
import React from 'react';
import type { Agent } from '../types';
import { GW_KEYS, GW_INFO } from '../constants';

interface DashboardProps {
  agents: Record<string, Agent>;
  activeCount: number;
  onControl: (gw: string, action: string) => void;
  onSetSelectedAgent: (gw: string) => void;
  onSetActiveTab: (tab: any) => void;
  onStartAll: () => void;
  onRestartAll: () => void;
  onLoadStatus: () => void;
  onLoadAllLogs: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  agents,
  activeCount,
  onControl,
  onSetSelectedAgent,
  onSetActiveTab,
  onStartAll,
  onRestartAll,
  onLoadStatus,
  onLoadAllLogs,
}) => {
  const stopAll = async () => {
    for (const gw of GW_KEYS) {
      await fetch(`/api/gateway/${gw}/stop`, { method: 'POST' });
    }
    setTimeout(onLoadStatus, 2000);
  };

  return (
    <div className="scroll animate-fade">
      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card glass">
          <div className="stat-label">Total Agents</div>
          <div className="stat-value">{GW_KEYS.length}</div>
          <div className="stat-sub">Ace · Ameri · Fah · Pudding · Alpha</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Active Gateways</div>
          <div className="stat-value">{activeCount}</div>
          <div className="stat-sub">of {GW_KEYS.length} running</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Uptime</div>
          <div className="stat-value">STABLE</div>
          <div className="stat-sub">Hub always active</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Network</div>
          <div className="stat-value">SECURE</div>
          <div className="stat-sub">VPN active</div>
        </div>
      </div>

      {/* Agent Overview */}
      <div className="panel glass">
        <div className="panel-hdr">AGENT OVERVIEW</div>
        <div className="panel-body">
          <div className="mini-agents-grid">
            {GW_KEYS.map(gw => {
              const info = GW_INFO[gw];
              const agent = agents[gw];
              const online = agent?.online || false;
              const modelFull = agent?.primary_model || '-';
              const model = modelFull.includes('/') ? modelFull.split('/').pop()! : modelFull;
              const subagents = agent?.subagents || [];
              return (
                <div key={gw} className={`mini-agent-card glass ${info.cls}`}>
                  <div className="mini-top">
                    <div>
                      <div className="mini-name">{info.emoji} {info.name}</div>
                      <div className="mini-port">PORT: {info.port}</div>
                    </div>
                    <span className={`status-dot ${online ? 'online' : 'offline'}`}></span>
                  </div>
                  <div className="mini-info">
                    <div className="mini-detail">
                      <span className="mini-label">Status</span>
                      <span className={`mini-val ${online ? 'text-green' : 'text-red'}`}>
                        {online ? 'Online' : 'Offline'}
                      </span>
                    </div>
                    <div className="mini-detail">
                      <span className="mini-label">Model</span>
                      <span className="mini-val model-name">{model.length > 22 ? model.substring(0, 22) + '...' : model}</span>
                    </div>
                    {subagents.length > 0 && (
                      <div className="mini-detail mini-subagents-wrap">
                        <span className="mini-label">Subagents ({subagents.length})</span>
                        <div className="mini-subagent-list">
                          {subagents.slice(0, 8).map((sa: any) => (
                            <span key={sa.id} className="mini-subagent-chip">{sa.name || sa.id}</span>
                          ))}
                          {subagents.length > 8 && <span className="mini-subagent-more">+{subagents.length - 8}</span>}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mini-actions">
                    <button className="btn-mini btn-start" onClick={() => onControl(gw, 'start')}>▶ Start</button>
                    <button className="btn-mini btn-stop"  onClick={() => onControl(gw, 'stop')}>■ Stop</button>
                    <button className="btn-mini btn-restart" onClick={() => onControl(gw, 'restart')}>🔄</button>
                    <button className="btn-mini btn-details" onClick={() => { onSetSelectedAgent(gw); onSetActiveTab('agents'); }}>→</button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* System Controls */}
      <div className="panel glass">
        <div className="panel-hdr">SYSTEM CONTROLS</div>
        <div className="panel-body">
          <div className="sys-controls-grid">
            <button className="btn-ctrl btn-sync" onClick={() => { onLoadStatus(); onLoadAllLogs(); }}>
              <span className="btn-ctrl-icon">↺</span>
              <span className="btn-ctrl-label">SYNC STATUS</span>
            </button>
            <button className="btn-ctrl btn-start-all" onClick={onStartAll}>
              <span className="btn-ctrl-icon">🚀</span>
              <span className="btn-ctrl-label">START ALL</span>
            </button>
            <button className="btn-ctrl btn-stop-all" onClick={stopAll}>
              <span className="btn-ctrl-icon">■</span>
              <span className="btn-ctrl-label">STOP ALL</span>
            </button>
            <button className="btn-ctrl btn-restart-all" onClick={onRestartAll}>
              <span className="btn-ctrl-icon">🔄</span>
              <span className="btn-ctrl-label">RESTART ALL</span>
            </button>
            <button className="btn-ctrl btn-terminal" onClick={() => onSetActiveTab('terminal')}>
              <span className="btn-ctrl-icon">💻</span>
              <span className="btn-ctrl-label">TERMINAL</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
