// src/components/CLIProviders.tsx
import React from 'react';

interface CLIProvidersProps {
  cliScanState: 'idle' | 'scanning' | 'done';
  detectedProviders: any[];
  onExecuteCliScan: () => void;
}

const CLIProviders: React.FC<CLIProvidersProps> = ({
  cliScanState,
  detectedProviders,
  onExecuteCliScan,
}) => {
  return (
    <div className="scroll animate-fade">
      <div className="panel glass">
        <div className="panel-hdr border-bottom">
          <span className="panel-title">🔑 API PROVIDERS</span>
          <p className="panel-subtitle">Detect and manage OAuth credentials from local CLI tools</p>
        </div>
        <div className="panel-body">
          <div className="scan-section glass dashed">
            <div className="scan-info">
              <h4>&gt;_ CLI OAuth Scan</h4>
              <p>Automatically detect AI tool credentials on this machine</p>
            </div>
            <button 
              className={`btn-premium ${cliScanState === 'scanning' ? 'btn-scanning' : 'btn-primary'}`}
              onClick={onExecuteCliScan} 
              disabled={cliScanState === 'scanning'}
            >
              <span>{cliScanState === 'scanning' ? '🔄' : '🔍'}</span>
              {cliScanState === 'scanning' ? 'Scanning Local System...' : 'Scan CLI OAuth'}
            </button>
          </div>

          <div className="chip-cloud">
            {['Google Cloud', 'GitHub CLI', 'Azure CLI', 'Hugging Face', 'Claude CLI', 'OpenAI CLI', 'Ollama'].map(c => (
              <span key={c} className="chip">{c}</span>
            ))}
          </div>

          <div className="results-list">
            {cliScanState === 'idle' && detectedProviders.length === 0 && (
              <div className="results-empty">Click "Scan CLI OAuth" to begin detection.</div>
            )}
            
            {detectedProviders.map((p, idx) => (
              <div key={idx} className={`result-card glass ${p.status === 'active' || p.status === 'registered' ? 'status-active' : ''}`}>
                <div className="result-left">
                  <span className={`status-dot ${p.status === 'active' || p.status === 'registered' ? 'online' : 'offline'}`} />
                  <div className="result-info">
                    <h4 className="result-name">
                      {p.name}
                      <span className="badge-brand">{p.badge}</span>
                      <span className="badge-status">{p.status}</span>
                    </h4>
                    <div className="result-path">{p.path}</div>
                    <div className="result-model">Default: {p.default_model} {p.models_count > 0 ? `(+${p.models_count} models)` : ''}</div>
                  </div>
                </div>
                {(p.status === 'registered' || p.status === 'active') && (
                  <button className="btn-link" onClick={() => alert('Linking coming soon!')}>+ LINK TO HUB</button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CLIProviders;
