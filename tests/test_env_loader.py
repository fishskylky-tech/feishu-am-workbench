"""Tests for runtime .env loading behavior."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from runtime.env_loader import load_dotenv


class EnvLoaderTests(unittest.TestCase):
    def test_load_dotenv_reads_key_value_pairs(self) -> None:
        # Save original values to restore after test
        orig_todo = os.environ.get("FEISHU_AM_TODO_TASKLIST_GUID")
        orig_base = os.environ.get("FEISHU_AM_BASE_TOKEN")
        try:
            os.environ.pop("FEISHU_AM_TODO_TASKLIST_GUID", None)
            os.environ.pop("FEISHU_AM_BASE_TOKEN", None)
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                (root / ".env").write_text(
                    """
# comment
FEISHU_AM_BASE_TOKEN=from_dotenv
export FEISHU_AM_TODO_TASKLIST_GUID=00000000-0000-4000-8000-000000000001
""".strip()
                    + "\n",
                    encoding="utf-8",
                )
                loaded = load_dotenv(root)

                self.assertIn("FEISHU_AM_BASE_TOKEN", loaded)
                self.assertIn("FEISHU_AM_TODO_TASKLIST_GUID", loaded)
                self.assertEqual(os.environ.get("FEISHU_AM_BASE_TOKEN"), "from_dotenv")
        finally:
            if orig_base is not None:
                os.environ["FEISHU_AM_BASE_TOKEN"] = orig_base
            else:
                os.environ.pop("FEISHU_AM_BASE_TOKEN", None)
            if orig_todo is not None:
                os.environ["FEISHU_AM_TODO_TASKLIST_GUID"] = orig_todo
            else:
                os.environ.pop("FEISHU_AM_TODO_TASKLIST_GUID", None)

    def test_load_dotenv_does_not_override_existing_env_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("FEISHU_AM_BASE_TOKEN=from_dotenv\n", encoding="utf-8")
            os.environ["FEISHU_AM_BASE_TOKEN"] = "from_shell"

            loaded = load_dotenv(root)

            self.assertNotIn("FEISHU_AM_BASE_TOKEN", loaded)
            self.assertEqual(os.environ.get("FEISHU_AM_BASE_TOKEN"), "from_shell")

            os.environ.pop("FEISHU_AM_BASE_TOKEN", None)


if __name__ == "__main__":
    unittest.main()
