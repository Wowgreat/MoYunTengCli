from typing import Any, Dict, List, Optional, Set

from myt_cli.client import MytClient
from myt_cli.exceptions import MultipleMatchesError, NotFoundError


class VmService:
    def __init__(self, client: MytClient) -> None:
        self._client = client

    def list_vms(self) -> List[Dict[str, Any]]:
        data = self._client.list_vms()
        return self._extract_items(data)

    def get_vm_by_name(self, name: str) -> Dict[str, Any]:
        data = self._client.list_vms(name=name)
        items = self._extract_items(data)

        candidates = [item for item in items if item.get("name") == name]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise MultipleMatchesError(f"Multiple VMs matched name: {name}")

        suffix_candidates = [item for item in items if self._matches_name_suffix(item.get("name"), name)]
        if len(suffix_candidates) == 1:
            return suffix_candidates[0]
        if len(suffix_candidates) > 1:
            raise MultipleMatchesError(f"Multiple VMs matched name suffix: {name}")

        raise NotFoundError(f"VM not found: {name}")

    def find_first_free_index_num(self, *, max_index_num: int) -> int:
        used_indexes = set()  # type: Set[int]
        for item in self.list_vms():
            index_num = self._extract_index_num(item)
            if index_num is not None and index_num > 0:
                used_indexes.add(index_num)

        for candidate in range(1, max_index_num + 1):
            if candidate not in used_indexes:
                return candidate
        raise NotFoundError(f"No free indexNum found in range 1-{max_index_num}")

    def _extract_items(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            raw_items = data.get("list", data.get("items", data.get("data", [])))
            if isinstance(raw_items, list):
                return [item for item in raw_items if isinstance(item, dict)]
        return []

    def _extract_index_num(self, item: Dict[str, Any]) -> Optional[int]:
        for key in ("indexNum", "index", "slot", "instanceNum"):
            value = item.get(key)
            if value is None or value == "":
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return None

    def _matches_name_suffix(self, value: Any, name: str) -> bool:
        if not isinstance(value, str):
            return False
        return value.endswith(f"_{name}")
