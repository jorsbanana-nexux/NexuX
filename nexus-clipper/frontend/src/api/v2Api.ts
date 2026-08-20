/**
 * NexuX V9.5 — V2 API Client (Mode-aware)
 * 
 * Frontend API client for the unified dual-mode system.
 */

const API_BASE = String(
  import.meta.env.VITE_NEXUX_API_URL ?? 'http://127.0.0.1:8000',
).replace(/\/$/, '');
const API_KEY = String(import.meta.env.VITE_NEXUX_API_KEY ?? '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (API_KEY) headers['X-API-Key'] = API_KEY;
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json())?.detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ── Types ──

export type NexuXMode = 'podcast' | 'creative';

export interface ModeInfo {
  mode: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  requires_url: boolean;
  requires_keyword: boolean;
  features: string[];
}

export interface GenerateV2Request {
  mode: NexuXMode;
  youtube_url?: string;
  keyword?: string;
  target_duration?: number;
  clip_count?: number;
  aspect_ratio?: string;
  subtitle_style?: string;
  auto_zoom?: boolean;
  face_tracking?: boolean;
  language?: string;
  remove_fillers?: boolean;
  voice_enabled?: boolean;
  voice_name?: string;
  sfx_enabled?: boolean;
  bgm_enabled?: boolean;
  max_sources?: number;
  color_grade?: string;
}

export interface GenerateV2Response {
  job_id: string;
  mode: string;
  status: string;
  message: string;
}

export interface KeywordExpansion {
  original: string;
  expanded: string[];
  niche: string | null;
  primary_terms: string[];
  secondary_terms: string[];
}

// ── API ──

export const v2Api = {
  getModes: () => request<ModeInfo[]>('/api/v2/modes'),
  
  getModeFeatures: (mode: string) =>
    request<ModeInfo>(`/api/v2/modes/${encodeURIComponent(mode)}/features`),

  generate: (payload: GenerateV2Request) =>
    request<GenerateV2Response>('/api/v2/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  expandKeyword: (keyword: string, maxTerms = 15) =>
    request<KeywordExpansion>(
      `/api/v2/keyword/expand?keyword=${encodeURIComponent(keyword)}&max_terms=${maxTerms}`,
    ),
};
