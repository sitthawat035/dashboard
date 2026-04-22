// components/AppHeader.tsx — Application header with title and actions
import { Maximize, Minimize } from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

interface AppHeaderProps {
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}

const PAGE_TITLES: Record<string, string> = {
  dashboard: 'Dashboard Overview',
  mission: '🎮 Mission Control',
  agents: 'Agent Manager',
  terminal: 'PowerShell Console',
  settings: 'CLI OAuth Providers',
  memory: 'Knowledge Base',
  logs: 'System Logs',
  multi: 'Engine Operations Center',
};

export default function AppHeader({ isFullscreen, onToggleFullscreen }: AppHeaderProps) {
  const activeTab = useAppStore(s => s.activeTab);
  const socketConnected = useAppStore(s => s.socketConnected);
  const socketReconnecting = useAppStore(s => s.socketReconnecting);

  return (
    <header className="main-header">
      <h2>{PAGE_TITLES[activeTab] || 'JOEPV Master'}</h2>
      <div className="header-actions">
        <div
          className="connection-status"
          title={socketConnected ? 'Real-time updates active' : socketReconnecting ? 'Reconnecting...' : 'Using polling fallback'}
        >
          <div className={`connection-dot ${socketConnected ? 'connected' : socketReconnecting ? 'reconnecting' : 'disconnected'}`} />
          <span className="connection-text">
            {socketConnected ? 'Live' : socketReconnecting ? 'Reconnecting' : 'Polling'}
          </span>
        </div>
        <button className="btn-header" onClick={onToggleFullscreen} title="Toggle Fullscreen">
          {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
        </button>
      </div>
    </header>
  );
}
