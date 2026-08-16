export type NexuXStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'interrupted';

export interface GenerateRequest {
  youtube_url: string;
  target_duration: number;
  aspect_ratio: string;
  subtitle_style: string;
  font: string;
  font_size: number;
  primary_color: string;
  highlight_color: string;
  stroke_color: string;
  stroke_width: number;
  position: 'top' | 'center' | 'bottom';
  animation: string;
  auto_zoom: boolean;
  face_tracking: boolean;
  clip_count: number;
  language?: string | null;
  normalize_audio: boolean;
  emoji_enabled: boolean;
}

export interface NexuXJob {
  job_id: string;
  status: NexuXStatus;
  progress: number;
  stage: string;
  output_path: string | null;
  error: string | null;
  clips: string[];
  broll: false;
  render_meta: Record<string, unknown>[];
  analysis_bundle: Record<string, unknown> | null;
}

const API_BASE = String(import.meta.env.VITE_NEXUX_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText || `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail || detail;
    } catch {
      // Keep the HTTP status when the body is not JSON.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const nexuxApi = {
  baseUrl: API_BASE,
  health: () => request<Record<string, unknown>>('/api/health'),
  styles: () => request<Record<string, unknown>>('/api/styles'),
  generate: (payload: GenerateRequest) => request<NexuXJob>('/api/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  job: (jobId: string) => request<NexuXJob>(`/api/job/${encodeURIComponent(jobId)}`),
  cancel: (jobId: string) => request<{ job_id: string; status: string }>(`/api/job/${encodeURIComponent(jobId)}`, {
    method: 'DELETE',
  }),
  downloadUrl: (jobId: string) => `${API_BASE}/api/download/${encodeURIComponent(jobId)}`,
};
