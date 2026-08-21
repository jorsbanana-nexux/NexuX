export type NexuXStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'interrupted';

export interface GenerateRequest {
  // Core fields (required)
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

  // Backend-managed fields (optional, defaults applied server-side)
  scene_detection?: boolean;
  screen_detection?: boolean;
  diarization?: boolean;
  color_grade?: string;
  video_codec?: string;
  audio_codec?: string;
  ai_scoring?: boolean;
  webhook_url?: string | null;

  // Advanced V8+ fields
  clip_prompt?: string | null;
  genre?: string;
  remove_fillers_pauses?: boolean;
  pause_threshold?: number;
  voice_over?: boolean;
  voice_over_text?: string | null;
  voice_style?: string;
  publish_platforms?: string[] | null;
  manual_ranges?: Array<{ start: number; end: number }> | null;
}

export interface RenderMeta {
  candidate_id?: string;
  timeline?: Record<string, unknown>;
  render?: Record<string, unknown>;
  editorial_rank?: number;
  editorial_signals?: Record<string, unknown>;
  editorial_evidence?: string;
  virality?: number;
  prompt_relevance?: number;
  genre?: string;
  dynamic_layout?: Record<string, unknown>;
  retrieval?: Record<string, unknown>;
  voiceover?: string | null;
}

export interface CritiqueReport {
  revision_required: boolean;
  issues: Array<{ severity: string; message: string }>;
}

export interface PublishPlan {
  platforms: string[];
  metadata: Record<string, unknown>;
}

export interface NexuXJob {
  job_id: string;
  status: NexuXStatus;
  progress: number;
  stage: string;
  output_path: string | null;
  error: string | null;
  created_at: string;
  clips: string[];
  broll: false;
  render_meta: RenderMeta[];
  analysis_bundle: Record<string, unknown> | null;
  critique?: CritiqueReport | null;
  revision?: { requested: boolean; actions: unknown[]; attempt: number } | null;
  publish_plan?: PublishPlan | null;
  editorial_decision?: Record<string, unknown> | null;
}

export interface NexuXHealth {
  status: string;
  canonical_runtime?: boolean;
  canonical_engine?: string;
  broll?: boolean;
  auth_enabled?: boolean;
  db_connected?: boolean;
  [key: string]: unknown;
}

export interface NexuXStyles {
  subtitle_styles: Array<{
    id: string;
    name: string;
    preview?: Record<string, unknown>;
  }>;
  aspect_ratios: string[];
  animations?: string[];
  positions?: string[];
  color_grades?: string[];
  video_codecs?: string[];
  audio_codecs?: string[];
  broll?: boolean;
  [key: string]: unknown;
}

export interface NexuXVision {
  job_id: string;
  analysis_bundle?: Record<string, unknown>;
  media?: Record<string, unknown>;
  scenes?: unknown[];
  subjects?: unknown[];
  quality?: Record<string, unknown>;
  source?: string;
}

export interface NexuXRenderQA {
  verdict?: string;
  [key: string]: unknown;
}

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

  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

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

export const nexuxApi = {
  baseUrl: API_BASE,
  health: () => request<NexuXHealth>('/api/health'),
  styles: () => request<NexuXStyles>('/api/styles'),

  // V9.5: Local video upload → returns local:// token usable as youtube_url
  upload: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const headers: Record<string, string> = {};
    if (API_KEY) headers['X-API-Key'] = API_KEY;
    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (!response.ok) {
      let detail = response.statusText || `HTTP ${response.status}`;
      try {
        const body = await response.json();
        detail = body?.detail || detail;
      } catch { /* keep status */ }
      throw new Error(detail);
    }
    return response.json() as Promise<{
      status: string;
      local_url: string;
      original_name: string;
      size_mb: number;
    }>;
  },
  generate: (payload: GenerateRequest) =>
    request<NexuXJob>('/api/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  job: (jobId: string) =>
    request<NexuXJob>(`/api/job/${encodeURIComponent(jobId)}`),
  jobs: (status?: string, limit?: number, offset?: number) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (limit) params.set('limit', String(limit));
    if (offset) params.set('offset', String(offset));
    const qs = params.toString();
    return request<{ total: number; jobs: NexuXJob[] }>(
      `/api/jobs${qs ? `?${qs}` : ''}`,
    );
  },
  cancel: (jobId: string) =>
    request<{ job_id: string; status: string }>(
      `/api/job/${encodeURIComponent(jobId)}`,
      { method: 'DELETE' },
    ),
  vision: (jobId: string) =>
    request<NexuXVision>(`/api/vision/${encodeURIComponent(jobId)}`),
  renderQA: (jobId: string) =>
    request<NexuXRenderQA>(`/api/render-qa/${encodeURIComponent(jobId)}`),
  critic: (jobId: string) =>
    request<{ job_id: string; critique: CritiqueReport; revision: Record<string, unknown> }>(
      `/api/critic/${encodeURIComponent(jobId)}`,
    ),
  publishPlan: (jobId: string) =>
    request<{ job_id: string; publish_plan: PublishPlan }>(
      `/api/publish/${encodeURIComponent(jobId)}`,
    ),
  publishEvent: (jobId: string, platform: string) =>
    request<{ job_id: string; platform: string; status: string }>(
      `/api/publish/${encodeURIComponent(jobId)}/${encodeURIComponent(platform)}`,
      { method: 'POST' },
    ),
  analytics: (jobId: string) =>
    request<Record<string, unknown>>(`/api/analytics/${encodeURIComponent(jobId)}`),
  downloadUrl: (jobId: string) => {
    const base = `${API_BASE}/api/download/${encodeURIComponent(jobId)}`;
    return API_KEY ? `${base}?key=${encodeURIComponent(API_KEY)}` : base;
  },
  // V8.5: Re-render clip with personalization settings from ClipEditorStudio
  rerenderClip: (jobId: string, clipIndex: number, settings: Record<string, unknown>) =>
    request<NexuXJob>(`/api/rerender/${encodeURIComponent(jobId)}/${clipIndex}`, {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
  // V8.5: Virality scores
  virality: (jobId: string) =>
    request<Record<string, unknown>>(`/api/virality/${encodeURIComponent(jobId)}`),
  // V8.5: Caption quality
  captionQuality: (jobId: string) =>
    request<Record<string, unknown>>(`/api/caption-quality/${encodeURIComponent(jobId)}`),
  // V8.5: Hook analysis
  hooks: (jobId: string) =>
    request<Record<string, unknown>>(`/api/hooks/${encodeURIComponent(jobId)}`),
  // V8.5: Auto-reframe
  reframe: (jobId: string) =>
    request<Record<string, unknown>>(`/api/reframe/${encodeURIComponent(jobId)}`),
  // V8.5: Supported platforms
  platforms: () =>
    request<{ platforms: Record<string, unknown>[] }>('/api/platforms'),

  // V9.0: Re-render with draggable overlay elements (TimelineEditorStudio)
  rerenderWithOverlays: (jobId: string, clipIndex: number, payload: Record<string, unknown>) =>
    request<{ status: string; output_url: string; changes_applied: string[] }>(
      `/api/rerender/${encodeURIComponent(jobId)}/${clipIndex}/overlays`,
      { method: 'POST', body: JSON.stringify(payload) },
    ),

  // V9.0: Repair / self-heal diagnostics
  repairDiagnose: () =>
    request<{ issues: { id: string; label: string; status: string; detail: string }[] }>('/api/repair/diagnose'),
  repairFixAll: () =>
    request<{ fixed: number; results: { id: string; label: string; status: string; detail: string }[] }>(
      '/api/repair/fix-all',
      { method: 'POST' },
    ),

  // V9.0: Real-time FFmpeg preview
  previewRender: (jobId: string, clipIndex: number, payload: Record<string, unknown>) =>
    request<{ preview_url: string; render_time: number }>(
      `/api/preview-render/${encodeURIComponent(jobId)}/${clipIndex}`,
      { method: 'POST', body: JSON.stringify(payload) },
    ),
};

export function buildOutputUrl(outputPath: string | null): string | null {
  if (!outputPath) return null;
  if (/^https?:\/\//i.test(outputPath)) return outputPath;
  return `${API_BASE}${outputPath.startsWith('/') ? '' : '/'}${outputPath}`;
}

/**
 * Poll a job until it reaches a terminal state.
 * Calls onUpdate on each poll, onFinish when terminal.
 * Returns a stop function to cancel polling.
 */
export function startJobPolling(
  jobId: string,
  onUpdate: (job: NexuXJob) => void,
  onFinish: (job: NexuXJob) => void,
  intervalMs = 1200,
): () => void {
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const tick = async () => {
    if (stopped) return;
    try {
      const job = await nexuxApi.job(jobId);
      onUpdate(job);
      if (['completed', 'failed', 'cancelled', 'interrupted'].includes(job.status)) {
        onFinish(job);
        return;
      }
    } catch (error) {
      onFinish({
        job_id: jobId,
        status: 'failed',
        progress: 0,
        stage: 'network_error',
        output_path: null,
        error: error instanceof Error ? error.message : String(error),
        created_at: new Date().toISOString(),
        clips: [],
        broll: false,
        render_meta: [],
        analysis_bundle: null,
      });
      return;
    }
    timer = setTimeout(tick, intervalMs);
  };

  void tick();
  return () => {
    stopped = true;
    if (timer) clearTimeout(timer);
  };
}


// ── Mode 2: Creative Compilation Engine ──

export interface Mode2Request {
  keyword: string;
  style_preset?: string;
  voice_enabled: boolean;
  voice_name: string;
  sfx_enabled: boolean;
  bgm_enabled: boolean;
  target_duration: number;
  max_sources: number;
}

export interface Mode2Response {
  status: 'success' | 'error';
  job_id: string;
  output_path?: string;
  thumbnail_path?: string;
  metadata?: {
    title: string;
    hashtags: string[];
    description: string;
    bgm_mood: string;
    total_duration: number;
    sources_used: number;
    keyword: string;
    processing_time: number;
    mode: string;
    sources_found: number;
    moments_found: number;
    clips_downloaded: number;
  };
  error?: string;
}

export interface Mode2Voice {
  id: string;
  name: string;
  lang: string;
}

export interface Mode2Job {
  job_id: string;
  status: string;
  has_video: boolean;
  has_thumbnail: boolean;
  keyword: string;
  title: string;
  hashtags: string[];
  total_duration: number;
  sources_used: number;
}

export const mode2Api = {
  generate: (payload: Mode2Request) =>
    request<Mode2Response>('/api/mode2/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  jobs: () => request<{ jobs: Mode2Job[] }>('/api/mode2/jobs'),

  voices: () => request<{ voices: Mode2Voice[] }>('/api/mode2/voices'),
};
