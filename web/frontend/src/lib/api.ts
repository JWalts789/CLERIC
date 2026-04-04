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
export async function startResearch(
  query: string,
  settings?: { model?: string; maxResults?: number },
): Promise<string> {
  const body: Record<string, any> = { query };
  if (settings?.model) body.model = settings.model;
  if (settings?.maxResults) body.max_search_results = settings.maxResults;

  const response = await fetch(`${API_BASE}/api/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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

// ============================================================
// History API
// ============================================================

export interface HistoryItem {
  id: string;
  query: string;
  status: string;
  overall_grade: string;
  created_at: string;
  duration_seconds: number;
  total_tokens: number;
}

export interface HistoryResponse {
  results: HistoryItem[];
  total: number;
}

export interface FullHistoryResult {
  id: string;
  query: string;
  status: string;
  result: any;
  mermaid_diagrams: Record<string, string>;
  created_at: string;
  duration_seconds: number;
  overall_grade: string;
  total_tokens_in: number;
  total_tokens_out: number;
}

/**
 * Fetch paginated history of past research results.
 */
export async function fetchHistory(
  limit: number = 20,
  offset: number = 0,
  search?: string,
): Promise<HistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (search) params.set('search', search);

  const response = await fetch(`${API_BASE}/api/history?${params}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * Fetch a single full result by ID.
 */
export async function fetchResult(id: string): Promise<FullHistoryResult> {
  const response = await fetch(`${API_BASE}/api/history/${id}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * Delete a stored result by ID.
 */
export async function deleteResult(id: string): Promise<{ deleted: boolean }> {
  const response = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// ============================================================
// Export API
// ============================================================

/**
 * Download a Markdown export of a result.
 */
export async function exportMarkdown(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/export/${id}/markdown`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'cleric_report.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Download a JSON export of a result.
 */
export async function exportJson(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/export/${id}/json`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'cleric_data.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
