import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Terminal, Copy, Check, Zap, AlertTriangle, GitBranch, RotateCcw, Plus, X } from 'lucide-react';
import { Terminal as XTerminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import '../styles/cli-helper.css';

// ── Types ──────────────────────────────────────────────────────────────────────
interface ShellBlock { shell: string; code: string; label: string; isSource: boolean; isDangerous: boolean; }
interface ParsedResponse { mode: 'CLI_COMMAND' | 'NL_WORKFLOW'; explanation: string; steps: string[]; blocks: ShellBlock[]; notes: string; sourceShell: string; }
interface ChatMessage { id: string; role: 'user' | 'ai' | 'error'; content: string; time: string; intent?: string; parsed?: ParsedResponse; }
interface TermSession { id: string; created: number; }

// ── Helpers ────────────────────────────────────────────────────────────────────
const DANGEROUS = [/rm\s+-rf/i, /del\s+\/f/i, /Remove-Item.*-Force/i, /rmdir\s+\/s/i, /format\s+[a-z]:/i, /curl.*\|\s*sh/i];
const isDangerous = (c: string) => DANGEROUS.some(p => p.test(c));

function detectInputMode(text: string): 'CLI_COMMAND' | 'NL_WORKFLOW' {
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length > 1) return 'NL_WORKFLOW';
  const cliPat = /(\||&&|;|\$[\w(]|>{1,2}|`|\-{1,2}\w+|\bsudo\b|\bgrep\b|\bawk\b|\bfind\b)/;
  if (cliPat.test(text)) return 'CLI_COMMAND';
  const wfPat = /แล้ว|จากนั้น|หลังจาก|ยกเว้น|ทั้งหมด|then|after|backup|deploy|compress|upload|export|find all|get all/i;
  if (wfPat.test(text)) return 'NL_WORKFLOW';
  return 'CLI_COMMAND';
}

function parseAIResponse(text: string, intentHint?: string): ParsedResponse {
  const lines = text.split('\n');
  const blocks: ShellBlock[] = [];
  let inCode = false, currentShell = '', currentCode: string[] = [];
  let explanation = '', steps: string[] = [], notes = '', sourceShell = '';
  const mode: 'CLI_COMMAND' | 'NL_WORKFLOW' = (intentHint === 'NL_WORKFLOW' || text.includes('Workflow Analysis') || text.includes('①')) ? 'NL_WORKFLOW' : 'CLI_COMMAND';

  for (const line of lines) {
    if (!explanation && (line.includes('[🔍') || line.includes('[🧠') || line.includes('แปลงคำสั่ง')))
      explanation = line.replace(/\[.*?\]/g, '').replace(/`/g, '').trim();
    if (/^[①②③④⑤⑥⑦⑧⑨⑩]/.test(line.trim())) steps.push(line.trim());
    if (line.includes('หมายเหตุ') || line.includes('Gotcha') || line.includes('⚠️')) notes += line + '\n';

    if (line.startsWith('```')) {
      if (!inCode) {
        inCode = true;
        const lang = line.slice(3).trim().toLowerCase();
        if (lang === 'powershell' || lang === 'ps1') currentShell = 'PowerShell';
        else if (lang === 'cmd' || lang === 'batch') currentShell = 'CMD';
        else if (['bash', 'sh', 'zsh', 'shell'].includes(lang)) currentShell = 'Linux (Bash)';
        else currentShell = lang || 'Shell';
        currentCode = [];
      } else {
        inCode = false;
        const code = currentCode.join('\n').trim();
        if (currentShell && code) {
          const labelMap: Record<string, string> = { 'PowerShell': '💠 PowerShell', 'CMD': '🖥️ CMD', 'Linux (Bash)': '🐧 Bash / Linux' };
          blocks.push({ shell: currentShell, code, label: labelMap[currentShell] || currentShell, isSource: currentShell === sourceShell, isDangerous: isDangerous(code) });
        }
        currentShell = '';
      }
    } else if (inCode) { currentCode.push(line); }

    if (!sourceShell && line.match(/(Bash|Linux|PowerShell|CMD)/i)) {
      const m = line.match(/(Bash|Linux|PowerShell|CMD)/i);
      if (m) sourceShell = m[0].toLowerCase().includes('bash') || m[0].toLowerCase().includes('linux') ? 'Linux (Bash)' : m[0];
    }
  }
  return { mode, explanation, steps, blocks, notes: notes.trim(), sourceShell };
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function IntentBadge({ mode }: { mode: 'CLI_COMMAND' | 'NL_WORKFLOW' }) {
  return mode === 'NL_WORKFLOW' ? (
    <span className="ch-intent-badge ch-intent-workflow">🧠 Workflow</span>
  ) : (
    <span className="ch-intent-badge ch-intent-cli">⚙️ CLI</span>
  );
}

function ShellTabs({ blocks, active, onSelect }: { blocks: ShellBlock[]; active: string; onSelect: (s: string) => void }) {
  return (
    <div className="ch-shell-tabs">
      {['ทั้งหมด', ...blocks.map(b => b.shell)].map(tab => (
        <button key={tab} onClick={() => onSelect(tab)} className={`ch-shell-tab ${active === tab ? 'active' : ''}`}>
          {tab === 'ทั้งหมด' ? '🔀 ทั้งหมด' : blocks.find(b => b.shell === tab)?.label || tab}
        </button>
      ))}
    </div>
  );
}

function CodeBlock({ block, onCopy, copied }: { block: ShellBlock; onCopy: (c: string) => void; copied: boolean }) {
  return (
    <div className={`ch-code-block ${block.isSource ? 'source' : ''}`}>
      <div className="ch-code-header">
        <div className="ch-code-meta">
          <span className="ch-code-label">{block.label}</span>
          {block.isSource && <span className="ch-code-tag detected">DETECTED</span>}
          {block.isDangerous && <span className="ch-code-tag danger"><AlertTriangle size={9} />อันตราย</span>}
        </div>
        <button onClick={() => onCopy(block.code)} className={`ch-copy-btn ${copied ? 'copied' : ''}`}>
          {copied ? <><Check size={11} />คัดลอกแล้ว</> : <><Copy size={11} />คัดลอก</>}
        </button>
      </div>
      <pre className="ch-code-pre"><code>{block.code}</code></pre>
    </div>
  );
}

function WorkflowSteps({ steps }: { steps: string[] }) {
  if (!steps.length) return null;
  return (
    <div className="ch-workflow-steps">
      <div className="ch-workflow-title">📋 Workflow ที่ตรวจพบ ({steps.length} ขั้นตอน)</div>
      {steps.map((s, i) => (
        <div key={i} className="ch-workflow-step">
          <span className="ch-step-num">{i + 1}</span>
          <span>{s.replace(/^[①②③④⑤⑥⑦⑧⑨⑩]\s*/, '')}</span>
        </div>
      ))}
    </div>
  );
}

function AIResponse({ msg, onCopy, copiedId, activeTab, onTabChange }: {
  msg: ChatMessage; onCopy: (c: string, id: string) => void;
  copiedId: string | null; activeTab: string; onTabChange: (t: string) => void;
}) {
  if (!msg.parsed) return null;
  const { mode, explanation, steps, blocks, notes } = msg.parsed;
  const visibleBlocks = activeTab === 'ทั้งหมด' ? blocks : blocks.filter(b => b.shell === activeTab);
  return (
    <div className="ch-ai-body">
      <div className="ch-ai-meta">
        <IntentBadge mode={mode} />
        {explanation && <span className="ch-ai-explain">{explanation}</span>}
      </div>
      {mode === 'NL_WORKFLOW' && <WorkflowSteps steps={steps} />}
      {blocks.length > 0 && <>
        <ShellTabs blocks={blocks} active={activeTab} onSelect={onTabChange} />
        {visibleBlocks.map((block, i) => (
          <CodeBlock key={i} block={block} onCopy={(c) => onCopy(c, `${msg.id}-${i}`)} copied={copiedId === `${msg.id}-${i}`} />
        ))}
      </>}
      {!blocks.length && <div className="ch-raw-text">{msg.content}</div>}
      {notes && (
        <div className="ch-notes">
          <strong>⚠️ Gotchas</strong>
          <p>{notes.replace(/^[⚠️*\s#]+/gm, '').trim()}</p>
        </div>
      )}
    </div>
  );
}

// ── Empty State ─────────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div className="ch-empty">
      <div className="ch-empty-icon"><Zap size={28} /></div>
      <div className="ch-empty-title">พร้อมรับคำสั่งแล้ว</div>
      <div className="ch-examples">
        <div className="ch-example-card cli">
          <div className="ch-example-mode">⚙️ CLI Mode</div>
          <code>ls -la</code>
          <code>Get-ChildItem -Recurse</code>
          <code>find . -name "*.log" | grep error</code>
        </div>
        <div className="ch-example-card workflow">
          <div className="ch-example-mode">🧠 Workflow Mode <span>(Shift+Enter = บรรทัดใหม่)</span></div>
          <div className="ch-example-nl">หาไฟล์ log ที่แก้ไขใน 3 วัน<br />ยกเว้น node_modules และ .git<br />กรองบรรทัดที่มี error แล้ว export</div>
        </div>
      </div>
    </div>
  );
}

// ── Simple Terminal Component ────────────────────────────────────────────────────
function SimpleTerminal({ sessionId }: { sessionId: string }) {
  const xtermRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<XTerminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const cmdBufRef = useRef('');
  const cursorPosRef = useRef(0);
  const lineCountRef = useRef(0);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const initializedRef = useRef(false);
  const PROMPT = '$ ';

  const writeOutput = useCallback((lines: string[]) => {
    const term = termRef.current;
    if (!term || lines.length === 0) return;
    try {
      term.write('\r\x1b[K');
      lines.forEach((l, i) => {
        term.write(l);
        if (i < lines.length - 1) term.write('\r\n');
      });
      term.write(PROMPT + cmdBufRef.current);
    } catch (e) {
      console.error('xterm write error:', e);
    }
  }, []);

  const pollOutput = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`/api/terminal/${sessionId}/poll?since=${lineCountRef.current}`, {
        credentials: 'include',
      });
      const data = await res.json();
      if (data.lines && data.lines.length > 0) {
        lineCountRef.current = data.total;
        writeOutput(data.lines);
      }
    } catch { /* ignore poll errors */ }
  }, [sessionId, writeOutput]);

  const sendCmd = useCallback(async (cmd: string) => {
    if (!sessionId || !cmd.trim()) return;
    const term = termRef.current;
    if (!term) return;

    cmdBufRef.current = '';
    cursorPosRef.current = 0;
    term.write('\r\n');

    try {
      await fetch('/api/terminal/input', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: sessionId, data: cmd.trim() }),
      });
    } catch {
      term.write('\r\n\x1b[31mConnection error\x1b[0m\r\n');
      term.write(PROMPT);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!xtermRef.current || initializedRef.current) return;
    initializedRef.current = true;

    try {
      console.log('[Terminal] Initializing xterm for session:', sessionId);

      const term = new XTerminal({
        cursorBlink: true,
        cursorStyle: 'block',
        fontSize: 13,
        fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace",
        theme: { background: '#0d1117', foreground: '#e6edf3', cursor: '#58a6ff' },
        scrollback: 5000,
        convertEol: true,
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(xtermRef.current);

      setTimeout(() => { try { fitAddon.fit(); } catch (e) { console.error('fit error:', e); } }, 100);

      termRef.current = term;
      fitRef.current = fitAddon;

      term.writeln('\x1b[36m╔══════════════════════════════════╗\x1b[0m');
      term.writeln('\x1b[36m║\x1b[0m  \x1b[1;33m⚡ CLI Terminal\x1b[0m              \x1b[36m║\x1b[0m');
      term.writeln('\x1b[36m╚══════════════════════════════════╝\x1b[0m');
      term.writeln('');
      term.write(PROMPT);

      // Start polling
      pollIntervalRef.current = setInterval(pollOutput, 500);

      term.onData((data) => {
        if (data === '\r') {
          sendCmd(cmdBufRef.current);
          return;
        }
        if (data === '\x7F' || data === '\b') {
          if (cursorPosRef.current > 0) {
            const buf = cmdBufRef.current;
            cmdBufRef.current = buf.slice(0, cursorPosRef.current - 1) + buf.slice(cursorPosRef.current);
            cursorPosRef.current--;
            term.write('\r\x1b[K' + PROMPT + cmdBufRef.current);
            const moveBack = cmdBufRef.current.length - cursorPosRef.current;
            if (moveBack > 0) term.write('\b'.repeat(moveBack));
          }
          return;
        }
        if (data === '\x03') {
          term.write('^C\r\n');
          cmdBufRef.current = '';
          cursorPosRef.current = 0;
          term.write(PROMPT);
          return;
        }
        if (data >= String.fromCharCode(32)) {
          const buf = cmdBufRef.current;
          cmdBufRef.current = buf.slice(0, cursorPosRef.current) + data + buf.slice(cursorPosRef.current);
          cursorPosRef.current += data.length;
          const rest = cmdBufRef.current.slice(cursorPosRef.current);
          term.write(data + rest + '\b'.repeat(rest.length));
        }
      });

      console.log('[Terminal] xterm initialized successfully');
    } catch (e) {
      console.error('[Terminal] xterm initialization error:', e);
      initializedRef.current = false;
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (termRef.current) {
        termRef.current.dispose();
        termRef.current = null;
      }
      fitRef.current = null;
      initializedRef.current = false;
    };
  }, [sessionId, sendCmd, pollOutput]);

  return <div ref={xtermRef} style={{ height: '100%', width: '100%', display: 'block' }} />;
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function CLIHelperPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem('cli_helper_history');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeTabs, setActiveTabs] = useState<Record<string, string>>({});
  const [provider, setProvider] = useState('');
  const [cliSubTab, setCliSubTab] = useState<'ai' | 'terminal'>('ai');
  const [termSessions, setTermSessions] = useState<Record<string, TermSession>>({});
  const [activeTermSid, setActiveTermSid] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const inputMode = detectInputMode(input);

  // ── Terminal handlers ──────────────────────────────────────────────────────────
  const createTerminal = useCallback(async () => {
    console.log('[CLI Helper] Creating terminal...');
    try {
      const res = await fetch('/api/terminal/create', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      console.log('[CLI Helper] Create response status:', res.status);
      const data = await res.json();
      console.log('[CLI Helper] Create response:', data);

      if (data.session_id) {
        const sid = data.session_id;
        setTermSessions(prev => {
          console.log('[CLI Helper] Adding session:', sid);
          return { ...prev, [sid]: { id: sid, created: Date.now() } };
        });
        setActiveTermSid(sid);
      } else if (data.error) {
        console.error('[CLI Helper] Create error:', data.error);
        alert('Failed to create terminal: ' + data.error);
      }
    } catch (e) {
      console.error('[CLI Helper] Create failed:', e);
      alert('Failed to create terminal: ' + String(e));
    }
  }, []);

  const killTerminal = useCallback((sid: string) => {
    console.log('[CLI Helper] Killing terminal:', sid);
    setTermSessions(prev => { const next = { ...prev }; delete next[sid]; return next; });
    if (activeTermSid === sid) {
      const remaining = Object.keys(termSessions).filter(k => k !== sid);
      setActiveTermSid(remaining.length > 0 ? remaining[0] : null);
    }
  }, [activeTermSid, termSessions]);

  // Auto-create terminal on terminal tab (only once)
  const terminalInitRef = useRef(false);
  useEffect(() => {
    if (cliSubTab === 'terminal' && Object.keys(termSessions).length === 0 && !terminalInitRef.current) {
      terminalInitRef.current = true;
      createTerminal();
    }
  }, [cliSubTab]);

  // ── Persist history to localStorage ────────────────────────────────────────
  useEffect(() => {
    try {
      localStorage.setItem('cli_helper_history', JSON.stringify(messages.slice(0, 40)));
    } catch { /* quota exceeded – ignore */ }
  }, [messages]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatRef.current && cliSubTab === 'ai') chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, cliSubTab]);

  const handleCopy = async (code: string, id: string) => {
    await navigator.clipboard.writeText(code.trim());
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async () => {
    const cmd = input.trim();
    if (!cmd || loading) return;
    const msgId = `ai-${Date.now()}`;
    const now = new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { id: `user-${Date.now()}`, role: 'user', content: cmd, time: now, intent: inputMode }]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/cli-helper/convert', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: cmd }) });
      const data = await res.json();
      if (data.error) {
        setMessages(prev => [...prev, { id: `err-${Date.now()}`, role: 'error', content: data.error, time: now }]);
      } else {
        if (data.provider) setProvider(data.provider);
        const intent: string = data.intent || inputMode;
        const parsed = parseAIResponse(data.answer, intent);
        setMessages(prev => [...prev, { id: msgId, role: 'ai', content: data.answer, time: now, intent, parsed }]);
        setActiveTabs(prev => ({ ...prev, [msgId]: 'ทั้งหมด' }));
      }
    } catch {
      setMessages(prev => [...prev, { id: `err-${Date.now()}`, role: 'error', content: 'เชื่อมต่อ API ไม่ได้ ลองใหม่อีกครั้ง', time: now }]);
    } finally { setLoading(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const lineCount = input.split('\n').length;

  return (
    <div className="cli-helper-v3">

      {/* ── Hub Header (SocialHub style) ── */}
      <div className="hub-header-glass ch-hub-header">
        <div className="hub-title-row">
          <div className="hub-icon-wrap">
            <Terminal size={26} />
          </div>
          <div>
            <div className="hub-title text-gradient">CLI Helper</div>
            <div className="hub-subtitle">วุ้นแปลภาษา Terminal — CLI Mode + Workflow Mode</div>
          </div>
        </div>

        {/* ── Sub Tabs ── */}
        <div className="cli-sub-tabs">
          <button
            className={`cli-sub-tab ${cliSubTab === 'ai' ? 'active' : ''}`}
            onClick={() => setCliSubTab('ai')}
          >
            🤖 AI Helper
          </button>
          <button
            className={`cli-sub-tab ${cliSubTab === 'terminal' ? 'active' : ''}`}
            onClick={() => setCliSubTab('terminal')}
          >
            💻 Terminal
          </button>
        </div>

        <div className="hub-stats-glass">
          {cliSubTab === 'ai' && (
            <>
              <div className="stat-card-glass">
                <div className="stat-val">{messages.filter(m => m.role === 'ai').length}</div>
                <div className="stat-label">แปลงแล้ว</div>
              </div>
              <div className="stat-card-glass">
                <div className="stat-val" style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>
                  {provider ? provider.replace(/[⚡🛸🚀☁️]/g, '').trim().split(' ')[0] : 'OpenClaw'}
                </div>
                <div className="stat-label">Provider</div>
              </div>
            </>
          )}
          {cliSubTab === 'terminal' && (
            <div className="stat-card-glass">
              <div className="stat-val">{Object.keys(termSessions).length}</div>
              <div className="stat-label">Sessions</div>
            </div>
          )}
        </div>
      </div>

      {/* ── AI Helper Tab ── */}
      {cliSubTab === 'ai' && (
        <div className="ch-panel">
          {/* Section header */}
          <div className="section-header">
            <Terminal size={14} />
            ประวัติการแปลง
            {messages.length > 0 && (
              <button className="ch-clear-btn" onClick={() => {
                setMessages([]);
                localStorage.removeItem('cli_helper_history');
              }}>
                <RotateCcw size={12} /> ล้าง
              </button>
            )}
          </div>

          {/* Chat messages */}
          <div className="ch-chat-scroll" ref={chatRef}>
            {messages.length === 0 && !loading && <EmptyState />}

            {messages.map(msg => (
              <div key={msg.id} className={`ch-msg ch-msg-${msg.role === 'error' ? 'error' : msg.role}`}>
                <div className="ch-msg-label">
                  <span>{msg.role === 'user' ? '👤 คุณ' : msg.role === 'ai' ? '🤖 AI' : '⛔ Error'}</span>
                  <span className="ch-msg-time">{msg.time}</span>
                  {msg.intent && <IntentBadge mode={msg.intent as 'CLI_COMMAND' | 'NL_WORKFLOW'} />}
                </div>

                {msg.role === 'ai' && msg.parsed ? (
                  <AIResponse msg={msg} onCopy={handleCopy} copiedId={copiedId}
                    activeTab={activeTabs[msg.id] || 'ทั้งหมด'}
                    onTabChange={tab => setActiveTabs(prev => ({ ...prev, [msg.id]: tab }))} />
                ) : msg.role === 'error' ? (
                  <div className="ch-error-bubble">{msg.content}</div>
                ) : (
                  <code className="ch-user-code">{msg.content}</code>
                )}
              </div>
            ))}

            {loading && (
              <div className="ch-msg ch-msg-ai">
                <div className="ch-msg-label">
                  <span>🤖 AI</span>
                  <span className="ch-msg-time">{inputMode === 'NL_WORKFLOW' ? '🧠 กำลังสังเคราะห์ Workflow...' : '⚙️ กำลังแปลงคำสั่ง...'}</span>
                </div>
                <div className="ch-loading"><div className="ch-dot" /><div className="ch-dot" /><div className="ch-dot" /></div>
              </div>
            )}
          </div>

          {/* ── Input area ── */}
          <div className={`ch-input-wrap ${inputMode === 'NL_WORKFLOW' && input.trim() ? 'workflow' : ''}`}>
            {inputMode === 'NL_WORKFLOW' && input.trim() && (
              <div className="ch-mode-hint">
                <GitBranch size={10} /> Workflow Mode — Enter ส่ง · Shift+Enter ขึ้นบรรทัดใหม่
              </div>
            )}
            <div className="ch-input-row">
              <textarea
                ref={inputRef}
                className="ch-textarea"
                placeholder={inputMode === 'NL_WORKFLOW'
                  ? 'อธิบาย workflow... (Shift+Enter ขึ้นบรรทัดใหม่, Enter ส่ง)'
                  : 'พิมพ์คำสั่ง หรืออธิบาย workflow เป็นภาษาไทย...'}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={Math.min(Math.max(lineCount, 1), 5)}
              />
              <button className={`ch-send ${inputMode === 'NL_WORKFLOW' && input.trim() ? 'workflow' : ''}`}
                onClick={handleSend} disabled={!input.trim() || loading} id="cli-helper-send-btn">
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Terminal Tab ── */}
      {cliSubTab === 'terminal' && (
        <div className="ch-terminal-panel">
          {/* Terminal tabs */}
          <div className="ch-term-tabs">
            {Object.values(termSessions).map((s) => (
              <div
                key={s.id}
                className={`ch-term-tab ${activeTermSid === s.id ? 'active' : ''}`}
                onClick={() => setActiveTermSid(s.id)}
              >
                <span>Terminal {s.id.substring(0, 4)}</span>
                <button
                  className="ch-term-tab-close"
                  onClick={(e) => { e.stopPropagation(); killTerminal(s.id); }}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
            <button className="ch-term-new" onClick={createTerminal}>
              <Plus size={14} /> New
            </button>
          </div>

          {/* Terminal body */}
          <div className="ch-term-body">
            {activeTermSid ? (
              <SimpleTerminal sessionId={activeTermSid} />
            ) : (
              <div className="ch-term-empty">
                <Terminal size={40} />
                <p>No terminal session</p>
                <button onClick={createTerminal}>
                  <Plus size={16} /> Create Terminal
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
