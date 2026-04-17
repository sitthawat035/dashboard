// components/AgentCard/ChatPanel.tsx — Chat conversation UI
interface ChatPanelProps {
  agentName: string;
  chatMessages: any[];
  chatInput: string;
  setChatInput: (val: string) => void;
  onSendChat: () => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  agentName, chatMessages, chatInput, setChatInput, onSendChat,
}) => {
  return (
    <div className="chat-container">
      <div className="chat-history">
        {chatMessages.length === 0 && <div className="chat-placeholder">💬 Start a conversation with {agentName}...</div>}
        {chatMessages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <div className="msg-header">
              <span className="msg-role">{m.role === 'user' ? 'YOU' : agentName}</span>
              <span className="msg-time">{new Date().toLocaleTimeString()}</span>
            </div>
            <div className="msg-content">{m.text}</div>
          </div>
        ))}
      </div>
      <div className="chat-input-row">
        <input value={chatInput} onChange={e => setChatInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && onSendChat()} placeholder="Type a message to agent..." />
        <button className="btn-send" onClick={onSendChat} disabled={!chatInput.trim()}>SEND</button>
      </div>
    </div>
  );
};

export default ChatPanel;
