#!/usr/bin/env python3
"""Sentinel PostToolUse Hook — Edit tracker, risk classifier, churn detector.

Fires AFTER every Edit/Write/MultiEdit. Responsibilities:
1. Log every edit to edit-log.jsonl (powers file-tracking scope for non-git projects)
2. Classify risk signals per file (from clamper's approach, expanded)
3. Detect churn (repeated edits to same file = approach problem)
4. Update adaptive confidence thresholds based on historical patterns

This hook is the foundation of Sentinel's non-git support:
the edit log IS the diff for projects without version control.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__)))


def get_data_dir():
    return os.path.join(get_plugin_root(), "data")


def append_jsonl(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a") as f:
        f.write(json.dumps(data) + "\n")


def read_jsonl_tail(filepath, n=100):
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


def load_config():
    config_path = os.path.join(get_data_dir(), "sentinel-config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "churn_threshold": 5,
        "auto_warn_on_risk": True,
        "adaptive_confidence": {
            "enabled": True,
            "base_threshold": 80,
            "min_threshold": 60,
            "max_threshold": 95,
            "decay_rate": 0.05
        }
    }


def classify_risk(file_path, tool_name, tool_input):
    """Classify risk signals for this edit. Expanded from clamper's approach."""
    signals = []
    path_lower = file_path.lower()
    content = tool_input.get("new_string", "") or tool_input.get("content", "")

    # Test file modification
    if any(p in path_lower for p in ["test_", "_test.", ".test.", "spec.", "tests/", "__tests__"]):
        signals.append("test-file-modification")

    # Config/build files
    config_patterns = [
        "package.json", "pyproject.toml", "cargo.toml", "go.mod",
        "makefile", "dockerfile", "docker-compose", ".env",
        "settings.py", "tsconfig", "webpack", "vite.config",
        "requirements.txt", "setup.py", "pipfile", "gemfile",
        "build.gradle", "pom.xml", "cmakelists"
    ]
    if any(p in path_lower for p in config_patterns):
        signals.append("config-file-modification")

    # Security-sensitive files
    security_patterns = [
        "auth", "login", "permission", "token", "session", "crypto",
        "secret", "password", "credential", "oauth", "jwt", "csrf"
    ]
    if any(p in path_lower for p in security_patterns):
        signals.append("security-sensitive-file")

    # Database/migration files
    if any(p in path_lower for p in ["migration", "schema", "seed", "sql"]):
        signals.append("database-modification")

    # CI/CD files
    if any(p in path_lower for p in [".github/workflows", ".gitlab-ci", "jenkinsfile", ".circleci"]):
        signals.append("ci-cd-modification")

    # API/route files
    if any(p in path_lower for p in ["route", "endpoint", "controller", "handler", "api/"]):
        signals.append("api-layer-modification")

    # Large edit (100+ lines of new content)
    if content and content.count("\n") > 100:
        signals.append("large-edit")

    # Deletion-heavy edit
    old_string = tool_input.get("old_string", "")
    if old_string and content:
        removed = old_string.count("\n")
        added = content.count("\n")
        if removed > added * 2 and removed > 10:
            signals.append("deletion-heavy")

    # New file creation
    if tool_name == "Write":
        signals.append("new-file-created")

    return signals


def count_session_edits(data_dir, file_path, session_id, window=50):
    """Count recent edits to same file in this session."""
    log_path = os.path.join(data_dir, "edit-log.jsonl")
    entries = read_jsonl_tail(log_path, window)
    return sum(
        1 for e in entries
        if e.get("session_id") == session_id
        and e.get("file_path") == file_path
        and e.get("event") == "edit_tracked"
    )


def get_risk_tier(signals):
    """Map risk signals to a tier (1-4) matching clamper's classification."""
    if not signals:
        return 1, "LOW"
    critical = {"database-modification", "ci-cd-modification", "security-sensitive-file"}
    high = {"config-file-modification", "api-layer-modification", "deletion-heavy"}
    medium = {"test-file-modification", "large-edit", "new-file-created"}

    if critical & set(signals):
        return 4 if len(signals) >= 2 else 3, "CRITICAL" if len(signals) >= 2 else "HIGH"
    if high & set(signals):
        return 3, "HIGH"
    if medium & set(signals):
        return 2, "MEDIUM"
    return 1, "LOW"


def trim_log(log_path, max_entries=3000, keep_entries=2000):
    """Auto-trim log to prevent unbounded growth."""
    entries = read_jsonl_tail(log_path, max_entries)
    if len(entries) >= max_entries - 100:
        trimmed = entries[-keep_entries:]
        with open(log_path, "w") as f:
            for entry in trimmed:
                f.write(json.dumps(entry) + "\n")


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

    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    config = load_config()
    now = datetime.now(timezone.utc).isoformat()

    file_path = tool_input.get("file_path", "unknown")
    risk_signals = classify_risk(file_path, tool_name, tool_input)
    risk_tier, risk_label = get_risk_tier(risk_signals)

    # Log every edit (this IS the non-git diff)
    edit_record = {
        "event": "edit_tracked",
        "tool": tool_name,
        "file_path": file_path,
        "risk_signals": risk_signals,
        "risk_tier": risk_tier,
        "risk_label": risk_label,
        "session_id": session_id,
        "timestamp": now
    }
    log_path = os.path.join(data_dir, "edit-log.jsonl")
    append_jsonl(log_path, edit_record)

    messages = []

    # Churn detection
    churn_threshold = config.get("churn_threshold", 5)
    edit_count = count_session_edits(data_dir, file_path, session_id)
    if edit_count >= churn_threshold:
        messages.append(
            f"SENTINEL CHURN: {os.path.basename(file_path)} edited {edit_count} times this session. "
            f"Repeated edits to the same file often indicate an approach problem, not an implementation problem. "
            f"Consider stepping back or running /sentinel:review to assess."
        )
        append_jsonl(log_path, {
            "event": "churn_detected",
            "file_path": file_path,
            "edit_count": edit_count,
            "session_id": session_id,
            "timestamp": now
        })

    # Risk-based warning
    if risk_signals and config.get("auto_warn_on_risk", True) and risk_tier >= 3:
        signal_str = ", ".join(risk_signals)
        messages.append(
            f"SENTINEL {risk_label} RISK: Edit to {os.path.basename(file_path)} "
            f"triggered signals: [{signal_str}]. "
            f"Recommend running /sentinel:review to verify this change."
        )

    # Auto-trim log
    trim_log(log_path)

    if messages:
        print(json.dumps({"systemMessage": "\n\n".join(messages)}))

    sys.exit(0)


if __name__ == "__main__":
    main()
