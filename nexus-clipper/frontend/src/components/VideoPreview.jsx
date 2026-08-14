import React from "react";
import { motion } from "framer-motion";
import { FiPlay, FiDownload, FiShare2 } from "react-icons/fi";
import GlassPanel from "./GlassPanel";

export default function VideoPreview() {
  return (
    <GlassPanel>
      <div style={{ textAlign: "center", padding: "40px 20px" }}>
        <div style={{
          width: "100%", maxWidth: 300, margin: "0 auto", aspectRatio: "9/16",
          background: "rgba(0,0,0,0.5)", borderRadius: 12,
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "1px solid rgba(99,102,241,0.3)",
        }}>
          <FiPlay style={{ fontSize: "2rem", color: "#6366f1" }} />
        </div>
        <p style={{ color: "#666", marginTop: 12, fontSize: "0.85rem" }}>
          Generated video will appear here
        </p>
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16 }}>
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#6366f1", color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem" }}
          >
            <FiDownload /> Download
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "transparent", color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem" }}
          >
            <FiShare2 /> Share
          </motion.button>
        </div>
      </div>
    </GlassPanel>
  );
}
