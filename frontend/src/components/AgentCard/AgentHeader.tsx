// components/AgentCard/AgentHeader.tsx — Agent identity, model selector, and control buttons
import { ExternalLink } from 'lucide-react';
import { useAgentCard } from '../../contexts/AgentCardContext';

const AgentHeader: React.FC = () => {
  const {
    gw, info, agent, online, allAgents,
    selectedModel, modelSaving, availableModels,
    isStarting,
    onSwitchAgent, changeModel, handleControlClick, onWatchLive,
  } = useAgentCard();

  return (
    <div className="agent-header">
      <div className="agent-switcher-row">
        <select title="Switch agent" className="agent-switcher-dropdown" value={gw} onChange={e => onSwitchAgent?.(e.target.value)} data-testid="agent-switcher">
          {allAgents.map((a) => <option key={a.id} value={a.id}>{a.emoji} {a.name}</option>)}
        </select>
        {agent?.token && (
          <button className="btn-cli-link" data-testid="open-cli-ui"
            onClick={() => window.open(`http://${window.location.hostname}:${info.port}/#token=${agent?.token}`, '_blank', 'noopener,noreferrer')}>
            <ExternalLink size={14} /> Open CLI UI
          </button>
        )}
      </div>

      <div className="agent-title-row">
        <span className="agent-emoji">{info.emoji}</span>
        <div className="agent-name-stack">
          <h3 data-testid="agent-detail-name">{info.name}</h3>
          <span className="agent-port">PORT: {info.port}</span>
        </div>
        <div className={`status-badge ${online ? 'online' : 'offline'}`} data-testid="agent-detail-status">
          {online ? '● ONLINE' : '● OFFLINE'}
        </div>
        {online && (
          <div className="soul-badge animate-fade">
            <span className="soul-tag">SOUL ACTIVE</span>
            <div className="traits-stack">
              <span className="trait">AUTONOMOUS</span>
              <span className="trait">MULTICONTENT</span>
            </div>
          </div>
        )}
      </div>

      <div className="model-selector-row">
        <label className="model-label">Model:</label>
        <select title="Select model" className="model-dropdown" value={selectedModel} onChange={e => changeModel(e.target.value)} disabled={modelSaving}>
          {availableModels.length === 0 && <option value="">No model info</option>}
          {availableModels.map((m: string) => <option key={m} value={m}>{m}</option>)}
        </select>
        {modelSaving && <span className="model-saving">Saving...</span>}
      </div>

      <div className="agent-controls">
        <button
          className={`btn-solid btn-start-ctrl ${online ? 'btn-danger' : isStarting ? 'btn-starting' : 'btn-green'}`}
          onClick={() => handleControlClick(gw, online ? 'stop' : 'start')}
          disabled={isStarting && !online}
          data-testid="agent-control-main"
        >
          {online ? (
            '■ STOP'
          ) : isStarting ? (
            <><span className="gw-spinner" />STARTING...</>
          ) : (
            '▶ START'
          )}
        </button>
        <button className="btn-solid" onClick={() => handleControlClick(gw, 'restart')} data-testid="agent-control-restart">🔄 RESTART</button>
        <button className="btn-solid" onClick={() => onWatchLive(gw)} data-testid="agent-control-watch">📺 WATCH LIVE</button>
      </div>
    </div>
  );
};

export default AgentHeader;
