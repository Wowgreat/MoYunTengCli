import time
from typing import Any, Callable, Dict, Optional

from myt_cli.exceptions import TaskFailedError, TaskTimeoutError


def wait_for_task(
    fetch_status: Callable[[], Dict[str, Any]],
    *,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_status = None  # type: Optional[Dict[str, Any]]
    while time.time() < deadline:
        last_status = fetch_status()
        status = str(last_status.get("status", "")).lower()
        if status in {"success", "done", "completed"}:
            return last_status
        if status in {"failed", "error"}:
            raise TaskFailedError(str(last_status))
        time.sleep(poll_interval_seconds)
    raise TaskTimeoutError(f"Timed out waiting for task: {last_status}")
