"""Unit tests for classifier routing."""

from __future__ import annotations

import unittest

from backend.rag.classifier import classify_sources


class ClassifierTests(unittest.TestCase):
    def test_routes_markdown_and_logs(self) -> None:
        sources = [
            {"title": "Guide", "url": "https://a", "snippet": "# Header\n- bullet\nMore text"},
            {"title": "Trace", "url": "https://b", "snippet": "ERROR stack trace http timeout warn"},
        ]
        items = classify_sources(sources)
        self.assertEqual(items[0].chunk_strategy, "markdown")
        self.assertEqual(items[1].chunk_strategy, "token")


if __name__ == "__main__":
    unittest.main()

