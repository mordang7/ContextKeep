"""Regression tests for category parsing and core memory operations.

These tests use an isolated temporary SQLite database, so they never touch
real ContextKeep data. They cover the HTML-escaped category name bug fixed
in PR #6: an escaped name such as "R&amp;D" must resolve to the existing
"R&D" category instead of silently creating a duplicate row.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from core.database import Database
from core.memory_manager import MemoryManager


class MemoryManagerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = Path(tempfile.mkdtemp(prefix="contextkeep-test-"))
        Database.set_path(cls._tmpdir / "test.db")
        cls.mm = MemoryManager()

    @classmethod
    def tearDownClass(cls) -> None:
        Database.close()
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_parse_categories_unescapes_html_entities(self) -> None:
        parsed = self.mm._parse_categories("Foo &amp; Bar, Baz &lt;Qux&gt;")
        self.assertEqual(parsed, ["Foo & Bar", "Baz <Qux>"])

    def test_plain_ampersand_names_are_unchanged(self) -> None:
        parsed = self.mm._parse_categories("R&D, AT&T, Q&A")
        self.assertEqual(parsed, ["R&D", "AT&T", "Q&A"])

    def test_escaped_category_resolves_to_existing_category(self) -> None:
        before = len(self.mm.list_categories())
        self.mm.create_category("R&D")
        memory = self.mm.store_memory(
            "escaped-category", "content", categories="R&amp;D"
        )
        after = len(self.mm.list_categories())
        # create_category added "R&D"; store_memory must reuse it, not add a copy.
        self.assertEqual(after, before + 1)
        self.assertEqual([c["name"] for c in memory["categories"]], ["R&D"])

    def test_escaped_and_literal_names_share_one_category(self) -> None:
        before = len(self.mm.list_categories())
        self.mm.store_memory("fork-a", "one", categories="Foo &amp; Bar")
        self.mm.store_memory("fork-b", "two", categories="Foo & Bar")
        self.assertEqual(len(self.mm.list_categories()), before + 1)

    def test_store_and_retrieve_roundtrip(self) -> None:
        self.mm.store_memory(
            "roundtrip-key", "hello world", categories=["Docs & Notes"]
        )
        memory = self.mm.retrieve_memory("roundtrip-key")
        self.assertIsNotNone(memory)
        assert memory is not None  # for type checkers
        self.assertEqual(memory["content"], "hello world")
        self.assertIn(
            "Docs & Notes", [c["name"] for c in memory["categories"]]
        )


if __name__ == "__main__":
    unittest.main()
