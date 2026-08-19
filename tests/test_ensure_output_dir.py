import tempfile
import unittest
from pathlib import Path

from src.history_db import ensure_output_dir


class EnsureOutputDirTests(unittest.TestCase):
    def test_creates_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            result = ensure_output_dir(out)
            self.assertTrue(result.is_dir())
            dest = result / ".ui_temp_jd.txt"
            dest.write_text("hello")
            self.assertEqual(dest.read_text(), "hello")

    def test_replaces_dangling_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.symlink_to(Path(tmp) / "missing-target")
            self.assertTrue(out.is_symlink())
            self.assertFalse(out.exists())
            result = ensure_output_dir(out)
            self.assertTrue(result.is_dir())
            self.assertFalse(result.is_symlink())
            dest = result / ".ui_temp_jd.txt"
            dest.write_text("hello")
            self.assertEqual(dest.read_text(), "hello")

    def test_keeps_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()
            marker = out / "keep-me.txt"
            marker.write_text("stay")
            ensure_output_dir(out)
            self.assertEqual(marker.read_text(), "stay")


if __name__ == "__main__":
    unittest.main()
