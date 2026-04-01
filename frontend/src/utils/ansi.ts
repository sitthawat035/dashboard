// src/utils/ansi.ts

// ── ANSI Code Handler ──
const FG_COLOR: Record<number, string> = {
  30:'#888', 31:'#ff7b72', 32:'#7ee787', 33:'#e3b341',
  34:'#79c0ff', 35:'#d2a8ff', 36:'#39c5cf', 37:'#c9d1d9',
  90:'#484f58', 91:'#ffa198', 92:'#56d364', 93:'#f0c674',
  94:'#58a6ff', 95:'#bc8cff', 96:'#56d4dd', 97:'#f0f6fc',
};

const BG_COLOR: Record<number, string> = {
  40:'#000', 41:'#7f1d1d', 42:'#14532d', 43:'#713f12',
  44:'#1e3a5f', 45:'#581c87', 46:'#164e63', 47:'#374151',
};

function ansi256ToHex(n: number): string {
  if (n < 16) {
    const basic: Record<number, string> = {
      0:'#000',1:'#800000',2:'#008000',3:'#808000',
      4:'#000080',5:'#800080',6:'#008080',7:'#c0c0c0',
      8:'#808080',9:'#ff0000',10:'#00ff00',11:'#ffff00',
      12:'#0000ff',13:'#ff00ff',14:'#00ffff',15:'#ffffff',
    };
    return basic[n] || '#fff';
  }
  if (n < 232) {
    const i = n - 16;
    const r = Math.floor(i / 36) * 51;
    const g = Math.floor((i % 36) / 6) * 51;
    const b = (i % 6) * 51;
    return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
  }
  const gray = 8 + (n - 232) * 10;
  return `#${gray.toString(16).repeat(3)}`;
}

export function ansiToHtml(text: string): string {
  let openSpan = false;

  const converted = text.replace(/\x1b\[([\d;]*)m/g, (_match, codes: string) => {
    if (!codes || codes === '0' || codes === '00') {
      if (openSpan) { openSpan = false; return '</span>'; }
      return '';
    }
    const arr = codes.split(';').map(Number);
    let styles: string[] = [];
    let needsOpen = false;

    for (let i = 0; i < arr.length; i++) {
      const c = arr[i];
      if (c === 0) { if (openSpan) { openSpan = false; return '</span>'; } continue; }
      if (c === 1) { styles.push('font-weight:bold'); needsOpen = true; continue; }
      if (c === 2) { styles.push('opacity:0.6'); needsOpen = true; continue; }
      if (c === 3) { styles.push('font-style:italic'); needsOpen = true; continue; }
      if (c === 4) { styles.push('text-decoration:underline'); needsOpen = true; continue; }
      if (FG_COLOR[c]) { styles.push(`color:${FG_COLOR[c]}`); needsOpen = true; continue; }
      if (BG_COLOR[c]) { styles.push(`background:${BG_COLOR[c]}`); needsOpen = true; continue; }
      if (c === 38 && arr[i+1] === 5) { styles.push(`color:${ansi256ToHex(arr[i+2])}`); needsOpen = true; i += 2; continue; }
      if (c === 48 && arr[i+1] === 5) { styles.push(`background:${ansi256ToHex(arr[i+2])}`); needsOpen = true; i += 2; continue; }
      if (c === 38 && arr[i+1] === 2) { styles.push(`color:rgb(${arr[i+2]},${arr[i+3]},${arr[i+4]})`); needsOpen = true; i += 4; continue; }
      if (c === 48 && arr[i+1] === 2) { styles.push(`background:rgb(${arr[i+2]},${arr[i+3]},${arr[i+4]})`); needsOpen = true; i += 4; continue; }
      if (c === 39) { styles.push('color:inherit'); continue; }
      if (c === 49) { styles.push('background:transparent'); continue; }
    }
    if (needsOpen && styles.length > 0) {
      if (openSpan) return `</span><span style="${styles.join(';')}">`;
      openSpan = true;
      return `<span style="${styles.join(';')}">`;
    }
    return '';
  });

  return openSpan ? converted + '</span>' : converted;
}

// ── Log Syntax Highlighter ──
// Preserves ANSI colors from gateway FIRST, then adds syntax highlighting only if no ANSI present
export function highlightLog(line: string): string {
  if (!line) return '';

  // 1. Process ANSI color codes FIRST to preserve original gateway colors
  const hasAnsi = line.includes('\x1b[');
  if (hasAnsi) {
    // ANSI-first: convert ANSI to HTML inline styles, preserve original colors
    let html = esc(line);
    if (html.includes('\x1b[')) {
      html = ansiToHtml(html);
    }
    // Only add minimal highlighting for timestamps and components (non-invasive)
    html = html.replace(
      /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2})/g,
      '<span class="hl-timestamp">$1</span>'
    );
    html = html.replace(
      /(\[\d{2}:\d{2}:\d{2}\])/g,
      '<span class="hl-timestamp">$1</span>'
    );
    return html;
  }

  // 2. No ANSI codes - apply full syntax highlighting
  let html = esc(line);

  // Quoted strings
  html = html.replace(
    /(&quot;[^&]*&quot;|"[^"]*"|'[^']*')/g,
    '<span class="hl-string">$1</span>'
  );

  // Timestamps
  html = html.replace(
    /(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2})/g,
    '<span class="hl-timestamp">$1</span>'
  );
  html = html.replace(
    /(\[\d{2}:\d{2}:\d{2}\])/g,
    '<span class="hl-timestamp">$1</span>'
  );

  // Component tags
  html = html.replace(
    /\[([a-zA-Z][\w\-:]*)\]/g,
    '<span class="hl-component">[$1]</span>'
  );

  // Error / Fatal / Failed
  html = html.replace(
    /\b(error|fatal|failed|fail|crash|exception|reject|denied|timeout|refused)\b/gi,
    '<span class="hl-error">$1</span>'
  );

  // Warning
  html = html.replace(
    /\b(warn|warning|deprecated|stale|ignored)\b/gi,
    '<span class="hl-warn">$1</span>'
  );

  // Success
  html = html.replace(
    /\b(ok|success|connected|started|listening|running|ready|active|online|mounted)\b/gi,
    '<span class="hl-success">$1</span>'
  );

  // URLs
  html = html.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<span class="hl-url">$1</span>'
  );

  // IP:Port
  html = html.replace(
    /\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})\b/g,
    '<span class="hl-ipport">$1</span>'
  );

  // Port numbers
  html = html.replace(
    /\b(port|Port)\s*[=:]\s*(\d+)/g,
    '$1=<span class="hl-number">$2</span>'
  );

  // Status icons
  html = html.replace(
    /(⚠️|✅|❌|🚀|🔗|⚡|➡️|→)/g,
    '<span class="hl-icon">$1</span>'
  );

  return html;
}

export function esc(s: string) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

export function classifyLog(line: string): string {
  const l = line.toLowerCase();
  if (l.includes('error') || l.includes('fatal') || l.includes('fail') || l.includes('crash')) return 'log-error';
  if (l.includes('warn') || l.includes('deprecated')) return 'log-warn';
  if (l.includes('ok') || l.includes('connected') || l.includes('started') || l.includes('listening') || l.includes('ready')) return 'log-success';
  if (l.includes('debug') || l.includes('trace')) return 'log-debug';
  return '';
}
