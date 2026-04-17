// components/AgentCard/ChatPanel.tsx — Chat interface with agent
import { useRef, useEffect } from 'react';
import { useAgentCard } from '../../contexts/AgentCardContext';

const ChatPanel: React.FC = () => {
  const {
    info, chatMessages, chatInput, setChatInput, sendChat,
  } = useAgentCard();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {chatMessages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <p>No messages yet</p>
            <p className="chat-empty-hint">Send a message to start chatting with {info.name}</p>
          </div>
        ) : (
          chatMessages.map((msg: any, i: number) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div className="chat-avatar">
                {msg.role === 'user' ? '👤' : msg.role === 'assistant' ? '🤖' : '⚙️'}
              </div>
              <div className="chat-bubble">
                <div className="chat-role">{msg.role === 'user' ? 'You' : msg.role === 'assistant' ? info.name : 'System'}</div>
                <div className="chat-text">{msg.text}</div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          className="chat-input"
          placeholder={`Message ${info.name}...`}
          value={chatInput}
          onChange={e => setChatInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="chat-send-btn" onClick={sendChat} disabled={!chatInput.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
