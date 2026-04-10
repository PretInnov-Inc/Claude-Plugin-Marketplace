#!/usr/bin/env python3
"""
Cortex PostToolUse Hook — Pattern Tracker + Warning Effectiveness Analyzer

After every tool execution, this hook:
1. Tracks tool usage frequency per project
2. Records file modification patterns
3. Detects repetitive operations (editing same file 5+ times = possible design issue)
4. Builds a usage profile that feeds into pattern mining
5. [SELF-ADAPT] Uses config-driven thresholds for repetitive edit detection
6. [SELF-ADAPT] Tracks ignored warnings for auto-suppression analysis
7. [SELF-ADAPT] Respects per-project suppression rules

Runs silently — no output to transcript unless a significant pattern is detected.
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

def get_cortex_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = Path(plugin_root) / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def append_jsonl(filepath, data):
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass

def count_recent_edits_to_file(tracker_file, file_path, window=20):
    """Count how many times a file was edited in the last N entries."""
    if not tracker_file.exists():
        return 0
    count = 0
    try:
        with open(tracker_file, "r") as f:
            lines = f.readlines()
            for line in lines[-window:]:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("file_path") == file_path and entry.get("tool") in ("Edit", "Write", "MultiEdit"):
                        count += 1
                except:
                    pass
    except:
        pass
    return count

def load_config(data_dir):
    """Load cortex-config.json for adaptive thresholds."""
    config_file = data_dir / "cortex-config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except:
            pass
    return {"thresholds": {"repetitive_edit_threshold": 5}, "suppressed_warnings": [], "project_overrides": {}}


def is_warning_suppressed(config, category, project):
    """Check if a warning is suppressed globally or per-project."""
    for suppression in config.get("suppressed_warnings", []):
        if suppression.get("category") == category:
            scope = suppression.get("scope", "global")
            if scope == "global" or scope == f"project:{project}":
                return True
    overrides = config.get("project_overrides", {}).get(project, {})
    if category in overrides.get("suppressed_rules", []):
        return True
    return False


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "unknown")
    cwd = hook_input.get("cwd", "")

    data_dir = get_cortex_data_dir()
    tracker_file = data_dir / "tool-usage.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    # Extract file path from tool input
    file_path = tool_input.get("file_path", "")
    command = tool_input.get("command", "") if tool_name == "Bash" else ""

    # Record usage
    record = {
        "tool": tool_name,
        "file_path": file_path,
        "command_preview": command[:100] if command else "",
        "project": os.path.basename(cwd) if cwd else "unknown",
        "session_id": session_id,
        "timestamp": now,
    }
    append_jsonl(tracker_file, record)

    # Load adaptive config for thresholds
    config = load_config(data_dir)
    thresholds = config.get("thresholds", {})
    edit_threshold = thresholds.get("repetitive_edit_threshold", 5)
    project = os.path.basename(cwd) if cwd else "unknown"

    # Check suppression
    suppressed = is_warning_suppressed(config, "repetitive-editing", project)

    # Check for repetitive edit pattern
    if tool_name in ("Edit", "Write", "MultiEdit") and file_path:
        edit_count = count_recent_edits_to_file(tracker_file, file_path, window=20)

        if edit_count >= edit_threshold:
            # Record as a pattern (always, even if warning is suppressed)
            pattern_record = {
                "pattern": "repetitive_editing",
                "detail": f"File {os.path.basename(file_path)} edited {edit_count} times in recent window",
                "file": file_path,
                "project": project,
                "timestamp": now,
            }
            append_jsonl(data_dir / "patterns.jsonl", pattern_record)

            # Warn Claude ONLY if not suppressed and first detection at threshold
            if edit_count == edit_threshold and not suppressed:
                output = {
                    "systemMessage": f"Cortex: File '{os.path.basename(file_path)}' has been edited {edit_count} times this session. Consider whether the approach needs rethinking."
                }
                print(json.dumps(output))
                sys.exit(0)

    # Auto-trim tool usage log (keep last 2000 entries)
    try:
        if tracker_file.exists():
            with open(tracker_file, "r") as f:
                lines = f.readlines()
            if len(lines) > 2500:
                with open(tracker_file, "w") as f:
                    f.writelines(lines[-2000:])
    except:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
