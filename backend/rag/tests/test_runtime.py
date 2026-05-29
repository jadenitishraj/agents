"""Unit tests for package-local runtime helpers."""

from __future__ import annotations

import unittest

from backend.rag.indexer import _collection_name as collection_name


class RuntimeTests(unittest.TestCase):
    def test_collection_name_is_stable_and_slugged(self) -> None:
        sources = [{"url": "https://example.com/a"}, {"url": "https://example.com/b"}]
        name = collection_name("What is Python?", sources)
        self.assertTrue(name.startswith("what-is-python"))
        self.assertLessEqual(len(name), 49)


if __name__ == "__main__":
    unittest.main()

