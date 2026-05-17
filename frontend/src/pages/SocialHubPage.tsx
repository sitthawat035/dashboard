// SocialHubPage.tsx — Central Social Media Hub
// All-in-one dashboard for managing social media accounts and posting
import { useState, useEffect } from 'react';
import { Facebook, Twitter, Instagram, Youtube, Globe, MessageCircle, BarChart2, Calendar, Send, CheckCircle, XCircle, ExternalLink, Zap, Sparkles, Clock, Power, History, ChevronDown, ChevronUp } from 'lucide-react';
import FacebookConnectPage from './FacebookConnectPage';
import '../styles/facebook.css';
import '../styles/engine-hub.css';
import '../styles/social-hub.css';

// Platform connection status from API
interface PlatformStatus {
  connected: boolean;
  username?: string;
  page_name?: string;
  obtained_at?: string;
}

const PLATFORM_COLORS: Record<string, string> = {
  facebook: '#1877f2',
  twitter: '#1da1f2',
  instagram: '#e1306c',
  youtube: '#ff0000',
};

const PLATFORM_ICONS: Record<string, React.ReactNode> = {
  facebook: <Facebook size={28} />,
  twitter: <Twitter size={28} />,
  instagram: <Instagram size={28} />,
  youtube: <Youtube size={28} />,
};

const PLATFORM_NAMES: Record<string, string> = {
  facebook: 'Facebook',
  twitter: 'X (Twitter)',
  instagram: 'Instagram',
  youtube: 'YouTube',
};

const PLATFORM_DESCRIPTIONS: Record<string, string> = {
  facebook: 'Post to pages, groups & stories',
  twitter: 'Tweets, threads & live audio',
  instagram: 'Posts, Reels & Stories',
  youtube: 'Videos, Shorts & Community',
};

// Quick action commands
interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  badge?: string;
  action?: () => void;
}

const quickActions: QuickAction[] = [
  {
    id: 'broadcast',
    label: 'Broadcast All',
    icon: <Send size={20} />,
    description: 'Post to all connected platforms',
    badge: 'Multi',
  },
  {
    id: 'schedule',
    label: 'Schedule Post',
    icon: <Calendar size={20} />,
    description: 'Queue content for later',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: <BarChart2 size={20} />,
    description: 'View performance metrics',
  },
  {
    id: 'ai_caption',
    label: 'AI Caption',
    icon: <Zap size={20} />,
    description: 'Generate engaging captions',
    badge: 'New',
  },
];

export default function SocialHubPage() {
  const [platformStatuses, setPlatformStatuses] = useState<Record<string, PlatformStatus>>({
    facebook: { connected: false },
    twitter: { connected: false },
    instagram: { connected: false },
    youtube: { connected: false },
  });
  const [activePlatform, setActivePlatform] = useState<string | null>(null);
  const [broadcastText, setBroadcastText] = useState('');
  const [broadcastResult, setBroadcastResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [broadcastLoading, setBroadcastLoading] = useState(false);
  const [showConnectToast, setShowConnectToast] = useState<string | null>(null);

  // Auto Pilot States
  const [activeJobs, setActiveJobs] = useState<any[]>([]);
  const [newRunTime, setNewRunTime] = useState('08:00');
  const [newNiche, setNewNiche] = useState('tech');
  const [newTone, setNewTone] = useState('professional');
  const [isPilotLoading, setIsPilotLoading] = useState(false);

  // AI Caption state
  const [aiCaption, setAiCaption] = useState('');

  // Post History
  interface PostHistoryItem {
    timestamp: string;
    status: 'success' | 'error';
    topic: string;
    message_preview: string;
    post_id: string;
    error: string;
    image_count: number;
  }
  const [postHistory, setPostHistory] = useState<PostHistoryItem[]>([]);
  const [historyExpanded, setHistoryExpanded] = useState(false);

  // ── Fetch platform statuses on load ──────────────────────────────────────
  useEffect(() => {
    fetchPlatformStatuses();
    fetchScheduleJobs();
    fetchPostHistory();
  }, []);

  const fetchPlatformStatuses = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch Facebook status
      const fbRes = await fetch('/api/facebook/status', { headers });
      if (fbRes.ok) {
        const fbData = await fbRes.json();
        setPlatformStatuses(prev => ({
          ...prev,
          facebook: { connected: fbData.connected, obtained_at: fbData.obtained_at }
        }));
      }
    } catch (err) {
      console.error('Error fetching platform statuses:', err);
    }
  };

  const fetchScheduleJobs = () => {
    const token = localStorage.getItem('token');
    fetch('/api/schedule', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.jobs) {
        const pipelineJobs = data.jobs.filter((j: any) => j.engine_id === 'full-pipeline' && j.active);
        setActiveJobs(pipelineJobs);
      }
    })
    .catch(err => console.error('Error fetching schedule:', err));
  };

  const fetchPostHistory = () => {
    fetch('/api/facebook/pipeline-history?limit=20')
      .then(r => r.json())
      .then(data => { if (data.history) setPostHistory(data.history); })
      .catch(() => {});
  };

  // ── Auto Pilot Functions ──────────────────────────────────────────────────
  const addAutoPilotJob = async () => {
    setIsPilotLoading(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        engine_id: 'full-pipeline',
        time: newRunTime,
        repeat: 'daily',
        options: { niche: newNiche, tone: newTone }
      };
      const res = await fetch('/api/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success && data.job_id) {
        setActiveJobs([...activeJobs, {
          id: data.job_id,
          time: newRunTime,
          options: { niche: newNiche, tone: newTone }
        }]);
        setNewRunTime('08:00');
      } else {
        alert('Failed to add job: ' + (data.error || 'Unknown error'));
      }
    } catch (e) {
      console.error(e);
      alert('Network error');
    }
    setIsPilotLoading(false);
  };

  const removeAutoPilotJob = async (jobId: string) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/schedule/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setActiveJobs(activeJobs.filter(j => j.id !== jobId));
      }
    } catch (e) {
      console.error(e);
    }
  };

  // ── Broadcast Function ────────────────────────────────────────────────────
  const handleBroadcast = async () => {
    if (!broadcastText.trim()) return;
    
    const connectedPlatforms = Object.entries(platformStatuses)
      .filter(([_, status]) => status.connected)
      .map(([id, _]) => id);
    
    if (connectedPlatforms.length === 0) {
      setBroadcastResult({ type: 'error', message: 'No platforms connected. Please connect at least one platform.' });
      setTimeout(() => setBroadcastResult(null), 4000);
      return;
    }

    setBroadcastLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Post to each connected platform
      let successCount = 0;
      let errorMessages: string[] = [];

      if (platformStatuses.facebook?.connected) {
        const res = await fetch('/api/facebook/post', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message: broadcastText })
        });
        if (res.ok) successCount++;
        else errorMessages.push('Facebook');
      }

      // Add Twitter, Instagram, YouTube posting logic here as they get connected
      
      if (successCount > 0) {
        setBroadcastResult({ 
          type: 'success', 
          message: `Posted successfully to ${successCount} platform(s)!` 
        });
        setBroadcastText('');
      } else {
        setBroadcastResult({ 
          type: 'error', 
          message: `Failed to post. ${errorMessages.length > 0 ? 'Failed: ' + errorMessages.join(', ') : ''}` 
        });
      }
    } catch (e) {
      setBroadcastResult({ type: 'error', message: 'Network error. Please try again.' });
    }
    setBroadcastLoading(false);
    setTimeout(() => setBroadcastResult(null), 4000);
  };

  // ── AI Caption Function ───────────────────────────────────────────────────
  const handleAiCaption = async () => {
    if (!broadcastText.trim()) {
      setAiCaption('Please enter some text first for caption enhancement.');
      return;
    }
    
    // Simple AI caption - in production this would call an AI API
    setTimeout(() => {
      const enhancedText = broadcastText + '\n\n✨ #viral #trending #mustsee';
      setAiCaption(enhancedText);
      setBroadcastText(enhancedText);
    }, 500);
  };

  // ── Quick Action Handlers ─────────────────────────────────────────────────
  const handleQuickAction = (actionId: string) => {
    switch (actionId) {
      case 'broadcast':
        handleBroadcast();
        break;
      case 'ai_caption':
        handleAiCaption();
        break;
      case 'schedule':
        // Open broadcast composer with schedule mode
        setBroadcastResult({
          type: 'success',
          message: 'Schedule mode: Set date/time in the composer and click Broadcast to queue.'
        });
        setTimeout(() => setBroadcastResult(null), 4000);
        break;
      case 'analytics':
        // Open analytics panel
        setBroadcastResult({
          type: 'success',
          message: 'Analytics: Connecting to platform APIs to fetch metrics...'
        });
        setTimeout(() => setBroadcastResult(null), 4000);
        break;
    }
  };

  // ── Platform connect/manage handler ──────────────────────────────────────
  const handlePlatformAction = (e: React.MouseEvent, id: string) => {
    // Card has no onClick — button is the ONLY trigger for expanding panels
    if (id === 'facebook') {
      setActivePlatform(prev => prev === 'facebook' ? null : 'facebook');
    } else {
      setShowConnectToast(PLATFORM_NAMES[id]);
      setTimeout(() => setShowConnectToast(null), 3000);
    }
  };

  const connectedCount = Object.values(platformStatuses).filter(p => p.connected).length;
  const successCount = postHistory.filter(h => h.status === 'success').length;

  return (
    <div className="social-hub">
      {/* ── Toast Notification ── */}
      {showConnectToast && (
        <div className="sh-toast">
          <Globe size={16} />
          <span><strong>{showConnectToast}</strong> integration coming soon!</span>
        </div>
      )}
      {/* ── Hub Header ── */}
      <div className="hub-header-glass">
        <div className="hub-title-row">
          <div className="hub-icon-wrap">
            <Globe size={32} />
          </div>
          <div>
            <h1 className="hub-title">Social <span className="text-gradient">Hub</span></h1>
            <p className="hub-subtitle">Centralized social media command center</p>
          </div>
        </div>
        <div className="hub-stats-glass">
          <div className="stat-card-glass">
            <span className="stat-val">{Object.keys(platformStatuses).length}</span>
            <span className="stat-label">Platforms</span>
          </div>
          <div className="stat-card-glass">
            <span className="stat-val text-gradient">{connectedCount}</span>
            <span className="stat-label">Connected</span>
          </div>
          <div className="stat-card-glass">
            <span className="stat-val">{activeJobs.length}</span>
            <span className="stat-label">Scheduled</span>
          </div>
          <div className="stat-card-glass">
            <span className="stat-val" style={{ color: '#3fb950' }}>{successCount}</span>
            <span className="stat-label">Posted ✅</span>
          </div>
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div className="qa-grid-glass">
        {quickActions.map(action => (
          <button
            key={action.id}
            className="qa-card-glass"
            onClick={() => handleQuickAction(action.id)}
          >
            <div className="qa-icon-glass">{action.icon}</div>
            <div className="qa-info">
              <span className="qa-label">{action.label}</span>
              <span className="qa-desc">{action.description}</span>
            </div>
            {action.badge && (
              <span className={`qa-badge ${action.badge.toLowerCase()}`}>{action.badge}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Broadcast Composer & AI ── */}
      <div className="broadcast-section">
        {/* Broadcast Composer */}
        <div className="broadcast-composer-glass">
          <div className="section-header">
            <MessageCircle size={20} color="#4facfe" />
            <span>Quick Broadcast</span>
          </div>
          <textarea
            className="broadcast-textarea"
            placeholder="What's on your mind? This will post to all connected platforms..."
            value={broadcastText}
            onChange={e => setBroadcastText(e.target.value)}
            maxLength={2000}
          />
          <div className="char-counter">{broadcastText.length}/2000</div>
          <div className="broadcast-controls">
            <div className="target-platforms">
              {Object.entries(platformStatuses).map(([id, status]) => (
                <div
                  key={id}
                  className={`target-chip ${status.connected ? 'active' : ''}`}
                  style={{ '--chip-color': PLATFORM_COLORS[id] } as React.CSSProperties}
                  title={status.connected ? `Will post to ${PLATFORM_NAMES[id]}` : `${PLATFORM_NAMES[id]} not connected`}
                >
                  {PLATFORM_ICONS[id]}
                </div>
              ))}
            </div>
            <button
              className="btn-broadcast"
              onClick={handleBroadcast}
              disabled={!broadcastText.trim() || broadcastLoading}
            >
              {broadcastLoading ? (
                <>
                  <span className="eh-spin"><Clock size={18} /></span>
                  Posting...
                </>
              ) : (
                <>
                  <Send size={18} />
                  Broadcast Now
                </>
              )}
            </button>
          </div>
          {broadcastResult && (
            <div className={`broadcast-result ${broadcastResult.type}`}>
              {broadcastResult.type === 'success' ? <CheckCircle size={18} /> : <XCircle size={18} />}
              {broadcastResult.message}
            </div>
          )}
          {aiCaption && (
            <div className="ai-caption-result">
              <Sparkles size={16} />
              <span>AI Enhanced:</span>
              <p>{aiCaption}</p>
            </div>
          )}
        </div>

        {/* 24/7 Auto Pilot Module */}
        <div className="ai-assistant-glass" style={{ border: activeJobs.length > 0 ? '1px solid #3fb950' : '' }}>
          <div className="ai-header">
            <div className="ai-header-left">
              <Clock size={20} color={activeJobs.length > 0 ? "#3fb950" : undefined} />
              <span className={activeJobs.length > 0 ? "text-gradient-success" : "text-gradient-purple"}>
                24/7 Auto Pilot
              </span>
            </div>
            {activeJobs.length > 0 && (
              <span className="active-badge">{activeJobs.length} ACTIVE</span>
            )}
          </div>
          <div className="ai-content">
            <p className="ai-description">
              Schedule multiple pipelines to post content automatically.
            </p>

            {/* Active Jobs List */}
            {activeJobs.length > 0 && (
              <div className="active-jobs-list">
                <div className="jobs-section-title">Active Schedules</div>
                {activeJobs.map(job => (
                  <div key={job.id} className="job-card">
                    <div className="job-info">
                      <div className="job-time">{job.time} <span className="job-repeat">(Daily)</span></div>
                      <div className="job-options">{job.options?.niche} • {job.options?.tone}</div>
                    </div>
                    <button
                      className="job-remove-btn"
                      onClick={() => removeAutoPilotJob(job.id)}
                      title="Remove Schedule"
                    >
                      <XCircle size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add New Job Form */}
            <div className="add-job-form">
              <div className="form-section-title">Add New Schedule</div>
              <div className="form-fields">
                <div className="form-field">
                  <label>Run Time</label>
                  <input
                    type="time"
                    value={newRunTime}
                    onChange={e => setNewRunTime(e.target.value)}
                    className="time-input"
                  />
                </div>
                <div className="form-field">
                  <label>Target Niche</label>
                  <select
                    value={newNiche}
                    onChange={e => setNewNiche(e.target.value)}
                    className="select-input"
                  >
                    <option value="tech">Tech & AI</option>
                    <option value="finance">Finance</option>
                    <option value="lifestyle">Lifestyle</option>
                    <option value="beauty">Beauty</option>
                    <option value="food">Food</option>
                    <option value="real-estate">Real Estate</option>
                  </select>
                </div>
                <div className="form-field">
                  <label>Content Tone</label>
                  <select
                    value={newTone}
                    onChange={e => setNewTone(e.target.value)}
                    className="select-input"
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="educational">Educational</option>
                  </select>
                </div>
              </div>
              <button
                className="btn-ai"
                onClick={addAutoPilotJob}
                disabled={isPilotLoading}
              >
                <Power size={16} />
                {isPilotLoading ? 'Saving...' : 'Add Schedule'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Auto-Pilot Post History ── */}
      <div className="ai-assistant-glass">
        <div
          className="ai-header"
          style={{ cursor: 'pointer' }}
          onClick={() => { setHistoryExpanded(p => !p); if (!historyExpanded) fetchPostHistory(); }}
        >
          <div className="ai-header-left">
            <History size={20} color="#4facfe" />
            <span className="text-gradient">Auto-Post History</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {postHistory.length > 0 && (
              <span style={{ fontSize: '0.75rem', color: '#8b949e' }}>{postHistory.length} records</span>
            )}
            {historyExpanded ? <ChevronUp size={16} color="#8b949e" /> : <ChevronDown size={16} color="#8b949e" />}
          </div>
        </div>
        {historyExpanded && (
          <div className="ai-content">
            {postHistory.length === 0 ? (
              <p className="ai-description" style={{ textAlign: 'center', padding: '16px 0' }}>
                📭 ยังไม่มีประวัติ — รัน Auto Pilot ครั้งแรกเพื่อเริ่มบันทึก
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {postHistory.map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '12px',
                    padding: '10px 12px', borderRadius: '10px',
                    background: item.status === 'success' ? 'rgba(63,185,80,0.07)' : 'rgba(248,81,73,0.07)',
                    border: `1px solid ${item.status === 'success' ? 'rgba(63,185,80,0.25)' : 'rgba(248,81,73,0.25)'}`,
                  }}>
                    <div style={{ paddingTop: '2px', flexShrink: 0 }}>
                      {item.status === 'success'
                        ? <CheckCircle size={16} color="#3fb950" />
                        : <XCircle size={16} color="#f85149" />}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
                        <span style={{
                          fontSize: '0.82rem', fontWeight: 600, color: '#e6edf3',
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '60%'
                        }}>
                          {item.topic || item.message_preview || '(ไม่มีหัวข้อ)'}
                        </span>
                        <span style={{ fontSize: '0.72rem', color: '#8b949e', flexShrink: 0 }}>
                          {item.timestamp}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px', marginTop: '5px', flexWrap: 'wrap', alignItems: 'center' }}>
                        {item.image_count > 0 && (
                          <span style={{ fontSize: '0.72rem', color: '#8b949e' }}>
                            🖼 {item.image_count} รูป
                          </span>
                        )}
                        {item.status === 'success' && item.post_id && (
                          <a
                            href={`https://www.facebook.com/${item.post_id}`}
                            target="_blank" rel="noreferrer"
                            style={{ fontSize: '0.72rem', color: '#4facfe', display: 'flex', alignItems: 'center', gap: '3px', textDecoration: 'none' }}
                          >
                            <ExternalLink size={11} /> ดูโพสต์
                          </a>
                        )}
                        {item.status === 'error' && item.error && (
                          <span style={{ fontSize: '0.72rem', color: '#f85149' }} title={item.error}>
                            ⚠️ {item.error.length > 70 ? item.error.slice(0, 70) + '…' : item.error}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Connected Platforms Grid ── */}
      <div className="section-header" style={{ marginTop: '8px' }}>
        <Globe size={20} />
        <span>Manage Platforms</span>
      </div>
      <div className="platform-grid-glass">
        {Object.entries(platformStatuses).map(([id, status]) => (
          <div
            key={id}
            className={`platform-card-premium ${activePlatform === id ? 'active' : ''}`}
            style={{ '--platform-color': PLATFORM_COLORS[id] } as React.CSSProperties}
          >
            <div className="pc-header">
              <div className="pc-icon-wrap">
                {PLATFORM_ICONS[id]}
              </div>
              <div className={`pc-status ${status.connected ? 'connected' : 'disconnected'}`}>
                {status.connected ? (
                  <>
                    <CheckCircle size={14} />
                    <span>Connected</span>
                  </>
                ) : (
                  <>
                    <XCircle size={14} />
                    <span>Disconnected</span>
                  </>
                )}
              </div>
            </div>
            <div className="pc-info">
              <h3>{PLATFORM_NAMES[id]}</h3>
              <p>{PLATFORM_DESCRIPTIONS[id]}</p>
            </div>
            <div className="pc-footer">
              <button
                className="pc-btn"
                onClick={(evt) => handlePlatformAction(evt, id)}
              >
                {status.connected ? 'Manage Platform' : 'Connect Account'}
                <ExternalLink size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── Facebook Expanded Integration ── */}
      {activePlatform === 'facebook' && (
        <div className="platform-expanded-glass">
          <FacebookConnectPage />
        </div>
      )}

      {/* ── Placeholder for Other Platforms ── */}
      {['twitter', 'instagram', 'youtube'].includes(activePlatform || '') && (
        <div className="platform-expanded-glass">
          <div className="coming-soon-panel">
            <Globe size={48} />
            <h3>{PLATFORM_NAMES[activePlatform!]} Integration</h3>
            <p>This platform integration is coming soon.</p>
            <div className="platform-badge" style={{ background: PLATFORM_COLORS[activePlatform!] }}>
              {PLATFORM_ICONS[activePlatform!]}
              <span>{PLATFORM_NAMES[activePlatform!]}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
