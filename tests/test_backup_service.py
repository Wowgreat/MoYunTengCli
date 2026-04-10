import unittest
import json
import tempfile
from pathlib import Path

from myt_cli.api import MytApp
from myt_cli.config import AppConfig, AuthConfig, BackupConfig, BoxConfig, LoggingConfig, RestoreConfig, TaskConfig
from myt_cli.config import BackupConfig
from myt_cli.exceptions import ConfigError
from myt_cli.services.backup_service import BackupService


class StubClient:
    def __init__(self, backups_response=None, export_failures=None):
        self.exported_names = []
        self.export_timeouts = []
        self.backups_response = backups_response or {"list": []}
        self.export_failures = export_failures or {}

    def export_vm(self, name, *, timeout_seconds=None):
        self.exported_names.append(name)
        self.export_timeouts.append(timeout_seconds)
        error = self.export_failures.get(name)
        if error is not None:
            raise error
        return {"exportName": "exported.zip"}

    def list_backups(self, *, name=None):
        return self.backups_response


class StubVmService:
    def __init__(self, items=None):
        self.items = items or [
            {
                "id": "vm-1",
                "name": "1775617170315_1_T0001",
                "status": "running",
            }
        ]

    def list_vms(self):
        return self.items

    def get_vm_by_name(self, name):
        for item in self.items:
            if item.get("name") == name:
                return item
        for item in self.items:
            item_name = item.get("name")
            if isinstance(item_name, str) and item_name.endswith(f"_{name}"):
                return item
        raise KeyError(name)


class BackupServiceTests(unittest.TestCase):
    def test_backup_uses_resolved_vm_name_for_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            client = StubClient()
            service = BackupService(
                client,
                StubVmService(),
                BackupConfig(
                    name_template="{vm}_{date}.zip",
                    download_dir=str(Path(temp_dir) / "artifacts" / "backups"),
                    export_timeout_seconds=300,
                ),
            )

            result = service.backup_vm("T0001")

        self.assertEqual(["1775617170315_1_T0001"], client.exported_names)
        self.assertEqual([300], client.export_timeouts)
        self.assertEqual("1775617170315_1_T0001", result["vm_name"])
        self.assertEqual("exported.zip", result["export_name"])

    def test_list_backups_returns_parsed_items(self):
        client = StubClient(backups_response={"list": [{"name": "b1.tar.gz"}]})
        service = BackupService(
            client,
            StubVmService(),
            BackupConfig(),
        )

        result = service.list_backups()

        self.assertEqual([{"name": "b1.tar.gz"}], result)

    def test_backup_vm_appends_mapping_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir) / "artifacts" / "backups"
            service = BackupService(
                StubClient(),
                StubVmService(),
                BackupConfig(download_dir=str(download_dir)),
            )

            result = service.backup_vm("T0001")
            mapping_path = download_dir.parent / "backup-mapping.json"
            records = json.loads(mapping_path.read_text(encoding="utf-8"))

        self.assertEqual("exported.zip", result["export_name"])
        self.assertEqual(1, len(records))
        self.assertEqual("1775617170315_1_T0001", records[0]["vm_name"])
        self.assertEqual("exported.zip", records[0]["backup_name"])
        self.assertIn("created_at", records[0])

    def test_backup_all_vms_skips_empty_slots_and_continues_after_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            client = StubClient(
                export_failures={"1775617170315_1_T0002": RuntimeError("boom")},
            )
            download_dir = Path(temp_dir) / "artifacts" / "backups"
            service = BackupService(
                client,
                StubVmService(
                    items=[
                        {"id": "vm-1", "name": "1775617170315_1_T0001", "status": "running"},
                        {"id": "slot-2", "name": "", "status": "empty"},
                        {"id": "vm-2", "name": "1775617170315_1_T0002", "status": "stopped"},
                    ]
                ),
                BackupConfig(download_dir=str(download_dir)),
            )

            result = service.backup_all_vms()
            mapping_path = download_dir.parent / "backup-mapping.json"
            records = json.loads(mapping_path.read_text(encoding="utf-8"))

        self.assertEqual(
            ["1775617170315_1_T0001", "1775617170315_1_T0002"],
            client.exported_names,
        )
        self.assertEqual(2, result["total"])
        self.assertEqual(1, result["success_count"])
        self.assertEqual(1, result["failure_count"])
        self.assertEqual(1, result["skipped_count"])
        self.assertEqual("1775617170315_1_T0001", result["successes"][0]["vm_name"])
        self.assertEqual("1775617170315_1_T0002", result["failures"][0]["vm_name"])
        self.assertEqual("boom", result["failures"][0]["error"])
        self.assertEqual(1, len(records))
        self.assertEqual("1775617170315_1_T0001", records[0]["vm_name"])

    def test_backup_vm_rejects_invalid_mapping_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir) / "artifacts" / "backups"
            mapping_path = download_dir.parent / "backup-mapping.json"
            mapping_path.parent.mkdir(parents=True, exist_ok=True)
            mapping_path.write_text('{"broken": true}', encoding="utf-8")
            service = BackupService(
                StubClient(),
                StubVmService(),
                BackupConfig(download_dir=str(download_dir)),
            )

            with self.assertRaises(ConfigError):
                service.backup_vm("T0001")


class MytAppBackupSdkTests(unittest.TestCase):
    def test_sdk_exposes_list_backups(self):
        config = AppConfig(
            box=BoxConfig(
                base_url="http://127.0.0.1:8000",
                timeout_seconds=30,
                verify_ssl=False,
                auth=AuthConfig(type="basic", username="admin", password="change-me"),
            ),
            task=TaskConfig(),
            backup=BackupConfig(),
            restore=RestoreConfig(),
            logging=LoggingConfig(),
        )
        app = MytApp(config)
        app.client = StubClient(backups_response={"list": [{"name": "sdk-backup.tar.gz"}]})
        app.backup_service = BackupService(app.client, app.vm_service, config.backup)

        result = app.list_backups()

        self.assertEqual([{"name": "sdk-backup.tar.gz"}], result)

    def test_sdk_exposes_backup_all_vms(self):
        config = AppConfig(
            box=BoxConfig(
                base_url="http://127.0.0.1:8000",
                timeout_seconds=30,
                verify_ssl=False,
                auth=AuthConfig(type="basic", username="admin", password="change-me"),
            ),
            task=TaskConfig(),
            backup=BackupConfig(),
            restore=RestoreConfig(),
            logging=LoggingConfig(),
        )
        app = MytApp(config)
        app.client = StubClient()
        app.vm_service = StubVmService(
            items=[{"id": "vm-1", "name": "1775617170315_1_T0001", "status": "running"}]
        )
        app.backup_service = BackupService(app.client, app.vm_service, config.backup)

        result = app.backup_all_vms()

        self.assertEqual(1, result["total"])
        self.assertEqual(1, result["success_count"])
        self.assertEqual(0, result["failure_count"])


if __name__ == "__main__":
    unittest.main()
