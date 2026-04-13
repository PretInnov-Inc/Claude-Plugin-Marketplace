#!/usr/bin/env python3
"""
codebase-radar run_index.py

CLI entry point for detached indexing. Invoked by `start_indexing` MCP tool
via subprocess.Popen — runs the indexer out of band so the MCP server stays
responsive while indexing of large trees can take minutes.

Progress is written to index-state.json during the run; pollers call
`get_status` to read it. On success or failure the exit code reflects
the outcome (0=success, non-zero=error); detailed error info is also
persisted to the project entry in index-state.json.

Usage:
    run_index.py --path /abs/project/root
                 [--incremental|--force-full]
                 [--job-id <id>]
"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from indexer import index_codebase  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="codebase-radar detached indexer")
    parser.add_argument("--path", required=True, help="Absolute path to project root")
    parser.add_argument("--incremental", action="store_true", default=True,
                        help="Only reindex changed files (default)")
    parser.add_argument("--force-full", action="store_true",
                        help="Drop and rebuild the entire index")
    parser.add_argument("--job-id", default=None, help="Opaque job id for correlation")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"ERROR: path is not a directory: {args.path}", file=sys.stderr)
        return 2

    try:
        result = index_codebase(
            args.path,
            incremental=(not args.force_full) and args.incremental,
            force_full=args.force_full,
            job_id=args.job_id,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        # The indexer already persists error state; also print to stderr for logs.
        print(f"ERROR: indexing failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
