// components/AgentCard/ChatPanel.tsx — Chat interface with streaming response
import { useRef, useEffect, useState, useCallback } from 'react';
import { useAgentCard } from '../../contexts/AgentCardContext';
import { useSocketEvents } from '../../hooks/useSocketEvents';

interface ChatStreamStart { agent_key: string; session_id: string; timestamp: string; }
interface ChatStreamChunk { agent_key: string; session_id: string; chunk: string; full: string; }
interface ChatStreamComplete { agent_key: string; session_id: string; full_response: string; timestamp: string; }
interface ChatStreamError { error: string; agent_key?: string; session_id?: string; }

const ChatPanel: React.FC = () => {
  const {
    gw, info, chatMessages, chatInput, setChatInput, sendChat,
  } = useAgentCard();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const streamingIndexRef = useRef<number>(-1);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, streamingText]);

  // Socket.IO streaming via useSocketEvents hook
  useSocketEvents({
    onChatStreamStart: useCallback((data: ChatStreamStart) => {
      if (data.agent_key === gw) {
        setIsStreaming(true);
        setStreamingText('');
        streamingIndexRef.current = chatMessages.length;
      }
    }, [gw, chatMessages.length]),

    onChatStreamChunk: useCallback((data: ChatStreamChunk) => {
      if (data.agent_key === gw) {
        setStreamingText(data.full || data.chunk);
      }
    }, [gw]),

    onChatStreamComplete: useCallback((data: ChatStreamComplete) => {
      if (data.agent_key === gw) {
        setIsStreaming(false);
        setStreamingText('');
        streamingIndexRef.current = -1;
      }
    }, [gw]),

    onChatStreamError: useCallback((data: ChatStreamError) => {
      if (!data.agent_key || data.agent_key === gw) {
        setIsStreaming(false);
        setStreamingText('');
        streamingIndexRef.current = -1;
        console.error('Chat stream error:', data.error);
      }
    }, [gw]),
  });

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  };

  // Build display messages including streaming
  const displayMessages = [...chatMessages];
  if (isStreaming && streamingText) {
    displayMessages.push({
      role: 'assistant',
      text: streamingText,
      isStreaming: true,
    });
  }

  return (
    <div className="chat-container">
      <div className="chat-history">
        {displayMessages.length === 0 && !isStreaming ? (
          <div className="chat-placeholder">
            <div className="chat-empty-icon">💬</div>
            <p>No messages yet</p>
            <p className="chat-empty-hint">Send a message to start chatting with {info.name}</p>
          </div>
        ) : (
          displayMessages.map((msg: any, i: number) => (
            <div key={i} className={`chat-msg ${msg.role}${msg.isStreaming ? ' streaming' : ''}`}>
              <div className="msg-header">
                <span className="msg-role">{msg.role === 'user' ? 'You' : msg.role === 'assistant' ? info.name : 'System'}</span>
                <span className="msg-time">{msg.isStreaming ? '● streaming' : new Date().toLocaleTimeString()}</span>
              </div>
              <div className="msg-content">{msg.text}</div>
              {msg.isStreaming && <span className="streaming-cursor">▊</span>}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder={`Message ${info.name}...`}
          value={chatInput}
          onChange={e => setChatInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
        />
        <button className="btn-send" onClick={sendChat} disabled={!chatInput.trim() || isStreaming}>
          {isStreaming ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
