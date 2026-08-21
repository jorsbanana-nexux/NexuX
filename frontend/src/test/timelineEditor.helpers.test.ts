/**
 * Tests for the V9.5 editor helpers that turn a job's diarized
 * transcript_segments into speaker rows + clip-relative transcript lines.
 */
import { describe, expect, it } from 'vitest';

import {
  buildRealSpeakers,
  buildRealTranscript,
  buildMockSpeakers,
  type RawSegment,
} from '../components/TimelineEditorStudio';

const SEGMENTS: RawSegment[] = [
  { start: 0, end: 2.0, text: 'Welcome back everyone', speaker: 'SPEAKER_00' },
  { start: 2.0, end: 4.5, text: 'Thank you for having me', speaker: 'SPEAKER_01' },
  { start: 4.5, end: 8.0, text: 'This is the shocking truth', speaker: 'SPEAKER_01' },
];

describe('buildRealSpeakers', () => {
  it('builds one speaker row per distinct speaker id', () => {
    const speakers = buildRealSpeakers(SEGMENTS);
    expect(speakers).not.toBeNull();
    expect(speakers).toHaveLength(2);
    expect(speakers![0].id).toBe('SPEAKER_00');
    expect(speakers![1].id).toBe('SPEAKER_01');
    expect(speakers![0].muted).toBe(false);
    expect(speakers![1].isolated).toBe(false);
  });

  it('pretty-prints SPEAKER_NN as Speaker N+1', () => {
    const speakers = buildRealSpeakers(SEGMENTS);
    expect(speakers![0].name).toBe('Speaker 1');
    expect(speakers![1].name).toBe('Speaker 2');
  });

  it('assigns stable colors per speaker', () => {
    const a = buildRealSpeakers(SEGMENTS)!;
    // Rebuild deterministically — same input should give same colors
    const b = buildRealSpeakers(SEGMENTS)!;
    expect(a.map(s => s.color)).toEqual(b.map(s => s.color));
  });

  it('returns null for empty segments', () => {
    expect(buildRealSpeakers([])).toBeNull();
  });

  it('defaults missing speaker to SPEAKER_00', () => {
    const speakers = buildRealSpeakers([{ start: 0, end: 1, text: 'x' }]);
    expect(speakers![0].id).toBe('SPEAKER_00');
  });
});

describe('buildRealTranscript', () => {
  it('slices segments to the selected clip range and shifts to clip-relative', () => {
    const out = buildRealTranscript(SEGMENTS, 2.0, 8.0);
    expect(out).toHaveLength(2);
    expect(out[0].start).toBeCloseTo(0);       // clip-relative
    expect(out[0].end).toBeCloseTo(2.5);
    expect(out[0].speakerId).toBe('SPEAKER_01');
    expect(out[0].words).toHaveLength(5);       // "Thank you for having me"
    expect(out[0].words[0].text).toBe('Thank');
    // Words spread evenly across the segment duration
    const step = (out[0].end - out[0].start) / out[0].words.length;
    expect(out[0].words[1].start).toBeCloseTo(out[0].words[0].end);
    expect(step).toBeGreaterThan(0);
  });

  it('filters out empty segments', () => {
    const empty: RawSegment[] = [{ start: 0, end: 1, text: '   ', speaker: 'SPEAKER_00' }];
    const out = buildRealTranscript(empty, 0, 2);
    expect(out).toHaveLength(0);
  });

  it('respects the clip boundaries', () => {
    const out = buildRealTranscript(SEGMENTS, 3.0, 5.0);
    // Segments 2 (2.0–4.5) and 3 (4.5–8.0) both overlap the 3.0–5.0 window.
    // Segment 1 ends at exactly 2.0, so it is excluded.
    expect(out).toHaveLength(2);
    expect(out[0].start).toBeCloseTo(0);          // clipped to window start
    expect(out[0].end).toBeCloseTo(1.5);          // clipped at window end: 4.5-3.0
    expect(out[1].end).toBeCloseTo(2.0);          // tail-capped at 2s window
    expect(out[0].speakerId).toBe('SPEAKER_01');
  });

  it('excludes segments outside the window', () => {
    const short: RawSegment[] = [
      { start: 0, end: 2.0, text: 'first one', speaker: 'SPEAKER_00' },
      { start: 10, end: 12, text: 'second one', speaker: 'SPEAKER_00' },
    ];
    const out = buildRealTranscript(short, 2.5, 8.0);
    // Segment 1 ends at 2.0 ≤ window start; segment 2 starts at 10 ≥ window end
    expect(out).toHaveLength(0);
  });
});

describe('buildMockSpeakers', () => {
  it('returns 2 fallback speakers', () => {
    const s = buildMockSpeakers();
    expect(s).toHaveLength(2);
    expect(s[0].name).toBe('Tanya');
    expect(s[1].name).toBe('Tomas');
  });
});
