// src/constants.ts
// This file is now light — most data is fetched dynamically from /api/status
export const GW_KEYS: string[] = []; 

const HOST = window.location.hostname;
export const GET_GATEWAY_URL = (port: number) => `http://${HOST}:${port}`;
