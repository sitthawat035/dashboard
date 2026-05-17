// hooks/useSocketEvents.ts — Centralized socket event management
// All socket event handlers are managed here to avoid duplication
import { useEffect, useCallback } from 'react';
import socketManager from '../utils/socket';
import { useAppStore } from '../stores/useAppStore';

// ─── Event Payload Types ─────────────────────────────────────────────────────────

interface ChatStreamStart {
  agent_key: string;
  session_id: string;
  timestamp: string;
}

interface ChatStreamChunk {
  agent_key: string;
  session_id: string;
  chunk: string;
  full: string;
}

interface ChatStreamComplete {
  agent_key: string;
  session_id: string;
  full_response: string;
  timestamp: string;
}

interface ChatStreamError {
  error: string;
  agent_key?: string;
  session_id?: string;
}

interface SubagentConversation {
  ts: string;
  text: string;
}

// ─── Options Interface ──────────────────────────────────────────────────────────

interface SocketEventsOptions {
  onAgentStatus?: (data: { agentId: string; status: string }) => void;
  onGatewayLogInit?: (data: { agent_id: string; lines: string[] }) => void;
  onGatewayLogLine?: (data: { agent_id: string; line: string }) => void;
  onGatewayLogLines?: (data: { agent_id: string; lines: string[] }) => void;
  // Chat streaming callbacks
  onChatStreamStart?: (data: ChatStreamStart) => void;
  onChatStreamChunk?: (data: ChatStreamChunk) => void;
  onChatStreamComplete?: (data: ChatStreamComplete) => void;
  onChatStreamError?: (data: ChatStreamError) => void;
  // Subagent conversation callback
  onSubagentConversation?: (data: SubagentConversation) => void;
}

export function useSocketEvents(options: SocketEventsOptions = {}) {
  const setSocketConnected = useAppStore(s => s.setSocketConnected);
  const setSocketReconnecting = useAppStore(s => s.setSocketReconnecting);
  const updateAgent = useAppStore(s => s.updateAgent);

  useEffect(() => {
    socketManager.connect();

    const handleConnect = () => {
      setSocketConnected(true);
      setSocketReconnecting(false);
    };

    const handleDisconnect = (reason: string) => {
      setSocketConnected(false);
      setSocketReconnecting(reason === 'io server disconnect' || reason === 'io client disconnect');
    };

    const handleConnectError = () => setSocketConnected(false);
    const handleReconnect = () => { setSocketConnected(true); setSocketReconnecting(false); };
    const handleReconnectError = () => setSocketReconnecting(true);
    const handleReconnectFailed = () => { setSocketConnected(false); setSocketReconnecting(false); };

    const handleAgentStatus = (data: { agentId: string; status: string }) => {
      updateAgent(data.agentId, { online: data.status === 'online' });
      options.onAgentStatus?.(data);
    };

    const handleGatewayLogInit = (data: { agent_id: string; lines: string[] }) => {
      options.onGatewayLogInit?.(data);
    };

    const handleGatewayLogLine = (data: { agent_id: string; line: string }) => {
      options.onGatewayLogLine?.(data);
    };

    const handleGatewayLogLines = (data: { agent_id: string; lines: string[] }) => {
      options.onGatewayLogLines?.(data);
    };

    // ─── Chat Streaming Handlers ───────────────────────────────────────────────────

    const handleChatStreamStart = (data: ChatStreamStart) => {
      console.log('[Socket] Chat stream started:', data);
      options.onChatStreamStart?.(data);
    };

    const handleChatStreamChunk = (data: ChatStreamChunk) => {
      options.onChatStreamChunk?.(data);
    };

    const handleChatStreamComplete = (data: ChatStreamComplete) => {
      console.log('[Socket] Chat stream complete:', data);
      options.onChatStreamComplete?.(data);
    };

    const handleChatStreamError = (data: ChatStreamError) => {
      console.error('[Socket] Chat stream error:', data);
      options.onChatStreamError?.(data);
    };

    // ─── Subagent Conversation Handler ───────────────────────────────────────────

    const handleSubagentConversation = (data: SubagentConversation) => {
      options.onSubagentConversation?.(data);
    };

    // Register all event handlers
    socketManager.on('connect', handleConnect);
    socketManager.on('disconnect', handleDisconnect);
    socketManager.on('connect_error', handleConnectError);
    socketManager.on('reconnect', handleReconnect);
    socketManager.on('reconnect_error', handleReconnectError);
    socketManager.on('reconnect_failed', handleReconnectFailed);
    socketManager.on('agent:status', handleAgentStatus);
    socketManager.on('gateway_log_init', handleGatewayLogInit);
    socketManager.on('gateway_log_line', handleGatewayLogLine);
    socketManager.on('gateway_log_lines', handleGatewayLogLines);
    // Chat streaming events
    socketManager.on('chat_stream_start', handleChatStreamStart);
    socketManager.on('chat_stream_chunk', handleChatStreamChunk);
    socketManager.on('chat_stream_complete', handleChatStreamComplete);
    socketManager.on('chat_stream_error', handleChatStreamError);
    // Subagent conversation
    socketManager.on('subagent_conversation', handleSubagentConversation);

    if (socketManager.isConnected()) handleConnect();

    return () => {
      // Cleanup all event handlers
      socketManager.off('connect', handleConnect);
      socketManager.off('disconnect', handleDisconnect);
      socketManager.off('connect_error', handleConnectError);
      socketManager.off('reconnect', handleReconnect);
      socketManager.off('reconnect_error', handleReconnectError);
      socketManager.off('reconnect_failed', handleReconnectFailed);
      socketManager.off('agent:status', handleAgentStatus);
      socketManager.off('gateway_log_init', handleGatewayLogInit);
      socketManager.off('gateway_log_line', handleGatewayLogLine);
      socketManager.off('gateway_log_lines', handleGatewayLogLines);
      // Chat streaming events
      socketManager.off('chat_stream_start', handleChatStreamStart);
      socketManager.off('chat_stream_chunk', handleChatStreamChunk);
      socketManager.off('chat_stream_complete', handleChatStreamComplete);
      socketManager.off('chat_stream_error', handleChatStreamError);
      // Subagent conversation
      socketManager.off('subagent_conversation', handleSubagentConversation);
    };
  }, [setSocketConnected, setSocketReconnecting, updateAgent, options]);

  // Helper to subscribe to log streams
  const subscribeToLogStream = useCallback((agentId: string) => {
    socketManager.emit('join_log_stream', { agent_id: agentId });
  }, []);

  const unsubscribeFromLogStream = useCallback((agentId: string) => {
    socketManager.emit('leave_log_stream', { agent_id: agentId });
  }, []);

  return {
    subscribeToLogStream,
    unsubscribeFromLogStream,
    isConnected: () => socketManager.isConnected(),
  };
}
