import React from "react";
import { motion } from "framer-motion";
import GlassPanel from "./GlassPanel";

const STAGES = ["Research", "Script & Audio", "Visual", "Execution", "QA & Export"];

export default function PipelineVisualizer() {
  return (
    <GlassPanel style={{ marginBottom: 20 }}>
      <h3 style={{ color: "#888", fontSize: "0.85rem", marginBottom: 16 }}>
        Pipeline Status
      </h3>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {STAGES.map((stage, i) => (
          <React.Fragment key={i}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15 }}
              style={{
                padding: "12px 16px", borderRadius: 12,
                background: "rgba(99,102,241,0.1)",
                border: "1px solid rgba(99,102,241,0.2)",
                fontSize: "0.8rem", color: "#ccc",
                textAlign: "center", minWidth: 100,
              }}
            >
              {stage}
            </motion.div>
            {i < STAGES.length - 1 && (
              <motion.div
                initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
                transition={{ delay: i * 0.15 + 0.1 }}
                style={{ width: 30, height: 1, background: "rgba(99,102,241,0.3)", transformOrigin: "left" }}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </GlassPanel>
  );
}
