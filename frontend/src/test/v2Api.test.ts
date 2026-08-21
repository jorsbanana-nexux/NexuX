/**
 * Tests for v2Api — the V9.5 dual-mode API client.
 * global.fetch is stubbed to respond like the real /api/v2/* endpoints.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { v2Api } from '../api/v2Api';

const ORIGINAL_FETCH = global.fetch;

beforeEach(() => {
  global.fetch = vi.fn();
});
afterEach(() => {
  global.fetch = ORIGINAL_FETCH;
});

const mockFetchOnce = (body: unknown, status = 200) => {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
};

describe('v2Api.modes', () => {
  it('fetches the dual-mode catalog', async () => {
    mockFetchOnce([
      {
        mode: 'podcast',
        name: 'Podcast Mode',
        description: 'Clip long podcasts',
        icon: '🎙️',
        color: 'from-blue-500 to-cyan-500',
        requires_url: true,
        requires_keyword: false,
        features: ['Hook detection'],
      },
      {
        mode: 'creative',
        name: 'AI Creative Mode',
        description: 'Keyword compilation',
        icon: '✨',
        color: 'from-purple-500 to-pink-500',
        requires_url: false,
        requires_keyword: true,
        features: ['Keyword expansion'],
      },
    ]);

    const modes = await v2Api.modes();

    const [url] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/v2/modes');
    expect(modes).toHaveLength(2);
    expect(modes[0].mode).toBe('podcast');
    expect(modes[1].requires_keyword).toBe(true);
  });
});

describe('v2Api.generate', () => {
  it('posts a podcast generation request', async () => {
    mockFetchOnce({
      job_id: 'podcast_abc123',
      mode: 'podcast',
      status: 'queued',
      message: 'started',
    });

    const res = await v2Api.generate({
      mode: 'podcast',
      youtube_url: 'https://www.youtube.com/watch?v=abc',
      target_duration: 45,
      clip_count: 5,
    });

    const [url, init] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/v2/generate');
    expect(init.method).toBe('POST');
    const body = JSON.parse(String(init.body));
    expect(body.mode).toBe('podcast');
    expect(body.youtube_url).toContain('youtube.com');
    expect(res.job_id).toBe('podcast_abc123');
    expect(res.status).toBe('queued');
  });

  it('posts a creative generation request', async () => {
    mockFetchOnce({
      job_id: 'creative_def456',
      mode: 'creative',
      status: 'queued',
      message: 'started',
    });

    const res = await v2Api.generate({
      mode: 'creative',
      keyword: 'motivasi belajar',
      voice_enabled: true,
      voice_name: 'id-ID-ArdiNeural',
    });

    const [, init] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse(String(init.body));
    expect(body.mode).toBe('creative');
    expect(body.keyword).toBe('motivasi belajar');
    expect(res.mode).toBe('creative');
  });

  it('throws with the server detail message on error', async () => {
    mockFetchOnce({ detail: 'Either youtube_url (Mode 1) or keyword (Mode 2) is required' }, 400);

    await expect(v2Api.generate({ mode: 'podcast' })).rejects.toThrow(
      /youtube_url.*keyword/i,
    );
  });
});

describe('v2Api.expandKeyword', () => {
  it('encodes the keyword and returns expansion terms', async () => {
    mockFetchOnce({
      original: 'motivasi belajar',
      expanded: ['motivasi belajar', 'inspirasi', 'self improvement'],
      niche: 'motivation',
      primary_terms: ['motivasi belajar'],
      secondary_terms: ['motivasi belajar 2026'],
    });

    const res = await v2Api.expandKeyword('motivasi belajar', 8);

    const [url] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/v2/keyword/expand');
    expect(String(url)).toContain('keyword=motivasi%20belajar');
    expect(String(url)).toContain('max_terms=8');
    expect(res.expanded.length).toBeGreaterThanOrEqual(3);
    expect(res.niche).toBe('motivation');
  });
});
