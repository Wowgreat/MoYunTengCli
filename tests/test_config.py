import tempfile
import textwrap
import unittest
from pathlib import Path

from myt_cli.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_backup_export_timeout(self):
        content = textwrap.dedent(
            """
            box:
              base_url: "http://10.0.103.227:8000"
              timeout_seconds: 30
              verify_ssl: false
              auth:
                type: "basic"
                username: "admin"
                password: "change-me"

            backup:
              export_timeout_seconds: 300
            """
        ).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(content, encoding="utf-8")

            config = load_config(path)

        self.assertEqual(300, config.backup.export_timeout_seconds)


if __name__ == "__main__":
    unittest.main()
