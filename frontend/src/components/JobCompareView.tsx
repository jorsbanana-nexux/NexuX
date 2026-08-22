import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import {
  BarChart3,
  Clapperboard,
  Clock,
  Layers,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { nexuxApi } from '../api/nexuxApi';
import type { JobCompareRow } from '../api/nexuxApi';

/**
 * JobCompareView — V9.6.1 multi-job compare dashboard
 * ====================================================
 * Cross-job quality matrix: mode (creative/podcast), clip count, source
 * duration stats, virality, processing time. Data: GET /api/jobs/compare.
 * This is the "Opus Clip doesn't have this" view — per-job A/B insight.
 */

function fmt(s: number | null | undefined, suffix = ''): string {
  if (s == null) return '—';
  return `${s}${suffix}`;
}

export default function JobCompareView() {
  const [rows, setRows] = useState<JobCompareRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await nexuxApi.jobsCompare(30);
      setRows(data.jobs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load compare data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const totalClips = rows.reduce((a, r) => a + r.clips_count, 0);
  const avgClips = rows.length ? (totalClips / rows.length).toFixed(1) : '0';
  const withStoryboard = rows.filter((r) => r.has_storyboard).length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md"
    >
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
            <BarChart3 className="h-5 w-5 text-violet-400" />
            Multi-Job Compare
          </h3>
          <p className="text-sm text-white/50">
            Cross-job quality matrix — beyond Opus Clip single-job view
          </p>
        </div>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/70 transition hover:border-white/25 hover:text-white disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Aggregate stats */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { icon: Clapperboard, label: 'Jobs', value: String(rows.length) },
          { icon: Layers, label: 'Total Clips', value: String(totalClips) },
          { icon: Sparkles, label: 'Avg Clips/Job', value: avgClips },
          { icon: TrendingUp, label: 'Storyboard Jobs', value: String(withStoryboard) },
        ].map(({ icon: Icon, label, value }) => (
          <div
            key={label}
            className="rounded-xl border border-white/10 bg-white/5 p-4 text-center"
          >
            <Icon className="mx-auto mb-1.5 h-4 w-4 text-violet-400" />
            <div className="text-xl font-bold text-white">{value}</div>
            <div className="text-xs text-white/40">{label}</div>
          </div>
        ))}
      </div>

      {/* Per-job table */}
      {loading && rows.length === 0 ? (
        <div className="py-8 text-center text-sm text-white/40">Loading jobs…</div>
      ) : rows.length === 0 ? (
        <div className="py-8 text-center text-sm text-white/40">
          No completed jobs yet. Run a Mode 2 generation to populate this view.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-white/40">
                <th className="pb-2 pr-4 font-medium">Job</th>
                <th className="pb-2 pr-4 font-medium">Mode</th>
                <th className="pb-2 pr-4 font-medium">Keyword</th>
                <th className="pb-2 pr-4 font-medium text-right">Clips</th>
                <th className="pb-2 pr-4 font-medium text-right">Sources</th>
                <th className="pb-2 pr-4 font-medium text-right">Avg Src Dur</th>
                <th className="pb-2 pr-4 font-medium text-right">Proc Time</th>
                <th className="pb-2 font-medium text-right">Virality</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <motion.tr
                  key={r.job_id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-white/5 hover:bg-white/5"
                >
                  <td className="py-3 pr-4 font-mono text-xs text-white/60">
                    {r.job_id.slice(0, 20)}
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        r.mode === 'mode2'
                          ? 'bg-violet-500/20 text-violet-300'
                          : 'bg-violet-500/20 text-violet-300'
                      }`}
                    >
                      {r.mode === 'mode2' ? 'Creative' : 'Podcast'}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-white/80">{r.keyword || r.title || '—'}</td>
                  <td className="py-3 pr-4 text-right text-white/70">{r.clips_count}</td>
                  <td className="py-3 pr-4 text-right text-white/70">{r.sources_used}</td>
                  <td className="py-3 pr-4 text-right text-white/70">
                    {fmt(r.avg_source_duration, 's')}
                  </td>
                  <td className="py-3 pr-4 text-right text-white/70">
                    {fmt(r.processing_time, 's')}
                  </td>
                  <td className="py-3 text-right text-white/70">
                    {r.avg_virality != null ? `${r.avg_virality}/10` : '—'}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 flex items-center gap-1.5 text-xs text-white/30">
        <Clock className="h-3 w-3" />
        Data aggregated from /api/jobs/compare — mode2 jobs from persisted
        metadata.json, podcast jobs from the jobs DB
      </div>
    </motion.div>
  );
}
