// types/ui.ts — UI-related types

export type LogTab = 'log' | 'err' | 'chat';
export type StdoutSubTab = 'gateway_logs' | 'shell';
export type TabId = 'dashboard' | 'mission' | 'agents' | 'terminal' | 'memory' | 'logs' | 'multi' | 'settings';
export type DetailTab = 'console' | 'config';
export type ScanState = 'idle' | 'scanning' | 'done';

export interface TermSession {
  id: string;
  lineCount: number;
  pollRef?: ReturnType<typeof setInterval> | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  text: string;
  timestamp?: string;
}

export interface TabConfig {
  id: TabId;
  label: string;
  icon?: string;
  disabled?: boolean;
}

export interface SidebarItem {
  id: TabId;
  label: string;
  icon: string;
  badge?: number;
  disabled?: boolean;
}

export interface StatCard {
  label: string;
  value: string | number;
  sub?: string;
  icon?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface ConnectionIndicator {
  status: 'connected' | 'disconnected' | 'reconnecting';
  text: string;
  color: string;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  code?: string;
  retry?: () => void;
}

export interface ModalConfig {
  isOpen: boolean;
  title: string;
  content?: React.ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
}

export interface ToastConfig {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  primaryColor: string;
  accentColor: string;
}

export interface LayoutConfig {
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  headerHeight: number;
  contentPadding: number;
}

export interface AnimationConfig {
  duration: number;
  easing: string;
  delay?: number;
}

export interface ResponsiveBreakpoint {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
}
