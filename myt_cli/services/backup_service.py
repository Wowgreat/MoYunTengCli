from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from myt_cli.client import MytClient
from myt_cli.config import BackupConfig
from myt_cli.services.backup_mapping_store import BackupMappingStore
from myt_cli.services.vm_service import VmService


class BackupService:
    def __init__(self, client: MytClient, vm_service: VmService, backup_config: BackupConfig) -> None:
        self._client = client
        self._vm_service = vm_service
        self._backup_config = backup_config
        self._mapping_store = BackupMappingStore(self._resolve_mapping_path())

    def backup_vm(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        resolved_name = vm.get("name") or name
        export_data = self._client.export_vm(
            resolved_name,
            timeout_seconds=self._backup_config.export_timeout_seconds,
        )
        export_name = export_data.get("exportName") or self._render_backup_name(resolved_name)
        result = {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "status": vm.get("status"),
            "export_name": export_name,
        }
        self._mapping_store.append(
            vm_name=str(result["vm_name"] or resolved_name),
            backup_name=export_name,
        )
        return result

    def list_backups(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._client.list_backups(name=name)
        return self._extract_items(data)

    def backup_all_vms(self) -> Dict[str, Any]:
        successes: List[Dict[str, Any]] = []
        failures: List[Dict[str, str]] = []
        skipped_count = 0

        for item in self._vm_service.list_vms():
            if not self._is_occupied_vm(item):
                skipped_count += 1
                continue

            vm_name = str(item.get("name"))
            try:
                successes.append(self.backup_vm(vm_name))
            except Exception as exc:
                failures.append(
                    {
                        "vm_name": vm_name,
                        "error": str(exc),
                    }
                )

        return {
            "total": len(successes) + len(failures),
            "success_count": len(successes),
            "failure_count": len(failures),
            "skipped_count": skipped_count,
            "successes": successes,
            "failures": failures,
        }

    def _render_backup_name(self, name: str) -> str:
        now = datetime.now()
        rendered = self._backup_config.name_template.format(
            vm=name,
            date=now.strftime("%Y%m%d"),
            time=now.strftime("%H%M%S"),
        )
        return rendered

    def _extract_items(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            raw_items = data.get("list", data.get("items", data.get("data", [])))
            if isinstance(raw_items, list):
                return [item for item in raw_items if isinstance(item, dict)]
        return []

    def _is_occupied_vm(self, item: Dict[str, Any]) -> bool:
        name = item.get("name")
        return isinstance(name, str) and bool(name.strip())

    def _resolve_mapping_path(self) -> Path:
        download_dir = Path(self._backup_config.download_dir)
        return download_dir.parent / "backup-mapping.json"
