// pages/BroadcastMonitorPage.tsx — Fullscreen broadcast history viewer for big screens
import { useState, useEffect, useCallback } from 'react';
import { Clock, RefreshCw, Monitor, ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import '../styles/broadcast-monitor.css';

interface HistoryFile {
  name: string;
  modified: string;
  size: number;
}

export default function BroadcastMonitorPage() {
  const [historyFiles, setHistoryFiles] = useState<HistoryFile[]>([]);
  const [selectedLog, setSelectedLog] = useState('');
  const [historyLog, setHistoryLog] = useState('');
  const [loading, setLoading] = useState(true);
  const [logLoading, setLogLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [engineId] = useState('full-pipeline');

  const fetchHistoryFiles = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/schedule/history/${engineId}`, { headers });
      const data = await res.json();
      if (data.success) {
        // Sort by name descending (newest first)
        const sorted = [...(data.files || [])].sort((a: HistoryFile, b: HistoryFile) =>
          b.name.localeCompare(a.name)
        );
        setHistoryFiles(sorted);
        setLastUpdated(new Date());
        // Auto-select first (newest) if none selected
        if (!selectedLog && sorted.length > 0) {
          setSelectedLog(sorted[0].name);
        }
      }
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  }, [engineId, selectedLog]);

  const fetchHistoryLog = useCallback(async (logName: string) => {
    setLogLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/schedule/history/${engineId}/${logName}`, { headers });
      const data = await res.json();
      if (data.success) {
        setHistoryLog(data.content || data.log || '');
      } else {
        setHistoryLog('Error loading log: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      setHistoryLog('Error loading log: ' + String(err));
    } finally {
      setLogLoading(false);
    }
  }, [engineId]);

  // Initial load
  useEffect(() => {
    fetchHistoryFiles();
  }, []);

  // Auto-refresh every 30s
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchHistoryFiles, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchHistoryFiles]);

  // Load log when selection changes
  useEffect(() => {
    if (selectedLog) {
      fetchHistoryLog(selectedLog);
    }
  }, [selectedLog, fetchHistoryLog]);

  const navigateLog = (direction: 'prev' | 'next') => {
    const idx = historyFiles.findIndex(f => f.name === selectedLog);
    if (idx === -1) return;
    if (direction === 'prev' && idx < historyFiles.length - 1) {
      setSelectedLog(historyFiles[idx + 1].name);
    } else if (direction === 'next' && idx > 0) {
      setSelectedLog(historyFiles[idx - 1].name);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes > 1024) return `${Math.round(bytes / 1024)}KB`;
    return `${bytes}B`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  // Parse log into sections for better display
  const parseLogSections = (log: string) => {
    const lines = log.split('\n');
    const sections: { time?: string; platform?: string; content: string; type: 'info' | 'success' | 'error' | 'post' }[] = [];
    let currentSection: typeof sections[0] | null = null;

    for (const line of lines) {
      const timeMatch = line.match(/^\[?(\d{2}:\d{2}:\d{2})\]?/);
      const platformMatch = line.match(/^\[?(facebook|twitter|instagram|youtube|thread|tiktok)]/i);
      const errorMatch = line.match(/error|fail|exception/i);
      const successMatch = line.match(/success|posted|published|complete|✅|✔/i);

      if (timeMatch || platformMatch) {
        if (currentSection) sections.push(currentSection);
        currentSection = {
          time: timeMatch ? timeMatch[1] : undefined,
          platform: platformMatch ? platformMatch[1] : undefined,
          content: line,
          type: errorMatch ? 'error' : successMatch ? 'success' : platformMatch ? 'post' : 'info'
        };
      } else {
        if (currentSection) {
          currentSection.content += '\n' + line;
          if (errorMatch) currentSection.type = 'error';
          else if (successMatch && currentSection.type !== 'error') currentSection.type = 'success';
        } else {
          currentSection = { content: line, type: errorMatch ? 'error' : 'info' };
        }
      }
    }
    if (currentSection) sections.push(currentSection);
    return sections;
  };

  const sections = parseLogSections(historyLog);

  return (
    <div className="broadcast-monitor">
      {/* Header */}
      <div className="bm-header">
        <div className="bm-title">
          <Monitor size={28} />
          <span>Broadcast Monitor</span>
        </div>
        <div className="bm-controls">
          {lastUpdated && (
            <span className="bm-updated">
              <Clock size={14} />
              Last updated: {formatTime(lastUpdated)}
            </span>
          )}
          <button
            className={`bm-btn ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title="Auto-refresh every 30s"
          >
            <RefreshCw size={16} className={autoRefresh ? 'spinning' : ''} />
            Auto
          </button>
          <button className="bm-btn" onClick={fetchHistoryFiles} title="Refresh list">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="bm-body">
        {/* File List Sidebar */}
        <div className="bm-sidebar">
          <div className="bm-sidebar-header">
            <FileText size={16} />
            <span>Run Logs ({historyFiles.length})</span>
          </div>
          <div className="bm-file-list">
            {loading ? (
              <div className="bm-loading">Loading...</div>
            ) : historyFiles.length === 0 ? (
              <div className="bm-empty">No runs yet</div>
            ) : (
              historyFiles.map((f) => (
                <div
                  key={f.name}
                  className={`bm-file-item ${selectedLog === f.name ? 'selected' : ''}`}
                  onClick={() => setSelectedLog(f.name)}
                >
                  <div className="bm-file-name">{f.name}</div>
                  <div className="bm-file-meta">
                    {f.modified} · {formatSize(f.size)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Log Viewer */}
        <div className="bm-log-area">
          {selectedLog && (
            <div className="bm-log-nav">
              <button
                className="bm-nav-btn"
                onClick={() => navigateLog('prev')}
                disabled={historyFiles.findIndex(f => f.name === selectedLog) >= historyFiles.length - 1}
              >
                <ChevronLeft size={20} />
                Newer
              </button>
              <span className="bm-log-name">{selectedLog}</span>
              <button
                className="bm-nav-btn"
                onClick={() => navigateLog('next')}
                disabled={historyFiles.findIndex(f => f.name === selectedLog) === 0}
              >
                Older
                <ChevronRight size={20} />
              </button>
            </div>
          )}

          <div className="bm-log-content">
            {logLoading ? (
              <div className="bm-loading-large">
                <RefreshCw size={32} className="spinning" />
                <span>Loading log...</span>
              </div>
            ) : !selectedLog ? (
              <div className="bm-placeholder">
                <Monitor size={64} style={{ opacity: 0.2 }} />
                <p>Select a run log from the sidebar to view its content</p>
              </div>
            ) : (
              <div className="bm-sections">
                {sections.map((section, i) => (
                  <div key={i} className={`bm-section bm-section-${section.type}`}>
                    {section.time && (
                      <span className="bm-section-time">{section.time}</span>
                    )}
                    {section.platform && (
                      <span className={`bm-section-platform bm-platform-${section.platform.toLowerCase()}`}>
                        {section.platform}
                      </span>
                    )}
                    <pre className="bm-section-content">{section.content}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
