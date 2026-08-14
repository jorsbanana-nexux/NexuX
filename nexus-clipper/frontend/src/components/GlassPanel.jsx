import React from "react";
import { motion } from "framer-motion";

export default function GlassPanel({ children, style, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        background: "rgba(255,255,255,0.03)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 20,
        padding: 20,
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
        ...style,
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
