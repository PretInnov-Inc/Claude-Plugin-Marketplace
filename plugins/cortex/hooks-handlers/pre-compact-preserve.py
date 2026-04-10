#!/usr/bin/env python3
"""
Cortex PreCompact Hook — Knowledge Preserver

Before Claude compacts context (loses older messages), this hook:
1. Extracts any learnings/decisions from the about-to-be-compacted context
2. Saves critical information to persistent storage
3. Ensures nothing valuable is lost during compaction

This is the SAFETY NET — compaction destroys context, this preserves the gold.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

def get_cortex_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = Path(plugin_root) / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def append_jsonl(filepath, data):
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except:
        pass

def extract_pre_compact_intelligence(transcript_path):
    """Extract critical info from transcript before it gets compacted."""
    if not transcript_path or not os.path.exists(transcript_path):
        return {}

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except:
        return {}

    intelligence = {
        "decisions": [],
        "file_paths_mentioned": [],
        "errors_encountered": [],
        "plans_created": False,
    }

    # Extract file paths that were being worked on
    paths = set(re.findall(r'(?:/[\w.-]+)+\.\w+', content[-20000:]))
    intelligence["file_paths_mentioned"] = list(paths)[:30]

    # Check if plans were created
    if re.search(r"(?:plan|Phase \d|implementation plan|roadmap)", content[-10000:], re.IGNORECASE):
        intelligence["plans_created"] = True

    # Extract user corrections (high value — these are decisions)
    corrections = re.findall(
        r"(?:don't|do not|never|stop|avoid|instead|rather|prefer|use|switch)\s+(.{10,100}?)(?:\.|!|\n)",
        content[-10000:],
        re.IGNORECASE
    )
    for c in corrections[:5]:
        intelligence["decisions"].append(c.strip())

    # Extract errors
    errors = re.findall(r"(?:Error|error|ERROR):\s*(.{10,200}?)(?:\n|$)", content[-10000:])
    intelligence["errors_encountered"] = [e.strip()[:200] for e in errors[:5]]

    return intelligence

def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    cwd = hook_input.get("cwd", "")
    transcript_path = hook_input.get("transcript_path", "")

    data_dir = get_cortex_data_dir()
    now = datetime.now(timezone.utc).isoformat()

    # Extract intelligence before compaction
    intel = extract_pre_compact_intelligence(transcript_path)

    if not intel:
        sys.exit(0)

    # Save decisions to journal
    for decision in intel.get("decisions", []):
        record = {
            "decision": decision,
            "type": "pre_compact_extraction",
            "project": os.path.basename(cwd) if cwd else "unknown",
            "session_id": session_id,
            "outcome": "pending",
            "timestamp": now,
        }
        append_jsonl(data_dir / "decision-journal.jsonl", record)

    # Save compaction event with context summary
    compact_record = {
        "event": "pre_compact",
        "session_id": session_id,
        "project": os.path.basename(cwd) if cwd else "unknown",
        "files_in_context": len(intel.get("file_paths_mentioned", [])),
        "had_plans": intel.get("plans_created", False),
        "errors_before_compact": len(intel.get("errors_encountered", [])),
        "decisions_preserved": len(intel.get("decisions", [])),
        "timestamp": now,
    }
    append_jsonl(data_dir / "session-log.jsonl", compact_record)

    # If plans were in context, warn
    if intel.get("plans_created"):
        learning = {
            "learning": f"Context compacted while plan was active in {os.path.basename(cwd) if cwd else 'unknown'}. Plans may need to be re-read from disk.",
            "category": "compaction-awareness",
            "session_id": session_id,
            "timestamp": now,
        }
        append_jsonl(data_dir / "learnings.jsonl", learning)

    sys.exit(0)

if __name__ == "__main__":
    main()
