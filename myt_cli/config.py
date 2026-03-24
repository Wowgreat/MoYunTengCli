from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from myt_cli.exceptions import ConfigError


@dataclass
class AuthConfig:
    type: str = "none"
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None


@dataclass
class BoxConfig:
    base_url: str
    timeout_seconds: int = 30
    verify_ssl: bool = False
    auth: AuthConfig = field(default_factory=AuthConfig)


@dataclass
class TaskConfig:
    poll_interval_seconds: int = 5
    timeout_seconds: int = 1800


@dataclass
class BackupConfig:
    name_template: str = "{vm}_{date}.zip"
    download_dir: str = "artifacts/backups"


@dataclass
class RestoreConfig:
    max_index_num: int = 24


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/myt-cli.log"


@dataclass
class AppConfig:
    box: BoxConfig
    task: TaskConfig
    backup: BackupConfig
    restore: RestoreConfig
    logging: LoggingConfig


def _require(mapping: Dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing config key: {key}")
    return mapping[key]


def load_config(path: Union[str, Path]) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    box_raw = _require(raw, "box")
    auth_raw = box_raw.get("auth", {})
    auth = AuthConfig(
        type=str(auth_raw.get("type", "none")).lower(),
        username=auth_raw.get("username"),
        password=auth_raw.get("password"),
        token=auth_raw.get("token"),
    )
    box = BoxConfig(
        base_url=str(_require(box_raw, "base_url")).rstrip("/"),
        timeout_seconds=int(box_raw.get("timeout_seconds", 30)),
        verify_ssl=bool(box_raw.get("verify_ssl", False)),
        auth=auth,
    )
    task_raw = raw.get("task", {})
    backup_raw = raw.get("backup", {})
    restore_raw = raw.get("restore", {})
    logging_raw = raw.get("logging", {})
    return AppConfig(
        box=box,
        task=TaskConfig(
            poll_interval_seconds=int(task_raw.get("poll_interval_seconds", 5)),
            timeout_seconds=int(task_raw.get("timeout_seconds", 1800)),
        ),
        backup=BackupConfig(
            name_template=str(backup_raw.get("name_template", "{vm}_{date}.zip")),
            download_dir=str(backup_raw.get("download_dir", "artifacts/backups")),
        ),
        restore=RestoreConfig(
            max_index_num=int(restore_raw.get("max_index_num", 24)),
        ),
        logging=LoggingConfig(
            level=str(logging_raw.get("level", "INFO")).upper(),
            file=str(logging_raw.get("file", "logs/myt-cli.log")),
        ),
    )
