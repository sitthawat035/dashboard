/**
 * HermesPage — Full Hermes Agent control panel.
 * Mobile-first responsive design.
 */

import { useState, useEffect, useCallback } from "react";
import { hermesApi } from "../utils/api";
import { useHermes } from "../hooks/useHermes";

// ─── Status Dot ──────────────────────────────────────────────────────────────
function StatusDot({ connected }: { connected: boolean }) {
  return (
    <span style={{
      display: "inline-block", width: 10, height: 10, borderRadius: "50%",
      backgroundColor: connected ? "#22c55e" : "#ef4444", marginRight: 8,
    }} />
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────
function Card({ children, style = {} }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: "#1e1e2e", border: "1px solid #333", borderRadius: 8,
      padding: 16, minWidth: 0, overflow: "hidden", ...style,
    }}>
      {children}
    </div>
  );
}

// ─── Button ──────────────────────────────────────────────────────────────────
function Btn({ onClick, disabled, variant = "default", children, style = {} }: {
  onClick?: () => void; disabled?: boolean; variant?: "default" | "primary" | "danger" | "ghost";
  children: React.ReactNode; style?: React.CSSProperties;
}) {
  const map: Record<string, { bg: string; color: string; hover: string }> = {
    default: { bg: "#333", color: "#ccc", hover: "#444" },
    primary: { bg: "#3b82f6", color: "#fff", hover: "#2563eb" },
    danger: { bg: "#ef4444", color: "#fff", hover: "#dc2626" },
    ghost: { bg: "transparent", color: "#888", hover: "#2a2a3a" },
  };
  const s = map[variant];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: disabled ? "#222" : s.bg, color: disabled ? "#555" : s.color,
        border: "none", borderRadius: 4, padding: "6px 14px", cursor: disabled ? "not-allowed" : "pointer",
        fontSize: 13, fontWeight: 500, transition: "all 0.15s", flexShrink: 0, ...style,
      }}
    >
      {children}
    </button>
  );
}

// ─── Toggle Switch ─────────────────────────────────────────────────────────────
function Toggle({ checked, onChange, disabled }: {
  checked: boolean; onChange: (v: boolean) => void; disabled?: boolean;
}) {
  return (
    <div
      onClick={() => !disabled && onChange(!checked)}
      style={{
        width: 40, height: 22, borderRadius: 11, background: checked ? "#3b82f6" : "#333",
        position: "relative", cursor: disabled ? "not-allowed" : "pointer", transition: "all 0.2s",
        opacity: disabled ? 0.5 : 1, flexShrink: 0,
      }}
    >
      <div style={{
        position: "absolute", top: 3, left: checked ? 21 : 3,
        width: 16, height: 16, borderRadius: "50%", background: "#fff",
        transition: "left 0.2s",
      }} />
    </div>
  );
}

// ─── Badge ─────────────────────────────────────────────────────────────────────
function Badge({ children, color = "#3b82f6" }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{
      background: color + "22", color, padding: "2px 8px", borderRadius: 4,
      fontSize: 11, fontWeight: 600, flexShrink: 0,
    }}>
      {children}
    </span>
  );
}

// ─── Spinner ───────────────────────────────────────────────────────────────────
function Spinner({ size = 16 }: { size?: number }) {
  return (
    <div style={{
      width: size, height: size, border: "2px solid #333", borderTopColor: "#3b82f6",
      borderRadius: "50%", animation: "spin 0.8s linear infinite", display: "inline-block",
    }} />
  );
}

// ─── Error Banner ─────────────────────────────────────────────────────────────
function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div style={{
      background: "#2a1a1a", border: "1px solid #ef4444", borderRadius: 6,
      padding: "12px 16px", color: "#fca5a5", fontSize: 13, marginBottom: 16,
    }}>
      ⚠️ {msg}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 1: Sessions
// ═══════════════════════════════════════════════════════════════════════════════
function SessionsWidget() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async (p = 1, q = "") => {
    setLoading(true); setError("");
    try {
      const data = q
        ? await hermesApi.searchSessions(q)
        : await hermesApi.listSessions(p);
      setSessions(data.sessions || []);
      setTotalPages(data.total_pages || data.totalPages || 1);
    } catch (e: any) {
      setError(e?.message || "Failed to load sessions");
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(page, search); }, [page]);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => { setPage(1); load(1, search); }, 400);
    return () => clearTimeout(t);
  }, [search]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this session?")) return;
    await hermesApi.deleteSession(id);
    load(page, search);
  };

  return (
    <div style={{ minWidth: 0, overflow: "hidden" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 12, minWidth: 0 }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search sessions..."
          style={{
            flex: "1 1 auto", minWidth: 0, background: "#111", color: "#e0e0e0",
            border: "1px solid #444", borderRadius: 6, padding: "6px 12px", fontSize: 13,
          }}
        />
        <Btn onClick={() => load(page, search)} style={{ flex: "0 0 auto" }}>↻</Btn>
      </div>

      {error && <ErrorBanner msg={error} />}

      <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 0 }}>
        {loading && sessions.length === 0
          ? <div style={{ textAlign: "center", padding: 20, color: "#666" }}><Spinner /> Loading...</div>
          : sessions.length === 0
          ? <div style={{ textAlign: "center", padding: 20, color: "#666" }}>No sessions found</div>
          : sessions.map((s) => (
            <div key={s.id || s.session_id} style={{
              display: "flex", alignItems: "center", gap: 8,
              background: "#1a1a2e", border: "1px solid #333", borderRadius: 6,
              padding: "10px 12px", minWidth: 0, overflow: "hidden",
            }}>
              <div style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
                <div style={{
                  fontSize: 13, fontWeight: 600, color: "#e0e0e0", marginBottom: 2,
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}>
                  {s.title || s.name || "Untitled Session"}
                </div>
                <div style={{ fontSize: 11, color: "#666", display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span>{s.message_count || 0} msgs</span>
                  <span>{s.tool_count || 0} tools</span>
                  <span>{s.platform || "CLI"}</span>
                </div>
              </div>
              <Btn variant="danger" onClick={() => handleDelete(s.id || s.session_id)}
                style={{ flex: "0 0 auto", padding: "4px 8px", fontSize: 12 }}>
                🗑
              </Btn>
            </div>
          ))}
      </div>

      <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
        <Btn disabled={page <= 1} onClick={() => setPage(p => p - 1)}>◀ Prev</Btn>
        <span style={{ color: "#888", fontSize: 13, alignSelf: "center" }}>Page {page}/{totalPages}</span>
        <Btn disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next ▶</Btn>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 2: Analytics
// ═══════════════════════════════════════════════════════════════════════════════
function AnalyticsWidget() {
  const [period, setPeriod] = useState("30d");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.getAnalytics(period);
      setData(d);
    } catch (e: any) { setError(e?.message || "Failed to load analytics"); }
    setLoading(false);
  }, [period]);

  useEffect(() => { load(); }, [load]);

  const fmt = (n: number | string) => {
    const v = typeof n === "string" ? parseFloat(n) : n;
    if (!v || isNaN(v)) return "—";
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + "M";
    if (v >= 1_000) return (v / 1_000).toFixed(1) + "K";
    return String(v);
  };

  const statCards = [
    { label: "Total Tokens", value: fmt(data?.total_tokens) },
    { label: "Input", value: fmt(data?.input_tokens) },
    { label: "Output", value: fmt(data?.output_tokens) },
    { label: "Sessions", value: fmt(data?.total_sessions) },
    { label: "API Calls", value: fmt(data?.api_calls) },
    { label: "Est. Cost", value: data?.estimated_cost ? `$${data.estimated_cost}` : "—" },
  ];

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      {loading && !data ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : !data ? (
        <div style={{ textAlign: "center", padding: 20, color: "#666" }}>No data</div>
      ) : (
        <>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
            gap: 10, marginBottom: 16, minWidth: 0,
          }}>
            {statCards.map((m) => (
              <Card key={m.label} style={{ textAlign: "center", padding: 12 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#3b82f6" }}>{m.value}</div>
                <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>{m.label}</div>
              </Card>
            ))}
          </div>
          {data.daily?.length > 0 && (
            <div style={{ overflowX: "auto", minWidth: 0 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, minWidth: 400 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #333", color: "#888" }}>
                    <th style={{ padding: "6px 8px", textAlign: "left" }}>Date</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>Sessions</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>Input</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>Output</th>
                  </tr>
                </thead>
                <tbody>
                  {data.daily.slice(0, 14).map((row: any) => (
                    <tr key={row.date} style={{ borderBottom: "1px solid #222" }}>
                      <td style={{ padding: "5px 8px", color: "#ccc" }}>{row.date}</td>
                      <td style={{ padding: "5px 8px", textAlign: "right" }}>{row.sessions ?? 0}</td>
                      <td style={{ padding: "5px 8px", textAlign: "right" }}>{fmt(row.input)}</td>
                      <td style={{ padding: "5px 8px", textAlign: "right" }}>{fmt(row.output)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 3: Models
// ═══════════════════════════════════════════════════════════════════════════════
function ModelsWidget() {
  const [models, setModels] = useState<any[]>([]);
  const [currentModel, setCurrentModel] = useState("");
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.listModels();
      setModels(d.models || d || []);
      setCurrentModel(d.current_model || d.currentModel || d.active_model || "");
    } catch (e: any) { setError(e?.message || "Failed to load models"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSwitch = async (name: string) => {
    if (name === currentModel) return;
    setSwitching(name);
    try {
      await hermesApi.switchModel(name);
      setCurrentModel(name);
    } catch (e: any) { setError(e?.message || "Failed to switch model"); }
    setSwitching("");
  };

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      {loading && !models.length ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : (
        <>
          {currentModel && (
            <div style={{
              marginBottom: 12, padding: "8px 12px", background: "#16653422",
              border: "1px solid #166534", borderRadius: 6, fontSize: 13, color: "#86efac",
            }}>
              Active: <strong>{currentModel}</strong>
            </div>
          )}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            gap: 10, minWidth: 0,
          }}>
            {models.map((m) => {
              const name = m.name || m.model || "";
              const isActive = name === currentModel;
              return (
                <Card key={name} style={{
                  border: isActive ? "1px solid #3b82f6" : "1px solid #333",
                }}>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                    <Badge color={m.provider_color || "#3b82f6"}>{m.provider || m.source || "—"}</Badge>
                    {isActive && <Badge color="#22c55e">ACTIVE</Badge>}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#e0e0e0", marginBottom: 6,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {name}
                  </div>
                  <div style={{ fontSize: 11, color: "#888" }}>
                    {m.tokens && <div>Tokens: {m.tokens}</div>}
                    {m.sessions != null && <div>Sessions: {m.sessions}</div>}
                  </div>
                  <Btn
                    variant="primary"
                    onClick={() => handleSwitch(name)}
                    disabled={!!switching || isActive}
                    style={{ width: "100%", marginTop: 10, fontSize: 12 }}
                  >
                    {switching === name ? <Spinner size={12} /> : isActive ? "✓ Active" : "Use This"}
                  </Btn>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 4: Logs
// ═══════════════════════════════════════════════════════════════════════════════
function LogsWidget() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [type, setType] = useState("agent");
  const [level, setLevel] = useState("all");
  const [lines, setLines] = useState(100);
  const [error, setError] = useState("");
  const [refreshIv, setRefreshIv] = useState<NodeJS.Timeout | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const data = await hermesApi.getLogs({ type, level, lines });
      setLogs(data.logs || data.entries || data || []);
    } catch (e: any) { setError(e?.message || "Failed to load logs"); }
    setLoading(false);
  }, [type, level, lines]);

  useEffect(() => {
    load();
    if (autoRefresh) {
      const iv = setInterval(load, 5000);
      setRefreshIv(iv);
    } else {
      if (refreshIv) { clearInterval(refreshIv); setRefreshIv(null); }
    }
    return () => { if (refreshIv) clearInterval(refreshIv); };
  }, [autoRefresh, load]);

  const levelColor = (l: string) => ({
    INFO: "#3b82f6", WARNING: "#f59e0b", ERROR: "#ef4444", DEBUG: "#888",
  }[l.toUpperCase()] || "#666");

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10, alignItems: "center" }}>
        {["agent", "errors", "gateway"].map((t) => (
          <Btn key={t} variant={type === t ? "primary" : "ghost"} onClick={() => setType(t)}
            style={{ fontSize: 11, padding: "3px 8px" }}>{t.toUpperCase()}</Btn>
        ))}
        <span style={{ width: 1, height: 20, background: "#333", margin: "0 4px" }} />
        {["all", "debug", "info", "warning", "error"].map((l) => (
          <Btn key={l} variant={level === l ? "primary" : "ghost"} onClick={() => setLevel(l)}
            style={{ fontSize: 11, padding: "3px 8px" }}>{l.toUpperCase()}</Btn>
        ))}
        <span style={{ width: 1, height: 20, background: "#333", margin: "0 4px" }} />
        {[50, 100, 200, 500].map((n) => (
          <Btn key={n} variant={lines === n ? "primary" : "ghost"} onClick={() => setLines(n)}
            style={{ fontSize: 11, padding: "3px 8px" }}>{n}</Btn>
        ))}
        <span style={{ flex: 1 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Toggle checked={autoRefresh} onChange={setAutoRefresh} />
          <span style={{ fontSize: 11, color: "#888" }}>Auto</span>
        </div>
        <Btn onClick={load} style={{ fontSize: 11, padding: "3px 8px" }}>↻</Btn>
      </div>

      <div style={{
        background: "#111", borderRadius: 6, padding: 10, maxHeight: 400, overflowY: "auto",
        fontFamily: "monospace", fontSize: 11, lineHeight: 1.5, minWidth: 0,
      }}>
        {loading && !logs.length ? (
          <div style={{ textAlign: "center", padding: 16, color: "#666" }}><Spinner /> Loading...</div>
        ) : logs.length === 0 ? (
          <div style={{ textAlign: "center", padding: 16, color: "#666" }}>No logs</div>
        ) : logs.map((line, i) => (
          <div key={i} style={{
            marginBottom: 1, color: "#a0a0a0", whiteSpace: "pre-wrap", wordBreak: "break-word",
          }}>
            {line.timestamp && (
              <span style={{ color: "#555", marginRight: 6 }}>
                {new Date(line.timestamp * 1000).toLocaleTimeString("en-GB", {
                  hour: "2-digit", minute: "2-digit", second: "2-digit",
                })}
              </span>
            )}
            {line.level && (
              <span style={{ color: levelColor(line.level), fontWeight: 600, marginRight: 6 }}>
                [{line.level}]
              </span>
            )}
            {line.component && <span style={{ color: "#818cf8", marginRight: 6 }}>{line.component}</span>}
            <span>{line.message || line.msg || JSON.stringify(line.data || line).substring(0, 200)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 5: Cron
// ═══════════════════════════════════════════════════════════════════════════════
function CronWidget() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", prompt: "", schedule: "" });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.getCronJobs();
      setJobs(d.jobs || d || []);
    } catch (e: any) { setError(e?.message || "Failed to load cron jobs"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleTrigger = async (id: string) => {
    try { await hermesApi.triggerCronJob(id); } catch (e) { console.error(e); }
  };

  const handleCreate = async () => {
    if (!form.name.trim() || !form.schedule.trim() || !form.prompt.trim()) return;
    setCreating(true);
    try {
      await hermesApi.createCronJob(form.name, form.prompt, form.schedule);
      setForm({ name: "", prompt: "", schedule: "" });
      setShowCreate(false);
      load();
    } catch (e: any) { setError(e?.message || "Create failed"); }
    setCreating(false);
  };

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <div style={{ marginBottom: 12 }}>
        <Btn variant="primary" onClick={() => setShowCreate(!showCreate)} style={{ fontSize: 13 }}>
          {showCreate ? "✕ Close" : "+ Create Job"}
        </Btn>
      </div>

      {showCreate && (
        <Card style={{ marginBottom: 16, border: "1px solid #3b82f6" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {(["name", "prompt", "schedule"] as const).map((field) => (
              <input
                key={field}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                placeholder={field === "prompt" ? "Task prompt..." : field === "schedule" ? "0 9 * * *" : `Job ${field}`}
                style={{
                  background: "#111", color: "#e0e0e0", border: "1px solid #444",
                  borderRadius: 4, padding: "8px 10px", fontSize: 13, minWidth: 0,
                }}
              />
            ))}
            <div style={{ display: "flex", gap: 8 }}>
              <Btn variant="primary" onClick={handleCreate}
                disabled={creating || !form.name.trim() || !form.schedule.trim() || !form.prompt.trim()} style={{ fontSize: 13 }}>
                {creating ? <Spinner size={12} /> : "Create"}
              </Btn>
              <Btn onClick={() => setShowCreate(false)} style={{ fontSize: 13 }}>Cancel</Btn>
            </div>
          </div>
        </Card>
      )}

      {loading && !jobs.length ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : jobs.length === 0 ? (
        <Card><div style={{ textAlign: "center", color: "#666", padding: 20 }}>No cron jobs</div></Card>
      ) : jobs.map((job) => (
        <Card key={job.id || job.job_id} style={{ marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
            gap: 12, minWidth: 0, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#e0e0e0", marginBottom: 4 }}>
                {job.name || job.id}
              </div>
              <div style={{ fontSize: 12, color: "#888", wordBreak: "break-word" }}>
                {String(job.prompt || "").substring(0, 80)}
              </div>
              <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>Schedule: {job.schedule || "—"}</div>
            </div>
            <Btn onClick={() => handleTrigger(job.id || job.job_id)}
              style={{ flex: "0 0 auto", fontSize: 12, padding: "4px 12px" }}>
              ▶ Run Now
            </Btn>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 6: Skills
// ═══════════════════════════════════════════════════════════════════════════════
function SkillsWidget() {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [showToolsetOnly, setShowToolsetOnly] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.listSkills();
      setSkills(d.skills || d || []);
    } catch (e: any) { setError(e?.message || "Failed to load skills"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleToggle = async (name: string, enabled: boolean) => {
    await hermesApi.toggleSkill(name, enabled);
    setSkills((prev) => prev.map((s) => s.name === name ? { ...s, enabled } : s));
  };

  const categories = ["all", ...Array.from(new Set(skills.map((s) => s.category).filter(Boolean)))];
  const filtered = skills.filter((s) => {
    const matchSearch = s.name.toLowerCase().includes(search.toLowerCase());
    const matchCat = category === "all" || s.category === category;
    const matchToolset = !showToolsetOnly || s.toolset;
    return matchSearch && matchCat && matchToolset;
  });

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search skills..."
          style={{
            flex: "1 1 140px", background: "#111", color: "#e0e0e0", border: "1px solid #444",
            borderRadius: 4, padding: "4px 10px", fontSize: 13, minWidth: 0,
          }}
        />
        <Btn variant={showToolsetOnly ? "primary" : "default"}
          onClick={() => setShowToolsetOnly(!showToolsetOnly)} style={{ fontSize: 12 }}>
          Toolset {showToolsetOnly ? "ON" : "OFF"}
        </Btn>
        <Btn onClick={load} disabled={loading} style={{ flex: "0 0 auto" }}>
          {loading ? <Spinner size={12} /> : "↻"}
        </Btn>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 12 }}>
        {categories.slice(0, 10).map((cat) => (
          <Btn key={cat} variant={category === cat ? "primary" : "ghost"}
            onClick={() => setCategory(cat)} style={{ fontSize: 11, padding: "3px 8px" }}>
            {cat === "all" ? "All" : cat}
          </Btn>
        ))}
      </div>

      {loading && !skills.length ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
          gap: 8, minWidth: 0,
        }}>
          {filtered.map((skill) => (
            <Card key={skill.name} style={{ padding: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                marginBottom: 6, gap: 8, minWidth: 0 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#e0e0e0",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {skill.name}
                </span>
                <Toggle
                  checked={skill.enabled !== false}
                  onChange={(v) => handleToggle(skill.name, v)}
                />
              </div>
              <div style={{ fontSize: 11, color: "#666", marginBottom: 4, overflow: "hidden",
                textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {skill.description || skill.category || ""}
              </div>
              {skill.toolset && <Badge color="#7c3aed">{skill.toolset}</Badge>}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 7: Plugins
// ═══════════════════════════════════════════════════════════════════════════════
function PluginsWidget() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [gitUrl, setGitUrl] = useState("");
  const [forceInstall, setForceInstall] = useState(false);
  const [enableAfterInstall, setEnableAfterInstall] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.listPlugins();
      setPlugins(d.plugins || d || []);
    } catch (e: any) { setError(e?.message || "Failed to load plugins"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleToggle = async (name: string, enabled: boolean) => {
    await hermesApi.togglePlugin(name, enabled);
    setPlugins((prev) => prev.map((p) => p.name === name ? { ...p, enabled } : p));
  };

  const handleInstall = async () => {
    if (!gitUrl.trim()) return;
    setInstalling(true); setInstallResult("");
    try {
      const result = await hermesApi.installPlugin(gitUrl, forceInstall, enableAfterInstall);
      setInstallResult(result.error || result.message || "Installed!");
      load(); setGitUrl("");
    } catch (e: any) { setInstallResult("Error: " + (e?.message || "")); }
    setInstalling(false);
  };

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <Card style={{ marginBottom: 16, border: "1px solid #333" }}>
        <div style={{ fontSize: 13, color: "#888", marginBottom: 8 }}>Install from Git</div>
        <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
          <input
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            placeholder="git URL or owner/repo"
            style={{
              flex: "1 1 160px", background: "#111", color: "#e0e0e0", border: "1px solid #444",
              borderRadius: 4, padding: "6px 10px", fontSize: 13, minWidth: 0,
            }}
          />
          <Btn variant="primary" onClick={handleInstall} disabled={installing || !gitUrl.trim()}>
            {installing ? <Spinner size={12} /> : "Install"}
          </Btn>
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#888", cursor: "pointer" }}>
            <Toggle checked={forceInstall} onChange={setForceInstall} />Force reinstall
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#888", cursor: "pointer" }}>
            <Toggle checked={enableAfterInstall} onChange={setEnableAfterInstall} />Enable after install
          </label>
        </div>
        {installResult && (
          <div style={{
            marginTop: 8, fontSize: 12,
            color: installResult.toLowerCase().includes("error") || installResult.toLowerCase().includes("fail") ? "#ef4444" : "#22c55e",
          }}>
            {installResult}
          </div>
        )}
      </Card>

      {loading && !plugins.length ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : plugins.length === 0 ? (
        <Card><div style={{ textAlign: "center", color: "#666", padding: 20 }}>No plugins found</div></Card>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {plugins.map((p) => (
            <Card key={p.name}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                gap: 12, flexWrap: "wrap", minWidth: 0 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: "#e0e0e0" }}>{p.name}</span>
                    <Badge color={p.source === "bundled" ? "#3b82f6" : "#888"}>{p.source || "—"}</Badge>
                    <Badge color={p.enabled ? "#22c55e" : "#888"}>{p.enabled ? "active" : "inactive"}</Badge>
                  </div>
                  <div style={{ fontSize: 12, color: "#888" }}>{p.description || ""}</div>
                  {p.version && <div style={{ fontSize: 11, color: "#666" }}>v{p.version}</div>}
                </div>
                <Btn onClick={() => handleToggle(p.name, !p.enabled)}
                  variant={p.enabled ? "default" : "primary"} style={{ fontSize: 12, padding: "4px 12px", flex: "0 0 auto" }}>
                  {p.enabled ? "Disable" : "Enable"}
                </Btn>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 8: Config
// ═══════════════════════════════════════════════════════════════════════════════
function ConfigWidget() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [section, setSection] = useState("all");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.getConfig();
      setConfig(d.config || d || {});
    } catch (e: any) { setError(e?.message || "Failed to load config"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    setSaving(true);
    try { await hermesApi.saveConfig(config); alert("Config saved!"); }
    catch (e: any) { setError(e?.message || "Save failed"); }
    setSaving(false);
  };

  const sections = config ? Object.keys(config).filter(k => typeof config[k] === "object" && k !== "_section_order") : [];
  const renderVal = (v: any): string => {
    if (typeof v === "boolean") return v ? "true" : "false";
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "object") return JSON.stringify(v);
    return String(v ?? "");
  };

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search config..."
          style={{
            flex: "1 1 140px", background: "#111", color: "#e0e0e0", border: "1px solid #444",
            borderRadius: 4, padding: "4px 10px", fontSize: 13, minWidth: 0,
          }}
        />
        <Btn onClick={load} disabled={loading}>{loading ? <Spinner size={12} /> : "↻ Refresh"}</Btn>
        <Btn variant="primary" onClick={handleSave} disabled={saving}>
          {saving ? <Spinner size={12} /> : "💾 Save"}
        </Btn>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 12 }}>
        <Btn variant={section === "all" ? "primary" : "ghost"} onClick={() => setSection("all")}
          style={{ fontSize: 11 }}>All ({sections.length})</Btn>
        {sections.slice(0, 10).map((sec) => (
          <Btn key={sec} variant={section === sec ? "primary" : "ghost"}
            onClick={() => setSection(sec)} style={{ fontSize: 11, padding: "3px 8px" }}>
            {sec}
          </Btn>
        ))}
      </div>

      {loading && !config ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : !config ? (
        <Card><div style={{ textAlign: "center", color: "#666", padding: 20 }}>No config data</div></Card>
      ) : (
        <div style={{ overflowX: "auto", minWidth: 0 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, minWidth: 500 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333", color: "#888" }}>
                <th style={{ padding: "6px 8px", textAlign: "left" }}>Key</th>
                <th style={{ padding: "6px 8px", textAlign: "left" }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {sections.flatMap((sec) => {
                const secData = config[sec] || {};
                return Object.entries(secData)
                  .filter(([k, v]) => {
                    const match = search === "" || k.toLowerCase().includes(search.toLowerCase());
                    return (section === "all" || section === sec) && match;
                  })
                  .slice(0, 20)
                  .map(([key, value]) => (
                    <tr key={`${sec}.${key}`} style={{ borderBottom: "1px solid #222" }}>
                      <td style={{ padding: "5px 8px", color: "#818cf8", whiteSpace: "nowrap" }}>{sec}.{key}</td>
                      <td style={{ padding: "5px 8px", color: "#ccc", maxWidth: 200 }}>
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}>
                          {renderVal(value)}
                        </span>
                      </td>
                    </tr>
                  ));
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 9: Gateway
// ═══════════════════════════════════════════════════════════════════════════════
function GatewayWidget({ connected }: { connected: boolean }) {
  const [restarting, setRestarting] = useState(false);
  const [updating, setUpdating] = useState(false);

  const handle = async (action: string, fn: () => Promise<void>) => {
    if (!confirm(`${action} Hermes Gateway?`)) return;
    if (action === "Restart" && connected) {
      setRestarting(true);
      try { await fn(); } catch (e) { console.error(e); }
      setRestarting(false);
    } else if (action === "Update") {
      setUpdating(true);
      try { await fn(); } catch (e) { console.error(e); }
      setUpdating(false);
    }
  };

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
      gap: 16, minWidth: 0,
    }}>
      {[
        { emoji: "🔄", label: "Restart Gateway", variant: "danger" as const, action: "Restart", fn: () => hermesApi.restartGateway() },
        { emoji: "⬆️", label: "Update Hermes", variant: "primary" as const, action: "Update", fn: () => hermesApi.updateHermes() },
      ].map(({ emoji, label, variant, action, fn }) => (
        <Card key={action} style={{ textAlign: "center", padding: 20 }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>{emoji}</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#e0e0e0", marginBottom: 8 }}>{label}</div>
          <div style={{ fontSize: 12, color: "#888", marginBottom: 16 }}>
            {action === "Restart" ? "Graceful restart of gateway process" : "Pull latest from repository"}
          </div>
          <Btn
            variant={variant}
            onClick={() => handle(action, fn)}
            disabled={!connected || restarting || updating}
            style={{ width: "100%" }}
          >
            {restarting || updating ? <Spinner size={12} /> : emoji} {action}
          </Btn>
        </Card>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// WIDGET 9: Keys
// ═══════════════════════════════════════════════════════════════════════════════
function KeysWidget() {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const d = await hermesApi.getKeys();
      setKeys(d.keys || d || []);
    } catch (e: any) { setError(e?.message || "Failed to load keys"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const providerColor = (p: string) => ({
    openrouter: "#a78bfa", openai: "#3b82f6", anthropic: "#22c55e",
    google: "#ea4335", nous: "#f59e0b", local: "#888",
  }[p?.toLowerCase()] || "#888");

  return (
    <div style={{ minWidth: 0 }}>
      {error && <ErrorBanner msg={error} />}
      <div style={{ marginBottom: 12 }}>
        <Btn onClick={load} style={{ fontSize: 13 }}>
          {loading ? <Spinner size={12} /> : "↻ Refresh"}
        </Btn>
      </div>
      {loading && !keys.length ? (
        <div style={{ textAlign: "center", padding: 20 }}><Spinner /> Loading...</div>
      ) : keys.length === 0 ? (
        <Card><div style={{ textAlign: "center", color: "#666", padding: 20 }}>No API keys configured</div></Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
          {keys.map((k, i) => (
            <Card key={i}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Badge color={providerColor(k.provider)}>{k.provider || "unknown"}</Badge>
                {k.valid === false && <Badge color="#ef4444">invalid</Badge>}
                {k.valid === true && <Badge color="#22c55e">valid</Badge>}
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#e0e0e0", marginBottom: 4,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {k.name || k.key_id || `Key ${i + 1}`}
              </div>
              <div style={{ fontSize: 11, color: "#666", fontFamily: "monospace" }}>
                {k.key ? `••••${k.key.slice(-6)}` : "—"}
              </div>
              {k.models && k.models.length > 0 && (
                <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {k.models.slice(0, 5).map((m: string) => (
                    <Badge key={m} color="#3b82f622" colorInner="#60a5fa">{m}</Badge>
                  ))}
                  {k.models.length > 5 && (
                    <Badge color="#333">+{k.models.length - 5}</Badge>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

type TabId = "sessions" | "analytics" | "models" | "logs" | "cron" | "skills" | "plugins" | "config" | "gateway" | "keys";

const TABS: { id: TabId; label: string; emoji: string }[] = [
  { id: "sessions", label: "Sessions", emoji: "📋" },
  { id: "analytics", label: "Analytics", emoji: "📊" },
  { id: "models", label: "Models", emoji: "🧠" },
  { id: "logs", label: "Logs", emoji: "📜" },
  { id: "cron", label: "Cron", emoji: "⏰" },
  { id: "skills", label: "Skills", emoji: "🛠" },
  { id: "plugins", label: "Plugins", emoji: "🔌" },
  { id: "config", label: "Config", emoji: "⚙️" },
  { id: "gateway", label: "Gateway", emoji: "🎛" },
  { id: "keys", label: "Keys", emoji: "🔑" },
];

export default function HermesPage() {
  const { status, isConnected } = useHermes();
  const [activeTab, setActiveTab] = useState<TabId>("sessions");

  return (
    <div style={{
      padding: "16px", maxWidth: "100%", overflowX: "hidden", boxSizing: "border-box",
      color: "#e0e0e0",
    }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        input, textarea, select, button { font-family: inherit; }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, color: "#e0e0e0" }}>
          🤖 Hermes Bridge
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <StatusDot connected={isConnected} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>
            {isConnected ? "Hermes Online" : "Hermes Offline"}
          </span>
          {status?.gateway_state && (
            <span style={{ color: "#888", fontSize: 13 }}>State: {status.gateway_state}</span>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div style={{
        display: "flex", gap: 4, marginBottom: 16,
        overflowX: "auto", paddingBottom: 4,
        borderBottom: "1px solid #333",
        scrollbarWidth: "thin", scrollbarColor: "#333 transparent",
      }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id ? "#1e3a5f" : "transparent",
              color: activeTab === tab.id ? "#60a5fa" : "#888",
              border: "1px solid",
              borderColor: activeTab === tab.id ? "#3b82f6" : "transparent",
              borderRadius: 6, padding: "6px 12px", cursor: "pointer",
              fontSize: 12, fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0,
            }}
          >
            {tab.emoji} {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ minWidth: 0 }}>
        {activeTab === "sessions" && <SessionsWidget />}
        {activeTab === "analytics" && <AnalyticsWidget />}
        {activeTab === "models" && <ModelsWidget />}
        {activeTab === "logs" && <LogsWidget />}
        {activeTab === "cron" && <CronWidget />}
        {activeTab === "skills" && <SkillsWidget />}
        {activeTab === "plugins" && <PluginsWidget />}
        {activeTab === "config" && <ConfigWidget />}
        {activeTab === "gateway" && <GatewayWidget connected={isConnected} />}
        {activeTab === "keys" && <KeysWidget />}
      </div>
    </div>
  );
}