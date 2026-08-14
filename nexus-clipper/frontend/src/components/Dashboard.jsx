import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiPlay, FiLink, FiDownload, FiCheckCircle, FiAlertCircle, FiLoader, FiUserCheck, FiUsers, FiTarget } from "react-icons/fi";
import useWebSocket from "../hooks/useWebSocket";
import GlassPanel from "./GlassPanel";

const SUBTITLE_STYLES = [
  { id: "hormozi", name: "Hormozi", icon: "💛", desc: "Kata per kata, highlight kuning" },
  { id: "mrbeast", name: "MrBeast", icon: "🦁", desc: "Tebal, stroke hitam, dinamis" },
  { id: "aliabdaal", name: "Ali Abdaal", icon: "✨", desc: "Minimalis, elegan, bersih" },
  { id: "minimalist", name: "Minimalist", icon: "🤍", desc: "Kecil putih, no animasi" },
  { id: "gaming", name: "Gaming", icon: "🎮", desc: "Bold, kontras, cepat" },
  { id: "cinematic", name: "Cinematic", icon: "🎬", desc: "Lebar, fade premium" },
  { id: "neon", name: "Neon", icon: "💜", desc: "Glow effect neon" },
  { id: "typewriter", name: "Typewriter", icon: "⌨️", desc: "Huruf muncul satu-satu" },
  { id: "tiktok_viral", name: "TikTok Viral", icon: "🔥", desc: "Acak, warna cerah" },
  { id: "documentary", name: "Documentary", icon: "📜", desc: "Serif, bawah, fade" },
  { id: "comedy", name: "Comedy", icon: "😂", desc: "Bouncy, timing komedi" },
  { id: "horror", name: "Horror", icon: "👻", desc: "Flicker, red highlight" },
  { id: "motivational", name: "Motivational", icon: "💪", desc: "Bold white, slow" },
  { id: "educational", name: "Educational", icon: "📚", desc: "Top, highlight terms" },
  { id: "custom", name: "Custom", icon: "🎨", desc: "Atur sendiri semuanya" },
];
const FONTS = ["Arial","Impact","Helvetica","Georgia","Verdana","Trebuchet MS","Comic Sans MS","Courier New","Tahoma","Times New Roman"];
const ANIMATIONS = [{ id: "pop", label: "Pop-up" },{ id: "fade", label: "Fade In" },{ id: "slide_up", label: "Slide Up" },{ id: "none", label: "Static" }];
const POSITIONS = [{ id: "top", label: "Atas" },{ id: "center", label: "Tengah" },{ id: "bottom", label: "Bawah" }];
const ASPECT_RATIOS = [{ id: "9:16", label: "9:16", desc: "TikTok", icon: "📱" },{ id: "1:1", label: "1:1", desc: "IG Feed", icon: "◻️" },{ id: "16:9", label: "16:9", desc: "YouTube", icon: "🖥️" },{ id: "4:5", label: "4:5", desc: "IG Portrait", icon: "📲" }];
const COLOR_PRESETS = [
  { name: "Default", primary: "#FFFFFF", highlight: "#FFD700", stroke: "#000000" },
  { name: "Neon Gold", primary: "#FFD700", highlight: "#FFA000", stroke: "#000000" },
  { name: "Fire Red", primary: "#FF4444", highlight: "#FFD600", stroke: "#8B0000" },
  { name: "Ocean Blue", primary: "#00E5FF", highlight: "#00FF88", stroke: "#003344" },
  { name: "Purple Haze", primary: "#E040FB", highlight: "#FFD700", stroke: "#4A0072" },
  { name: "Mint Green", primary: "#69F0AE", highlight: "#FFFF00", stroke: "#1B5E20" },
  { name: "Coral", primary: "#FF8A80", highlight: "#FFEA00", stroke: "#B71C1C" },
  { name: "Ice", primary: "#82B1FF", highlight: "#FFD700", stroke: "#0D47A1" },
];

export default function Dashboard() {
  const { connected, trackJob } = useWebSocket();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [generating, setGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState(null);
  const [activeTab, setActiveTab] = useState("style");
  const [lastJobId, setLastJobId] = useState("");

  const [config, setConfig] = useState({
    subtitle_style: "hormozi", font: "Arial", font_size: 48,
    primary_color: "#FFFFFF", highlight_color: "#FFD700", stroke_color: "#000000",
    stroke_width: 3, position: "center", animation: "pop",
    auto_zoom: true, aspect_ratio: "9:16", clip_count: 3, target_duration: 60,
    language: "",
    face_tracking: true,               // NEW
    dynamic_subtitle_position: true,    // NEW
    diarization: true,                  // NEW
  });

  const u = (key, val) => setConfig(p => ({ ...p, [key]: val }));

  const handleGenerate = async () => {
    if (!youtubeUrl.trim()) return alert("Paste YouTube link dulu!");
    setGenerating(true);
    setJobStatus({ status: "queued", progress: 0, stage: "Starting..." });
    try {
      const res = await fetch("/api/generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: youtubeUrl, ...config }),
      });
      if (!res.ok) throw new Error(await res.text());
      const { job_id } = await res.json();
      setLastJobId(job_id); trackJob(job_id);
      const poll = setInterval(async () => {
        try {
          const jr = await fetch(`/api/job/${job_id}`);
          const job = await jr.json();
          setJobStatus(job);
          if (job.status === "completed" || job.status === "failed") { clearInterval(poll); setGenerating(false); }
        } catch { clearInterval(poll); setGenerating(false); }
      }, 1000);
    } catch (e) { setJobStatus({ status: "failed", error: e.message }); setGenerating(false); }
  };

  const stages = ["downloading","face_tracking","transcribing","analyzing","rendering","completed"];
  const stageIcons = { downloading:"⬇️", face_tracking:"👤", transcribing:"🎙️", analyzing:"🔍", rendering:"🎬", completed:"✅" };

  return (
    <div style={{ position: "relative", zIndex: 1, padding: 12, maxWidth: 1500, margin: "0 auto" }}>
      {/* HEADER */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        style={{ textAlign: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 900,
          background: "linear-gradient(135deg,#6366f1,#8b5cf6,#ec4899)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: 4 }}>
          NEXUS-CLIPPER AI ULTRA
        </h1>
        <p style={{ color: "#666", fontSize: "0.8rem" }}>
          WhisperX Diarization · MediaPipe Face Tracking · Dynamic Subtitles · FFmpeg Render &nbsp;|&nbsp; 100% Free
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 10, fontSize: "0.75rem", flexWrap: "wrap" }}>
          <span style={{ color: connected ? "#4ade80" : "#ef4444" }}>{connected ? "● Connected" : "● Disconnected"}</span>
          <span style={{ color: "#6366f1" }}><FiUserCheck style={{ verticalAlign: "middle" }} /> Face Tracking</span>
          <span style={{ color: "#8b5cf6" }}><FiUsers style={{ verticalAlign: "middle" }} /> Multi-Speaker</span>
          {jobStatus && (
            <span style={{ color: jobStatus.status === "completed" ? "#4ade80" : jobStatus.status === "failed" ? "#ef4444" : "#f59e0b" }}>
              {jobStatus.status === "completed" ? <FiCheckCircle style={{ verticalAlign: "middle" }} /> :
               jobStatus.status === "failed" ? <FiAlertCircle style={{ verticalAlign: "middle" }} /> :
               <FiLoader style={{ verticalAlign: "middle", animation: "spin 1s linear infinite" }} />}
              {" "}{jobStatus.status === "completed" ? "Complete" : jobStatus.status === "failed" ? "Failed" : `${jobStatus.progress || 0}%`}
            </span>
          )}
        </div>
      </motion.div>

      {/* TWO COLUMNS */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.8fr", gap: 14 }}>

        {/* LEFT COLUMN */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <GlassPanel style={{ padding: 16 }}>
            <h3 style={{ fontSize: "0.8rem", color: "#aaa", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
              <FiLink /> Paste YouTube Link
            </h3>
            <input value={youtubeUrl} onChange={e => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid rgba(99,102,241,0.3)",
                background: "rgba(255,255,255,0.04)", color: "#fff", fontSize: "0.8rem", outline: "none", boxSizing: "border-box" }} />
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={handleGenerate} disabled={generating || !youtubeUrl.trim()}
              style={{ marginTop: 8, width: "100%", padding: "10px", borderRadius: 8, border: "none",
                background: generating ? "rgba(99,102,241,0.3)" : "linear-gradient(135deg,#6366f1,#8b5cf6)",
                color: "#fff", fontSize: "0.85rem", fontWeight: 700, cursor: generating ? "wait" : "pointer",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              {generating ? <FiLoader style={{ animation: "spin 1s linear infinite" }} /> : <FiPlay />}
              {generating ? "PROCESSING..." : "GENERATE CLIPS"}
            </motion.button>
          </GlassPanel>

          {/* PROGRESS */}
          {jobStatus && (
            <GlassPanel style={{ padding: 14 }}>
              <h3 style={{ fontSize: "0.75rem", color: "#aaa", marginBottom: 6 }}>
                {jobStatus.status === "completed" ? <FiCheckCircle style={{ color: "#4ade80", verticalAlign: "middle" }} /> :
                 jobStatus.status === "failed" ? <FiAlertCircle style={{ color: "#ef4444", verticalAlign: "middle" }} /> :
                 <FiLoader style={{ verticalAlign: "middle", animation: "spin 1s linear infinite" }} />}
                {" "}Job: {lastJobId || "..."}
              </h3>
              <div style={{ width: "100%", background: "rgba(255,255,255,0.08)", borderRadius: 8, height: 4, marginBottom: 6 }}>
                <motion.div initial={{ width: 0 }} animate={{ width: `${jobStatus.progress || 0}%` }}
                  style={{ height: "100%", borderRadius: 8,
                    background: jobStatus.status === "failed" ? "#ef4444" : jobStatus.status === "completed" ? "#4ade80" : "#6366f1" }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.6rem", color: "#555", flexWrap: "wrap" }}>
                {stages.map((s, i) => {
                  const si = stages.indexOf(jobStatus.stage || "");
                  const done = jobStatus.status === "completed" || si > i;
                  const active = si === i;
                  return (
                    <span key={s} style={{ opacity: done ? 1 : active ? 1 : 0.3, color: done ? "#4ade80" : active ? "#6366f1" : "#555" }}>
                      {stageIcons[s] || "⏳"} {s}
                    </span>
                  );
                })}
              </div>
              {jobStatus.speakers != null && (
                <div style={{ marginTop: 6, fontSize: "0.65rem", color: "#8b5cf6" }}>
                  <FiUsers style={{ verticalAlign: "middle" }} /> Speakers detected: {jobStatus.speakers}
                </div>
              )}
              {jobStatus.error && (
                <div style={{ marginTop: 6, padding: 6, borderRadius: 6, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#ef4444", fontSize: "0.65rem" }}>
                  {jobStatus.error}
                </div>
              )}
            </GlassPanel>
          )}

          {/* OUTPUT PREVIEW */}
          {jobStatus?.output_path && (
            <GlassPanel style={{ padding: 14 }}>
              <h3 style={{ fontSize: "0.75rem", color: "#4ade80", marginBottom: 6 }}>✅ Video Ready!</h3>
              <div style={{ background: "#000", borderRadius: 8, overflow: "hidden", marginBottom: 6 }}>
                <video controls src={`/output/${jobStatus.output_path.split('/').slice(-2).join('/')}`}
                  style={{ width: "100%", maxHeight: 180 }} />
              </div>
              <a href={`/output/${jobStatus.output_path.split('/').slice(-2).join('/')}`} download
                style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4, padding: "6px",
                  borderRadius: 6, background: "rgba(74,222,128,0.15)", border: "1px solid rgba(74,222,128,0.3)",
                  color: "#4ade80", fontSize: "0.75rem", textDecoration: "none", fontWeight: 600 }}>
                <FiDownload /> Download
              </a>
            </GlassPanel>
          )}
        </div>

        {/* RIGHT COLUMN — Customization */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
            {[["style","🎨 Style","15+"],["text","🔤 Text","10+"],["colors","🌈 Colors","8"],["video","🎬 Video","10+"]].map(([id,label,count]) => (
              <button key={id} onClick={() => setActiveTab(activeTab === id ? "" : id)}
                style={{ padding: "6px 12px", borderRadius: 6, border: "none", fontSize: "0.7rem", fontWeight: 600,
                  background: activeTab === id ? "rgba(99,102,241,0.18)" : "rgba(255,255,255,0.03)",
                  color: activeTab === id ? "#fff" : "#777", cursor: "pointer",
                  border: `1px solid ${activeTab === id ? "rgba(99,102,241,0.3)" : "rgba(255,255,255,0.06)"}` }}>
                {label} <span style={{ fontSize: "0.55rem", opacity: 0.5 }}>{count}</span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {/* STYLE */}
            {activeTab === "style" && (
              <motion.div key="s" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <GlassPanel style={{ padding: 14 }}>
                  <h3 style={{ fontSize: "0.75rem", color: "#aaa", marginBottom: 8 }}>🎨 15 Subtitle Style Presets</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 6 }}>
                    {SUBTITLE_STYLES.map(s => (
                      <button key={s.id} onClick={() => u("subtitle_style", s.id)}
                        style={{ padding: "6px 3px", borderRadius: 8, textAlign: "center",
                          border: config.subtitle_style === s.id ? "1px solid rgba(99,102,241,0.5)" : "1px solid rgba(255,255,255,0.08)",
                          background: config.subtitle_style === s.id ? "rgba(99,102,241,0.12)" : "rgba(255,255,255,0.02)",
                          color: config.subtitle_style === s.id ? "#fff" : "#777", cursor: "pointer" }}>
                        <div style={{ fontSize: "1.2rem" }}>{s.icon}</div>
                        <div style={{ fontSize: "0.6rem", fontWeight: 600 }}>{s.name}</div>
                        <div style={{ fontSize: "0.5rem", opacity: 0.5, lineHeight: 1.2 }}>{s.desc}</div>
                      </button>
                    ))}
                  </div>
                </GlassPanel>
              </motion.div>
            )}

            {/* TEXT */}
            {activeTab === "text" && (
              <motion.div key="t" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <GlassPanel style={{ padding: 14 }}>
                  <h3 style={{ fontSize: "0.75rem", color: "#aaa", marginBottom: 8 }}>🔤 Text Settings</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8 }}>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>Font</label>
                      <select value={config.font} onChange={e => u("font", e.target.value)}
                        style={{ width: "100%", padding: "6px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.04)", color: "#fff", fontSize: "0.7rem" }}>
                        {FONTS.map(f => <option key={f}>{f}</option>)}</select>
                    </div>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>Size: {config.font_size}px</label>
                      <input type="range" min={24} max={96} value={config.font_size} onChange={e => u("font_size", Number(e.target.value))}
                        style={{ width: "100%", accentColor: "#6366f1" }} />
                    </div>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>Position</label>
                      <div style={{ display: "flex", gap: 2 }}>
                        {POSITIONS.map(p => (
                          <button key={p.id} onClick={() => u("position", p.id)}
                            style={{ flex: 1, padding: "5px 3px", borderRadius: 5, border: config.position === p.id ? "1px solid rgba(99,102,241,0.5)" : "1px solid rgba(255,255,255,0.08)",
                              background: config.position === p.id ? "rgba(99,102,241,0.15)" : "transparent",
                              color: config.position === p.id ? "#fff" : "#777", fontSize: "0.55rem", cursor: "pointer" }}>
                            {p.label}</button>))}
                      </div>
                    </div>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>Animation</label>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
                        {ANIMATIONS.map(a => (
                          <button key={a.id} onClick={() => u("animation", a.id)}
                            style={{ padding: "4px 3px", borderRadius: 5, border: config.animation === a.id ? "1px solid rgba(99,102,241,0.5)" : "1px solid rgba(255,255,255,0.08)",
                              background: config.animation === a.id ? "rgba(99,102,241,0.15)" : "transparent",
                              color: config.animation === a.id ? "#fff" : "#777", fontSize: "0.55rem", cursor: "pointer" }}>
                            {a.label}</button>))}
                      </div>
                    </div>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>Stroke: {config.stroke_width}px</label>
                    <input type="range" min={0} max={10} value={config.stroke_width} onChange={e => u("stroke_width", Number(e.target.value))}
                      style={{ width: "100%", accentColor: "#6366f1" }} />
                  </div>
                </GlassPanel>
              </motion.div>
            )}

            {/* COLORS */}
            {activeTab === "colors" && (
              <motion.div key="c" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <GlassPanel style={{ padding: 14 }}>
                  <h3 style={{ fontSize: "0.75rem", color: "#aaa", marginBottom: 8 }}>🌈 Colors & Effects</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 5, marginBottom: 10 }}>
                    {COLOR_PRESETS.map(p => (
                      <button key={p.name} onClick={() => { u("primary_color",p.primary); u("highlight_color",p.highlight); u("stroke_color",p.stroke); }}
                        style={{ padding: 5, borderRadius: 6, border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)", cursor: "pointer", textAlign: "center" }}>
                        <div style={{ display: "flex", justifyContent: "center", gap: 2, marginBottom: 1 }}>
                          <div style={{ width: 10, height: 10, borderRadius: "50%", background: p.primary }} />
                          <div style={{ width: 10, height: 10, borderRadius: "50%", background: p.highlight }} />
                          <div style={{ width: 10, height: 10, borderRadius: "50%", background: p.stroke }} />
                        </div>
                        <div style={{ fontSize: "0.55rem", color: "#888" }}>{p.name}</div>
                      </button>))}
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
                    {[["Text","primary_color"],["Highlight","highlight_color"],["Stroke","stroke_color"]].map(([label,key]) => (
                      <div key={key}>
                        <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 3 }}>{label}</label>
                        <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
                          <input type="color" value={config[key]} onChange={e => u(key, e.target.value)}
                            style={{ width: 28, height: 28, borderRadius: 4, border: "1px solid rgba(255,255,255,0.2)", cursor: "pointer" }} />
                          <input type="text" value={config[key]} onChange={e => u(key, e.target.value)}
                            style={{ flex: 1, padding: "4px", borderRadius: 4, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.04)", color: "#fff", fontSize: "0.65rem", fontFamily: "monospace" }} />
                        </div>
                      </div>))}
                  </div>
                </GlassPanel>
              </motion.div>
            )}

            {/* VIDEO SETTINGS — with NEW advanced toggles */}
            {activeTab === "video" && (
              <motion.div key="v" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <GlassPanel style={{ padding: 14 }}>
                  <h3 style={{ fontSize: "0.75rem", color: "#aaa", marginBottom: 8 }}>🎬 Video Settings</h3>

                  {/* Aspect Ratio */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, marginBottom: 10 }}>
                    {ASPECT_RATIOS.map(r => (
                      <button key={r.id} onClick={() => u("aspect_ratio", r.id)}
                        style={{ padding: "6px 3px", borderRadius: 6, textAlign: "center",
                          border: config.aspect_ratio === r.id ? "1px solid rgba(99,102,241,0.5)" : "1px solid rgba(255,255,255,0.08)",
                          background: config.aspect_ratio === r.id ? "rgba(99,102,241,0.12)" : "rgba(255,255,255,0.02)",
                          color: config.aspect_ratio === r.id ? "#fff" : "#777", cursor: "pointer" }}>
                        <div style={{ fontSize: "1rem" }}>{r.icon}</div>
                        <div style={{ fontSize: "0.55rem", fontWeight: 600 }}>{r.label}</div>
                        <div style={{ fontSize: "0.45rem", opacity: 0.5 }}>{r.desc}</div>
                      </button>))}
                  </div>

                  {/* Duration + Clip Count */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 2 }}>Duration: {config.target_duration}s</label>
                      <input type="range" min={15} max={180} step={5} value={config.target_duration} onChange={e => u("target_duration", Number(e.target.value))}
                        style={{ width: "100%", accentColor: "#6366f1" }} />
                    </div>
                    <div>
                      <label style={{ fontSize: "0.6rem", color: "#666", display: "block", marginBottom: 2 }}>Clips: {config.clip_count}</label>
                      <input type="range" min={1} max={10} value={config.clip_count} onChange={e => u("clip_count", Number(e.target.value))}
                        style={{ width: "100%", accentColor: "#6366f1" }} />
                    </div>
                  </div>

                  {/* ── ADVANCED TOGGLES (NEW!) ── */}
                  <div style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: 10, padding: 10, marginBottom: 8 }}>
                    <h4 style={{ fontSize: "0.65rem", color: "#8b5cf6", marginBottom: 8, display: "flex", alignItems: "center", gap: 4 }}>
                      <FiTarget /> Advanced Features (Opus-Clip Level)
                    </h4>

                    <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 0", cursor: "pointer", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <FiUserCheck style={{ color: config.face_tracking ? "#4ade80" : "#555" }} />
                        <span style={{ fontSize: "0.65rem", color: "#ccc" }}>Face Tracking & Auto-Zoom</span>
                        <span style={{ fontSize: "0.5rem", color: "#555" }}>MediaPipe AI — detects face, smoothly zooms to speaker</span>
                      </span>
                      <input type="checkbox" checked={config.face_tracking} onChange={e => u("face_tracking", e.target.checked)}
                        style={{ accentColor: "#6366f1", width: 16, height: 16 }} />
                    </label>

                    <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 0", cursor: "pointer", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <FiUsers style={{ color: config.diarization ? "#4ade80" : "#555" }} />
                        <span style={{ fontSize: "0.65rem", color: "#ccc" }}>Multi-Speaker Detection</span>
                        <span style={{ fontSize: "0.5rem", color: "#555" }}>WhisperX Diarization — each speaker gets unique subtitle color</span>
                      </span>
                      <input type="checkbox" checked={config.diarization} onChange={e => u("diarization", e.target.checked)}
                        style={{ accentColor: "#6366f1", width: 16, height: 16 }} />
                    </label>

                    <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 0", cursor: "pointer" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <FiTarget style={{ color: config.dynamic_subtitle_position ? "#4ade80" : "#555" }} />
                        <span style={{ fontSize: "0.65rem", color: "#ccc" }}>Dynamic Subtitle Position</span>
                        <span style={{ fontSize: "0.5rem", color: "#555" }}>Subtitles follow speaker position automatically</span>
                      </span>
                      <input type="checkbox" checked={config.dynamic_subtitle_position} onChange={e => u("dynamic_subtitle_position", e.target.checked)}
                        style={{ accentColor: "#6366f1", width: 16, height: 16 }} />
                    </label>
                  </div>

                  {/* Other toggles */}
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 3, fontSize: "0.65rem", color: "#aaa", cursor: "pointer" }}>
                      <input type="checkbox" checked={config.auto_zoom} onChange={e => u("auto_zoom", e.target.checked)}
                        style={{ accentColor: "#6366f1" }} /> Auto-Zoom
                    </label>
                    <select value={config.language || ""} onChange={e => u("language", e.target.value || null)}
                      style={{ padding: "5px 8px", borderRadius: 5, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.04)", color: "#fff", fontSize: "0.65rem" }}>
                      <option value="">Auto-detect Language</option>
                      <option value="en">English</option><option value="id">Indonesian</option>
                      <option value="es">Spanish</option><option value="fr">French</option>
                      <option value="de">German</option><option value="pt">Portuguese</option>
                      <option value="ja">Japanese</option><option value="ko">Korean</option>
                    </select>
                  </div>
                </GlassPanel>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div style={{ textAlign: "center", marginTop: 24, padding: 12, color: "#333", fontSize: "0.6rem" }}>
        Nexus-Clipper AI Ultra v2.0 · WhisperX + MediaPipe + FFmpeg · 100% Free & Open Source · No B-Roll · No API Keys
      </div>
    </div>
  );
}
