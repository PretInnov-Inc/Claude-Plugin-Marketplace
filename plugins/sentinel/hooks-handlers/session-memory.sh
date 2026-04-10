#!/usr/bin/env bash
# Sentinel SessionStart Hook — Memory Context Loader (Category E)
#
# Fires at every session start. Reads learnings, decisions, and anti-patterns
# accumulated across past sessions and injects them into Claude's system prompt
# as additionalContext. This is the "accumulated wisdom" layer — Claude starts
# each session already knowing what worked, what failed, and what to avoid.
#
# Data sources (all in ${CLAUDE_PLUGIN_ROOT}/data/):
#   learnings.jsonl     — verified learnings from past sessions
#   decisions.jsonl     — architectural decisions with outcomes
#   anti-patterns.jsonl — patterns to avoid (learned from failures)
#   session-log.jsonl   — session health history
#
# Output: JSON with hookSpecificOutput.additionalContext injected to system prompt

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
DATA_DIR="${PLUGIN_ROOT}/data"

# Ensure data dir exists silently
mkdir -p "$DATA_DIR"

# Read config for limits
MAX_LEARNINGS=15
MAX_DECISIONS=5
MAX_ANTI_PATTERNS=8

CONFIG_FILE="${DATA_DIR}/sentinel-config.json"
if [ -f "$CONFIG_FILE" ]; then
  MAX_LEARNINGS=$(python3 -c "
import json
try:
  d = json.load(open('$CONFIG_FILE'))
  print(d.get('memory', {}).get('max_learnings_in_context', 15))
except:
  print(15)
" 2>/dev/null || echo 15)
  MAX_DECISIONS=$(python3 -c "
import json
try:
  d = json.load(open('$CONFIG_FILE'))
  print(d.get('memory', {}).get('max_decisions_in_context', 5))
except:
  print(5)
" 2>/dev/null || echo 5)
  MAX_ANTI_PATTERNS=$(python3 -c "
import json
try:
  d = json.load(open('$CONFIG_FILE'))
  print(d.get('memory', {}).get('max_anti_patterns_in_context', 8))
except:
  print(8)
" 2>/dev/null || echo 8)
fi

# Build the context via Python for safe JSON construction
python3 << PYEOF
import json, os, sys
from pathlib import Path

data_dir = Path("${DATA_DIR}")
max_learnings = ${MAX_LEARNINGS}
max_decisions = ${MAX_DECISIONS}
max_anti_patterns = ${MAX_ANTI_PATTERNS}

def read_jsonl_tail(path, n):
    """Read last n non-empty lines from a JSONL file."""
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

def read_session_health(path, n=10):
    """Read last n sessions for health summary."""
    items = read_jsonl_tail(path, n * 2)
    stops = [i for i in items if i.get("event") == "session_stop"]
    return stops[-n:]

sections = []

# 1. Learnings
learnings = read_jsonl_tail(data_dir / "learnings.jsonl", max_learnings)
if learnings:
    lines = []
    for l in learnings:
        cat = l.get("category", "general")
        msg = l.get("learning", "").strip()
        confidence = l.get("confidence", "")
        if msg:
            conf_str = f" [{confidence}]" if confidence else ""
            lines.append(f"  [{cat}]{conf_str} {msg}")
    if lines:
        sections.append("## Sentinel Learnings (from past sessions)\n" + "\n".join(lines))

# 2. Anti-patterns
anti_patterns = read_jsonl_tail(data_dir / "anti-patterns.jsonl", max_anti_patterns)
if anti_patterns:
    lines = []
    for ap in anti_patterns:
        pattern = ap.get("pattern", "").strip()
        reason = ap.get("reason", "").strip()
        if pattern:
            r_str = f" — {reason}" if reason else ""
            lines.append(f"  AVOID: {pattern}{r_str}")
    if lines:
        sections.append("## Anti-Patterns (do NOT repeat these)\n" + "\n".join(lines))

# 3. Recent decisions
decisions = read_jsonl_tail(data_dir / "decisions.jsonl", max_decisions)
if decisions:
    lines = []
    for d in decisions:
        decision = d.get("decision", "").strip()
        outcome = d.get("outcome", "pending")
        context = d.get("context", "").strip()
        if decision:
            outcome_icon = {"success": "✓", "failure": "✗", "pending": "?"}.get(outcome, "?")
            ctx_str = f" ({context})" if context else ""
            lines.append(f"  {outcome_icon} {decision}{ctx_str}")
    if lines:
        sections.append("## Recent Decisions\n" + "\n".join(lines))

# 4. Session health trend
sessions = read_session_health(data_dir / "session-log.jsonl")
if sessions:
    scores = [s.get("health_score", 0) for s in sessions if "health_score" in s]
    if scores:
        avg = sum(scores) / len(scores)
        trend = "improving" if len(scores) >= 2 and scores[-1] > scores[0] else "declining" if len(scores) >= 2 and scores[-1] < scores[0] else "stable"
        last_score = scores[-1]
        sections.append(f"## Session Health\n  Last: {last_score}/100 | Avg ({len(scores)} sessions): {avg:.0f}/100 | Trend: {trend}")

if not sections:
    # No memory yet — output nothing to avoid unnecessary noise
    sys.exit(0)

context_text = "# Sentinel Memory Context\n\n" + "\n\n".join(sections)
context_text += "\n\n---\n*Use /sentinel:flow-memory to view full history or /sentinel:dx-meta to manage project setup.*"

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context_text
    }
}
print(json.dumps(output))
PYEOF

exit 0
