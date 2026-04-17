// components/AgentCard/ShellAccess.tsx — Shell terminal mini-panel
import type { UseAgentShellReturn } from '../../hooks/useAgentShell';

interface ShellAccessProps {
  agentName: string;
  shell: UseAgentShellReturn;
}

const ShellAccess: React.FC<ShellAccessProps> = ({ agentName, shell }) => {
  const {
    shellSid, shellLines, shellInput, setShellInput,
    shellAlive, shellRef, initShell, sendShellCmd, killShell,
  } = shell;

  return (
    <div className="shell-container">
      <div className="shell-header">
        <span className="shell-status">
          {shellAlive ? <span className="text-green-400">● LIVE</span> : <span className="text-gray-500">○ OFFLINE</span>}
        </span>
        {!shellSid ? (
          <button className="btn-mini btn-start" onClick={initShell}>▶ START SHELL</button>
        ) : (
          <>
            <button className="btn-mini btn-stop" onClick={killShell}>■ KILL</button>
            <button className="btn-mini btn-restart" onClick={() => { killShell(); setTimeout(initShell, 500); }}>🔄 RESTART</button>
          </>
        )}
      </div>
      <div className="shell-viewer" ref={shellRef}>
        {shellLines.map((line, i) => <div key={i} className="shell-line">{line}</div>)}
        {shellLines.length === 0 && !shellAlive && (
          <div className="shell-empty">Press START SHELL to begin a PowerShell session for {agentName}</div>
        )}
      </div>
      <div className="shell-input-row">
        <input value={shellInput} onChange={e => setShellInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') sendShellCmd(); }}
          placeholder="Enter PowerShell command..." disabled={!shellSid || !shellAlive} />
        <button className="btn-send" onClick={sendShellCmd} disabled={!shellInput.trim() || !shellSid || !shellAlive}>SEND</button>
      </div>
    </div>
  );
};

export default ShellAccess;
