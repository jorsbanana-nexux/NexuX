from __future__ import annotations

import os
import signal
import subprocess
import threading
from collections.abc import Sequence
from typing import Any

_PROCESSES: dict[str, subprocess.Popen[Any]] = {}
_LOCK = threading.RLock()


def run(
    cmd: Sequence[str],
    *,
    key: str | None = None,
    timeout: int | float | None = None,
    cwd: str | None = None,
    text: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[Any]:
    kwargs: dict[str, Any] = {"cwd": cwd, "text": text}
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    else:
        kwargs["stdout"] = None
        kwargs["stderr"] = None
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    process = subprocess.Popen(list(cmd), **kwargs)
    if key:
        with _LOCK:
            _PROCESSES[key] = process
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        terminate(key or process)
        stdout, stderr = process.communicate()
        raise TimeoutError(f"Process timed out after {timeout}s: {cmd[0]}")
    finally:
        if key:
            with _LOCK:
                _PROCESSES.pop(key, None)


def terminate(key_or_process: str | subprocess.Popen[Any]) -> bool:
    if isinstance(key_or_process, str):
        with _LOCK:
            process = _PROCESSES.get(key_or_process)
    else:
        process = key_or_process
    if process is None or process.poll() is not None:
        return False
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
        return True
    except (OSError, subprocess.SubprocessError):
        try:
            process.kill()
        except OSError:
            return False
        return True


def is_running(key: str) -> bool:
    with _LOCK:
        process = _PROCESSES.get(key)
    return bool(process and process.poll() is None)
