import unittest

from myt_cli.client import MytClient
from myt_cli.exceptions import MultipleMatchesError, NotFoundError
from myt_cli.services.vm_service import VmService


class StubClient(MytClient):
    def __init__(self, responses):
        self._responses = responses

    def list_vms(self, *, name=None, running=None, index_num=None):
        return self._responses


class VmServiceNameLookupTests(unittest.TestCase):
    def test_get_vm_by_name_returns_exact_match(self):
        service = VmService(
            StubClient(
                {
                    "list": [
                        {"name": "1775617170315_1_T0001"},
                        {"name": "T0001"},
                    ]
                }
            )
        )

        vm = service.get_vm_by_name("T0001")

        self.assertEqual("T0001", vm["name"])

    def test_get_vm_by_name_accepts_unique_suffix_match(self):
        service = VmService(
            StubClient(
                {
                    "list": [
                        {"name": "1775617170315_1_T0001"},
                    ]
                }
            )
        )

        vm = service.get_vm_by_name("T0001")

        self.assertEqual("1775617170315_1_T0001", vm["name"])

    def test_get_vm_by_name_rejects_ambiguous_suffix_match(self):
        service = VmService(
            StubClient(
                {
                    "list": [
                        {"name": "1775617170315_1_T0001"},
                        {"name": "2775617170315_2_T0001"},
                    ]
                }
            )
        )

        with self.assertRaises(MultipleMatchesError):
            service.get_vm_by_name("T0001")

    def test_get_vm_by_name_raises_not_found_for_missing_name(self):
        service = VmService(
            StubClient(
                {
                    "list": [
                        {"name": "1775617170315_1_T0002"},
                    ]
                }
            )
        )

        with self.assertRaises(NotFoundError):
            service.get_vm_by_name("T0001")


if __name__ == "__main__":
    unittest.main()
