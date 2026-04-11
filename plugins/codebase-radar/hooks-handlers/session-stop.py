#!/usr/bin/env python3
"""
Stop hook handler for codebase-radar.
STDLIB ONLY — no external dependencies.

Reads transcript, counts search_code invocations, extracts queries,
logs to search-log.jsonl, updates config.json stats.
"""

import json
import os
import sys
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def trim_jsonl(file_path: str, max_entries: int = 500, trim_to: int = 400):
    """Trim JSONL file to trim_to entries if it exceeds max_entries."""
    try:
        with open(file_path, "r") as f:
            lines = [line for line in f if line.strip()]
        if len(lines) > max_entries:
            # Keep the most recent trim_to entries
            lines = lines[-trim_to:]
            with open(file_path, "w") as f:
                f.writelines(lines)
    except Exception:
        pass


def main():
    plugin_data = os.environ.get(
        "CLAUDE_PLUGIN_DATA",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar")
    )

    # Read stdin for session info
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
    cwd = os.getcwd()

    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            session_id = data.get("session_id", session_id)
            cwd = data.get("cwd", cwd)
    except Exception:
        pass

    # Compute project hash
    project_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]

    # Read transcript if available
    transcript_path = os.environ.get("CLAUDE_TRANSCRIPT", "")
    search_count = 0
    extracted_queries = []

    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, "r", errors="replace") as f:
                transcript_text = f.read()

            # Count search_code invocations
            search_count = len(re.findall(r"search_code", transcript_text))

            # Extract queries from search_code calls — look for query="..." or query: "..."
            query_matches = re.findall(
                r'search_code[^}]{0,200}?query["\s]*[:=]["\s]*([^"\'}{,\n]{3,200})',
                transcript_text,
                re.IGNORECASE | re.DOTALL
            )
            # Also look for quoted query values
            query_matches += re.findall(
                r'"query"\s*:\s*"([^"]{3,200})"',
                transcript_text
            )
            # Deduplicate and take first 10
            seen = set()
            for q in query_matches:
                q_clean = q.strip().strip('"\'').strip()
                if q_clean and q_clean not in seen:
                    seen.add(q_clean)
                    extracted_queries.append(q_clean)
                if len(extracted_queries) >= 10:
                    break
        except Exception:
            pass

    # Read project index stats
    state_path = os.path.join(plugin_data, "index-state.json")
    files_indexed = 0
    chunks_total = 0
    last_indexed = None

    try:
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                state = json.load(f)
            project_entry = state.get("projects", {}).get(project_hash, {})
            files_indexed = project_entry.get("files_indexed", 0)
            chunks_total = project_entry.get("chunks_total", 0)
            last_indexed = project_entry.get("last_indexed")
    except Exception:
        pass

    # Build log entry
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "project_hash": project_hash,
        "cwd": cwd,
        "search_count": search_count,
        "queries": extracted_queries,
        "index_snapshot": {
            "files_indexed": files_indexed,
            "chunks_total": chunks_total,
            "last_indexed": last_indexed
        }
    }

    # Append to search-log.jsonl
    log_path = os.path.join(plugin_data, "search-log.jsonl")
    try:
        os.makedirs(plugin_data, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        trim_jsonl(log_path, max_entries=500, trim_to=400)
    except Exception:
        pass

    # Update config.json stats
    config_path = os.path.join(plugin_data, "config.json")
    try:
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)

        stats = config.setdefault("stats", {})
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        stats["total_searches"] = stats.get("total_searches", 0) + search_count
        stats["total_files_indexed"] = max(
            stats.get("total_files_indexed", 0),
            files_indexed
        )

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
