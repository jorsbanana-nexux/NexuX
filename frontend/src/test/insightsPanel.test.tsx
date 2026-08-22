/**
 * Tests for the V9.6 Beyond-Opus insights surface:
 * nexuxApi.retentionHeatmap/hookLab bindings + InsightsPanel rendering.
 * global.fetch is stubbed to respond like the real backend endpoints.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

import { nexuxApi } from '../api/nexuxApi';
import { InsightsPanel } from '../components/InsightsPanel';

const ORIGINAL_FETCH = global.fetch;

const HEATMAP = {
  curve: [
    { t: 0, retention: 95, speech_rate: 3.2, silent: false, spike: true },
    { t: 5, retention: 78, speech_rate: 2.8, silent: false, spike: false },
    { t: 10, retention: 40, speech_rate: 0.1, silent: true, spike: false },
    { t: 15, retention: 60, speech_rate: 3.0, silent: false, spike: false },
  ],
  avg_retention: 68.2,
  final_retention: 60,
  grade: 'B',
  dropoff_points: [{ t: 10, drop: 22, reason: 'silence' }],
  strongest_window: { t_start: 0, t_end: 5, retention: 95 },
  hook_strength: 88,
  duration: 15,
};

const HOOKLAB = {
  job_id: 'job-1',
  clip_index: 0,
  variants: [
    { text: 'The secret nobody tells you', start_offset: 0, duration: 2.4,
      score: 91, archetype: 'curiosity', description: 'Curiosity gap', rank: 1 },
    { text: 'This changes everything', start_offset: 1.2, duration: 2.1,
      score: 84, archetype: 'bold_claim', description: 'Bold claim', rank: 2 },
  ],
  count: 2,
};

function stubFetch(heatmapRes: Response, hookLabRes: Response) {
  global.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/retention')) return Promise.resolve(heatmapRes.clone());
    if (url.includes('/hook-lab')) return Promise.resolve(hookLabRes.clone());
    return Promise.reject(new Error(`unexpected fetch ${url}`));
  }) as typeof fetch;
}

const jsonRes = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

beforeEach(() => {});
afterEach(() => {
  global.fetch = ORIGINAL_FETCH;
});

describe('nexuxApi insights bindings', () => {
  it('retentionHeatmap hits /api/clips/{job}/{idx}/retention', async () => {
    stubFetch(jsonRes(HEATMAP), jsonRes(HOOKLAB));
    const res = await nexuxApi.retentionHeatmap('job-1', 2);
    const [url] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/clips/job-1/2/retention');
    expect(res.grade).toBe('B');
    expect(res.curve).toHaveLength(4);
  });

  it('hookLab hits /hook-lab with n query param', async () => {
    stubFetch(jsonRes(HEATMAP), jsonRes(HOOKLAB));
    const res = await nexuxApi.hookLab('job-1', 0, 3);
    const [url] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/clips/job-1/0/hook-lab?n=3');
    expect(res.variants[0].archetype).toBe('curiosity');
  });
});

describe('InsightsPanel', () => {
  it('renders retention grade, drop-off reason, and hook variants', async () => {
    stubFetch(jsonRes(HEATMAP), jsonRes(HOOKLAB));
    render(<InsightsPanel jobId="job-1" clipIndex={0} />);

    await waitFor(() => {
      expect(screen.getByText(/Retention Heatmap/i)).toBeTruthy();
    });

    expect(screen.getByText(/B · 68%/)).toBeTruthy();
    expect(screen.getByText(/hening/i)).toBeTruthy(); // silence → 'hening'
    expect(screen.getByText(/Momen terkuat: 0s–5s/)).toBeTruthy();
    expect(screen.getByText(/#1 · curiosity/)).toBeTruthy();
    expect(screen.getByText('The secret nobody tells you')).toBeTruthy();
    expect(screen.getByText(/#2 · bold_claim/)).toBeTruthy();
  });

  it('shows a friendly message when both endpoints fail', async () => {
    const err = jsonRes({ detail: 'Not found' }, 404);
    stubFetch(err, err);
    render(<InsightsPanel jobId="job-x" clipIndex={9} />);

    await waitFor(() => {
      expect(screen.getByText(/belum tersedia/i)).toBeTruthy();
    });
  });
});

describe('nexuxApi.titleCtr (Title Studio)', () => {
  it('posts title to /api/title-ctr and parses result', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(jsonRes({
        score: 74, grade: 'A',
        strengths: ['Power words: secret'],
        weaknesses: [],
        suggestions: [],
      })),
    ) as typeof fetch;

    const res = await nexuxApi.titleCtr('The Secret Nobody Tells You');
    const [url, init] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/title-ctr');
    expect(init.method).toBe('POST');
    expect(JSON.parse(String(init.body))).toEqual({
      title: 'The Secret Nobody Tells You',
      clip_text: '',
    });
    expect(res.grade).toBe('A');
    expect(res.score).toBe(74);
  });
});
