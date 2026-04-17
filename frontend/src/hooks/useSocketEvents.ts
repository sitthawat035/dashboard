// hooks/useSocketEvents.ts — Centralized socket event management
// All socket event handlers are managed here to avoid duplication
import { useEffect, useCallback, useRef } from 'react';
import socketManager from '../utils/socket';
import { useAppStore } from '../stores/useAppStore';

interface SocketEventsOptions {
  onAgentStatus?: (data: { agentId: string; status: string }) => void;
  onGatewayLogInit?: (data: { agent_id: string; lines: string[] }) => void;
  onGatewayLogLine?: (data: { agent_id: string; line: string }) => void;
  onGatewayLogLines?: (data: { agent_id: string; lines: string[] }) => void;
  onTerminalCreated?: (data: { session_id: string }) => void;
}

export function useSocketEvents(options: SocketEventsOptions = {}) {
  const setSocketConnected = useAppStore(s => s.setSocketConnected);
  const setSocketReconnecting = useAppStore(s => s.setSocketReconnecting);
  const updateAgent = useAppStore(s => s.updateAgent);

  const terminalListenersRef = useRef<{ [key: string]: Function }>({});

  const setupTerminalListener = useCallback((sid: string) => {
    if (terminalListenersRef.current[sid]) return;
    
    const handler = (output: string) => {
      const writeFn = (window as any).__termWriteOutput;
      if (typeof writeFn === 'function') writeFn(output);
    };
    
    terminalListenersRef.current[sid] = handler;
    socketManager.on(`terminal_output_${sid}`, handler);
  }, []);

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

    const handleTerminalCreated = (data: { session_id: string }) => {
      setupTerminalListener(data.session_id);
      options.onTerminalCreated?.(data);
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
    socketManager.on('terminal_created', handleTerminalCreated);

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
      socketManager.off('terminal_created', handleTerminalCreated);

      // Cleanup terminal listeners
      Object.keys(terminalListenersRef.current).forEach(sid => {
        socketManager.off(`terminal_output_${sid}`, terminalListenersRef.current[sid]);
      });
      terminalListenersRef.current = {};
    };
  }, [setSocketConnected, setSocketReconnecting, updateAgent, options, setupTerminalListener]);

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
