"""Nexus-Clipper v3 — Centralized Logging"""
import logging, sys, json
from datetime import datetime
from typing import Optional, Callable

_ws_callbacks: list = []

def register_ws_broadcast(callback: Callable):
    _ws_callbacks.append(callback)

def broadcast_log(level: str, agent_id: str, message: str, data=None):
    payload = json.dumps({
        "type": "agent_log",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "agent_id": agent_id,
        "message": message,
        "data": data or {},
    })
    for cb in _ws_callbacks:
        try:
            cb(payload)
        except Exception:
            pass

class AgentLogger:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"nexus.agent.{agent_id}")
        if not self.logger.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(logging.Formatter(
                f"%(asctime)s | {agent_id} | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"))
            self.logger.addHandler(h)
            self.logger.setLevel(logging.INFO)

    def info(self, msg, **data):
        self.logger.info(msg)
        broadcast_log("info", self.agent_id, msg, data)

    def warn(self, msg, **data):
        self.logger.warning(msg)
        broadcast_log("warn", self.agent_id, msg, data)

    def error(self, msg, **data):
        self.logger.error(msg)
        broadcast_log("error", self.agent_id, msg, data)

    def success(self, msg, **data):
        self.logger.info(f"[SUCCESS] {msg}")
        broadcast_log("success", self.agent_id, msg, data)

def setup_logging(level="INFO"):
    root = logging.getLogger("nexus")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

def get_logger(agent_id: str = "main") -> AgentLogger:
    return AgentLogger(agent_id)
