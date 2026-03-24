from datetime import datetime
from typing import Any, Dict

from myt_cli.client import MytClient
from myt_cli.config import BackupConfig
from myt_cli.services.vm_service import VmService


class BackupService:
    def __init__(self, client: MytClient, vm_service: VmService, backup_config: BackupConfig) -> None:
        self._client = client
        self._vm_service = vm_service
        self._backup_config = backup_config

    def backup_vm(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        export_data = self._client.export_vm(name)
        export_name = export_data.get("exportName") or self._render_backup_name(name)
        return {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "status": vm.get("status"),
            "export_name": export_name,
        }

    def _render_backup_name(self, name: str) -> str:
        now = datetime.now()
        rendered = self._backup_config.name_template.format(
            vm=name,
            date=now.strftime("%Y%m%d"),
            time=now.strftime("%H%M%S"),
        )
        return rendered
