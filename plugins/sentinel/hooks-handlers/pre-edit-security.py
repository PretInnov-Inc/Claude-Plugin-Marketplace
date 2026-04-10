#!/usr/bin/env python3
"""Sentinel PreToolUse Hook — Security pattern blocker.

Fires BEFORE Edit/Write/MultiEdit. Matches file paths and content against
an extensible pattern library (security-patterns.json). Blocks the edit
with exit code 2 on first match, showing remediation guidance.

Inspired by security-guidance plugin but expanded:
- Loads patterns from external JSON (extensible without code changes)
- Session-scoped dedup (warn once per file+rule per session)
- Auto-cleanup of stale state files
- Works on ANY project (no git dependency)
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__)))


def get_data_dir():
    return os.path.join(get_plugin_root(), "data")


def load_patterns():
    """Load security patterns from external JSON file."""
    patterns_file = os.path.join(get_data_dir(), "security-patterns.json")
    if os.path.exists(patterns_file):
        try:
            with open(patterns_file, "r") as f:
                data = json.load(f)
                return data.get("patterns", [])
        except (json.JSONDecodeError, IOError):
            pass
    return []


def get_state_file(session_id):
    """Session-specific state file to track which warnings have been shown."""
    state_dir = os.path.expanduser("~/.claude")
    return os.path.join(state_dir, f"sentinel_security_state_{session_id}.json")


def cleanup_old_state_files():
    """Remove state files older than 7 days."""
    try:
        state_dir = os.path.expanduser("~/.claude")
        if not os.path.exists(state_dir):
            return
        cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        for fname in os.listdir(state_dir):
            if fname.startswith("sentinel_security_state_") and fname.endswith(".json"):
                fpath = os.path.join(state_dir, fname)
                try:
                    if os.path.getmtime(fpath) < cutoff:
                        os.remove(fpath)
                except OSError:
                    pass
    except Exception:
        pass


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_state(session_id, shown_warnings):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown_warnings), f)
    except IOError:
        pass


def extract_content(tool_name, tool_input):
    """Extract content to scan from tool input."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(edit.get("new_string", "") for edit in edits)
    return ""


def check_patterns(file_path, content, patterns):
    """Check file path and content against all patterns. Returns first match."""
    path_lower = file_path.lower()

    for pattern in patterns:
        if not pattern.get("enabled", True):
            continue

        # Path-based patterns
        path_patterns = pattern.get("path_patterns", [])
        for pp in path_patterns:
            if pp in path_lower:
                return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")

        # Content substring patterns
        substrings = pattern.get("substrings", [])
        if content:
            for sub in substrings:
                if sub in content:
                    return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")

        # Content regex patterns (optional, stdlib re)
        regex_patterns = pattern.get("regex", [])
        if content and regex_patterns:
            import re
            for rx in regex_patterns:
                try:
                    if re.search(rx, content):
                        return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")
                except re.error:
                    continue

    return None, None, None


def main():
    # Periodically clean up (5% chance)
    if random.random() < 0.05:
        cleanup_old_state_files()

    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "default")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    patterns = load_patterns()

    rule_id, severity, reminder = check_patterns(file_path, content, patterns)

    if rule_id and reminder:
        warning_key = f"{file_path}::{rule_id}"
        shown = load_state(session_id)

        if warning_key not in shown:
            shown.add(warning_key)
            save_state(session_id, shown)

            # Format the warning
            severity_label = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM"}.get(severity, "WARNING")
            output = f"SENTINEL [{severity_label}] {reminder}"
            print(output, file=sys.stderr)

            # Block on critical/high severity
            if severity in ("critical", "high"):
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
