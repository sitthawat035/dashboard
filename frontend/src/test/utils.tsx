// src/test/utils.tsx — Test utilities
import type { ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Custom render function with providers
function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, {
    ...options,
  });
}

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };
export { userEvent };

// Mock data helpers
export const mockAgent = {
  id: 'test-agent',
  name: 'Test Agent',
  emoji: '🤖',
  port: 10000,
  online: true,
  color: '#00ff00',
};

export const mockLogData = {
  log: ['Line 1', 'Line 2', 'Line 3'],
  err: ['Error 1'],
  log_size: 3,
  err_size: 1,
};

export const mockChatMessage = {
  role: 'user' as const,
  text: 'Hello, agent!',
};

export const mockSubagentLog = {
  id: 'subagent-1',
  agent: 'test-agent',
  session_key: 'session-1',
  task: 'Test task',
  status: 'running' as const,
  timestamp: '2024-01-01T00:00:00Z',
};

// Wait helper
export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock API response helper
export function mockApiResponse<T>(data: T, ok = true, status = 200) {
  return {
    ok,
    status,
    data,
  };
}

// Mock socket event helper
export function mockSocketEvent(event: string, data: unknown) {
  return {
    event,
    data,
    timestamp: new Date().toISOString(),
  };
}
