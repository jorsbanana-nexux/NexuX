import { useState, useEffect, useRef, useCallback } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";
const POLL_INTERVAL = 1000;

export default function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [agentStatus, setAgentStatus] = useState({});
  const [logs, setLogs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [wsMode, setWsMode] = useState(false);
  const pollTimerRef = useRef(null);
  const isUnmountingRef = useRef(false);
  const lastJobIdRef = useRef(null);

  const trackJob = useCallback((jobId) => { lastJobIdRef.current = jobId; }, []);

  const pollBackend = useCallback(async () => {
    if (isUnmountingRef.current) return;
    try {
      const r = await fetch(`${BACKEND_URL}/api/health`);
      setConnected(r.ok);
      if (lastJobIdRef.current) {
        try {
          const jr = await fetch(`${BACKEND_URL}/api/job/${lastJobIdRef.current}`);
          if (jr.ok) setCurrentJob(await jr.json());
        } catch {}
      }
    } catch { setConnected(false); }
  }, []);

  useEffect(() => {
    isUnmountingRef.current = false;
    pollBackend();
    pollTimerRef.current = setInterval(pollBackend, POLL_INTERVAL);
    return () => { isUnmountingRef.current = true; if (pollTimerRef.current) clearInterval(pollTimerRef.current); };
  }, [pollBackend]);

  return { connected, agentStatus, logs, currentJob, sendMessage: () => true, wsMode, trackJob };
}
