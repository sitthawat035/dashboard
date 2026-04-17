// components/AgentCard/GatewayConsole.tsx — Gateway log viewer with offline/starting/failed overlays
import LogViewerTerminal from '../LogViewerTerminal';

interface GatewayConsoleProps {
  gw: string;
  agentName: string;
  online: boolean;
  isStarting: boolean;
  startFailed: boolean;
  onControlClick: (gw: string, action: string) => void;
}

const GatewayConsole: React.FC<GatewayConsoleProps> = ({
  gw, agentName, online, isStarting, startFailed, onControlClick,
}) => {
  return (
    <div className="gw-terminal-container">
      {/* Always render terminal for live logs */}
      <LogViewerTerminal agentId={gw} />
      {/* Offline overlay - shown when gateway is offline and not starting */}
      {!online && !isStarting && !startFailed && (
        <div className="gateway-offline-overlay animate-fade">
          <div className="offline-icon">🔌</div>
          <h4>Gateway Offline</h4>
          <p>Start the {agentName} gateway to see live logs.</p>
          <div className="failed-actions">
            <button className="btn-mini btn-start" style={{ marginTop: '15px' }} onClick={() => onControlClick(gw, 'start')}>
              ▶ START NOW
            </button>
            <button className="btn-mini gw-overlay-sync" style={{ marginTop: '15px' }}
              onClick={() => {
                const t = document.querySelector('.gw-sync-btn') as HTMLButtonElement;
                if (t) t.click();
              }}
              title="Load logs from file even when offline"
            >
              🔄 SYNC LOGS
            </button>
          </div>
        </div>
      )}
      {/* Starting overlay */}
      {isStarting && !online && (
        <div className="gateway-starting-overlay animate-fade">
          <div className="gw-ring-spinner" />
          <h4>Gateway Starting...</h4>
          <p>Launching {agentName} in background. Logs will appear shortly.</p>
          <span className="gw-starting-hint">This may take up to 3 minutes</span>
        </div>
      )}
      {/* Start Failed overlay */}
      {startFailed && !online && !isStarting && (
        <div className="gateway-failed-overlay animate-fade">
          <div className="failed-icon">⚠️</div>
          <h4>Failed to Start</h4>
          <p>Gateway didn't come online. It may already be running, or a config error occurred.</p>
          <div className="failed-actions">
            <button className="btn-mini btn-start" onClick={() => onControlClick(gw, 'start')}>
              ▶ Try Again
            </button>
            <button className="btn-mini btn-restart-ml" onClick={() => onControlClick(gw, 'restart')}>
              🔄 Restart
            </button>
          </div>
          <span className="gw-starting-hint">Check Gateway Logs tab for details</span>
        </div>
      )}
    </div>
  );
};

export default GatewayConsole;
