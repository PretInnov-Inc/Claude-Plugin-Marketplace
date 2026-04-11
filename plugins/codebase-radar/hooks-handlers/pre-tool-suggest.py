#!/usr/bin/env python3
"""
PreToolUse hook handler for codebase-radar.
STDLIB ONLY — no external dependencies.

Fires before Grep or Glob tool calls.
Suggests using search_code MCP tool for semantic search instead.
Never blocks — always exits 0.
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

    # Extract the search pattern
    tool_input = data.get("tool_input", data)
    pattern = (
        tool_input.get("pattern")
        or tool_input.get("query")
        or tool_input.get("glob")
        or tool_input.get("include")
        or ""
    )

    tool_name = data.get("tool_name", "Grep/Glob")

    if pattern:
        suggestion = (
            f"Before using {tool_name} with pattern '{pattern}', consider calling the MCP tool "
            f"`search_code` with query='{pattern}' for semantic hybrid search. "
            "It combines BM25 keyword matching and dense vector search to find conceptually "
            "related code even when exact terms don't match. Proceed with the original tool if "
            "you need literal pattern matching."
        )
    else:
        suggestion = (
            f"Consider using the MCP tool `search_code` for semantic code search instead of "
            f"{tool_name}. It supports natural language queries and finds conceptually related code."
        )

    output = {"systemMessage": suggestion}
    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block
        sys.exit(0)
