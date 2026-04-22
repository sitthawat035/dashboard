import React, { useState, useEffect, useRef } from 'react';
import { subagentApi } from '../../utils/api';

interface ConvMessage { ts: string; text: string; }

interface ConversationLogProps {
  agentId: string;
  agentName: string;
}

const ConversationLog: React.FC<ConversationLogProps> = ({ agentId, agentName }) => {
  const [messages, setMessages] = useState<ConvMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = async () => {
    try {
      const { ok, data } = await subagentApi.conversation(agentId);
      if (ok && data) {
        setMessages(data.messages || []);
      }
      setLoading(false);
    } catch {}
  };

  useEffect(() => {
    setLoading(true);
    load();
  }, [agentId]);

  useEffect(() => {
    if (autoRefresh) {
      timerRef.current = setInterval(load, 3000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [autoRefresh, agentId]);

  useEffect(() => {
    if (autoRefresh && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, autoRefresh]);

  if (loading && messages.length === 0) {
    return <div className="conv-loading"><div className="conv-spinner" /><span>Loading conversation…</span></div>;
  }

  if (messages.length === 0) {
    return (
      <div className="conv-empty">
        <div className="conv-empty-icon">💬</div>
        <div className="conv-empty-title">No Conversation Yet</div>
        <div className="conv-empty-sub">{agentName} hasn't logged any conversation to the gateway log file yet.</div>
      </div>
    );
  }

  return (
    <div className="conv-log-wrapper">
      <div className="conv-toolbar">
        <span className="conv-count">{messages.length} messages</span>
        <label className="sa-toggle-label">
          <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
          <span>Auto-refresh</span>
        </label>
      </div>
      <div className="conv-log-scroll" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className="conv-msg-block">
            <div className="conv-msg-ts">{m.ts}</div>
            <pre className="conv-msg-text">{m.text}</pre>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConversationLog;
