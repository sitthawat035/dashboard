// pages/AgentPage.tsx — Now uses Zustand store (reduced from 16 props → 0)
import React from 'react';

import AgentCard from '../components/AgentCard';
import { useAppStore } from '../stores/useAppStore';

const AgentPage: React.FC = () => {
  const agents = useAppStore(s => s.agents);
  const selectedAgent = useAppStore(s => s.selectedAgent);
  const setSelectedAgent = useAppStore(s => s.setSelectedAgent);
  const logData = useAppStore(s => s.logData);
  const logTab = useAppStore(s => s.logTab);
  const setLogTabForAgent = useAppStore(s => s.setLogTabForAgent);
  const stdoutSubTab = useAppStore(s => s.stdoutSubTab);
  const setStdoutSubTabForAgent = useAppStore(s => s.setStdoutSubTabForAgent);
  const control = useAppStore(s => s.control);
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const chatSessions = useAppStore(s => s.chatSessions);
  const setChatMessagesForAgent = useAppStore(s => s.setChatMessagesForAgent);
  const chatInputs = useAppStore(s => s.chatInputs);
  const setChatInputForAgent = useAppStore(s => s.setChatInputForAgent);
  const subagentLogs = useAppStore(s => s.subagentLogs);
  const loadStatus = useAppStore(s => s.loadStatus);

  const agentList = Object.values(agents).sort((a, b) => a.id.localeCompare(b.id));

  const watchGwLog = (_gw: string) => {
    setActiveTab('terminal');
  };

  if (selectedAgent && agents[selectedAgent]) {
    const agent = agents[selectedAgent];
    return (
      <div className="agent-detail-view animate-fade">
        <button className="back-btn" onClick={() => setSelectedAgent(null)}>← BACK TO FLEET</button>
        <AgentCard
          key={selectedAgent}
          gw={selectedAgent}
          info={{
            name: agent.name,
            emoji: agent.emoji,
            port: agent.port,
            cls: agent.id
          }}
          agent={agent}
          logData={logData[selectedAgent] || { log: [], err: [] }}
          curLogTab={logTab[selectedAgent] || 'log'}
          onSwitchTab={tab => {
            setLogTabForAgent(selectedAgent, tab);
            if (tab === 'log' && !stdoutSubTab[selectedAgent]) {
              setStdoutSubTabForAgent(selectedAgent, 'gateway_logs');
            }
          }}
          stdoutSubTab={stdoutSubTab[selectedAgent] || 'gateway_logs'}
          onSwitchStdoutSubTab={tab => setStdoutSubTabForAgent(selectedAgent, tab)}
          onControl={control}
          onWatchLive={watchGwLog}
          onSwitchAgent={setSelectedAgent}
          chatMessages={chatSessions[selectedAgent] || []}
          setChatMessages={(updater: any) => setChatMessagesForAgent(selectedAgent, updater)}
          chatInput={chatInputs[selectedAgent] || ''}
          setChatInput={(val: string) => setChatInputForAgent(selectedAgent, val)}
          subagentLogs={subagentLogs.filter(log => log.agent === selectedAgent)}
          onRefreshStatus={loadStatus}
          allAgents={agentList}
        />
      </div>
    );
  }

  return (
    <div className="agents-grid animate-fade">
      {agentList.map(agent => {
        const gw = agent.id;
        const online = agent.online || false;
        const modelFull = agent.primary_model || '-';
        const model = modelFull.includes('/') ? modelFull.split('/').pop()! : modelFull;
        const subCount = agent.subagents?.length || 0;
        
        return (
          <div 
            key={gw} 
            className="agent-mini-item glass" 
            style={{ borderLeftColor: agent.color || 'var(--primary)' }}
            onClick={() => setSelectedAgent(gw)}
          >
            <div className="agi-top">
              <span className="agi-emoji">{agent.emoji}</span>
              <span className="agi-name">{agent.name}</span>
              <span className={`status-dot ${online ? 'online' : 'offline'}`} />
            </div>
            <div className="agi-details">
              <div className="agi-row"><span className="agi-label">Port</span><span className="agi-val">{agent.port}</span></div>
              <div className="agi-row"><span className="agi-label">Status</span><span className={`agi-val ${online ? 'text-green' : 'text-red'}`}>{online ? 'Online' : 'Offline'}</span></div>
              <div className="agi-row"><span className="agi-label">Model</span><span className="agi-val agi-model">{model.length > 18 ? model.substring(0, 18) + '...' : model}</span></div>
              {subCount > 0 && <div className="agi-row"><span className="agi-label">Subagents</span><span className="agi-val">{subCount}</span></div>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AgentPage;
