// src/constants.ts
export const GW_KEYS = ['ace', 'ameri', 'fah', 'pudding', 'alpha'];

export const GW_INFO: Record<string, { name: string; emoji: string; port: number; cls: string }> = {
  ace:     { name: 'Ace',     emoji: '🚀', port: 18889, cls: 'ace' },
  ameri:   { name: 'Ameri',   emoji: '🧠', port: 18890, cls: 'ameri' },
  fah:     { name: 'Fah',     emoji: '💖', port: 20000, cls: 'fah' },
  pudding: { name: 'Pudding', emoji: '🍮', port: 18891, cls: 'pudding' },
  alpha:   { name: 'Alpha',   emoji: '⚙️', port: 10000, cls: 'alpha' },
};

const HOST = window.location.hostname;

// OpenCLAW Gateway REST API endpoints (direct, no Control UI)
export const OPENCLAW_API: Record<string, string> = {
  ace:     `http://${HOST}:18889`,
  ameri:   `http://${HOST}:18890`,
  fah:     `http://${HOST}:20000`,
  pudding: `http://${HOST}:18891`,
  alpha:   `http://${HOST}:10000`,
};
