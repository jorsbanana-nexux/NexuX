"""Tests for yt-dlp resilience: anti-403 args, proxy support, self-updater."""
import os
import subprocess
import importlib
from unittest.mock import patch, MagicMock

import pytest


def _reload_env(**env):
    """Reload constants+download with a fresh env, return the download module."""
    for k in ("NEXUX_COOKIES_FILE", "NEXUX_COOKIES_BROWSER", "NEXUX_PLAYER_CLIENTS",
              "NEXUX_PROXY", "NEXUX_YTDLP_AUTO_UPDATE", "NEXUX_YTDLP_PIP_ARGS"):
        os.environ.pop(k, None)
    os.environ.update(env)
    import engine.constants as constants
    importlib.reload(constants)
    import engine.download as download
    importlib.reload(download)
    return download


class TestCommonArgs:
    def test_default_args_empty(self):
        dl = _reload_env()
        assert dl._ytdlp_common_args() == []

    def test_cookies_file(self):
        dl = _reload_env(NEXUX_COOKIES_FILE="/tmp/cookies.txt")
        assert dl._ytdlp_common_args() == ["--cookies", "/tmp/cookies.txt"]

    def test_cookies_browser_used_when_no_file(self):
        dl = _reload_env(NEXUX_COOKIES_BROWSER="chrome")
        assert dl._ytdlp_common_args() == ["--cookies-from-browser", "chrome"]

    def test_cookies_file_wins_over_browser(self):
        dl = _reload_env(NEXUX_COOKIES_FILE="/tmp/c.txt", NEXUX_COOKIES_BROWSER="chrome")
        assert "--cookies-from-browser" not in dl._ytdlp_common_args()

    def test_player_clients(self):
        dl = _reload_env(NEXUX_PLAYER_CLIENTS="android,ios")
        assert dl._ytdlp_common_args() == ["--extractor-args",
                                           "youtube:player_client=android,ios"]

    def test_proxy(self):
        dl = _reload_env(NEXUX_PROXY="socks5://127.0.0.1:1080")
        assert dl._ytdlp_common_args() == ["--proxy", "socks5://127.0.0.1:1080"]

    def test_args_present_in_all_commands(self):
        dl = _reload_env(NEXUX_PROXY="http://proxy:8080")
        with patch.object(dl.subprocess, "run") as m:
            m.return_value = MagicMock(returncode=1, stderr="probe")
            # get_video_info raises on failure — fine, we only inspect argv
            with pytest.raises(RuntimeError):
                dl.get_video_info("https://youtube.com/watch?v=x")
            cmd = m.call_args[0][0]
            assert "--proxy" in cmd
            assert cmd[cmd.index("--proxy") + 1] == "http://proxy:8080"


class TestSelfUpdater:
    def test_403_triggers_reactive_update_and_single_retry(self):
        dl = _reload_env()
        calls = []

        def fake_run(cmd, **kw):
            calls.append(cmd)
            if len(calls) == 1:
                return MagicMock(returncode=1, stderr="ERROR: HTTP Error 403: Forbidden")
            return MagicMock(returncode=0, stdout='{"title": "ok", "duration": 1}')

        with patch.object(dl.subprocess, "run", side_effect=fake_run), \
             patch.object(dl.ytdlp_updater, "update_now", return_value=True) as upd:
            info = dl.get_video_info("https://youtube.com/watch?v=x")
        assert info["title"] == "ok"
        upd.assert_called_once()
        assert len(calls) == 2  # exactly one retry

    def test_non_403_failure_does_not_update(self):
        dl = _reload_env()
        with patch.object(dl.subprocess, "run",
                          return_value=MagicMock(returncode=1, stderr="Video unavailable")), \
             patch.object(dl.ytdlp_updater, "update_now") as upd:
            with pytest.raises(RuntimeError):
                dl.get_video_info("https://youtube.com/watch?v=x")
        upd.assert_not_called()

    def test_update_now_disabled_by_env(self):
        _reload_env(NEXUX_YTDLP_AUTO_UPDATE="0")
        import engine.constants as constants
        importlib.reload(constants)
        import engine.ytdlp_updater as updater
        importlib.reload(updater)
        assert updater.update_now(reason="test") is False
        assert updater.maybe_update_on_403("HTTP Error 403: Forbidden") is False
        # restore default for other tests
        _reload_env()

    def test_update_now_verifies_version_and_never_raises(self):
        _reload_env()
        import engine.ytdlp_updater as updater
        importlib.reload(updater)
        # pip failing must be swallowed, not propagated
        with patch.object(updater.subprocess, "run",
                          return_value=MagicMock(returncode=1, stderr="boom")):
            assert updater.update_now(reason="test") is False
        # subprocess raising (e.g. pip missing) must also be swallowed
        with patch.object(updater.subprocess, "run", side_effect=OSError("no pip")):
            assert updater.update_now(reason="test") is False

    def test_pip_cmd_is_deterministic_list_no_shell(self):
        _reload_env(NEXUX_YTDLP_PIP_ARGS="--index-url,https://example.com/simple")
        import engine.ytdlp_updater as updater
        importlib.reload(updater)
        cmd = updater._build_pip_cmd()
        assert isinstance(cmd, list)
        assert "yt-dlp" in cmd and "--upgrade" in cmd
        i = cmd.index("--index-url")
        assert cmd[i + 1] == "https://example.com/simple"
        _reload_env()

    def test_background_updater_thread_starts(self):
        _reload_env()
        import engine.ytdlp_updater as updater
        importlib.reload(updater)
        started = []
        with patch.object(updater.threading, "Thread") as T:
            T.return_value.start = lambda: started.append(True)
            updater.start_background_updater()
        assert started, "daemon thread should be started"
        # second call is a no-op (idempotent)
        with patch.object(updater.threading, "Thread") as T2:
            updater.start_background_updater()
            T2.assert_not_called()
