#!/usr/bin/env python3
"""
PostToolUse hook handler for codebase-radar.
STDLIB ONLY — no external dependencies.

Fires after Write, Edit, or MultiEdit tool calls.
Tells Claude to call reindex_file MCP tool for the modified file.
"""

import json
import sys


def main():
    # Read stdin
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    # Extract tool_input — handle both flat and nested structures
    tool_input = data.get("tool_input", data)

    # Try common keys for the file path
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("new_path")
        or tool_input.get("filePath")
        or ""
    )

    if not file_path:
        sys.exit(0)

    output = {
        "systemMessage": (
            f"File '{file_path}' was just modified. "
            f"Call the MCP tool `reindex_file` with path='{file_path}' "
            "to update the codebase-radar semantic search index so future searches reflect this change."
        )
    }

    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
