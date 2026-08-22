"""
NexuX V9.6.2 — yt-dlp Self-Updater
====================================
Keeps yt-dlp current so YouTube extractor fixes ship to NexuX
automatically (yt-dlp releases fixes almost weekly when YouTube
changes its bot detection).

Safety properties:
- Never runs on the hot path: background thread, delayed start.
- Process-wide threading.Lock: the updater and job-triggered updates
  can never race each other.
- Deterministic command list passed to subprocess (no shell=True).
- All failures are caught and logged — the app NEVER crashes because
  of a failed update; the previous yt-dlp version keeps working.
- Verification: after install, the version is re-read; only then is
  the update reported as applied.
- Opt-out: NEXUX_YTDLP_AUTO_UPDATE=0 disables everything (air-gapped
  or centrally managed deployments).

Two entry points:
- start_background_updater(): called once from the app lifespan.
- update_now(): reactive — called by the download layer when it sees
  a 403/bot-gate signature, so a broken extractor self-heals mid-session.
"""
import re
import sys
import time
import shutil
import logging
import subprocess
import threading

from .constants import YTDLP_AUTO_UPDATE, YTDLP_UPDATE_DELAY, YTDLP_PIP_EXTRA_ARGS

log = logging.getLogger("nexus.ytdlp")

_update_lock = threading.Lock()
_updater_started = False

# Stderr signatures that mean "the extractor itself is broken / blocked" —
# the right remedy is updating yt-dlp, not retrying the same version.
_403_PATTERN = re.compile(r"403|forbidden", re.IGNORECASE)
_BOT_GATE_PATTERN = re.compile(
    r"Sign in to confirm|not a bot|po token|This video is unavailable",
    re.IGNORECASE,
)

# Commands the pip module understands. Defensive guard: the pip args env var
# is admin-controlled, but never allow option values to be smuggled in as
# separate argv entries that pip would treat as targets.
_PIP_FLAGS_WITH_VALUE = {"--index-url", "--extra-index-url", "--trusted-host", "--proxy"}


def _ytdlp_version() -> str:
    exe = shutil.which("yt-dlp")
    if not exe:
        return ""
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception:
        return ""


def _build_pip_cmd() -> list:
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
           "-q", "--upgrade", "yt-dlp"]
    args = list(YTDLP_PIP_EXTRA_ARGS)
    i = 0
    while i < len(args):
        flag = args[i]
        if flag in _PIP_FLAGS_WITH_VALUE and i + 1 < len(args):
            cmd += [flag, args[i + 1]]
            i += 2
        else:
            cmd.append(flag)
            i += 1
    return cmd


def update_now(reason: str = "manual") -> bool:
    """Upgrade yt-dlp to the latest release. Returns True if the version changed.

    Serialized via a process-wide lock — safe to call from any thread,
    including the download layer's reactive 403 path.
    """
    if not YTDLP_AUTO_UPDATE:
        return False
    with _update_lock:
        before = _ytdlp_version()
        log.info(f"[yt-dlp updater] Update triggered ({reason}). Installed: {before or 'not found'}")
        try:
            r = subprocess.run(
                _build_pip_cmd(),
                capture_output=True, text=True, timeout=300,
            )
            if r.returncode != 0:
                log.warning(f"[yt-dlp updater] pip upgrade failed: {r.stderr[-300:]}")
                return False
        except Exception as e:
            log.warning(f"[yt-dlp updater] Update failed (non-fatal): {e}")
            return False
        after = _ytdlp_version()
        if after and after != before:
            log.info(f"[yt-dlp updater] ✅ Updated {before or 'none'} → {after}")
            return True
        log.info(f"[yt-dlp updater] Already up to date ({after or before or 'unknown'})")
        return False


def maybe_update_on_403(stderr: str) -> bool:
    """Reactive self-heal: if a yt-dlp failure looks like YouTube's bot gate,
    try upgrading yt-dlp once. Caller decides whether to retry the download."""
    if not _403_PATTERN.search(stderr):
        return False
    if _BOT_GATE_PATTERN.search(stderr):
        log.warning("[yt-dlp updater] Bot-gate detected — see README: provide "
                    "NEXUX_COOKIES_FILE for a durable fix.")
    return update_now(reason="http-403")


def start_background_updater() -> None:
    """Kick off the delayed background self-update. Called once at app startup."""
    global _updater_started
    if not YTDLP_AUTO_UPDATE or _updater_started:
        return
    _updater_started = True

    def _loop():
        time.sleep(YTDLP_UPDATE_DELAY)  # keep startup fast
        try:
            update_now(reason="startup")
        except Exception as e:
            log.warning(f"[yt-dlp updater] Startup update failed (non-fatal): {e}")

    threading.Thread(target=_loop, daemon=True, name="ytdlp-updater").start()
    log.info(f"[yt-dlp updater] Background self-update scheduled (+{YTDLP_UPDATE_DELAY}s)")
