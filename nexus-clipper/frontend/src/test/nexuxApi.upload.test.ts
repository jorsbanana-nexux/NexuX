/**
 * Tests for nexuxApi.upload() — the V9.5 local video upload binding.
 * No mocking of the API module: we stub global.fetch to capture the request
 * and respond like the real /api/upload endpoint would.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { nexuxApi } from '../api/nexuxApi';

const ORIGINAL_FETCH = global.fetch;

beforeEach(() => {
  global.fetch = vi.fn();
});
afterEach(() => {
  global.fetch = ORIGINAL_FETCH;
});

describe('nexuxApi.upload', () => {
  it('posts multipart FormData with the file field', async () => {
    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'ok',
          local_url: 'local://abc123.mp4',
          original_name: 'clip.mp4',
          size_mb: 0.001,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    const res = await nexuxApi.upload(file);

    expect(global.fetch).toHaveBeenCalledOnce();
    const [url, init] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain('/api/upload');
    expect(init.method).toBe('POST');
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.body as FormData).get('file')).toBe(file);
    expect(res.local_url).toBe('local://abc123.mp4');
    expect(res.status).toBe('ok');
  });

  it('throws with the server detail message on error', async () => {
    const file = new File(['x'], 'x.txt', { type: 'text/plain' });
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: "Unsupported file type '.txt'." }),
        { status: 400, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(nexuxApi.upload(file)).rejects.toThrow("Unsupported file type '.txt'");
  });

  it('surfaced HTTP status detail on non-JSON failure', async () => {
    const file = new File(['x'], 'clip.mp4', { type: 'video/mp4' });
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response('oops', { status: 500, statusText: 'Internal Server Error' }),
    );

    await expect(nexuxApi.upload(file)).rejects.toThrow();
  });
});
