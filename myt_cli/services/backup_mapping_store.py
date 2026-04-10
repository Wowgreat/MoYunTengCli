import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from myt_cli.exceptions import ConfigError


class BackupMappingStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, *, vm_name: str, backup_name: str) -> None:
        records = self._read_records()
        records.append(
            {
                "vm_name": vm_name,
                "backup_name": backup_name,
                "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
            }
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_records(self) -> List[Dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid backup mapping file: {self._path}") from exc
        if not isinstance(raw, list):
            raise ConfigError(f"Backup mapping file must be a JSON array: {self._path}")
        return [item for item in raw if isinstance(item, dict)]
