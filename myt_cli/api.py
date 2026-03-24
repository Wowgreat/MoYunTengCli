from pathlib import Path
from typing import Dict, List, Optional, Union

from myt_cli.client import MytClient
from myt_cli.config import AppConfig, load_config
from myt_cli.services.backup_service import BackupService
from myt_cli.services.restore_service import RestoreService
from myt_cli.services.s5_service import S5Service
from myt_cli.services.start_service import StartService
from myt_cli.services.vm_service import VmService


class MytApp:
    """Reusable Python API for the same operations exposed by the CLI."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = MytClient(config.box)
        self.vm_service = VmService(self.client)
        self.backup_service = BackupService(self.client, self.vm_service, config.backup)
        self.restore_service = RestoreService(self.client, self.vm_service, config.backup, config.restore)
        self.start_service = StartService(self.client, self.vm_service)
        self.s5_service = S5Service(self.client, self.vm_service)

    def list_vms(self) -> List[Dict]:
        return self.vm_service.list_vms()

    def get_vm_status(self, name: str) -> Dict:
        return self.vm_service.get_vm_by_name(name)

    def start_vm(self, name: str) -> Dict:
        return self.start_service.start_vm(name)

    def stop_vm(self, name: str) -> Dict:
        return self.start_service.stop_vm(name)

    def delete_vm(self, name: str) -> Dict:
        return self.start_service.delete_vm(name)

    def backup_vm(self, name: str) -> Dict:
        return self.backup_service.backup_vm(name)

    def restore_backup(self, *, backup_name: str, target_name: Optional[str] = None, index_num: Optional[int] = None) -> Dict:
        return self.restore_service.restore_backup(
            backup_name=backup_name,
            index_num=index_num,
            target_name=target_name,
        )

    def get_s5_status(self, name: str) -> Dict:
        return self.s5_service.get_status(name)

    def set_s5_proxy(
        self,
        *,
        name: str,
        proxy_ip: str,
        proxy_port: int,
        proxy_user: str,
        proxy_password: str,
        proxy_type: Optional[int] = 2,
    ) -> Dict:
        return self.s5_service.set_proxy(
            name=name,
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_password=proxy_password,
            proxy_type=proxy_type,
        )

    def stop_s5_proxy(self, name: str) -> Dict:
        return self.s5_service.stop_proxy(name)


def create_app(config: AppConfig) -> MytApp:
    return MytApp(config)


def create_app_from_path(path: Union[str, Path]) -> MytApp:
    return MytApp(load_config(path))
