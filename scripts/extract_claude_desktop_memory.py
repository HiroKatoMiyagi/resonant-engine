#!/usr/bin/env python3
"""CLI tool to extract memories from macOS Claude Desktop.

Usage:
    python scripts/extract_claude_desktop_memory.py
    python scripts/extract_claude_desktop_memory.py --output ~/my_memories.json
    python scripts/extract_claude_desktop_memory.py --format markdown --output ~/memories.md
    python scripts/extract_claude_desktop_memory.py --custom-path ~/custom/claude/path
    python scripts/extract_claude_desktop_memory.py --scan-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge.providers.macos.claude_desktop_memory import ClaudeDesktopMemoryExtractor


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract memories from macOS Claude Desktop application"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="~/claude_desktop_memories.json",
        help="Output file path (default: ~/claude_desktop_memories.json)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--custom-path",
        "-p",
        type=str,
        help="Custom path to Claude Desktop data directory",
    )
    parser.add_argument(
        "--scan-only",
        "-s",
        action="store_true",
        help="Only scan for files, don't extract memories",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )

    args = parser.parse_args()

    print("Claude Desktop Memory Extractor")
    print("=" * 40)

    # Initialize extractor
    extractor = ClaudeDesktopMemoryExtractor(custom_path=args.custom_path)

    # Discover paths
    print("\nDiscovering Claude Desktop data directories...")
    paths = extractor.discover_claude_data_paths()

    if not paths:
        print("\nNo Claude Desktop data directories found.")
        print("Checked locations:")
        for path in extractor.DEFAULT_PATHS:
            print(f"  - {Path(path).expanduser()}")
        if args.custom_path:
            print(f"  - {Path(args.custom_path).expanduser()}")
        return 1

    print(f"Found {len(paths)} data director{'y' if len(paths) == 1 else 'ies'}:")
    for path in paths:
        print(f"  - {path}")

    if args.scan_only:
        print("\nScanning directories...")
        for path in paths:
            scan_result = extractor.scan_directory(path)
            print(f"\n{path}:")
            print(f"  SQLite databases: {len(scan_result['sqlite_databases'])}")
            for db in scan_result["sqlite_databases"]:
                print(f"    - {db}")
            print(f"  JSON files: {len(scan_result['json_files'])}")
            for jf in scan_result["json_files"]:
                print(f"    - {jf}")
            if args.verbose:
                print(f"  Other files: {len(scan_result['other_files'])}")
        return 0

    # Extract memories
    print("\nExtracting memories...")
    memories = extractor.extract_all()

    print(f"Found {len(memories)} memor{'y' if len(memories) == 1 else 'ies'}")

    if not memories:
        print("\nNo memories found. This could mean:")
        print("  - Claude Desktop has no saved memories yet")
        print("  - Memory format is different from expected")
        print("  - Permissions issue accessing the files")
        print("\nScan results:")
        print(json.dumps(extractor.scan_results, indent=2))
        return 0

    # Export
    if args.format == "json":
        output_file = extractor.export_to_json(args.output)
    else:
        if not args.output.endswith(".md"):
            args.output = args.output.rsplit(".", 1)[0] + ".md"
        output_file = extractor.export_to_markdown(args.output)

    print(f"\nExported to: {output_file}")

    # Show summary
    if args.verbose:
        print("\nMemory Preview (first 3):")
        for i, memory in enumerate(memories[:3], 1):
            print(f"\n{i}. {memory.content[:100]}...")
            print(f"   Source: {memory.source}")

    summary = extractor.get_summary()
    print(f"\nSources: {', '.join(summary['sources'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
