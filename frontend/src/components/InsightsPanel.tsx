import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'motion/react';
import {
  Activity,
  TrendingDown,
  Zap,
  AlertTriangle,
  CheckCircle2,
  FlaskConical,
} from 'lucide-react';
import { nexuxApi } from '../api/nexuxApi';
import type { RetentionHeatmap, HookLabResult } from '../api/nexuxApi';

/**
 * InsightsPanel — V9.6 "Beyond Opus" analytics
 * =============================================
 * Retention heatmap (per-second curve with drop-off reasons) + Hook Lab
 * (ranked hook variants). Data: GET /api/clips/{job}/{idx}/retention|hook-lab.
 */

interface InsightsPanelProps {
  jobId: string;
  clipIndex: number;
}

const GRADE_COLORS: Record<string, string> = {
  S: 'text-amber-300 border-amber-400/50 bg-amber-400/10',
  A: 'text-emerald-300 border-emerald-400/50 bg-emerald-400/10',
  B: 'text-violet-300 border-violet-400/50 bg-violet-400/10',
  C: 'text-yellow-300 border-yellow-400/50 bg-yellow-400/10',
  D: 'text-rose-300 border-rose-400/50 bg-rose-400/10',
};

function retentionColor(r: number): string {
  if (r >= 70) return '#34d399';
  if (r >= 50) return '#22d3ee';
  if (r >= 35) return '#facc15';
  return '#fb7185';
}

export const InsightsPanel: React.FC<InsightsPanelProps> = ({ jobId, clipIndex }) => {
  const [heatmap, setHeatmap] = useState<RetentionHeatmap | null>(null);
  const [hookLab, setHookLab] = useState<HookLabResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.allSettled([
      nexuxApi.retentionHeatmap(jobId, clipIndex),
      nexuxApi.hookLab(jobId, clipIndex, 5),
    ]).then(([h, l]) => {
      if (cancelled) return;
      if (h.status === 'fulfilled') setHeatmap(h.value);
      if (l.status === 'fulfilled') setHookLab(l.value);
      if (h.status === 'rejected' && l.status === 'rejected') {
        setError('Data insight belum tersedia untuk klip ini.');
      }
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [jobId, clipIndex]);

  const svgPath = useMemo(() => {
    if (!heatmap || heatmap.curve.length === 0) return '';
    const W = 320, H = 120, PAD = 6;
    const n = heatmap.curve.length;
    return heatmap.curve
      .map((p, i) => {
        const x = PAD + (i / Math.max(1, n - 1)) * (W - 2 * PAD);
        const y = PAD + (1 - p.retention / 100) * (H - 2 * PAD);
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }, [heatmap]);

  if (loading) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center gap-2 text-violet-300 text-xs font-mono">
          <Activity className="w-4 h-4 animate-pulse" />
          Menganalisis retensi & hook…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 text-stone-400 text-xs font-mono">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-5">
      {/* ── Retention Heatmap ── */}
      {heatmap && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-300" />
              <span className="text-xs font-mono uppercase tracking-wider text-stone-300">
                Retention Heatmap
              </span>
            </div>
            <span className={`px-2 py-0.5 rounded-md border text-xs font-bold ${GRADE_COLORS[heatmap.grade] || GRADE_COLORS.C}`}>
              {heatmap.grade} · {Math.round(heatmap.avg_retention)}%
            </span>
          </div>

          {svgPath && (
            <div className="rounded-lg border border-white/10 bg-black/30 p-2">
              <svg viewBox="0 0 320 120" className="w-full h-28">
                <defs>
                  <linearGradient id="retFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d={`${svgPath} L314,114 L6,114 Z`} fill="url(#retFill)" />
                <path d={svgPath} fill="none" stroke="#22d3ee" strokeWidth="1.6" />
                {heatmap.curve.map((p, i) => (
                  <circle
                    key={i}
                    cx={6 + (i / Math.max(1, heatmap.curve.length - 1)) * 308}
                    cy={6 + (1 - p.retention / 100) * 108}
                    r={p.silent ? 2.6 : 0}
                    fill="#fb7185"
                  />
                ))}
                {heatmap.dropoff_points.map((d, i) => {
                  const n = heatmap.curve.length;
                  const idx = heatmap.curve.findIndex((c) => c.t >= d.t);
                  if (idx < 0) return null;
                  const x = 6 + (idx / Math.max(1, n - 1)) * 308;
                  const y = 6 + (1 - heatmap.curve[idx].retention / 100) * 108;
                  return <polygon key={i} points={`${x},${y - 5} ${x - 4},${y - 11} ${x + 4},${y - 11}`} fill="#facc15" />;
                })}
              </svg>
              <div className="flex justify-between text-[10px] font-mono text-stone-500 px-1">
                <span>0s</span>
                <span>{Math.round(heatmap.duration)}s</span>
              </div>
            </div>
          )}

          {heatmap.dropoff_points.length > 0 && (
            <div className="mt-2 space-y-1">
              {heatmap.dropoff_points.slice(0, 3).map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-[11px] font-mono text-stone-400">
                  <TrendingDown className="w-3 h-3 text-yellow-400 shrink-0" />
                  <span>
                    {d.t.toFixed(0)}s — drop {d.drop.toFixed(0)}% (
                    {d.reason === 'silence' ? 'hening' : d.reason === 'low_density' ? 'ucapan jarang' : 'decay alami'})
                  </span>
                </div>
              ))}
            </div>
          )}
          {heatmap.strongest_window && (
            <div className="mt-2 flex items-center gap-2 text-[11px] font-mono text-emerald-300">
              <CheckCircle2 className="w-3 h-3 shrink-0" />
              Momen terkuat: {heatmap.strongest_window.t_start.toFixed(0)}s–{heatmap.strongest_window.t_end.toFixed(0)}s
            </div>
          )}
        </div>
      )}

      {/* ── Hook Lab ── */}
      {hookLab && hookLab.variants.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <FlaskConical className="w-4 h-4 text-fuchsia-300" />
            <span className="text-xs font-mono uppercase tracking-wider text-stone-300">
              Hook Lab
            </span>
            <span className="text-[10px] font-mono text-stone-500">
              {hookLab.count} varian
            </span>
          </div>
          <div className="space-y-2">
            {hookLab.variants.map((v) => (
              <motion.div
                key={v.rank}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: v.rank * 0.05 }}
                className={`rounded-lg border p-2.5 ${
                  v.rank === 1
                    ? 'border-fuchsia-400/40 bg-fuchsia-400/5'
                    : 'border-white/10 bg-white/[0.03]'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-fuchsia-300">
                    #{v.rank} · {v.archetype}
                  </span>
                  <span className="flex items-center gap-1 text-[11px] font-bold text-white">
                    <Zap className="w-3 h-3 text-amber-300" />
                    {Math.round(v.score)}
                  </span>
                </div>
                <p className="text-xs text-stone-200 leading-snug line-clamp-2">{v.text}</p>
                {v.start_offset !== 0 && (
                  <p className="text-[10px] font-mono text-stone-500 mt-1">
                    geser mulai {v.start_offset > 0 ? '+' : ''}{v.start_offset.toFixed(1)}s
                  </p>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
