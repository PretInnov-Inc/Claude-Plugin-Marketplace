#!/usr/bin/env python3
"""
Sentinel PostCompact Hook — Memory Re-injector (Category E)

Fires immediately after Claude Code compacts the conversation transcript.
When compaction happens mid-session, the SessionStart memory injection
(done by session-memory.sh) is no longer in the context window. This hook
re-injects the sentinel memory context so Claude continues with accumulated
wisdom, not a blank slate.

The compact_summary from the event is also prepended so Claude has both:
  1. The compaction summary (what happened before)
  2. The sentinel memory index (learnings, anti-patterns, decisions)

Pure stdlib — no pip dependencies.
"""

import json
import os
import sys
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def read_jsonl_tail(path: Path, n: int) -> list:
    if not path.exists():
        return []
    items = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []
    return items[-n:]


def build_memory_context(data_dir: Path) -> str:
    """Build a compact memory context for re-injection after compaction."""
    sections = []

    # Load config limits
    config_path = data_dir / "sentinel-config.json"
    max_l, max_d, max_ap = 10, 3, 5  # conservative defaults post-compact
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            mem = cfg.get("memory", {})
            # Use slightly reduced limits post-compact to save context space
            max_l = max(5, mem.get("max_learnings_in_context", 15) // 2)
            max_d = max(2, mem.get("max_decisions_in_context", 5) // 2)
            max_ap = max(3, mem.get("max_anti_patterns_in_context", 8) // 2)
        except Exception:
            pass

    # Learnings
    learnings = read_jsonl_tail(data_dir / "learnings.jsonl", max_l)
    if learnings:
        lines = [
            f"  [{l.get('category', 'general')}] {l.get('learning', '').strip()}"
            for l in learnings if l.get("learning", "").strip()
        ]
        if lines:
            sections.append("## Sentinel Learnings\n" + "\n".join(lines))

    # Anti-patterns
    aps = read_jsonl_tail(data_dir / "anti-patterns.jsonl", max_ap)
    if aps:
        lines = [
            f"  AVOID: {ap.get('pattern', '').strip()}"
            for ap in aps if ap.get("pattern", "").strip()
        ]
        if lines:
            sections.append("## Anti-Patterns\n" + "\n".join(lines))

    # Recent decisions
    decisions = read_jsonl_tail(data_dir / "decisions.jsonl", max_d)
    if decisions:
        icons = {"success": "✓", "failure": "✗", "pending": "?"}
        lines = [
            f"  {icons.get(d.get('outcome', 'pending'), '?')} {d.get('decision', '').strip()}"
            for d in decisions if d.get("decision", "").strip()
        ]
        if lines:
            sections.append("## Recent Decisions\n" + "\n".join(lines))

    if not sections:
        return ""

    return "# Sentinel Memory (re-injected after compaction)\n\n" + "\n\n".join(sections)


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    data_dir = Path(get_plugin_root()) / "data"
    memory_context = build_memory_context(data_dir)

    if not memory_context:
        sys.exit(0)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostCompact",
            "additionalContext": memory_context
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
