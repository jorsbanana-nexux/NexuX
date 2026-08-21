/**
 * NexuX V9.5 — Dual-Mode API Client
 * ==================================
 * Typed client for the unified /api/v2/* endpoints:
 * - GET  /api/v2/modes                  → list both modes + features
 * - GET  /api/v2/modes/{mode}/features  → single mode details
 * - GET  /api/v2/keyword/expand         → preview keyword expansion
 * - POST /api/v2/generate               → start generation (podcast or creative)
 */

export type NexuXMode = 'podcast' | 'creative';

export interface V2ModeInfo {
  mode: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  requires_url: boolean;
  requires_keyword: boolean;
  features: string[];
}

export interface V2GenerateRequest {
  mode: NexuXMode;
  // Podcast
  youtube_url?: string;
  target_duration?: number;
  clip_count?: number;
  aspect_ratio?: string;
  subtitle_style?: string;
  auto_zoom?: boolean;
  face_tracking?: boolean;
  language?: string | null;
  remove_fillers?: boolean;
  // Creative
  keyword?: string;
  voice_enabled?: boolean;
  voice_name?: string;
  sfx_enabled?: boolean;
  bgm_enabled?: boolean;
  max_sources?: number;
  // Shared
  color_grade?: string;
}

export interface V2GenerateResponse {
  job_id: string;
  mode: string;
  status: string;
  message: string;
}

export interface V2KeywordExpansion {
  original: string;
  expanded: string[];
  niche: string | null;
  primary_terms: string[];
  secondary_terms: string[];
}

const API_BASE = String(
  import.meta.env.VITE_NEXUX_API_URL ?? 'http://127.0.0.1:8000',
).replace(/\/$/, '');

const API_KEY = String(import.meta.env.VITE_NEXUX_API_KEY ?? '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
  };
  if (API_KEY) headers['X-API-Key'] = API_KEY;

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    let detail = response.statusText || `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail || detail;
    } catch {
      // Keep the HTTP status for non-JSON responses.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export const v2Api = {
  modes: () => request<V2ModeInfo[]>('/api/v2/modes'),

  modeFeatures: (mode: string) =>
    request<V2ModeInfo>(`/api/v2/modes/${encodeURIComponent(mode)}/features`),

  expandKeyword: (keyword: string, maxTerms = 15) =>
    request<V2KeywordExpansion>(
      `/api/v2/keyword/expand?keyword=${encodeURIComponent(keyword)}&max_terms=${maxTerms}`,
    ),

  generate: (payload: V2GenerateRequest) =>
    request<V2GenerateResponse>('/api/v2/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
