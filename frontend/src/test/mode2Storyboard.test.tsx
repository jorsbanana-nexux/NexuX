import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Mode2Console } from '../components/Mode2Console';
import { v2Api, type Mode2StoryboardResult } from '../api/v2Api';
import { mode2Api } from '../api/nexuxApi';

vi.mock('../api/v2Api', () => ({
  v2Api: {
    mode2Storyboard: vi.fn(),
  },
}));
vi.mock('../api/nexuxApi', () => ({
  mode2Api: {
    generate: vi.fn(),
    voices: vi.fn().mockResolvedValue({ voices: [] }),
  },
  buildOutputUrl: (p: string) => p,
}));

const storyboardResult: Mode2StoryboardResult = {
  status: 'ok',
  keyword: 'saitama',
  archetypes: ['Hook & Overview', 'Kenapa / Why'],
  clips_per_archetype: 1,
  total_clips: 3,
  storyboard: [
    {
      clip_idx: 1,
      archetype: 'Hook & Overview',
      role: 'hook',
      video_title: 'Saitama One Punch!',
      video_url: 'https://youtu.be/a',
      video_id: 'a',
      thumbnail_url: 'https://i.ytimg.com/vi/a/hqdefault.jpg',
      duration: 45,
      view_count: 100000,
      channel: 'Ch1',
      reason: 'found',
      source_query: 'saitama',
    },
    {
      clip_idx: 2,
      archetype: 'Kenapa / Why',
      role: 'beat',
      video_title: 'Kenapa Saitama Kuat',
      video_url: 'https://youtu.be/b',
      video_id: 'b',
      thumbnail_url: 'https://i.ytimg.com/vi/b/hqdefault.jpg',
      duration: 30,
      view_count: 50000,
      channel: 'Ch2',
      reason: 'found',
      source_query: 'kenapa saitama',
    },
    {
      clip_idx: 3,
      archetype: 'Sisi Gelap / Dark Side',
      role: 'payoff',
      video_title: 'Sisi Gelap Genos',
      video_url: 'https://youtu.be/c',
      video_id: 'c',
      thumbnail_url: 'https://i.ytimg.com/vi/c/hqdefault.jpg',
      duration: 60,
      view_count: 200000,
      channel: 'Ch3',
      reason: 'found',
      source_query: 'sisi gelap saitama',
    },
  ],
};

describe('Mode2Console storyboard editing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (v2Api.mode2Storyboard as any).mockResolvedValue(storyboardResult);
    (mode2Api.generate as any).mockResolvedValue({ status: 'success', job_id: 'm2_1' });
  });

  it('renders storyboard clips with roles and thumbnails', async () => {
    const { container } = render(<Mode2Console />);
    await userEvent.type(screen.getByPlaceholderText(/peter parker/i), 'saitama');
    await userEvent.click(screen.getByText(/Preview Storyboard/i));
    await waitFor(() => expect(screen.getAllByText(/hook|beat|payoff/i)).toHaveLength(3));
    expect(screen.getByText('Saitama One Punch!')).toBeInTheDocument();
    expect(container.querySelectorAll('img')).toHaveLength(3);
  });

  it('removes a clip and relabels roles', async () => {
    render(<Mode2Console />);
    await userEvent.type(screen.getByPlaceholderText(/peter parker/i), 'saitama');
    await userEvent.click(screen.getByText(/Preview Storyboard/i));
    await screen.findByText('Saitama One Punch!');

    const removeButtons = screen.getAllByRole('button', { name: /Remove clip/i });
    await userEvent.click(removeButtons[1]); // remove the beat clip

    expect(screen.queryByText('Kenapa Saitama Kuat')).not.toBeInTheDocument();
    expect(screen.getByText(/Storyboard — 2 klip/)).toBeInTheDocument();
    // payoff label moves to last remaining clip
    expect(screen.getByText('payoff')).toBeInTheDocument();
  });

  it('sends remaining storyboard clips on compile', async () => {
    render(<Mode2Console />);
    await userEvent.type(screen.getByPlaceholderText(/peter parker/i), 'saitama');
    await userEvent.click(screen.getByText(/Preview Storyboard/i));
    await screen.findByText('Saitama One Punch!');

    await userEvent.click(screen.getAllByRole('button', { name: /Remove clip/i })[0]);
    await userEvent.click(screen.getByText(/Buat dari Storyboard/));

    expect(mode2Api.generate).toHaveBeenCalled();
    const payload = (mode2Api.generate as any).mock.calls[0][0];
    expect(payload.storyboard).toHaveLength(2);
  });
});
