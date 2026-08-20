/**
 * NexuX V9.5 — Editor API Client
 * 
 * Frontend API client for the post-render personalization editor.
 * Connects to /api/editor/* endpoints.
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

export interface CreatorTemplate {
  id: string;
  name: string;
  creator: string;
  description: string;
  badge: string;
  badge_color: string;
  style_id: string;
  animation: string;
  zoom_style: string;
  color_grade: string;
  speed_ramp: boolean;
  speed_ramp_type: string;
}

export interface SubtitleStylePreset {
  id: string;
  name: string;
  font: string;
  font_size: number;
  primary: string;
  highlight: string;
  position: string;
  animation: string;
}

export interface EffectOption {
  id: string;
  name: string;
  description: string;
}

export interface EffectsCatalog {
  zoom_styles: EffectOption[];
  color_grades: EffectOption[];
  speed_ramp_types: EffectOption[];
  animations: EffectOption[];
  positions: EffectOption[];
  aspect_ratios: { id: string; name: string; w: number; h: number }[];
}

export interface PersonalizationRequest {
  subtitle_style?: string;
  font?: string;
  font_size?: number;
  primary_color?: string;
  highlight_color?: string;
  stroke_color?: string;
  stroke_width?: number;
  position?: string;
  animation?: string;
  highlight_words?: boolean;
  show_emojis?: boolean;
  bg_bar?: boolean;
  bg_opacity?: number;

  zoom_style?: string;
  zoom_level?: number;
  color_grade?: string;
  speed_ramp?: boolean;
  speed_ramp_type?: string;

  aspect_ratio?: string;
  auto_reframe?: boolean;
  face_tracking?: boolean;

  bgm_volume?: number;
  voice_volume?: number;
  normalize_audio?: boolean;
  bass_boost?: boolean;
  sfx_enabled?: boolean;

  watermark_text?: string;
  watermark_position?: string;
  show_watermark?: boolean;

  trim_start?: number;
  trim_end?: number;

  template_id?: string;
  overlays?: Array<Record<string, unknown>>;
}

export interface ReRenderResponse {
  status: string;
  clip_index?: number;
  output_url: string;
  changes_applied: string[];
}

export interface ClipDetails {
  job_id: string;
  clip_index: number;
  clip_url: string;
  render_meta: Record<string, unknown>;
  analysis: Record<string, unknown> | null;
  duration: number;
  transcript: Array<Record<string, unknown>>;
}

export interface ClipTranscript {
  job_id: string;
  clip_index: number;
  segments: Array<{
    id: string;
    speaker: string;
    start: number;
    end: number;
    text: string;
    words: Array<Record<string, unknown>>;
  }>;
  total_segments: number;
}

// ── API ──

export const editorApi = {
  getTemplates: () =>
    request<{ templates: CreatorTemplate[]; count: number }>('/api/editor/templates'),

  getStyles: () =>
    request<{ styles: SubtitleStylePreset[]; count: number }>('/api/editor/styles'),

  getEffects: () =>
    request<EffectsCatalog>('/api/editor/effects'),

  getClipDetails: (jobId: string, clipIdx: number) =>
    request<ClipDetails>(`/api/editor/clip/${encodeURIComponent(jobId)}/${clipIdx}`),

  getClipTranscript: (jobId: string, clipIdx: number) =>
    request<ClipTranscript>(`/api/editor/clip/${encodeURIComponent(jobId)}/${clipIdx}/transcript`),

  previewRender: (jobId: string, clipIdx: number, payload: {
    subtitle_style?: string;
    zoom_style?: string;
    color_grade?: string;
    aspect_ratio?: string;
    preview_duration?: number;
  }) =>
    request<{ preview_url: string; render_time: number }>(
      `/api/editor/preview/${encodeURIComponent(jobId)}/${clipIdx}`,
      { method: 'POST', body: JSON.stringify(payload) },
    ),

  reRenderClip: (jobId: string, clipIdx: number, settings: PersonalizationRequest) =>
    request<ReRenderResponse>(
      `/api/editor/rerender/${encodeURIComponent(jobId)}/${clipIdx}`,
      { method: 'POST', body: JSON.stringify(settings) },
    ),

  reRenderAll: (jobId: string, settings: PersonalizationRequest) =>
    request<{ status: string; clips_rendered: number; output_urls: string[]; changes_applied: string[] }>(
      `/api/editor/rerender/${encodeURIComponent(jobId)}/all`,
      { method: 'POST', body: JSON.stringify(settings) },
    ),
};
