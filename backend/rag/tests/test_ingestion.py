"""Unit tests for hot-folder ingestion."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.rag.parser import load_local_sources, move_processed


class IngestionTests(unittest.TestCase):
    def test_loads_and_moves_pending_text_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"RAG_DATA_DIR": tmp}):
                pending = Path(tmp) / "need-processing"
                pending.mkdir(parents=True)
                source = pending / "lesson.md"
                source.write_text("# Lesson\n\nPython supports automation.", encoding="utf-8")

                sources, files = load_local_sources()
                self.assertEqual(sources[0]["source_type"], "local_document")
                self.assertIn("Python supports automation", sources[0]["content"])

                move_processed(files)
                self.assertFalse(source.exists())
                self.assertTrue((Path(tmp) / "processed" / "lesson.md").exists())


if __name__ == "__main__":
    unittest.main()
