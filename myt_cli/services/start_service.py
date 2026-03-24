from typing import Any, Dict

from myt_cli.client import MytClient
from myt_cli.services.vm_service import VmService


class StartService:
    def __init__(self, client: MytClient, vm_service: VmService) -> None:
        self._client = client
        self._vm_service = vm_service

    def start_vm(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        status = str(vm.get("status", "")).lower()
        if status == "running":
            return {
                "vm_name": vm.get("name"),
                "vm_id": vm.get("id"),
                "status": "running",
                "changed": False,
            }
        self._client.start_vm(name)
        refreshed = self._vm_service.get_vm_by_name(name)
        return {
            "vm_name": refreshed.get("name"),
            "vm_id": refreshed.get("id"),
            "status": refreshed.get("status"),
            "changed": True,
        }

    def stop_vm(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        status = str(vm.get("status", "")).lower()
        if status in {"stopped", "stop", "exited"}:
            return {
                "vm_name": vm.get("name"),
                "vm_id": vm.get("id"),
                "status": status or "stopped",
                "changed": False,
            }
        self._client.stop_vm(name)
        refreshed = self._vm_service.get_vm_by_name(name)
        return {
            "vm_name": refreshed.get("name"),
            "vm_id": refreshed.get("id"),
            "status": refreshed.get("status"),
            "changed": True,
        }

    def delete_vm(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        self._client.delete_vm(name)
        return {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "deleted": True,
        }
