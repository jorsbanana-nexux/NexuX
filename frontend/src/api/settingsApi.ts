/**
 * NexuX V9.7 — Settings API client.
 * Mirrors backend/api_v97_settings.py (/api/settings/*).
 */

const API_BASE = String(
  import.meta.env.VITE_NEXUX_API_URL ?? 'http://127.0.0.1:8000',
).replace(/\/$/, '');

const API_KEY = String(import.meta.env.VITE_NEXUX_API_KEY ?? '');

export interface NexuxSettings {
  transcription_model: string;
  language: string | null;
  diarization: boolean;
  batch_size: number;
  word_timestamps: boolean;
  proxy_url: string;
  player_clients: string;
  auto_update_ytdlp: boolean;
}

export interface ModelVariantMeta {
  label: string;
  size_approx: string;
  description: string;
}

export interface SettingsResponse {
  settings: NexuxSettings;
  variants: Record<string, ModelVariantMeta>;
  env: { HF_TOKEN_set: boolean; has_gpu: boolean };
}

export interface ModelInfo {
  id: string;
  label: string;
  size_approx: string;
  description: string;
  downloaded: boolean;
  active: boolean;
}

export interface ModelsResponse {
  whisperx_installed: boolean;
  models: ModelInfo[];
  preload: Record<string, PreloadStatus>;
}

export interface PreloadStatus {
  status: 'downloading' | 'done' | 'error';
  variant: string;
  message: string;
}

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
      // keep status text
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const settingsApi = {
  get: () => request<SettingsResponse>('/api/settings'),

  patch: (updates: Partial<NexuxSettings>) =>
    request<{ ok: boolean; settings: NexuxSettings }>('/api/settings', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),

  models: () => request<ModelsResponse>('/api/settings/models'),

  preload: (variant: string, installWhisperx = false) =>
    request<{ ok: boolean; job: string; variant: string }>(
      '/api/settings/models/preload',
      { method: 'POST', body: JSON.stringify({ variant, install_whisperx: installWhisperx }) },
    ),

  preloadStatus: (jobId: string) =>
    request<PreloadStatus>(`/api/settings/models/preload/${encodeURIComponent(jobId)}`),

  reset: () =>
    request<{ ok: boolean; settings: NexuxSettings }>('/api/settings/reset', {
      method: 'DELETE',
    }),
};
