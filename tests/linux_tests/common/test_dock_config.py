import json
import tempfile
import unittest
from pathlib import Path

from platforms.linux.common.dock_config import dock_hack_enabled, load_dock_config


class DockConfigTests(unittest.TestCase):
    def test_creates_default_config_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "nested" / "dolphin.json"
            config = load_dock_config(path)
            self.assertEqual({"dock_hack_enabled": True}, config)
            self.assertTrue(path.exists())
            self.assertTrue(dock_hack_enabled(path))

    def test_reads_existing_disabled_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dolphin.json"
            path.write_text(json.dumps({"dock_hack_enabled": False}))
            self.assertFalse(dock_hack_enabled(path))

    def test_falls_back_to_default_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dolphin.json"
            path.write_text("not json")
            self.assertTrue(dock_hack_enabled(path))


if __name__ == "__main__":
    unittest.main()
