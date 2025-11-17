"""Tests for macOS Claude Desktop memory extractor."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from bridge.providers.macos.claude_desktop_memory import (
    ClaudeDesktopMemoryExtractor,
    MemoryEntry,
)


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_basic_creation(self):
        """Test basic memory entry creation."""
        entry = MemoryEntry(content="Test memory content")
        assert entry.content == "Test memory content"
        assert entry.source == "claude_desktop"
        assert entry.tags is None
        assert entry.metadata is None

    def test_full_creation(self):
        """Test memory entry with all fields."""
        entry = MemoryEntry(
            content="Full memory",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-02T00:00:00",
            source="test_source",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
        )
        assert entry.content == "Full memory"
        assert entry.created_at == "2025-01-01T00:00:00"
        assert entry.tags == ["tag1", "tag2"]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = MemoryEntry(
            content="Dict test", tags=["test"], metadata={"extra": "data"}
        )
        result = entry.to_dict()
        assert isinstance(result, dict)
        assert result["content"] == "Dict test"
        assert result["tags"] == ["test"]
        assert result["metadata"] == {"extra": "data"}


class TestClaudeDesktopMemoryExtractor:
    """Tests for ClaudeDesktopMemoryExtractor."""

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = ClaudeDesktopMemoryExtractor()
        assert extractor.custom_path is None
        assert extractor.found_memories == []

    def test_initialization_with_custom_path(self):
        """Test extractor with custom path."""
        extractor = ClaudeDesktopMemoryExtractor(custom_path="/custom/path")
        assert extractor.custom_path == "/custom/path"

    def test_discover_paths_with_custom(self):
        """Test path discovery includes custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = ClaudeDesktopMemoryExtractor(custom_path=tmpdir)
            paths = extractor.discover_claude_data_paths()
            assert Path(tmpdir) in paths

    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = ClaudeDesktopMemoryExtractor()
            result = extractor.scan_directory(Path(tmpdir))
            assert result["path"] == tmpdir
            assert result["sqlite_databases"] == []
            assert result["json_files"] == []

    def test_scan_directory_with_files(self):
        """Test scanning directory with database and JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            db_path = Path(tmpdir) / "memories.db"
            db_path.touch()
            json_path = Path(tmpdir) / "config.json"
            json_path.write_text("{}")

            extractor = ClaudeDesktopMemoryExtractor()
            result = extractor.scan_directory(Path(tmpdir))

            assert str(db_path) in result["sqlite_databases"]
            assert str(json_path) in result["json_files"]

    def test_extract_from_sqlite_with_memory_table(self):
        """Test extracting memories from SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create memory table
            cursor.execute("""
                CREATE TABLE user_memories (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute(
                "INSERT INTO user_memories (content, created_at) VALUES (?, ?)",
                ("Test memory 1", "2025-01-01"),
            )
            cursor.execute(
                "INSERT INTO user_memories (content, created_at) VALUES (?, ?)",
                ("Test memory 2", "2025-01-02"),
            )
            conn.commit()
            conn.close()

            extractor = ClaudeDesktopMemoryExtractor()
            memories = extractor.extract_from_sqlite(str(db_path))

            assert len(memories) == 2
            assert memories[0].content == "Test memory 1"
            assert memories[1].content == "Test memory 2"

    def test_extract_from_json_list(self):
        """Test extracting memories from JSON array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "memories.json"
            data = [
                {"content": "Memory 1", "created_at": "2025-01-01"},
                {"content": "Memory 2", "tags": ["important"]},
            ]
            json_path.write_text(json.dumps(data))

            extractor = ClaudeDesktopMemoryExtractor()
            memories = extractor.extract_from_json(str(json_path))

            assert len(memories) == 2
            assert memories[0].content == "Memory 1"
            assert memories[1].tags == ["important"]

    def test_extract_from_json_dict_with_memories_key(self):
        """Test extracting from JSON with 'memories' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "data.json"
            data = {
                "version": "1.0",
                "memories": [
                    {"text": "Memory A"},
                    {"text": "Memory B"},
                ],
            }
            json_path.write_text(json.dumps(data))

            extractor = ClaudeDesktopMemoryExtractor()
            memories = extractor.extract_from_json(str(json_path))

            assert len(memories) == 2
            assert memories[0].content == "Memory A"

    def test_extract_from_json_string_items(self):
        """Test extracting from JSON with string items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "simple.json"
            data = ["Memory string 1", "Memory string 2"]
            json_path.write_text(json.dumps(data))

            extractor = ClaudeDesktopMemoryExtractor()
            memories = extractor.extract_from_json(str(json_path))

            assert len(memories) == 2
            assert memories[0].content == "Memory string 1"

    def test_export_to_json(self):
        """Test exporting memories to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = ClaudeDesktopMemoryExtractor()
            extractor.found_memories = [
                MemoryEntry(content="Export test 1"),
                MemoryEntry(content="Export test 2"),
            ]

            output_path = Path(tmpdir) / "export.json"
            result = extractor.export_to_json(str(output_path))

            assert Path(result).exists()
            with open(result) as f:
                data = json.load(f)
            assert data["total_memories"] == 2
            assert len(data["memories"]) == 2

    def test_export_to_markdown(self):
        """Test exporting memories to Markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = ClaudeDesktopMemoryExtractor()
            extractor.found_memories = [
                MemoryEntry(
                    content="Markdown test",
                    created_at="2025-01-01",
                    tags=["tag1"],
                )
            ]

            output_path = Path(tmpdir) / "export.md"
            result = extractor.export_to_markdown(str(output_path))

            assert Path(result).exists()
            content = Path(result).read_text()
            assert "# Claude Desktop Memory Export" in content
            assert "Markdown test" in content
            assert "tag1" in content

    def test_get_summary(self):
        """Test getting extraction summary."""
        extractor = ClaudeDesktopMemoryExtractor()
        extractor.found_memories = [
            MemoryEntry(content="A", source="source1"),
            MemoryEntry(content="B", source="source2"),
            MemoryEntry(content="C", source="source1"),
        ]

        summary = extractor.get_summary()
        assert summary["total_memories"] == 3
        assert set(summary["sources"]) == {"source1", "source2"}

    def test_extract_all_empty(self):
        """Test extract_all with no Claude directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Point to non-existent path
            extractor = ClaudeDesktopMemoryExtractor(
                custom_path=f"{tmpdir}/nonexistent"
            )
            # Override default paths to avoid actual system check
            extractor.DEFAULT_PATHS = []

            memories = extractor.extract_all()
            assert memories == []
            assert "status" in extractor.scan_results

    def test_full_extraction_pipeline(self):
        """Test complete extraction from directory with multiple sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create SQLite database
            db_path = Path(tmpdir) / "memory.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE memories (id INTEGER PRIMARY KEY, content TEXT)"
            )
            cursor.execute("INSERT INTO memories (content) VALUES (?)", ("DB Memory",))
            conn.commit()
            conn.close()

            # Create JSON file
            json_path = Path(tmpdir) / "context.json"
            json_path.write_text(json.dumps([{"content": "JSON Memory"}]))

            # Extract
            extractor = ClaudeDesktopMemoryExtractor(custom_path=tmpdir)
            extractor.DEFAULT_PATHS = []  # Only use custom path
            memories = extractor.extract_all()

            assert len(memories) == 2
            contents = {m.content for m in memories}
            assert "DB Memory" in contents
            assert "JSON Memory" in contents
