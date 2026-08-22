import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Type, TrendingUp, Lightbulb, AlertTriangle } from 'lucide-react';
import { nexuxApi } from '../api/nexuxApi';
import type { TitleCtrResult } from '../api/nexuxApi';

/**
 * TitleStudio — V9.6 live title CTR scoring
 * =========================================
 * Debounced (400ms) scoring of a candidate title against the transparent
 * 7-factor CTR model (POST /api/title-ctr). Shows score dial, strengths,
 * weaknesses, and concrete rewrite suggestions.
 */

interface TitleStudioProps {
  initialTitle?: string;
  clipText?: string;
}

const GRADE_STYLES: Record<string, string> = {
  S: 'text-amber-300 border-amber-400/50 bg-amber-400/10',
  A: 'text-emerald-300 border-emerald-400/50 bg-emerald-400/10',
  B: 'text-violet-300 border-violet-400/50 bg-violet-400/10',
  C: 'text-yellow-300 border-yellow-400/50 bg-yellow-400/10',
  D: 'text-rose-300 border-rose-400/50 bg-rose-400/10',
};

export const TitleStudio: React.FC<TitleStudioProps> = ({ initialTitle = '', clipText = '' }) => {
  const [title, setTitle] = useState(initialTitle);
  const [result, setResult] = useState<TitleCtrResult | null>(null);
  const [scoring, setScoring] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const seqRef = useRef(0);

  useEffect(() => {
    if (!title.trim()) {
      setResult(null);
      setScoring(false);
      return;
    }
    setScoring(true);
    if (timerRef.current) clearTimeout(timerRef.current);
    const seq = ++seqRef.current;
    timerRef.current = setTimeout(() => {
      nexuxApi.titleCtr(title, clipText)
        .then((res) => { if (seqRef.current === seq) setResult(res); })
        .catch(() => {})
        .finally(() => { if (seqRef.current === seq) setScoring(false); });
    }, 400);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [title, clipText]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Type className="w-4 h-4 text-amber-300" />
        <span className="text-xs font-mono uppercase tracking-wider text-stone-300">
          Title Studio
        </span>
        {scoring && (
          <span className="text-[10px] font-mono text-stone-500 animate-pulse">scoring…</span>
        )}
      </div>

      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Tulis judul klip Anda…"
        maxLength={300}
        className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder:text-stone-500 focus:outline-none focus:border-amber-400/50 transition-colors"
      />

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-lg border border-white/10 bg-black/30 p-3 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[11px] font-mono text-stone-400">
                <TrendingUp className="w-3.5 h-3.5 text-amber-300" />
                Prediksi CTR relatif
              </span>
              <span className={`px-2 py-0.5 rounded-md border text-xs font-bold ${GRADE_STYLES[result.grade] || GRADE_STYLES.C}`}>
                {result.grade} · {Math.round(result.score)}
              </span>
            </div>

            {result.strengths.length > 0 && (
              <ul className="space-y-1">
                {result.strengths.map((s, i) => (
                  <li key={i} className="text-[11px] font-mono text-emerald-300 flex gap-1.5">
                    <span>+</span><span>{s}</span>
                  </li>
                ))}
              </ul>
            )}
            {result.weaknesses.length > 0 && (
              <ul className="space-y-1">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="text-[11px] font-mono text-rose-300 flex gap-1.5">
                    <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" /><span>{w}</span>
                  </li>
                ))}
              </ul>
            )}
            {result.suggestions.length > 0 && (
              <ul className="space-y-1 pt-1 border-t border-white/5">
                {result.suggestions.slice(0, 3).map((sg, i) => (
                  <li key={i} className="text-[11px] font-mono text-amber-200 flex gap-1.5">
                    <Lightbulb className="w-3 h-3 mt-0.5 shrink-0" /><span>{sg}</span>
                  </li>
                ))}
              </ul>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
