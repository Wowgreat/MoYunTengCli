from typing import Any, Dict, Optional

from myt_cli.client import AndroidVmClient, MytClient
from myt_cli.services.vm_service import VmService


class S5Service:
    def __init__(self, client: MytClient, vm_service: VmService) -> None:
        self._client = client
        self._vm_service = vm_service

    def get_status(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        android_client = self._build_android_client(vm)
        payload = android_client.get_s5_status()
        return {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "android_api_host": android_client._host,
            "android_api_port": android_client._port,
            "proxy": payload.get("data", {}),
            "message": payload.get("msg"),
        }

    def set_proxy(
        self,
        *,
        name: str,
        proxy_ip: str,
        proxy_port: int,
        proxy_user: str,
        proxy_password: str,
        proxy_type: Optional[int],
    ) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        android_client = self._build_android_client(vm)
        payload = android_client.set_s5_proxy(
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_password=proxy_password,
            proxy_type=proxy_type,
        )
        return {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "android_api_host": android_client._host,
            "android_api_port": android_client._port,
            "message": payload.get("msg"),
            "proxy_ip": proxy_ip,
            "proxy_port": proxy_port,
            "proxy_type": proxy_type,
        }

    def stop_proxy(self, name: str) -> Dict[str, Any]:
        vm = self._vm_service.get_vm_by_name(name)
        android_client = self._build_android_client(vm)
        payload = android_client.stop_s5_proxy()
        return {
            "vm_name": vm.get("name"),
            "vm_id": vm.get("id"),
            "android_api_host": android_client._host,
            "android_api_port": android_client._port,
            "message": payload.get("msg"),
        }

    def _build_android_client(self, vm: Dict[str, Any]) -> AndroidVmClient:
        device_info = self._client.get_device_info()
        host = str(device_info.get("ip") or vm.get("ip") or "").strip()
        port = self._resolve_android_api_port(vm)

        return AndroidVmClient(
            host=host,
            port=port,
            timeout_seconds=self._client._config.timeout_seconds,
            verify_ssl=self._client._config.verify_ssl,
        )

    def _resolve_android_api_port(self, vm: Dict[str, Any]) -> int:
        port_bindings = vm.get("portBindings") or {}

        # In your real environment, MYT Android API is reachable through the
        # box IP plus the mapped 9082/tcp host port, such as box_ip:30001.
        mapped_port = self._extract_host_port(port_bindings, "9082/tcp")
        if mapped_port is not None:
            return mapped_port

        # Keep fallbacks in case another machine exposes the proxy API on 10008.
        mapped_port = self._extract_host_port(port_bindings, "10008/tcp")
        if mapped_port is not None:
            return mapped_port

        index_num = int(vm.get("indexNum") or 0)
        if index_num > 0:
            return 30000 + (index_num - 1) * 100 + 1
        return 9082

    def _extract_host_port(self, port_bindings: Dict[str, Any], key: str) -> Optional[int]:
        bindings = port_bindings.get(key)
        if not isinstance(bindings, list) or not bindings:
            return None
        host_port = bindings[0].get("HostPort")
        if host_port in (None, ""):
            return None
        try:
            return int(host_port)
        except (TypeError, ValueError):
            return None
