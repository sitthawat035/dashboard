// hooks/useSubagents.ts — Subagent log polling
// State now lives in Zustand store, this hook provides actions only
import { useCallback } from 'react';
import { subagentApi } from '../utils/api';
import { useAppStore } from '../stores/useAppStore';

export function useSubagents() {
  // Read state from Zustand store
  const subagentLogs = useAppStore(s => s.subagentLogs);
  const setSubagentLogs = useAppStore(s => s.setSubagentLogs);

  const loadSubagentLogs = useCallback(async () => {
    const { ok, data } = await subagentApi.stream();
    if (ok && data) {
      // Update store directly instead of local state
      setSubagentLogs(data.subagents || []);
    }
  }, [setSubagentLogs]);

  return { subagentLogs, loadSubagentLogs };
}
