import { useState, useEffect, useRef } from 'react';
import { Play, Activity, CheckCircle, AlertCircle, Terminal, Cpu, RefreshCw, Clock, Maximize2, Minimize2, Settings2, Copy, Calendar, Zap, Image } from 'lucide-react';
import { engineApi } from '../utils/api';

interface EngineStatus {
  status: 'idle' | 'running' | 'success' | 'error';
  started_at?: number;
  finished_at?: number;
  exit_code?: number;
  log_tail?: string[];
}

interface Engine {
  name: string;
  description: string;
  path: string;
  _status?: EngineStatus;
}


interface VeoOptions {
  aspectRatio: '9:16' | '16:9' | '1:1';
  duration: '5s' | '8s' | '10s';
  style: string;
  imagePath: string;
}

interface LookforwardOptions {
  topic: string;
  tone: 'professional' | 'casual' | 'educational';
  contentType: 'full' | 'quick' | 'strategy-only' | 'content-only';
  includeImages: boolean;
  wordCount: number;
}

interface ShopeeOptions {
  keyword: string;
  limit: number;
}

interface FbPosterOptions {
  mode: 'manual' | 'scheduled';
  scheduleTime: string;
  repeat: 'once' | 'daily' | 'weekdays';
  contentSource: 'latest' | 'custom';
  packagePath: string;
}

interface ImageGenOptions {
  packagePath: string;
  model: 'FLUX.1-schnell' | 'FLUX.1-dev';
  numImages: number;
}

interface TrendScanOptions {
  niche: string;        // preset key or 'custom'
  customNiche: string;  // free-form if niche === 'custom'
}

export default function EngineHubPage() {
  const [engines, setEngines] = useState<Record<string, Engine>>({});
  const [loading, setLoading] = useState(true);
  const [activeEngine, setActiveEngine] = useState<string | null>(null);
  const [liveLog, setLiveLog] = useState<Record<string, string[]>>({});
  const [fullscreen, setFullscreen] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showOptions, setShowOptions] = useState(false);
  
  const [veoOptions, setVeoOptions] = useState<VeoOptions>({
    aspectRatio: '9:16',
    duration: '8s',
    style: 'Commercial',
    imagePath: '',
  });

  const [lookforwardOptions, setLookforwardOptions] = useState<LookforwardOptions>({
    topic: '',
    tone: 'professional',
    contentType: 'full',
    includeImages: true,
    wordCount: 800,
  });

  const [shopeeOptions, setShopeeOptions] = useState<ShopeeOptions>({
    keyword: '',
    limit: 50,
  });

  const [fbPosterOptions, setFbPosterOptions] = useState<FbPosterOptions>({
    mode: 'manual',
    scheduleTime: '09:00',
    repeat: 'daily',
    contentSource: 'latest',
    packagePath: '',
  });

  const [imageGenOptions, setImageGenOptions] = useState<ImageGenOptions>({
    packagePath: '',
    model: 'FLUX.1-schnell',
    numImages: 2,
  });

  const TREND_NICHES = [
    { key: 'tech',        label: '🤖 Tech & AI' },
    { key: 'finance',     label: '💰 Finance & Investment' },
    { key: 'lifestyle',   label: '✨ Lifestyle & Wellness' },
    { key: 'beauty',      label: '💄 Beauty & Skincare' },
    { key: 'food',        label: '🍜 Food & Restaurant' },
    { key: 'real-estate', label: '🏠 Real Estate' },
    { key: 'health',      label: '🏥 Health & Medical' },
    { key: 'custom',      label: '🔍 Custom...' },
  ];

  const [trendScanOptions, setTrendScanOptions] = useState<TrendScanOptions>({
    niche: 'tech',
    customNiche: '',
  });

  const [scheduleMsg, setScheduleMsg] = useState<string>('');

  const [viewMode, setViewMode] = useState<'live'|'history'|'preview'>('live');
  const [historyFiles, setHistoryFiles] = useState<string[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<string>('');
  const [historyLog, setHistoryLog] = useState<string>('');
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const statusPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logPanelRef = useRef<HTMLDivElement>(null);

  const copyLog = () => {
    if (activeEngine && liveLog[activeEngine]) {
      // Clean ANSI escape codes from clipboard too
      const cleanLogs = liveLog[activeEngine].map(line => line.replace(/\x1b\[[0-9;]*m/g, ''));
      navigator.clipboard.writeText(cleanLogs.join('\n'));
      alert('Copied to clipboard!');
    }
  };

  useEffect(() => {
    fetchEngines();
    statusPollRef.current = setInterval(pollStatus, 2000);
    return () => { if (statusPollRef.current) clearInterval(statusPollRef.current); };
  }, []);

  useEffect(() => {
    if (activeEngine && viewMode === 'history') {
      fetchHistoryList(activeEngine);
    } else if (activeEngine && viewMode === 'preview') {
      fetchPreview(activeEngine);
    }
  }, [activeEngine, viewMode]);

  const fetchHistoryList = async (id: string) => {
    try {
      const { ok, data } = await engineApi.history(id);
      if (ok && data?.files) {
        setHistoryFiles(data.files);
        if (data.files.length > 0) {
          setSelectedHistory(data.files[0]);
          fetchHistoryLog(id, data.files[0]);
        } else {
          setHistoryLog('No history logs found.');
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchHistoryLog = async (id: string, file: string) => {
    try {
      const { ok, data } = await engineApi.historyLog(id, file);
      if (ok && data?.content) {
        setHistoryLog(data.content);
      }
    } catch (e) {}
  };

  const fetchPreview = async (id: string) => {
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      const { ok, data } = await engineApi.preview(id);
      if (ok && data) {
        setPreviewData(data);
      } else {
        setPreviewData({ error: 'No preview available.' });
      }
    } catch (e) {
      setPreviewData({ error: 'Failed to fetch preview.' });
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    if (autoScroll && logPanelRef.current) {
      logPanelRef.current.scrollTop = logPanelRef.current.scrollHeight;
    }
  }, [liveLog, activeEngine, autoScroll]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isAtBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  const fetchEngines = async () => {
    try {
      const { ok, data } = await engineApi.list();
      if (ok && data) {
        setEngines(data);
        if (!activeEngine && Object.keys(data).length > 0) {
          setActiveEngine(Object.keys(data)[0]);
        }
      }
    } catch (e) {
      console.error('Failed to fetch engines:', e);
    } finally {
      setLoading(false);
    }
  };

  const pollStatus = async () => {
    try {
      const { ok, data: statusData } = await engineApi.status();
      
      if (ok && statusData) {
        // Get current active engine - use functional update to get latest
        setEngines(prev => {
          // First update to get latest state
          const updated = { ...prev };
          for (const [id, engine] of Object.entries(updated)) {
            if (statusData[id]) {
              updated[id] = { ...engine, _status: statusData[id] };
            }
          }
          return updated;
        });
        
        // Then update logs
        const newLogs: Record<string, string[]> = {};
        for (const [id, status] of Object.entries(statusData as Record<string, any>)) {
          if (status?.log_tail && status.log_tail.length > 0) {
            newLogs[id] = status.log_tail;
          }
        }
        
        if (Object.keys(newLogs).length > 0) {
          console.log('Setting logs:', newLogs);
          setLiveLog(prev => ({ ...prev, ...newLogs }));
        }
      }
    } catch (e) {
      console.error('Poll status error:', e);
    }
  };

  const runEngine = async (id: string) => {
    try {
      let options: Record<string, any> | undefined;
      
      
      // Add options for veo-gen engine
      if (id === 'veo-gen') {
        options = {
          aspect_ratio: veoOptions.aspectRatio,
          duration: veoOptions.duration,
          style: veoOptions.style,
          image_path: veoOptions.imagePath,
        };
      }

      // Add options for lookforward engine
      if (id === 'lookforward' && lookforwardOptions.topic) {
        options = {
          topic: lookforwardOptions.topic,
          tone: lookforwardOptions.tone,
          content_type: lookforwardOptions.contentType,
          include_images: lookforwardOptions.includeImages,
          word_count: lookforwardOptions.wordCount,
        };
      }

      // Add options for shopee engine
      if (id === 'shopee-scraper' && shopeeOptions.keyword) {
        options = {
          keyword: shopeeOptions.keyword,
          limit: shopeeOptions.limit,
        };
      }

      // Image Gen options
      if (id === 'image-gen') {
        options = {
          package_path: imageGenOptions.packagePath || undefined,
          model: imageGenOptions.model,
          num_images: imageGenOptions.numImages,
        };
      }

      // FB Poster options
      if (id === 'fb-poster') {
        options = {
          mode: fbPosterOptions.mode,
          schedule_time: fbPosterOptions.scheduleTime,
          repeat: fbPosterOptions.repeat,
          package_path: fbPosterOptions.contentSource === 'custom' ? fbPosterOptions.packagePath : undefined,
        };
      }

      // Trend Scan niche options
      if (id === 'trend-scan') {
        if (trendScanOptions.niche === 'custom' && trendScanOptions.customNiche.trim()) {
          options = { custom_niche: trendScanOptions.customNiche.trim() };
        } else if (trendScanOptions.niche !== 'tech') {
          options = { niche: trendScanOptions.niche };
        }
      }
      
      const { ok, data } = await engineApi.run(id, options || {});
      if (ok && data?.success) {
        if (data.scheduled) {
          setScheduleMsg(`✅ Scheduled! Job ID: ${data.job_id} — ${data.message}`);
          setTimeout(() => setScheduleMsg(''), 8000);
          return; // Don't update running status for scheduled jobs
        }
        setEngines(prev => ({
          ...prev,
          [id]: { ...prev[id], _status: { status: 'running', started_at: Date.now() / 1000 } }
        }));
      }
    } catch (e) {
      console.error('Failed to start engine:', e);
    }
  };

  const getState = (id: string) => engines[id]?._status?.status || 'idle';

  const getElapsed = (engine: Engine) => {
    const s = engine._status;
    if (!s?.started_at) return null;
    const end = s.finished_at || Date.now() / 1000;
    const sec = Math.round(end - s.started_at);
    if (sec < 60) return `${sec}s`;
    return `${Math.floor(sec / 60)}m ${sec % 60}s`;
  };

  const ENGINE_META: Record<string, { icon: string; color: string; label: string }> = {
    'trend-scan':     { icon: '📡', color: '#00f2ff', label: 'Trend Scan' },
    'lookforward':    { icon: '🧠', color: '#a78bfa', label: 'Lookforward' },
    'shopee-scraper': { icon: '🛒', color: '#f97316', label: 'Shopee' },
    'fb-poster':      { icon: '📘', color: '#3b82f6', label: 'FB Poster' },
    'veo-gen':        { icon: '🎬', color: '#ec4899', label: 'VEO Gen' },
    'social-poster':  { icon: '🌐', color: '#10b981', label: 'Social' },
    'image-gen':      { icon: '🖼️', color: '#f59e0b', label: 'Image Gen' },
  };

  const engineList = Object.entries(engines);
  const runningCount = engineList.filter(([id]) => getState(id) === 'running').length;

  if (loading) {
    return (
      <div className="multi-loading">
        <div className="multi-spinner" />
        <p>Scanning Engine Fleet...</p>
      </div>
    );
  }

  return (
    <div className={`eh-tabs-container ${fullscreen ? 'eh-fullscreen' : ''}`}>
      {/* Main Content */}
      <div className="eh-main">

        {/* Header */}
        <div className="eh-main-header">
          <div className="eh-main-title">
            <Cpu size={20} style={{ color: 'var(--primary)' }} />
            <span className="eh-page-title">Engine Operations Center</span>
            {runningCount > 0 && (
              <span className="eh-running-badge">
                <Activity size={11} className="eh-spin" />
                {runningCount} RUNNING
              </span>
            )}
          </div>
          <div className="eh-main-actions">
            {activeEngine && engines[activeEngine!]?._status?.started_at && (
              <div className="eh-main-timer">
                <Clock size={14} />
                {getElapsed(engines[activeEngine!])}
              </div>
            )}
            <button className="eh-main-btn" onClick={() => setFullscreen(!fullscreen)}>
              {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <button className="eh-main-btn" onClick={pollStatus}>
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        {/* Engine Card Grid */}
        <div className="eh-engine-grid">
          {engineList.map(([id, engine]) => {
            const state = getState(id);
            const meta = ENGINE_META[id] || { icon: '⚙️', color: '#00f2ff', label: engine.name };
            return (
              <button
                key={id}
                className={`eh-engine-card ${activeEngine === id ? 'active' : ''} state-${state}`}
                onClick={() => { setActiveEngine(id); setShowOptions(false); setViewMode('live'); }}
                style={{ '--card-color': meta.color } as React.CSSProperties}
              >
                <span className={`eh-card-status-dot ${state}`} />
                <div className="eh-card-icon">{meta.icon}</div>
                <div className="eh-card-name">{meta.label}</div>
                {state === 'running' && <div className="eh-card-pulse" />}
              </button>
            );
          })}
        </div>

        {/* Active Engine Description */}
        {activeEngine && engines[activeEngine] && (
          <div className="eh-main-desc">
            <strong style={{ color: ENGINE_META[activeEngine]?.color || 'var(--primary)', marginRight: '8px' }}>
              {ENGINE_META[activeEngine]?.icon} {engines[activeEngine].name}
            </strong>
            <span style={{ opacity: 0.6 }}>—</span>
            <span style={{ marginLeft: '8px' }}>{engines[activeEngine].description}</span>
          </div>
        )}

        {/* Output Panel */}
        <div className="eh-output-panel">
          <div className="eh-output-header" style={{ gap: '20px' }}>
            <div style={{ display: 'flex', gap: '15px' }}>
              <span 
                style={{ cursor: 'pointer', opacity: viewMode === 'live' ? 1 : 0.5, borderBottom: viewMode === 'live' ? '2px solid var(--primary)' : 'none', paddingBottom: '4px' }}
                onClick={() => setViewMode('live')}
              >
                <Terminal size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} /> LIVE
              </span>
              <span 
                style={{ cursor: 'pointer', opacity: viewMode === 'history' ? 1 : 0.5, borderBottom: viewMode === 'history' ? '2px solid var(--primary)' : 'none', paddingBottom: '4px' }}
                onClick={() => setViewMode('history')}
              >
                <Clock size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} /> HISTORY
              </span>
              {(activeEngine === 'lookforward' || activeEngine === 'shopee-scraper') && (
                <span 
                  style={{ cursor: 'pointer', opacity: viewMode === 'preview' ? 1 : 0.5, borderBottom: viewMode === 'preview' ? '2px solid var(--primary)' : 'none', paddingBottom: '4px' }}
                  onClick={() => setViewMode('preview')}
                >
                  <Activity size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} /> PREVIEW
                </span>
              )}
            </div>
            
            {viewMode === 'live' && runningCount > 0 && <span className="eh-output-live">LIVE</span>}
            {viewMode === 'live' && (
              <>
                <button 
                  className="eh-output-scroll-btn"
                  onClick={copyLog}
                  style={{ marginLeft: 'auto', marginRight: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}
                  title="Copy Output"
                >
                  <Copy size={12} /> COPY
                </button>
                <button 
                  className={`eh-output-scroll-btn ${autoScroll ? 'active' : ''}`}
                  onClick={() => setAutoScroll(!autoScroll)}
                  style={{ marginLeft: '0' }}
                  title={autoScroll ? 'Auto-scroll ON - Click to disable' : 'Auto-scroll OFF - Click to enable'}
                >
                  {autoScroll ? '⬇ Auto' : '⬇ Manual'}
                </button>
              </>
            )}
          </div>
          
          {viewMode === 'live' && (
          <div className="eh-output-body" ref={logPanelRef} onScroll={handleScroll}>
            {activeEngine && liveLog[activeEngine]?.map((line, i) => {
              const cleanLine = line.replace(/\x1b\[[0-9;]*m/g, '');
              const urlRegex = /(https?:\/\/[^\s]+)/g;
              const hasUrl = urlRegex.test(cleanLine);
              return (
              <div key={i} className={`eh-output-line ${cleanLine.toLowerCase().includes('error') ? 'error' : ''}`}>
                {!hasUrl ? cleanLine : cleanLine.split(urlRegex).map((part, idx) => 
                  part.match(urlRegex) 
                    ? <a key={idx} href={part} target="_blank" rel="noreferrer" style={{color: '#00d4ff', textDecoration: 'underline'}}>{part}</a> 
                    : part
                )}
              </div>
            )})}
            {(!activeEngine || !liveLog[activeEngine]?.length) && (
              <div className="eh-output-empty">
                {activeEngine 
                  ? 'No output yet. Run the engine.' 
                  : 'Select an engine to view output.'}
              </div>
            )}
          </div>
          )}

          {viewMode === 'history' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ padding: '8px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <select 
                   style={{ padding: '6px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', outline: 'none' }}
                   value={selectedHistory} 
                   onChange={(e) => {
                     setSelectedHistory(e.target.value);
                     if (activeEngine) fetchHistoryLog(activeEngine, e.target.value);
                   }}
                >
                  {historyFiles.map(f => <option key={f} value={f}>{f}</option>)}
                  {historyFiles.length === 0 && <option>No history</option>}
                </select>
              </div>
              <div className="eh-output-body" style={{ whiteSpace: 'pre-wrap', flex: 1 }}>
                 {historyLog || <span style={{ opacity: 0.5 }}>No content.</span>}
              </div>
            </div>
          )}

          {viewMode === 'preview' && (
            <div className="eh-output-body" style={{ color: '#eee' }}>
              {previewLoading && <div style={{ padding: 20 }}>Loading preview...</div>}
              {previewData?.error && <div style={{ color: 'var(--danger)', padding: 20 }}>{previewData.error}</div>}
              
              {previewData?.preview_type === 'lookforward' && (
                 <div style={{ padding: '10px' }}>
                   <div style={{ background: 'rgba(0,242,255,0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(0,242,255,0.1)', marginBottom: '16px' }}>
                     <h3 style={{ color: 'var(--primary)', margin: '0 0 8px 0', fontSize: '1.1rem' }}>📦 {previewData.data.project}</h3>
                   </div>
                   
                   {previewData.data.caption && (
                     <div style={{ marginBottom: 16 }}>
                       <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 4 }}>Caption</div>
                       <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px 14px', borderRadius: '8px', borderLeft: '3px solid var(--primary)' }}>
                         {previewData.data.caption}
                       </div>
                     </div>
                   )}
                   
                   {previewData.data.hashtags && (
                     <div style={{ marginBottom: 16 }}>
                       <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 4 }}>Hashtags</div>
                       <div style={{ color: '#00d4ff' }}>{previewData.data.hashtags}</div>
                     </div>
                   )}
                   
                   {previewData.data.image_prompts && (
                     <div style={{ marginBottom: 16 }}>
                       <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                         <span>Image Prompts Guide</span>
                         <button 
                            onClick={() => { navigator.clipboard.writeText(previewData.data.image_prompts); alert('Copied Prompts!'); }}
                            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', borderRadius: '4px', cursor: 'pointer', padding: '2px 8px', fontSize: '0.7rem' }}
                         >COPY PROMPTS</button>
                       </div>
                       <div style={{ background: 'rgba(255,200,0,0.05)', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #ffcc00', whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.85rem', color: '#ffd54f' }}>
                         {previewData.data.image_prompts}
                       </div>
                     </div>
                   )}
                   
                   {previewData.data.post && (
                     <div style={{ marginTop: 20 }}>
                       <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                         <span>Post Content</span>
                         <button 
                            onClick={() => { navigator.clipboard.writeText(previewData.data.post); alert('Copied Post!'); }}
                            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', borderRadius: '4px', cursor: 'pointer', padding: '2px 8px', fontSize: '0.7rem' }}
                         >COPY POST</button>
                       </div>
                       <div style={{ background: '#1a1b26', padding: '20px', borderRadius: '8px', whiteSpace: 'pre-wrap', fontFamily: 'system-ui, -apple-system', fontSize: '0.9rem', lineHeight: '1.6' }}>
                         {previewData.data.post}
                       </div>
                     </div>
                   )}
                 </div>
              )}
              
              {previewData?.preview_type === 'shopee' && (
                 <div style={{ padding: '10px' }}>
                   <h3 style={{ color: 'var(--primary)', marginBottom: '16px' }}>🛒 Shopee Top Products Scraped</h3>
                   <div style={{ overflowX: 'auto' }}>
                     <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                       <thead>
                         <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                           <th style={{ padding: '10px', color: 'var(--text-muted)', fontWeight: 'normal' }}>Name</th>
                           <th style={{ padding: '10px', color: 'var(--text-muted)', fontWeight: 'normal' }}>Price (฿)</th>
                           <th style={{ padding: '10px', color: 'var(--text-muted)', fontWeight: 'normal' }}>Link</th>
                         </tr>
                       </thead>
                       <tbody>
                         {previewData.data.items?.map((item: any, idx: number) => (
                           <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                             <td style={{ padding: '10px' }}>
                               <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                 {item.image_url && <img src={item.image_url} alt="img" style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: '4px' }} />}
                                 <span title={item.name}>{item.name?.substring(0, 50)}...</span>
                               </div>
                             </td>
                             <td style={{ padding: '10px', color: '#ff6b9d', fontWeight: 'bold' }}>{item.price}</td>
                             <td style={{ padding: '10px' }}><a href={item.url} target="_blank" rel="noreferrer" style={{color: '#00d4ff', textDecoration: 'none', padding: '4px 8px', border: '1px solid rgba(0,212,255,0.3)', borderRadius: '4px'}}>View</a></td>
                           </tr>
                         ))}
                       </tbody>
                     </table>
                     {previewData.data.items?.length === 0 && <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>No items found in CSV.</div>}
                   </div>
                 </div>
              )}
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="eh-main-controls">
          {(activeEngine === 'lookforward' || activeEngine === 'veo-gen' || activeEngine === 'shopee-scraper' || activeEngine === 'fb-poster' || activeEngine === 'image-gen' || activeEngine === 'trend-scan') && (
            <button
              className={`eh-options-btn ${showOptions ? 'active' : ''}`}
              onClick={() => setShowOptions(!showOptions)}
            >
              <Settings2 size={16} />
              OPTIONS
            </button>
          )}
          {activeEngine && (
            <button
              className={`eh-run-btn ${getState(activeEngine) === 'running' ? 'running' : ''} ${getState(activeEngine) === 'success' ? 'success' : ''} ${getState(activeEngine) === 'error' ? 'error' : ''}`}
              onClick={() => runEngine(activeEngine)}
              disabled={getState(activeEngine) === 'running'}
            >
              {getState(activeEngine) === 'running' ? (
                <>
                  <Activity size={18} className="eh-spin" />
                  RUNNING...
                </>
              ) : getState(activeEngine) === 'success' ? (
                <>
                  <CheckCircle size={18} />
                  COMPLETED
                </>
              ) : getState(activeEngine) === 'error' ? (
                <>
                  <AlertCircle size={18} />
                  FAILED - RETRY?
                </>
              ) : activeEngine === 'fb-poster' && fbPosterOptions.mode === 'scheduled' ? (
                <>
                  <Calendar size={18} />
                  SCHEDULE POST
                </>
              ) : (
                <>
                  <Play size={18} />
                  RUN ENGINE
                </>
              )}
            </button>
          )}

          {/* Schedule notification */}
          {scheduleMsg && (
            <div style={{ marginTop: '10px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(0,255,128,0.08)', border: '1px solid rgba(0,255,128,0.25)', color: '#00ff80', fontSize: '0.85rem', fontFamily: 'monospace' }}>
              {scheduleMsg}
            </div>
          )}
        </div>

        
        {/* VEO Options Panel */}
        {showOptions && activeEngine === 'veo-gen' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Settings2 size={16} />
              <span>VEO Video Options</span>
            </div>
            <div className="eh-options-body">
              <div className="eh-option-row">
                <div className="eh-option-group">
                  <label>Aspect Ratio / สัดส่วน</label>
                  <select
                    value={veoOptions.aspectRatio}
                    onChange={(e) => setVeoOptions(p => ({ ...p, aspectRatio: e.target.value as any }))}
                  >
                    <option value="9:16">9:16 (แนวตั้ง)</option>
                    <option value="16:9">16:9 (แนวนอน)</option>
                    <option value="1:1">1:1 (จัตุรัส)</option>
                  </select>
                </div>

                <div className="eh-option-group">
                  <label>Duration / ความยาว</label>
                  <select
                    value={veoOptions.duration}
                    onChange={(e) => setVeoOptions(p => ({ ...p, duration: e.target.value as any }))}
                  >
                    <option value="5s">5 วินาที</option>
                    <option value="8s">8 วินาที</option>
                    <option value="10s">10 วินาที</option>
                  </select>
                </div>
              </div>

              <div className="eh-option-group" style={{ marginBottom: '16px' }}>
                <label>Target Image / รูปภาพสิ้นค้า (ป้อน Path เต็ม หรืออัปโหลด)</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    placeholder="e.g., C:\Images\product.jpg หรือกดปุ่มด้านขวา 👉"
                    value={veoOptions.imagePath}
                    onChange={(e) => setVeoOptions(p => ({ ...p, imagePath: e.target.value }))}
                    style={{ flex: 1 }}
                  />
                  <label style={{ display: 'flex', alignItems: 'center', background: 'var(--primary)', color: '#000', padding: '0 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: '800', fontSize: '0.75rem' }}>
                    UPLOAD
                    <input type="file" style={{ display: 'none' }} accept="image/*" onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        try {
                          const res = await engineApi.upload(file);
                          if (res.success && res.path) {
                             setVeoOptions(p => ({ ...p, imagePath: res.path }));
                             alert('🚀 อัปโหลดรูปภาพสำเร็จ! พร้อมรันแล้ว!');
                          } else {
                             alert('❌ อัปโหลดพัง: ' + res.error);
                          }
                        } catch(err) { alert('❌ อัปโหลดไม่สำเร็จ หรือ Server ขัดข้อง'); }
                      }
                    }} />
                  </label>
                </div>
              </div>

              <div className="eh-option-group">
                <label>Style / สไตล์</label>
                <input
                  type="text"
                  placeholder="e.g., Commercial, Cinematic, Minimal"
                  value={veoOptions.style}
                  onChange={(e) => setVeoOptions(p => ({ ...p, style: e.target.value }))}
                />
              </div>
            </div>
          </div>
        )}

        {/* Lookforward Options Panel */}
        {showOptions && activeEngine === 'lookforward' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Settings2 size={16} />
              <span>Content Options</span>
            </div>
            <div className="eh-options-body">
              <div className="eh-option-group">
                <label>Topic / หัวข้อ</label>
                <input
                  type="text"
                  placeholder="e.g., AI agents จะเปลี่ยนวงการ Tech อย่างไร?"
                  value={lookforwardOptions.topic}
                  onChange={(e) => setLookforwardOptions(p => ({ ...p, topic: e.target.value }))}
                />
              </div>
              
              <div className="eh-option-row">
                <div className="eh-option-group">
                  <label>Tone / โทน</label>
                  <select
                    value={lookforwardOptions.tone}
                    onChange={(e) => setLookforwardOptions(p => ({ ...p, tone: e.target.value as any }))}
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual / สบายๆ</option>
                    <option value="educational">Educational / สอนหน่อย</option>
                  </select>
                </div>
                
                <div className="eh-option-group">
                  <label>Content Type / หมดหมู่</label>
                  <select
                    value={lookforwardOptions.contentType}
                    onChange={(e) => setLookforwardOptions(p => ({ ...p, contentType: e.target.value as any }))}
                  >
                    <option value="full">Full Pipeline / เต็มระบบ</option>
                    <option value="quick">Quick / รวดเร็ว</option>
                    <option value="strategy-only">Strategy Only / กลยุทธ์อย่างเดียว</option>
                    <option value="content-only">Content Only / โพสต์อย่างเดียว</option>
                  </select>
                </div>
              </div>
              
              <div className="eh-option-row">
                <div className="eh-option-group">
                  <label>Word Count</label>
                  <select
                    value={lookforwardOptions.wordCount}
                    onChange={(e) => setLookforwardOptions(p => ({ ...p, wordCount: parseInt(e.target.value) }))}
                  >
                    <option value="300">300 คำ (สั้น)</option>
                    <option value="500">500 คำ (กลาง)</option>
                    <option value="800">800 คำ (ยาว)</option>
                    <option value="1200">1200 คำ (Very Long)</option>
                  </select>
                </div>
                
                <div className="eh-option-group eh-option-checkbox">
                  <label>
                    <input
                      type="checkbox"
                      checked={lookforwardOptions.includeImages}
                      onChange={(e) => setLookforwardOptions(p => ({ ...p, includeImages: e.target.checked }))}
                    />
                    Include Images
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Shopee Options Panel */}
        {showOptions && activeEngine === 'shopee-scraper' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Settings2 size={16} />
              <span>Shopee Scraper Options</span>
            </div>
            <div className="eh-options-body">
              <div className="eh-option-row">
                <div className="eh-option-group">
                  <label>Keyword / คำค้นหา</label>
                  <input
                    type="text"
                    placeholder="e.g., กระเป๋าสะพายข้าง"
                    value={shopeeOptions.keyword}
                    onChange={(e) => setShopeeOptions(p => ({ ...p, keyword: e.target.value }))}
                  />
                </div>
                
                <div className="eh-option-group">
                  <label>Limit (จำนวนข้อความที่ดึง)</label>
                  <input
                    type="number"
                    value={shopeeOptions.limit}
                    onChange={(e) => setShopeeOptions(p => ({ ...p, limit: parseInt(e.target.value) || 10 }))}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* FB Poster Options Panel */}
        {showOptions && activeEngine === 'fb-poster' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Calendar size={16} />
              <span>Facebook Auto-Post Options</span>
            </div>
            <div className="eh-options-body">
              {/* Mode selector */}
              <div className="eh-option-group">
                <label>Post Mode / โหมด</label>
                <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                  {(['manual', 'scheduled'] as const).map(m => (
                    <label key={m} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '6px 14px', borderRadius: '8px', border: `1px solid ${fbPosterOptions.mode === m ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}`, background: fbPosterOptions.mode === m ? 'rgba(0,242,255,0.08)' : 'transparent', transition: 'all 0.2s' }}>
                      <input type="radio" name="fb-mode" value={m} checked={fbPosterOptions.mode === m} onChange={() => setFbPosterOptions(p => ({ ...p, mode: m }))} style={{ display: 'none' }} />
                      {m === 'manual' ? <Zap size={14} /> : <Calendar size={14} />}
                      {m === 'manual' ? 'Manual (ทันที)' : 'Scheduled (ตั้งเวลา)'}
                    </label>
                  ))}
                </div>
              </div>

              {/* Schedule options */}
              {fbPosterOptions.mode === 'scheduled' && (
                <div className="eh-option-row">
                  <div className="eh-option-group">
                    <label>⏰ Post Time / เวลาโพสต์</label>
                    <input
                      type="time"
                      value={fbPosterOptions.scheduleTime}
                      onChange={(e) => setFbPosterOptions(p => ({ ...p, scheduleTime: e.target.value }))}
                    />
                  </div>
                  <div className="eh-option-group">
                    <label>🔁 Repeat / ทำซ้ำ</label>
                    <select
                      value={fbPosterOptions.repeat}
                      onChange={(e) => setFbPosterOptions(p => ({ ...p, repeat: e.target.value as any }))}
                    >
                      <option value="once">Once / ครั้งเดียว</option>
                      <option value="daily">Daily / ทุกวัน</option>
                      <option value="weekdays">Weekdays / จันทร์-ศุกร์</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Content source */}
              <div className="eh-option-group">
                <label>📦 Content Source / แหล่งเนื้อหา</label>
                <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                  {(['latest', 'custom'] as const).map(s => (
                    <label key={s} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '6px 14px', borderRadius: '8px', border: `1px solid ${fbPosterOptions.contentSource === s ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}`, background: fbPosterOptions.contentSource === s ? 'rgba(0,242,255,0.08)' : 'transparent', transition: 'all 0.2s' }}>
                      <input type="radio" name="fb-source" value={s} checked={fbPosterOptions.contentSource === s} onChange={() => setFbPosterOptions(p => ({ ...p, contentSource: s }))} style={{ display: 'none' }} />
                      {s === 'latest' ? '🔍 Auto (latest ready_to_post)' : '📁 Custom Path'}
                    </label>
                  ))}
                </div>
                {fbPosterOptions.contentSource === 'custom' && (
                  <input
                    type="text"
                    placeholder="e.g., C:\data\content\lookforward\ready_to_post\..."
                    value={fbPosterOptions.packagePath}
                    onChange={(e) => setFbPosterOptions(p => ({ ...p, packagePath: e.target.value }))}
                    style={{ marginTop: '8px' }}
                  />
                )}
              </div>

              {/* Info banner */}
              {fbPosterOptions.mode === 'scheduled' && (
                <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(0,242,255,0.05)', border: '1px solid rgba(0,242,255,0.15)', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                  ⚡ Jobs persist across server restarts. Check <code>/api/schedule</code> to view all scheduled jobs.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Image Gen Options Panel */}
        {showOptions && activeEngine === 'image-gen' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Image size={16} />
              <span>Image Gen Options (FLUX)</span>
            </div>
            <div className="eh-options-body">
              <div className="eh-option-group">
                <label>📦 Package Path <span style={{ opacity: 0.5, fontWeight: 'normal' }}>(ว่าง = auto-detect latest)</span></label>
                <input
                  type="text"
                  placeholder="Leave empty to use latest Lookforward output automatically"
                  value={imageGenOptions.packagePath}
                  onChange={(e) => setImageGenOptions(p => ({ ...p, packagePath: e.target.value }))}
                />
              </div>
              <div className="eh-option-row">
                <div className="eh-option-group">
                  <label>🤖 Model</label>
                  <select
                    value={imageGenOptions.model}
                    onChange={(e) => setImageGenOptions(p => ({ ...p, model: e.target.value as any }))}
                  >
                    <option value="FLUX.1-schnell">FLUX.1-schnell (Fast, Free)</option>
                    <option value="FLUX.1-dev">FLUX.1-dev (Quality)</option>
                  </select>
                </div>
                <div className="eh-option-group">
                  <label>🖼️ Number of Images</label>
                  <select
                    value={imageGenOptions.numImages}
                    onChange={(e) => setImageGenOptions(p => ({ ...p, numImages: parseInt(e.target.value) }))}
                  >
                    <option value={1}>1 รูป</option>
                    <option value={2}>2 รูป</option>
                    <option value={3}>3 รูป</option>
                    <option value={4}>4 รูป</option>
                  </select>
                </div>
              </div>
              <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(255,200,0,0.05)', border: '1px solid rgba(255,200,0,0.15)', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                ⚡ ต้องตั้งค่า <code>HF_TOKEN</code> ใน .env — จะอ่าน image prompts จาก Lookforward output อัตโนมัติ
              </div>
            </div>
          </div>
        )}

        {/* Trend Scan Options Panel */}
        {showOptions && activeEngine === 'trend-scan' && (
          <div className="eh-options-panel">
            <div className="eh-options-header">
              <Activity size={16} />
              <span>Trend Scan — Niche Selector</span>
            </div>
            <div className="eh-options-body">
              <div className="eh-option-group">
                <label>📡 Niche / หมวดหมู่ที่ต้องการสแกน</label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
                  {TREND_NICHES.map(n => (
                    <button
                      key={n.key}
                      onClick={() => setTrendScanOptions(p => ({ ...p, niche: n.key }))}
                      style={{
                        padding: '7px 14px',
                        borderRadius: '20px',
                        border: `1px solid ${trendScanOptions.niche === n.key ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}`,
                        background: trendScanOptions.niche === n.key ? 'rgba(0,242,255,0.12)' : 'rgba(255,255,255,0.02)',
                        color: trendScanOptions.niche === n.key ? 'var(--primary)' : 'var(--text-secondary)',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.18s',
                        boxShadow: trendScanOptions.niche === n.key ? '0 0 12px rgba(0,242,255,0.2)' : 'none',
                      }}
                    >
                      {n.label}
                    </button>
                  ))}
                </div>
              </div>

              {trendScanOptions.niche === 'custom' && (
                <div className="eh-option-group">
                  <label>✏️ Custom Niche Description</label>
                  <input
                    type="text"
                    placeholder="เช่น: ธุรกิจ SME ไทย, อสังหาริมทรัพย์เชียงใหม่, ท่องเที่ยวเกาหลี..."
                    value={trendScanOptions.customNiche}
                    onChange={(e) => setTrendScanOptions(p => ({ ...p, customNiche: e.target.value }))}
                    autoFocus
                  />
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    💡 AI จะสร้าง search queries และวิเคราะห์ trend เฉพาะ niche ที่คุณระบุ
                  </div>
                </div>
              )}

              <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(0,242,255,0.04)', border: '1px solid rgba(0,242,255,0.1)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                🔄 Query pool หมุนเวียนตามวันในปี — ไม่มีการยิง query ซ้ำ &bull; ผลลัพธ์บันทึกใน <code>latest_trends.json</code>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
