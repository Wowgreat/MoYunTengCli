import unittest
import tempfile
from pathlib import Path

from myt_cli.cli import _format_output, _resolve_config_path, build_parser


class CliFormatTests(unittest.TestCase):
    def test_format_backup_success_output(self):
        result = {
            "vm_name": "1775617170315_1_T0001",
            "vm_id": "vm-1",
            "status": "exited",
            "export_name": "1775617170315_1_T0001-2026040811-AJ6acK.tar.gz",
        }

        rendered = _format_output(result)

        self.assertIn("[OK] Backup completed", rendered)
        self.assertIn("VM: 1775617170315_1_T0001", rendered)
        self.assertIn("Backup: 1775617170315_1_T0001-2026040811-AJ6acK.tar.gz", rendered)

    def test_format_backup_list_output(self):
        result = {
            "backups": [
                {"name": "b1.tar.gz", "created": "2026-04-08 12:00:00"},
                {"name": "b2.tar.gz"},
            ]
        }

        rendered = _format_output(result)

        self.assertIn("Backup Archives:", rendered)
        self.assertIn("b1.tar.gz", rendered)
        self.assertIn("b2.tar.gz", rendered)

    def test_format_backup_all_output(self):
        result = {
            "total": 2,
            "success_count": 1,
            "failure_count": 1,
            "skipped_count": 1,
            "successes": [{"vm_name": "1775617170315_1_T0001", "export_name": "b1.tar.gz"}],
            "failures": [{"vm_name": "1775617170315_1_T0002", "error": "boom"}],
        }

        rendered = _format_output(result)

        self.assertIn("[OK] Batch backup completed", rendered)
        self.assertIn("Total: 2", rendered)
        self.assertIn("Success: 1", rendered)
        self.assertIn("Failed: 1", rendered)
        self.assertIn("Skipped: 1", rendered)
        self.assertIn("1775617170315_1_T0001", rendered)
        self.assertIn("1775617170315_1_T0002", rendered)

    def test_build_parser_supports_backups_command(self):
        args = build_parser().parse_args(["backups", "--name", "b1.tar.gz"])

        self.assertEqual("backups", args.command)
        self.assertEqual("b1.tar.gz", args.name)

    def test_build_parser_supports_backup_all_command(self):
        args = build_parser().parse_args(["backup-all"])

        self.assertEqual("backup-all", args.command)


class CliConfigResolutionTests(unittest.TestCase):
    def test_resolve_config_path_prefers_current_working_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "cwd"
            package_dir = Path(temp_dir) / "package"
            current.mkdir()
            package_dir.mkdir()
            expected = current / "config.yaml"
            expected.write_text("box:\n  base_url: test\n", encoding="utf-8")

            resolved = _resolve_config_path("config.yaml", cwd=current, package_dir=package_dir)

        self.assertEqual(expected, resolved)

    def test_resolve_config_path_falls_back_to_package_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "cwd"
            package_dir = Path(temp_dir) / "package"
            current.mkdir()
            package_dir.mkdir()
            expected = package_dir / "config.yaml"
            expected.write_text("box:\n  base_url: test\n", encoding="utf-8")

            resolved = _resolve_config_path("config.yaml", cwd=current, package_dir=package_dir)

        self.assertEqual(expected, resolved)


if __name__ == "__main__":
    unittest.main()
