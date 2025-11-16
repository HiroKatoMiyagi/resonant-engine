"""macOS Claude Desktop Memory Extractor.

Extracts user-added memories from Claude Desktop app on macOS.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """Represents a single memory entry from Claude Desktop."""

    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    source: str = "claude_desktop"
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ClaudeDesktopMemoryExtractor:
    """Extract memories from macOS Claude Desktop application."""

    DEFAULT_PATHS = [
        "~/Library/Application Support/Claude",
        "~/Library/Containers/com.anthropic.claude/Data/Library/Application Support",
        "~/.claude-memory",
        "~/.anthropic",
    ]

    SQLITE_DB_NAMES = [
        "memories.db",
        "memory.db",
        "claude.db",
        "data.db",
        "context.db",
    ]

    JSON_FILE_NAMES = [
        "memories.json",
        "memory.json",
        "user_memories.json",
        "context.json",
    ]

    def __init__(self, custom_path: Optional[str] = None) -> None:
        """Initialize extractor with optional custom path."""
        self.custom_path = custom_path
        self.found_memories: List[MemoryEntry] = []
        self.scan_results: Dict[str, Any] = {}

    def discover_claude_data_paths(self) -> List[Path]:
        """Discover all potential Claude Desktop data directories."""
        found_paths = []

        # Check default paths
        paths_to_check = self.DEFAULT_PATHS.copy()
        if self.custom_path:
            paths_to_check.insert(0, self.custom_path)

        for path_str in paths_to_check:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_dir():
                found_paths.append(path)

        return found_paths

    def scan_directory(self, directory: Path) -> Dict[str, Any]:
        """Scan a directory for Claude Desktop data files."""
        result = {
            "path": str(directory),
            "sqlite_databases": [],
            "json_files": [],
            "other_files": [],
        }

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    if item.suffix == ".db" or item.suffix == ".sqlite":
                        result["sqlite_databases"].append(str(item))
                    elif item.suffix == ".json":
                        result["json_files"].append(str(item))
                    elif item.name in self.SQLITE_DB_NAMES:
                        result["sqlite_databases"].append(str(item))
                    elif item.name in self.JSON_FILE_NAMES:
                        result["json_files"].append(str(item))
                    else:
                        result["other_files"].append(str(item))
        except PermissionError as e:
            result["error"] = f"Permission denied: {e}"

        return result

    def extract_from_sqlite(self, db_path: str) -> List[MemoryEntry]:
        """Extract memories from SQLite database."""
        memories = []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Common memory table patterns
            memory_tables = [
                t
                for t in tables
                if any(
                    keyword in t.lower()
                    for keyword in ["memory", "context", "knowledge", "fact", "user"]
                )
            ]

            for table in memory_tables:
                try:
                    cursor.execute(f"SELECT * FROM {table}")  # noqa: S608
                    rows = cursor.fetchall()

                    for row in rows:
                        row_dict = dict(row)
                        content = self._extract_content_from_row(row_dict)
                        if content:
                            memory = MemoryEntry(
                                content=content,
                                created_at=row_dict.get(
                                    "created_at", row_dict.get("timestamp")
                                ),
                                updated_at=row_dict.get("updated_at"),
                                source=f"sqlite:{db_path}:{table}",
                                metadata=row_dict,
                            )
                            memories.append(memory)
                except sqlite3.Error:
                    continue

            conn.close()
        except sqlite3.Error as e:
            self.scan_results[db_path] = {"error": str(e)}

        return memories

    def _extract_content_from_row(self, row: Dict[str, Any]) -> Optional[str]:
        """Extract content field from a database row."""
        content_fields = ["content", "text", "memory", "value", "data", "fact"]
        for field in content_fields:
            if field in row and row[field]:
                return str(row[field])
        return None

    def extract_from_json(self, json_path: str) -> List[MemoryEntry]:
        """Extract memories from JSON file."""
        memories = []

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    memory = self._parse_json_memory(item, json_path)
                    if memory:
                        memories.append(memory)
            elif isinstance(data, dict):
                # Check for common memory container keys
                for key in ["memories", "items", "data", "entries", "knowledge"]:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            memory = self._parse_json_memory(item, json_path)
                            if memory:
                                memories.append(memory)
                        break
                else:
                    # Single memory object
                    memory = self._parse_json_memory(data, json_path)
                    if memory:
                        memories.append(memory)

        except (json.JSONDecodeError, IOError) as e:
            self.scan_results[json_path] = {"error": str(e)}

        return memories

    def _parse_json_memory(
        self, item: Any, source_path: str
    ) -> Optional[MemoryEntry]:
        """Parse a JSON object into a MemoryEntry."""
        if not isinstance(item, dict):
            if isinstance(item, str):
                return MemoryEntry(content=item, source=f"json:{source_path}")
            return None

        content = None
        for key in ["content", "text", "memory", "value", "fact", "description"]:
            if key in item:
                content = str(item[key])
                break

        if not content:
            return None

        return MemoryEntry(
            content=content,
            created_at=item.get("created_at", item.get("timestamp")),
            updated_at=item.get("updated_at"),
            source=f"json:{source_path}",
            tags=item.get("tags", []),
            metadata=item,
        )

    def extract_all(self) -> List[MemoryEntry]:
        """Extract all memories from discovered locations."""
        self.found_memories = []
        self.scan_results = {}

        # Discover paths
        data_paths = self.discover_claude_data_paths()

        if not data_paths:
            self.scan_results["status"] = "No Claude Desktop data directories found"
            return []

        self.scan_results["discovered_paths"] = [str(p) for p in data_paths]

        # Scan each directory
        for path in data_paths:
            scan_result = self.scan_directory(path)
            self.scan_results[str(path)] = scan_result

            # Extract from SQLite databases
            for db_path in scan_result["sqlite_databases"]:
                memories = self.extract_from_sqlite(db_path)
                self.found_memories.extend(memories)

            # Extract from JSON files
            for json_path in scan_result["json_files"]:
                memories = self.extract_from_json(json_path)
                self.found_memories.extend(memories)

        return self.found_memories

    def export_to_json(self, output_path: str) -> str:
        """Export extracted memories to JSON file."""
        if not self.found_memories:
            self.extract_all()

        export_data = {
            "extracted_at": datetime.now().isoformat(),
            "total_memories": len(self.found_memories),
            "memories": [m.to_dict() for m in self.found_memories],
            "scan_results": self.scan_results,
        }

        output_file = Path(output_path).expanduser()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return str(output_file)

    def export_to_markdown(self, output_path: str) -> str:
        """Export extracted memories to Markdown file."""
        if not self.found_memories:
            self.extract_all()

        lines = [
            "# Claude Desktop Memory Export",
            "",
            f"Extracted at: {datetime.now().isoformat()}",
            f"Total memories: {len(self.found_memories)}",
            "",
            "---",
            "",
        ]

        for i, memory in enumerate(self.found_memories, 1):
            lines.append(f"## Memory {i}")
            lines.append("")
            lines.append(memory.content)
            lines.append("")
            if memory.created_at:
                lines.append(f"*Created: {memory.created_at}*")
            if memory.tags:
                lines.append(f"*Tags: {', '.join(memory.tags)}*")
            lines.append(f"*Source: {memory.source}*")
            lines.append("")
            lines.append("---")
            lines.append("")

        output_file = Path(output_path).expanduser()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(output_file)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of extraction results."""
        return {
            "total_memories": len(self.found_memories),
            "sources": list(set(m.source for m in self.found_memories)),
            "scan_results": self.scan_results,
        }
