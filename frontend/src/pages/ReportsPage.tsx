import { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, FileText, TrendingUp, ShoppingCart, Film, Image, Share2, ChevronDown, ChevronRight, CheckCircle, AlertCircle, Clock, Sparkles, Zap, Globe, Brain } from 'lucide-react';
import '../styles/reports.css';

interface LookforwardPost {
  name: string;
  has_caption: boolean;
  has_post: boolean;
  has_hashtags: boolean;
  has_images: boolean;
  insight_score: number | string;
}

interface ReadyToPost {
  date: string;
  count: number;
  posts: LookforwardPost[];
}

interface TrendTopic {
  topic: string;
  reason: string;
}

interface Pipeline {
  run_id: string;
  status: string;
  topic: string;
  created: string;
}

interface ReportData {
  lookforward: {
    ready_to_post: ReadyToPost[];
    drafts: { date: string; count: number }[];
    pipeline_count: number;
    recent_pipelines: Pipeline[];
  };
  trend_scan: {
    date: string;
    niche: string;
    topics_count: number;
    topics: TrendTopic[];
  };
  veo_gen: {
    scripts_count: number;
    screenshots_count: number;
    has_walkthrough: boolean;
    has_config: boolean;
  };
  shopee: {
    tools_count: number;
    steps_count: number;
    has_cookies: boolean;
    last_error: string | null;
  };
  image_gen: { scripts_count: number };
  social: { scripts_count: number };
  generated_at: string;
}

const API_BASE = window.location.origin;

const ENGINE_CARDS = [
  { key: 'lookforward', label: 'LookForward', icon: <Brain size={20} />, color: '#f472b6' },
  { key: 'trend_scan', label: 'Trend Scan', icon: <TrendingUp size={20} />, color: '#818cf8' },
  { key: 'veo_gen', label: 'VEO Gen', icon: <Film size={20} />, color: '#38bdf8' },
  { key: 'shopee', label: 'Shopee', icon: <ShoppingCart size={20} />, color: '#fb923c' },
  { key: 'image_gen', label: 'Image Gen', icon: <Image size={20} />, color: '#34d399' },
  { key: 'social', label: 'Social', icon: <Globe size={20} />, color: '#60a5fa' },
];

export default function ReportsPage() {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeEngine, setActiveEngine] = useState('lookforward');
  const [expandedPost, setExpandedPost] = useState<string | null>(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/reports/scan`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReport(); }, []);

  const totalPosts = data?.lookforward.ready_to_post.reduce((s, r) => s + r.count, 0) || 0;
  const totalDrafts = data?.lookforward.drafts.reduce((s, d) => s + d.count, 0) || 0;

  const getEngineStatus = (key: string) => {
    if (!data) return 'idle';
    switch (key) {
      case 'lookforward': return totalPosts > 0 ? 'success' : 'idle';
      case 'trend_scan': return data.trend_scan.topics_count > 0 ? 'success' : 'idle';
      case 'veo_gen': return data.veo_gen.scripts_count > 0 ? 'success' : 'idle';
      case 'shopee': return data.shopee.last_error ? 'error' : data.shopee.tools_count > 0 ? 'success' : 'idle';
      case 'image_gen': return data.image_gen.scripts_count > 0 ? 'success' : 'idle';
      case 'social': return data.social.scripts_count > 0 ? 'success' : 'idle';
      default: return 'idle';
    }
  };

  const activeColor = ENGINE_CARDS.find(c => c.key === activeEngine)?.color || '#00f2ff';

  return (
    <div className="rp-page">
      {/* Header */}
      <div className="rp-header">
        <div className="rp-header-left">
          <div className="rp-header-icon">
            <BarChart3 size={20} color="#fff" />
          </div>
          <div>
            <div className="rp-header-title">ENGINE REPORTS</div>
            <div className="rp-header-sub">
              {data?.generated_at ? `Updated: ${data.generated_at}` : 'Scanning...'}
            </div>
          </div>
        </div>
        <button className="rp-refresh-btn" onClick={fetchReport} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'rp-spin' : ''} />
        </button>
      </div>

      {error && <div className="rp-error">❌ {error}</div>}

      {/* Engine Cards Grid */}
      <div className="rp-engine-grid">
        {ENGINE_CARDS.map(card => {
          const status = getEngineStatus(card.key);
          return (
            <div
              key={card.key}
              className={`rp-engine-card ${activeEngine === card.key ? 'active' : ''}`}
              style={{ '--card-color': card.color } as React.CSSProperties}
              onClick={() => setActiveEngine(card.key)}
            >
              <div className={`rp-card-dot rp-dot-${status}`} />
              <div className="rp-card-icon" style={{ color: card.color }}>{card.icon}</div>
              <div className="rp-card-name">{card.label}</div>
            </div>
          );
        })}
      </div>

      {/* Summary Stats Bar */}
      {data && (
        <div className="rp-stats-bar">
          <div className="rp-stat">
            <span className="rp-stat-value" style={{ color: '#00ff88' }}>{totalPosts}</span>
            <span className="rp-stat-label">Ready</span>
          </div>
          <div className="rp-stat-divider" />
          <div className="rp-stat">
            <span className="rp-stat-value" style={{ color: '#ffcc00' }}>{totalDrafts}</span>
            <span className="rp-stat-label">Drafts</span>
          </div>
          <div className="rp-stat-divider" />
          <div className="rp-stat">
            <span className="rp-stat-value" style={{ color: '#818cf8' }}>{data.trend_scan.topics_count}</span>
            <span className="rp-stat-label">Trends</span>
          </div>
          <div className="rp-stat-divider" />
          <div className="rp-stat">
            <span className="rp-stat-value" style={{ color: '#38bdf8' }}>{data.lookforward.pipeline_count}</span>
            <span className="rp-stat-label">Pipelines</span>
          </div>
        </div>
      )}

      {/* Active Engine Panel */}
      <div className="rp-panel" style={{ '--panel-color': activeColor } as React.CSSProperties}>
        {!data && !loading && (
          <div className="rp-empty">
            <Sparkles size={32} style={{ opacity: 0.3 }} />
            <p>Press Refresh to scan engine outputs</p>
          </div>
        )}

        {loading && (
          <div className="rp-loading">
            <div className="rp-loading-spinner" />
            <p>Scanning engines...</p>
          </div>
        )}

        {data && activeEngine === 'lookforward' && <LookforwardPanel data={data.lookforward} expandedPost={expandedPost} setExpandedPost={setExpandedPost} />}
        {data && activeEngine === 'trend_scan' && <TrendScanPanel data={data.trend_scan} />}
        {data && activeEngine === 'veo_gen' && <VeoPanel data={data.veo_gen} />}
        {data && activeEngine === 'shopee' && <ShopeePanel data={data.shopee} />}
        {data && activeEngine === 'image_gen' && <SimplePanel title="Image Gen" scripts={data.image_gen.scripts_count} />}
        {data && activeEngine === 'social' && <SimplePanel title="Social" scripts={data.social.scripts_count} />}
      </div>
    </div>
  );
}

// ─── Engine Panels ──────────────────────────────

function LookforwardPanel({ data, expandedPost, setExpandedPost }: {
  data: ReportData['lookforward'];
  expandedPost: string | null;
  setExpandedPost: (v: string | null) => void;
}) {
  return (
    <div className="rp-panel-inner">
      {data.ready_to_post.length > 0 && (
        <>
          <div className="rp-section-title">
            <CheckCircle size={14} className="text-green-400" />
            Ready to Post
          </div>
          {data.ready_to_post.map(rtp => (
            <div key={rtp.date} className="rp-date-group">
              <div className="rp-date-label">📅 {rtp.date} — {rtp.count} posts</div>
              {rtp.posts.map((p, i) => (
                <div
                  key={i}
                  className={`rp-post-item ${expandedPost === `${rtp.date}-${i}` ? 'expanded' : ''}`}
                  onClick={() => setExpandedPost(expandedPost === `${rtp.date}-${i}` ? null : `${rtp.date}-${i}`)}
                >
                  <div className="rp-post-header">
                    <div className="rp-post-icons">
                      {p.has_caption && <span title="Has caption">📝</span>}
                      {p.has_post && <span title="Has post text">📄</span>}
                      {p.has_hashtags && <span title="Has hashtags">#️⃣</span>}
                      {p.has_images && <span title="Has images">🖼️</span>}
                    </div>
                    <span className="rp-post-name">{p.name}</span>
                    <span className="rp-post-score">⭐{p.insight_score}</span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </>
      )}

      {data.drafts.length > 0 && (
        <>
          <div className="rp-section-title" style={{ marginTop: 16 }}>
            <Clock size={14} style={{ color: '#ffcc00' }} />
            Drafts
          </div>
          <div className="rp-draft-grid">
            {data.drafts.map(d => (
              <div key={d.date} className="rp-draft-chip">
                {d.date}: <strong>{d.count}</strong>
              </div>
            ))}
          </div>
        </>
      )}

      {data.recent_pipelines.length > 0 && (
        <>
          <div className="rp-section-title" style={{ marginTop: 16 }}>
            <Zap size={14} style={{ color: '#38bdf8' }} />
            Recent Pipelines
          </div>
          {data.recent_pipelines.slice(-6).reverse().map(p => (
            <div key={p.run_id} className="rp-pipeline-item">
              <span className={`rp-pipeline-dot ${p.status}`} />
              <span className="rp-pipeline-id">{p.run_id}</span>
              <span className="rp-pipeline-topic">{p.topic.slice(0, 55)}...</span>
              <span className="rp-pipeline-time">{p.created.slice(11, 16)}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function TrendScanPanel({ data }: { data: ReportData['trend_scan'] }) {
  return (
    <div className="rp-panel-inner">
      <div className="rp-meta-row">
        <span>📅 {data.date}</span>
        <span>Niche: {data.niche}</span>
      </div>
      {data.topics.map((t, i) => (
        <div key={i} className="rp-trend-card">
          <div className="rp-trend-num">{i + 1}</div>
          <div className="rp-trend-body">
            <div className="rp-trend-topic">{t.topic}</div>
            <div className="rp-trend-reason">{t.reason}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function VeoPanel({ data }: { data: ReportData['veo_gen'] }) {
  return (
    <div className="rp-panel-inner">
      <div className="rp-stats-grid">
        <MiniStat label="Scripts" value={data.scripts_count} color="#38bdf8" />
        <MiniStat label="Screenshots" value={data.screenshots_count} color="#f472b6" />
        <MiniStat label="Walkthrough" value={data.has_walkthrough ? '✅' : '❌'} color="#00ff88" />
        <MiniStat label="Config" value={data.has_config ? '✅' : '❌'} color="#ffcc00" />
      </div>
    </div>
  );
}

function ShopeePanel({ data }: { data: ReportData['shopee'] }) {
  return (
    <div className="rp-panel-inner">
      <div className="rp-stats-grid">
        <MiniStat label="Tools" value={data.tools_count} color="#fb923c" />
        <MiniStat label="Steps" value={data.steps_count} color="#60a5fa" />
        <MiniStat label="Cookies" value={data.has_cookies ? '✅' : '❌'} color="#00ff88" />
      </div>
      {data.last_error && (
        <div className="rp-error-inline">
          ⚠️ {data.last_error}
        </div>
      )}
    </div>
  );
}

function SimplePanel({ title, scripts }: { title: string; scripts: number }) {
  return (
    <div className="rp-panel-inner">
      <div className="rp-stats-grid">
        <MiniStat label="Scripts" value={scripts} color="#00f2ff" />
      </div>
      <div className="rp-empty" style={{ padding: 30 }}>
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No output data yet</p>
      </div>
    </div>
  );
}

function MiniStat({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="rp-mini-stat">
      <div className="rp-mini-stat-label">{label}</div>
      <div className="rp-mini-stat-value" style={{ color }}>{value}</div>
    </div>
  );
}
