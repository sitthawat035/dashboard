// components/AppRouter.tsx — Application router for different tabs
import { useAppStore } from '../stores/useAppStore';
import Dashboard from '../pages/DashboardPage';
import MissionControl from '../pages/MissionControlPage';
import AgentPage from '../pages/AgentPage';
import TerminalModule from './TerminalModule';
import CLIProviders from './CLIProviders';
import EngineHub from '../pages/EngineHubPage';
import HermesPage from '../pages/HermesPage';

interface AppRouterProps {
  // Terminal props
  termSessions: any;
  activeTermSid: string | null;
  setActiveTermSid: (sid: string | null) => void;
  onKillTerm: (sid: string) => void;
  onNewSession: () => void;
  onTermSend: () => void;
  cmdHistory: string[];
  onHistoryUp: () => string | null;
  onHistoryDown: () => string | null;
  onPushHistory: (cmd: string) => void;

  // CLI Providers props
  cliScanState: 'idle' | 'scanning' | 'done';
  detectedProviders: any[];
  onExecuteCliScan: () => void;
}

export default function AppRouter({
  termSessions, activeTermSid, setActiveTermSid,
  onKillTerm, onNewSession, onTermSend,
  cmdHistory, onHistoryUp, onHistoryDown, onPushHistory,
  cliScanState, detectedProviders, onExecuteCliScan,
}: AppRouterProps) {
  const activeTab = useAppStore(s => s.activeTab);
  const agents = useAppStore(s => s.agents);

  return (
    <section className="view-port">
      {activeTab === 'dashboard' && <Dashboard />}
      {activeTab === 'mission' && <MissionControl agents={agents} />}
      {activeTab === 'agents' && <AgentPage />}

      {activeTab === 'terminal' && (
        <TerminalModule
          termSessions={termSessions}
          activeTermSid={activeTermSid}
          setActiveTermSid={setActiveTermSid}
          onKillTerm={onKillTerm}
          onNewSession={onNewSession}
          onTermSend={onTermSend}
          cmdHistory={cmdHistory}
          onHistoryUp={onHistoryUp}
          onHistoryDown={onHistoryDown}
          onPushHistory={onPushHistory}
        />
      )}

      {activeTab === 'settings' && (
        <CLIProviders
          cliScanState={cliScanState}
          detectedProviders={detectedProviders}
          onExecuteCliScan={onExecuteCliScan}
        />
      )}

      {activeTab === 'multi' && <EngineHub />}
      {activeTab === 'hermes' && <HermesPage />}
    </section>
  );
}
