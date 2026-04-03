// ============================================================
// C.L.E.R.I.C. — API Client
// ============================================================

import type { WSEvent } from './types';

const API_BASE = import.meta.env.VITE_API_URL || '';
const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;

/**
 * Start a research pipeline by submitting a query.
 * Returns the job ID for WebSocket tracking.
 */
export async function startResearch(query: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.job_id;
}

/**
 * Connect to the WebSocket for real-time pipeline updates.
 */
export function connectWebSocket(
  jobId: string,
  onEvent: (event: WSEvent) => void,
  onClose?: () => void,
  onError?: (error: Event) => void,
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/${jobId}`);

  ws.onmessage = (messageEvent) => {
    try {
      const event: WSEvent = JSON.parse(messageEvent.data);
      onEvent(event);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onclose = () => {
    onClose?.();
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError?.(error);
  };

  return ws;
}
