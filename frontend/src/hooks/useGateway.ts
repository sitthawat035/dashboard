// hooks/useGateway.ts — Gateway control: start/stop/restart, startAll, restartAll, killAll
import { useCallback } from 'react';
import { gatewayApi, systemApi } from '../utils/api';

export function useGateway(loadStatus: () => void, onAuthExpired?: () => void) {
  const control = useCallback(async (gw: string, action: string) => {
    const { status } = await gatewayApi.control(gw, action);
    if (status === 401) {
      onAuthExpired?.();
      return;
    }
    setTimeout(loadStatus, 2500);
  }, [loadStatus, onAuthExpired]);

  const startAll = useCallback(async () => {
    const { status } = await gatewayApi.startAll();
    if (status === 401) { onAuthExpired?.(); return; }
    setTimeout(loadStatus, 3000);
  }, [loadStatus, onAuthExpired]);

  const restartAll = useCallback(async (agentIds: string[]) => {
    for (const gw of agentIds) {
      const { status } = await gatewayApi.control(gw, 'restart');
      if (status === 401) { onAuthExpired?.(); return; }
      await new Promise(r => setTimeout(r, 1800));
    }
    setTimeout(loadStatus, 2500);
  }, [loadStatus, onAuthExpired]);

  const killAll = useCallback(async () => {
    try {
      const { status, data } = await systemApi.killAll();
      if (status === 401) { onAuthExpired?.(); return; }
      if (data?.success) {
        alert('GLOBAL WIPE COMPLETED: ' + data.message);
        loadStatus();
      }
    } catch (e) {
      alert('Error during sweep: ' + e);
    }
  }, [loadStatus, onAuthExpired]);

  return { control, startAll, restartAll, killAll };
}
