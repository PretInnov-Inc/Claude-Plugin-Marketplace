#!/usr/bin/env python3
"""Clamper PostToolUse Hook — Verification trigger after code edits.

Fires after Edit/Write/MultiEdit. Tracks edit patterns and triggers
verification warnings when confidence thresholds demand review.
This is the "Clamp" — Claude Code doesn't verify its own output.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_clamper_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return os.path.join(plugin_root, "data")
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def append_jsonl(filepath, data):
    with open(filepath, "a") as f:
        f.write(json.dumps(data) + "\n")


def read_jsonl_tail(filepath, n=50):
    entries = []
    if not os.path.exists(filepath):
        return entries
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries[-n:]


def load_config(data_dir):
    config_path = os.path.join(data_dir, "clamper-config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {"thresholds": {"auto_verify_on_edit": True, "verification_confidence_minimum": 80}}


def detect_risky_edit(tool_name, tool_input):
    """Detect edits that warrant verification based on risk signals."""
    risk_signals = []
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("new_string", "") or tool_input.get("content", "")
    command = tool_input.get("command", "")

    # Signal: editing test files (risk of breaking test assertions)
    if any(p in file_path for p in ["test_", "_test.", ".test.", "spec.", "tests/"]):
        risk_signals.append("test-file-modification")

    # Signal: editing config/build files
    config_patterns = [
        "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
        "Makefile", "Dockerfile", "docker-compose", ".env",
        "settings.py", "config.", "tsconfig", "webpack", "vite.config"
    ]
    if any(p in file_path for p in config_patterns):
        risk_signals.append("config-file-modification")

    # Signal: editing auth/security-related files
    security_patterns = ["auth", "login", "permission", "token", "session", "crypto", "secret"]
    if any(p in file_path.lower() for p in security_patterns):
        risk_signals.append("security-sensitive-file")

    # Signal: large edit (content over 100 lines)
    if content and content.count("\n") > 100:
        risk_signals.append("large-edit")

    # Signal: deletion-heavy edit (more removed than added)
    old_string = tool_input.get("old_string", "")
    if old_string and content:
        removed_lines = old_string.count("\n")
        added_lines = content.count("\n")
        if removed_lines > added_lines * 2 and removed_lines > 10:
            risk_signals.append("deletion-heavy")

    return risk_signals


def count_session_edits(data_dir, file_path, session_id, window=20):
    """Count recent edits to the same file in this session."""
    log_path = os.path.join(data_dir, "verification-log.jsonl")
    entries = read_jsonl_tail(log_path, window)
    count = 0
    for entry in entries:
        if (entry.get("session_id") == session_id and
                entry.get("file_path") == file_path and
                entry.get("event") == "edit_tracked"):
            count += 1
    return count


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "unknown")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    data_dir = get_clamper_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    config = load_config(data_dir)
    now = datetime.now(timezone.utc).isoformat()

    file_path = tool_input.get("file_path", "unknown")
    risk_signals = detect_risky_edit(tool_name, tool_input)

    # Track every edit
    edit_record = {
        "event": "edit_tracked",
        "tool": tool_name,
        "file_path": file_path,
        "risk_signals": risk_signals,
        "session_id": session_id,
        "timestamp": now
    }
    append_jsonl(os.path.join(data_dir, "verification-log.jsonl"), edit_record)

    # Check for repetitive editing (churn signal)
    edit_count = count_session_edits(data_dir, file_path, session_id)
    messages = []

    if edit_count >= 5:
        messages.append(
            f"CLAMPER CHURN DETECTED: {file_path} has been edited {edit_count} times this session. "
            f"Consider stepping back — repeated edits to the same file often indicate an approach problem, "
            f"not an implementation problem. Run /clamp to verify current state."
        )
        append_jsonl(os.path.join(data_dir, "verification-log.jsonl"), {
            "event": "churn_detected",
            "file_path": file_path,
            "edit_count": edit_count,
            "session_id": session_id,
            "timestamp": now
        })

    # Risk-based verification prompt
    if risk_signals and config.get("thresholds", {}).get("auto_verify_on_edit", True):
        risk_level = "HIGH" if len(risk_signals) >= 2 else "MEDIUM"
        signal_str = ", ".join(risk_signals)
        messages.append(
            f"CLAMPER {risk_level} RISK: Edit to {os.path.basename(file_path)} "
            f"triggered signals: [{signal_str}]. "
            f"Recommend running /clamp to verify this change against project standards."
        )

    # Auto-trim verification log
    log_path = os.path.join(data_dir, "verification-log.jsonl")
    entries = read_jsonl_tail(log_path, 3000)
    if len(entries) > 2500:
        trimmed = entries[-2000:]
        with open(log_path, "w") as f:
            for entry in trimmed:
                f.write(json.dumps(entry) + "\n")

    if messages:
        output = {"systemMessage": "\n\n".join(messages)}
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
