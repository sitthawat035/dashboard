// components/AppRouter.tsx — Application router for different tabs
import { useAppStore } from '../stores/useAppStore';
import Dashboard from '../pages/DashboardPage';
import MissionControl from '../pages/MissionControlPage';
import AgentPage from '../pages/AgentPage';
import CLIProviders from './CLIProviders';
import EngineHub from '../pages/EngineHubPage';
import HermesPage from '../pages/HermesPage';
import ReportsPage from '../pages/ReportsPage';
import SocialHubPage from '../pages/SocialHubPage';
import BroadcastMonitorPage from '../pages/BroadcastMonitorPage';
import CLIHelperPage from '../pages/CLIHelperPage';

interface AppRouterProps {
  // CLI Providers props
  cliScanState: 'idle' | 'scanning' | 'done';
  detectedProviders: any[];
  onExecuteCliScan: () => void;
}

export default function AppRouter({
  cliScanState, detectedProviders, onExecuteCliScan,
}: AppRouterProps) {
  const activeTab = useAppStore(s => s.activeTab);
  const agents = useAppStore(s => s.agents);

  return (
    <section className="view-port">
      {activeTab === 'dashboard' && <Dashboard />}
      {activeTab === 'mission' && <MissionControl agents={agents} />}
      {activeTab === 'agents' && <AgentPage />}
      {activeTab === 'settings' && (
        <CLIProviders
          cliScanState={cliScanState}
          detectedProviders={detectedProviders}
          onExecuteCliScan={onExecuteCliScan}
        />
      )}
      {activeTab === 'multi' && <EngineHub />}
      {activeTab === 'hermes' && <HermesPage />}
      {activeTab === 'reports' && <ReportsPage />}
      {activeTab === 'social' && <SocialHubPage />}
      {activeTab === 'broadcast-monitor' && <BroadcastMonitorPage />}
      {activeTab === 'cli-helper' && <CLIHelperPage />}
      {!['dashboard', 'mission', 'agents', 'settings', 'multi', 'hermes', 'reports', 'social', 'broadcast-monitor', 'cli-helper'].includes(activeTab) && (
        <div className="empty-state">
          <h3>Tab not found</h3>
          <p>The requested view "{activeTab}" is not available. Try selecting a different tab.</p>
        </div>
      )}
    </section>
  );
}
