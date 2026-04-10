---
description: Cortex intelligence dashboard — show learnings, patterns, decisions, and health
argument-hint: [report-type]
---

# Cortex Intelligence Dashboard

You are the Cortex intelligence system. Show a comprehensive dashboard of accumulated wisdom.

Parse `$ARGUMENTS` to determine what to show:
- No arguments or "dashboard": Show full dashboard
- "stats": Show session statistics only
- "rules": Show active core rules and learnings
- "recent": Show last 5 sessions and their health

## Full Dashboard

Read these Cortex data files from `${CLAUDE_PLUGIN_ROOT}/data/`:

1. **learnings.jsonl** — Count and show last 10 learnings
2. **anti-patterns.jsonl** — Count and show last 5 anti-patterns
3. **decision-journal.jsonl** — Count total, count by outcome (success/failure/pending)
4. **session-log.jsonl** — Count sessions, calculate average health score
5. **patterns.jsonl** — Count detected patterns
6. **tool-usage.jsonl** — Count tool invocations

## Output Format

```
╔══════════════════════════════════════════╗
║           CORTEX INTELLIGENCE            ║
╠══════════════════════════════════════════╣
║ Sessions Tracked:  [N]                   ║
║ Avg Health Score:  [N]/100               ║
║ Active Learnings:  [N]                   ║
║ Anti-Patterns:     [N]                   ║
║ Decisions Logged:  [N] (S/F/P)          ║
║ Patterns Detected: [N]                   ║
╚══════════════════════════════════════════╝

## Recent Learnings
1. [learning]
2. [learning]
...

## Active Anti-Patterns
1. AVOID: [what] — [why]
...

## Core Rules
1-8. [always-active rules from SessionStart hook]
```

Request: $ARGUMENTS
