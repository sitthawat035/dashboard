// pages/DashboardPage.tsx — Now uses Zustand store (reduced from 9 props → 0)
import React from 'react';

import { gatewayApi } from '../utils/api';
import { useAppStore } from '../stores/useAppStore';

const Dashboard: React.FC = () => {
  const agents = useAppStore(s => s.agents);

  const setSelectedAgent = useAppStore(s => s.setSelectedAgent);
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const startAll = useAppStore(s => s.startAll);
  const restartAll = useAppStore(s => s.restartAll);
  const loadStatus = useAppStore(s => s.loadStatus);

  const agentKeys = Object.keys(agents);
  const agentList = Object.values(agents).sort((a, b) => a.id.localeCompare(b.id));
  const activeCount = Object.values(agents).filter((a: any) => a.online).length;

  const stopAll = async () => {
    for (const gw of agentKeys) {
      await gatewayApi.stop(gw);
    }
    setTimeout(loadStatus, 2000);
  };

  return (
    <div className="scroll">
      <div className="stats-grid">
        <div className="stat-card glass">
          <div className="stat-label">Active Agents</div>
          <div className="stat-value">{activeCount}/{agentList.length}</div>
          <div className="stat-sub">{activeCount === agentList.length ? 'All systems operational' : `${agentList.length - activeCount} agents offline`}</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-label">Fleet Status</div>
          <div className="stat-value">{activeCount > 0 ? 'ACTIVE' : 'IDLE'}</div>
        </div>
      </div>

      <div className="fleet-actions" style={{ display: 'flex', gap: '10px', marginBottom: '20px'}}>
        <button className="btn-solid btn-green" onClick={startAll}>▶ START ALL</button>
        <button className="btn-solid btn-danger" onClick={stopAll}>■ STOP ALL</button>
        <button className="btn-solid" onClick={restartAll}>🔄 RESTART ALL</button>
      </div>

      <div className="agents-grid">
        {agentList.map(agent => {
          const online = agent.online || false;
          return (
            <div key={agent.id} className="agent-mini-item glass"
              style={{ borderLeftColor: agent.color || 'var(--primary)' }}
              onClick={() => { setSelectedAgent(agent.id); setActiveTab('agents'); }}
            >
              <div className="agi-top">
                <span className="agi-emoji">{agent.emoji}</span>
                <span className="agi-name">{agent.name}</span>
                <span className={`status-dot ${online ? 'online' : 'offline'}`} />
              </div>
              <div className="agi-details">
                <div className="agi-row"><span className="agi-label">Port</span><span className="agi-val">{agent.port}</span></div>
                <div className="agi-row"><span className="agi-label">Status</span><span className={`agi-val ${online ? 'text-green' : 'text-red'}`}>{online ? 'Online' : 'Offline'}</span></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
