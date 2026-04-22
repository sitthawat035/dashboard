// hooks/useLogStream.ts — Log loading + Socket.IO log streaming
// State now lives in Zustand store, this hook provides actions only
import { useCallback } from 'react';
import { gatewayApi } from '../utils/api';
import { useAppStore } from '../stores/useAppStore';

export function useLogStream() {
  // Read state from Zustand store
  const logData = useAppStore(s => s.logData);
  const updateLogData = useAppStore(s => s.updateLogData);

  const loadLog = useCallback(async (gw: string) => {
    const { ok, data } = await gatewayApi.getLog(gw);
    if (!ok || !data) return;
    
    // Update store directly instead of local state
    updateLogData(gw, {
      log: data.log || [],
      err: data.err || [],
      log_size: data.log_size,
      err_size: data.err_size,
    });
  }, [updateLogData]);

  const loadAllLogs = useCallback(async (agentIds: string[]) => {
    if (!agentIds || agentIds.length === 0) return;
    await Promise.all(agentIds.map(gw => loadLog(gw)));
  }, [loadLog]);

  // Called by socket event: gateway_log_init
  const handleGatewayLogInit = useCallback((data: { agent_id: string; lines: string[] }) => {
    const current = useAppStore.getState().logData[data.agent_id];
    updateLogData(data.agent_id, {
      log: data.lines,
      err: current?.err || [],
      log_size: data.lines.length,
      err_size: current?.err_size || 0,
    });
  }, [updateLogData]);

  // Called by socket event: gateway_log_line
  const handleGatewayLogLine = useCallback((data: { agent_id: string; line: string }) => {
    const current = useAppStore.getState().logData[data.agent_id] || { log: [], err: [] };
    const newLog = [...current.log, data.line].slice(-100);
    
    updateLogData(data.agent_id, {
      log: newLog,
      log_size: newLog.length,
    });
  }, [updateLogData]);

  return {
    logData,
    loadLog,
    loadAllLogs,
    handleGatewayLogInit,
    handleGatewayLogLine,
  };
}
