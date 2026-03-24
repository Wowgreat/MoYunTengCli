import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from myt_cli.config import BoxConfig
from myt_cli.exceptions import ApiRequestError, AuthError


LOGGER = logging.getLogger(__name__)


class MytClient:
    """Thin wrapper around the documented API endpoints."""

    def __init__(self, config: BoxConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        auth_type = config.auth.type
        if auth_type == "basic":
            self._session.auth = (config.auth.username or "admin", config.auth.password or "")
        elif auth_type == "bearer":
            token = config.auth.token or ""
            self._session.headers["Authorization"] = f"Bearer {token}"

    def list_vms(self, *, name: Optional[str] = None, running: Optional[bool] = None, index_num: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if name:
            params["name"] = name
        if running is not None:
            params["running"] = str(running).lower()
        if index_num is not None:
            params["indexNum"] = index_num
        return self._request("GET", "/android", params=params)

    def start_vm(self, name: str) -> Dict[str, Any]:
        return self._request("POST", "/android/start", json={"name": name})

    def stop_vm(self, name: str) -> Dict[str, Any]:
        return self._request("POST", "/android/stop", json={"name": name})

    def delete_vm(self, name: str) -> Dict[str, Any]:
        return self._request("DELETE", "/android", json={"name": name})

    def export_vm(self, name: str) -> Dict[str, Any]:
        return self._request("POST", "/android/export", json={"name": name})

    def list_backups(self, *, name: Optional[str] = None) -> Dict[str, Any]:
        params = {"name": name} if name else None
        return self._request("GET", "/backup", params=params)

    def download_backup(self, name: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = self._session.get(
            self._url("/backup/download"),
            params={"name": name},
            timeout=self._config.timeout_seconds,
            verify=self._config.verify_ssl,
            stream=True,
        )
        self._raise_for_status(response)
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return destination

    def import_vm(self, *, archive_path: Path, index_num: int, name: Optional[str] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {"indexNum": str(index_num)}
        if name:
            data["name"] = name
        with archive_path.open("rb") as file_handle:
            files = {"file": (archive_path.name, file_handle, "application/zip")}
            return self._request("POST", "/android/import", data=data, files=files)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return self._request("GET", "/android/task-status", params={"taskId": task_id})

    def get_device_info(self) -> Dict[str, Any]:
        return self._request("GET", "/info/device")

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        LOGGER.debug("request %s %s", method, path)
        try:
            response = self._session.request(
                method=method,
                url=self._url(path),
                timeout=self._config.timeout_seconds,
                verify=self._config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiRequestError(f"Request failed for {path}: {exc}") from exc
        self._raise_for_status(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiRequestError(f"Invalid JSON response from {path}") from exc

        code = payload.get("code")
        if code not in (0, "0", None):
            message = payload.get("message", "unknown API error")
            if code == 401:
                raise AuthError(message)
            raise ApiRequestError(f"{path}: {message}")
        return payload.get("data") or {}

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.status_code == 401:
            raise AuthError("Authentication failed")
        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get("message") or response.text
            except ValueError:
                message = response.text
            raise ApiRequestError(f"HTTP {response.status_code}: {message}")

    def _url(self, path: str) -> str:
        return f"{self._config.base_url}{path}"


class AndroidVmClient:
    """Client for MYT Android API endpoints served by a single VM."""

    def __init__(self, *, host: str, port: int, timeout_seconds: int, verify_ssl: bool) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def get_s5_status(self) -> Dict[str, Any]:
        return self._request("GET", "/proxy")

    def set_s5_proxy(
        self,
        *,
        proxy_ip: str,
        proxy_port: int,
        proxy_user: str,
        proxy_password: str,
        proxy_type: Optional[int],
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "cmd": 2,
            "ip": proxy_ip,
            "port": proxy_port,
            "usr": proxy_user,
            "pwd": proxy_password,
        }
        if proxy_type is not None:
            params["type"] = proxy_type
        return self._request("GET", "/proxy", params=params)

    def stop_s5_proxy(self) -> Dict[str, Any]:
        return self._request("GET", "/proxy", params={"cmd": 3})

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            response = self._session.request(
                method=method,
                url=self._url(path),
                timeout=self._timeout_seconds,
                verify=self._verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiRequestError(f"Android API request failed for {path}: {exc}") from exc
        if response.status_code >= 400:
            raise ApiRequestError(f"Android API HTTP {response.status_code}: {response.text}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiRequestError(f"Invalid Android API JSON response from {path}") from exc

        code = payload.get("code")
        if code not in (200, "200"):
            message = payload.get("error") or payload.get("msg") or "unknown Android API error"
            raise ApiRequestError(f"{path}: {message}")
        return payload

    def _url(self, path: str) -> str:
        return f"http://{self._host}:{self._port}{path}"
