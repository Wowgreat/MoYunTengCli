from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

from myt_cli.client import MytClient
from myt_cli.config import BackupConfig, RestoreConfig
from myt_cli.exceptions import ConflictError, MultipleMatchesError, NotFoundError
from myt_cli.services.vm_service import VmService


class RestoreService:
    def __init__(
        self,
        client: MytClient,
        vm_service: VmService,
        backup_config: BackupConfig,
        restore_config: RestoreConfig,
    ) -> None:
        self._client = client
        self._vm_service = vm_service
        self._backup_config = backup_config
        self._restore_config = restore_config

    def restore_backup(self, *, backup_name: str, index_num: Optional[int], target_name: Optional[str]) -> Dict[str, Any]:
        backup = self._find_backup(backup_name)
        if target_name:
            self._ensure_target_name_available(target_name)
        selected_index_num = index_num or self._vm_service.find_first_free_index_num(
            max_index_num=self._restore_config.max_index_num
        )
        with TemporaryDirectory(prefix="myt-cli-restore-") as temp_dir:
            archive_path = Path(temp_dir) / backup["name"]
            self._client.download_backup(backup["name"], archive_path)
            imported = self._client.import_vm(
                archive_path=archive_path,
                index_num=selected_index_num,
                name=target_name,
            )
        resulting_name = imported.get("name") or target_name or backup["name"]
        vm = self._vm_service.get_vm_by_name(resulting_name)
        return {
            "backup_name": backup["name"],
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "status": vm.get("status"),
            "index_num": selected_index_num,
        }

    def _find_backup(self, backup_name: str) -> Dict[str, Any]:
        data = self._client.list_backups(name=backup_name)
        candidates = [item for item in self._extract_items(data) if item.get("name") == backup_name]
        if not candidates:
            raise NotFoundError(f"Backup not found: {backup_name}")
        if len(candidates) > 1:
            raise MultipleMatchesError(f"Multiple backups matched name: {backup_name}")
        return candidates[0]

    def _ensure_target_name_available(self, target_name: str) -> None:
        try:
            self._vm_service.get_vm_by_name(target_name)
        except NotFoundError:
            return
        raise ConflictError(f"Target VM name already exists: {target_name}")

    def _extract_items(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            raw_items = data.get("list", data.get("items", data.get("data", [])))
            if isinstance(raw_items, list):
                return [item for item in raw_items if isinstance(item, dict)]
        return []
