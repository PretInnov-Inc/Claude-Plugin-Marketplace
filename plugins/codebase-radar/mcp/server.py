#!/usr/bin/env python3
"""
codebase-radar MCP Server

Registers 6 tools: index_codebase, search_code, reindex_file,
get_status, clear_index, configure.

Runs as a stdio MCP server using the mcp SDK.
"""

import asyncio
import os
import sys
import json
import traceback
from pathlib import Path
from typing import Any, Optional

# Ensure mcp package is importable from venv
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError as e:
    print(f"MCP SDK not found: {e}. Run scripts/install.sh to set up the venv.", file=sys.stderr)
    sys.exit(1)

# Internal modules
sys.path.insert(0, str(Path(__file__).parent))
from indexer import index_codebase as _index_codebase, reindex_file as _reindex_file
from searcher import search_code as _search_code
from state import get_status as _get_status, clear_index as _clear_index, configure as _configure


app = Server("codebase-radar")


def _error_text(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"ERROR: {msg}")]


def _ok_text(data: Any) -> list[types.TextContent]:
    if isinstance(data, str):
        return [types.TextContent(type="text", text=data)]
    return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="index_codebase",
            description=(
                "Build or refresh the semantic search index for a codebase directory. "
                "Chunks code files, embeds them, and stores in LanceDB. "
                "Use incremental=true (default) to only process changed files."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the project root to index."
                    },
                    "incremental": {
                        "type": "boolean",
                        "description": "If true (default), only reindex changed files.",
                        "default": True
                    },
                    "force_full": {
                        "type": "boolean",
                        "description": "If true, clear and rebuild the entire index.",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="search_code",
            description=(
                "Semantic hybrid search (BM25 + dense vector) over an indexed codebase. "
                "Returns ranked code chunks with file paths and line numbers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language or code query."
                    },
                    "project_root": {
                        "type": "string",
                        "description": "Absolute path to the project root."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return. Default: 10.",
                        "default": 10
                    },
                    "path_filter": {
                        "type": "string",
                        "description": "Optional: filter results to paths containing this substring."
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional: filter by language (e.g. 'python', 'typescript')."
                    }
                },
                "required": ["query", "project_root"]
            }
        ),
        types.Tool(
            name="reindex_file",
            description=(
                "Update the semantic index for a single modified file. "
                "Removes old chunks for the file and re-chunks, re-embeds, and re-inserts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to reindex."
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="get_status",
            description=(
                "Get the current index status and statistics for a project directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_root": {
                        "type": "string",
                        "description": "Absolute path to the project root."
                    }
                },
                "required": ["project_root"]
            }
        ),
        types.Tool(
            name="clear_index",
            description=(
                "Clear the semantic index for a project. "
                "Drops the LanceDB table and removes state. Requires confirm=true."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_root": {
                        "type": "string",
                        "description": "Absolute path to the project root."
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm destructive operation.",
                        "default": False
                    }
                },
                "required": ["project_root"]
            }
        ),
        types.Tool(
            name="configure",
            description=(
                "Read or update codebase-radar configuration. "
                "Call with no updates to read current config. "
                "Pass updates dict to apply changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "updates": {
                        "type": "object",
                        "description": "Dict of config keys to update. Use nested keys for sections.",
                        "default": {}
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "index_codebase":
            path = arguments.get("path", "")
            if not path or not os.path.isdir(path):
                return _error_text(f"Path does not exist or is not a directory: '{path}'")
            incremental = arguments.get("incremental", True)
            force_full = arguments.get("force_full", False)
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _index_codebase(path, incremental=incremental, force_full=force_full)
            )
            return _ok_text(result)

        elif name == "search_code":
            query = arguments.get("query", "")
            project_root = arguments.get("project_root", "")
            top_k = int(arguments.get("top_k", 10))
            path_filter = arguments.get("path_filter")
            language = arguments.get("language")
            if not query:
                return _error_text("query is required")
            if not project_root:
                return _error_text("project_root is required")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _search_code(project_root, query, top_k=top_k,
                                     path_filter=path_filter, language=language)
            )
            return _ok_text(result)

        elif name == "reindex_file":
            path = arguments.get("path", "")
            if not path:
                return _error_text("path is required")
            if not os.path.isfile(path):
                return _error_text(f"File does not exist: '{path}'")
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _reindex_file(path)
            )
            return _ok_text(result)

        elif name == "get_status":
            project_root = arguments.get("project_root", "")
            if not project_root:
                return _error_text("project_root is required")
            result = _get_status(project_root)
            return _ok_text(result)

        elif name == "clear_index":
            project_root = arguments.get("project_root", "")
            confirm = arguments.get("confirm", False)
            if not project_root:
                return _error_text("project_root is required")
            if not confirm:
                return _error_text(
                    "confirm=true is required to clear the index. This operation cannot be undone."
                )
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _clear_index(project_root, confirm=True)
            )
            return _ok_text(result)

        elif name == "configure":
            updates = arguments.get("updates", {})
            result = _configure(updates)
            return _ok_text(result)

        else:
            return _error_text(f"Unknown tool: {name}")

    except Exception as e:
        tb = traceback.format_exc()
        return _error_text(f"Tool '{name}' failed: {e}\n\n{tb}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
