#!/usr/bin/env python3
"""
SessionStart hook handler for codebase-radar.
STDLIB ONLY — no external dependencies.

Reads index-state.json, computes diff vs current filesystem,
and emits instructions for Claude to call MCP index/reindex tools.
"""

import json
import os
import sys
import hashlib
import fnmatch
from pathlib import Path
from datetime import datetime, timezone


def compute_file_hash(file_path: str) -> str:
    """Compute sha256 of first 8KB of a file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            h.update(f.read(8192))
        return h.hexdigest()
    except (OSError, IOError):
        return ""


def matches_exclusion(rel_path: str, patterns: list) -> bool:
    """Check if a relative path matches any exclusion glob pattern."""
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Also check if any path component matches
        parts = rel_path.replace("\\", "/")
        if fnmatch.fnmatch(parts, pattern):
            return True
    return False


def bootstrap_venv_if_missing(plugin_data: str, plugin_root: str) -> dict | None:
    """
    If the MCP venv is missing, kick off install.sh in the background.
    Returns a hook output dict if bootstrap was triggered, else None.
    The MCP server cannot start without the venv, so this is the difference
    between a working plugin and a broken one for first-time users.
    """
    import subprocess
    venv_python = os.path.join(plugin_data, "venv", "bin", "python3")
    if os.path.exists(venv_python):
        return None

    install_script = os.path.join(plugin_root, "scripts", "install.sh")
    if not os.path.exists(install_script):
        return None

    log_path = os.path.join(plugin_data, "install.log")
    os.makedirs(plugin_data, exist_ok=True)
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = plugin_root
    env["CLAUDE_PLUGIN_DATA"] = plugin_data
    try:
        with open(log_path, "ab") as logf:
            subprocess.Popen(
                ["bash", install_script],
                stdout=logf, stderr=logf,
                env=env, start_new_session=True,
            )
    except Exception:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "[codebase-radar] First-run: MCP server venv is missing. "
                "Auto-installing dependencies in the background (lancedb, sentence-transformers, "
                "tree-sitter — takes 2-5 minutes). The MCP search tools will be unavailable "
                "this session but will work in the next session. "
                f"Install log: {log_path}"
            )
        }
    }


def main():
    plugin_data = os.environ.get(
        "CLAUDE_PLUGIN_DATA",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar")
    )
    plugin_root = os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        str(Path(__file__).parent.parent)
    )

    # First-run bootstrap: install MCP venv if missing, then exit early
    bootstrap = bootstrap_venv_if_missing(plugin_data, plugin_root)
    if bootstrap is not None:
        print(json.dumps(bootstrap))
        return

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

    # Compute project hash from cwd
    project_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]

    # Read index-state.json
    state_path = os.path.join(plugin_data, "index-state.json")
    state = {"version": "1.0.0", "projects": {}}
    try:
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                state = json.load(f)
    except Exception:
        pass

    projects = state.get("projects", {})
    project_entry = projects.get(project_hash)

    # Read config for exclusion patterns
    config_path = os.path.join(plugin_data, "config.json")
    exclusion_patterns = [
        "node_modules/**", ".git/**", "**/*.min.js", "**/*.lock",
        "dist/**", "build/**", "__pycache__/**", "*.pyc",
        "**/*.egg-info/**", ".venv/**", "venv/**"
    ]
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            exclusion_patterns = config.get("exclusions", {}).get("patterns", exclusion_patterns)
    except Exception:
        pass

    # --- Case 1: Project not indexed at all ---
    if not project_entry:
        output = {
            "hookSpecificOutput": {
                "additionalContext": (
                    f"[codebase-radar] Project at '{cwd}' has NOT been indexed yet. "
                    f"Project hash: {project_hash}. "
                    "The semantic search index is empty for this project."
                ),
                "systemMessage": (
                    f"The codebase-radar plugin has detected that the project at '{cwd}' "
                    "has no semantic search index. Call the MCP tool `index_codebase` with "
                    f"path='{cwd}' to build the index. This enables fast semantic code search "
                    "with `/radar:search` for the rest of this session."
                )
            }
        }
        print(json.dumps(output))
        return

    # --- Case 2: Project is indexed — compute filesystem diff ---
    stored_hashes = project_entry.get("file_hashes", {})
    files_indexed = project_entry.get("files_indexed", 0)
    chunks_total = project_entry.get("chunks_total", 0)
    last_indexed = project_entry.get("last_indexed", "unknown")
    embedding_model = project_entry.get("embedding_model", "all-MiniLM-L6-v2")

    changed_files = []
    new_files = []
    current_files = set()

    try:
        for root, dirs, files in os.walk(cwd):
            # Prune excluded directories in-place
            dirs[:] = [
                d for d in dirs
                if not matches_exclusion(
                    os.path.relpath(os.path.join(root, d), cwd),
                    exclusion_patterns
                )
            ]
            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, cwd)

                if matches_exclusion(rel_path, exclusion_patterns):
                    continue

                current_files.add(rel_path)
                current_hash = compute_file_hash(abs_path)

                if not current_hash:
                    continue

                if rel_path not in stored_hashes:
                    new_files.append(abs_path)
                elif stored_hashes[rel_path] != current_hash:
                    changed_files.append(abs_path)
    except Exception:
        pass

    all_modified = changed_files + new_files
    total_changed = len(all_modified)

    # Build stats context
    stats_context = (
        f"[codebase-radar] Index stats for '{cwd}': "
        f"files_indexed={files_indexed}, chunks={chunks_total}, "
        f"last_indexed={last_indexed}, embedding_model={embedding_model}, "
        f"changed_since_last_index={total_changed}"
    )

    # --- Case 2a: Many changes — suggest full reindex ---
    if total_changed > 50:
        output = {
            "hookSpecificOutput": {
                "additionalContext": stats_context,
                "systemMessage": (
                    f"codebase-radar detected {total_changed} changed/new files in '{cwd}' "
                    f"since the last index ({last_indexed}). "
                    "Rather than reindexing each file individually, call the MCP tool "
                    f"`index_codebase` with path='{cwd}' and incremental=true to do a fast "
                    "incremental refresh of the semantic search index."
                )
            }
        }
        print(json.dumps(output))
        return

    # --- Case 2b: Small number of changes — list individual files ---
    if total_changed > 0:
        file_list = "\n".join(f"  - {f}" for f in all_modified[:50])
        system_msg = (
            f"codebase-radar detected {total_changed} modified/new file(s) in '{cwd}' "
            f"since the last index ({last_indexed}). "
            "Call the MCP tool `reindex_file` for each of the following files to keep "
            "the semantic search index current:\n" + file_list
        )
    else:
        system_msg = (
            f"codebase-radar: The semantic index for '{cwd}' is up to date "
            f"({files_indexed} files, {chunks_total} chunks, last indexed {last_indexed}). "
            "Use `/radar:search <query>` for semantic code search."
        )

    output = {
        "hookSpecificOutput": {
            "additionalContext": stats_context,
            "systemMessage": system_msg
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block the session
        sys.exit(0)
