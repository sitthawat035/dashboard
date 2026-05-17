// QuickCommands.tsx — Preset command shortcuts for agent management
// Replaces ShellAccess — provides powerful one-click agent actions
import { useState } from 'react';
import { useAppStore } from '../../stores/useAppStore';
import { gatewayApi } from '../../utils/api';
import { Play, Square, RotateCcw, Zap, FileText, Trash2, RefreshCw, Terminal, HardDrive, Cpu, Activity } from 'lucide-react';

interface QuickCommandsProps {
  agentKey: string;
  agentName: string;
  agentStatus: string;
}

interface PresetCommand {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  variant: 'primary' | 'danger' | 'info' | 'success';
  action: () => void;
  confirm?: string;
  disabled?: boolean;
}

export default function QuickCommands({ agentKey, agentName, agentStatus }: QuickCommandsProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const loadStatus = useAppStore(s => s.loadStatus);

  const isRunning = agentStatus === 'running';

  const runAction = async (cmd: PresetCommand, cmdId: string) => {
    if (cmd.confirm && !window.confirm(cmd.confirm)) return;
    setLoading(cmdId);
    try {
      await cmd.action();
    } finally {
      setTimeout(() => {
        setLoading(null);
        loadStatus();
      }, 2000);
    }
  };

  const commands: PresetCommand[] = [
    {
      id: 'restart',
      label: 'Restart Gateway',
      description: 'Stop then start fresh',
      icon: <RotateCcw size={16} />,
      variant: 'info',
      action: async () => { await gatewayApi.control(agentKey, 'restart'); },
    },
    {
      id: 'refresh',
      label: 'Refresh Status',
      description: 'Poll latest status',
      icon: <RefreshCw size={16} />,
      variant: 'info',
      action: async () => { await loadStatus(); },
    },
    {
      id: 'logs',
      label: 'View Logs',
      description: 'Tail gateway log file',
      icon: <FileText size={16} />,
      variant: 'info',
      action: async () => {
        // Switch to gateway logs tab
        const store = useAppStore.getState();
        store.setStdoutSubTabForAgent(agentKey, 'gateway_logs');
      },
    },
    {
      id: 'health',
      label: 'Health Check',
      description: 'Verify gateway responds',
      icon: <Activity size={16} />,
      variant: 'info',
      action: async () => {
        await gatewayApi.control(agentKey, 'health');
      },
    },
    {
      id: 'chat',
      label: 'Open Chat',
      description: 'Switch to chat panel',
      icon: <Terminal size={16} />,
      variant: 'info',
      action: async () => {
        const store = useAppStore.getState();
        store.setLogTabForAgent(agentKey, 'chat');
      },
    },
    {
      id: 'memory',
      label: 'Check Memory',
      description: 'Memory usage snapshot',
      icon: <HardDrive size={16} />,
      variant: 'info',
      action: async () => {
        await gatewayApi.control(agentKey, 'status');
      },
    },
    {
      id: 'start',
      label: isRunning ? 'Restart Gateway' : 'Start Gateway',
      description: isRunning ? 'Force restart agent' : 'Launch gateway process',
      icon: isRunning ? <RotateCcw size={16} /> : <Play size={16} />,
      variant: isRunning ? 'danger' : 'success',
      action: async () => {
        if (isRunning) {
          await gatewayApi.control(agentKey, 'restart');
        } else {
          await gatewayApi.control(agentKey, 'start');
        }
      },
      confirm: isRunning ? 'Restart this gateway?' : undefined,
    },
    {
      id: 'stop',
      label: 'Stop Gateway',
      description: 'Kill gateway process',
      icon: <Square size={16} />,
      variant: 'danger',
      action: async () => { await gatewayApi.control(agentKey, 'stop'); },
      confirm: 'Stop this gateway? This will terminate all active sessions.',
      disabled: !isRunning,
    },
  ];

  return (
    <div className="quick-commands">
      <div className="qc-header">
        <div className="qc-agent-info">
          <Cpu size={16} />
          <span className="qc-agent-name">{agentName}</span>
          <span className={`qc-status-badge ${agentStatus}`}>{agentStatus}</span>
        </div>
      </div>

      <div className="qc-grid">
        {commands.map(cmd => (
          <button
            key={cmd.id}
            className={`qc-btn qc-${cmd.variant}`}
            onClick={() => runAction(cmd, cmd.id)}
            disabled={loading !== null || cmd.disabled}
          >
            <div className="qc-btn-icon">{cmd.icon}</div>
            <div className="qc-btn-info">
              <span className="qc-btn-label">{cmd.label}</span>
              <span className="qc-btn-desc">{cmd.description}</span>
            </div>
            {loading === cmd.id && <RefreshCw size={14} className="qc-spinner" />}
          </button>
        ))}
      </div>
    </div>
  );
}
