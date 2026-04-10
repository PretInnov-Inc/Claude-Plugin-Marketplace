---
description: Run workspace hygiene — clean dead weight from .claude/ directory
argument-hint: [category or 'all']
---

# Cortex Clean

Activate the `workspace-hygiene` skill. Run the cleanup process.

If `$ARGUMENTS` specifies a category, clean only that:
- "telemetry" — Remove failed telemetry events
- "session-env" — Remove empty session-env directories
- "todos" — Remove empty todo files
- "debug" — Remove old debug logs (keep last 5)
- "security" — Remove old security warning files (keep last 10)
- "history" — Remove old file-history (30+ days)
- "cortex" — Trim Cortex's own data files
- "all" — Run all categories
- No args — Show assessment only (dry run)

**CRITICAL**: Always show the assessment FIRST. Never delete without user confirmation.

Also run Cortex data file trimming:
- `tool-usage.jsonl` → keep last 2000 entries
- `prompt-log.jsonl` → keep last 500 entries
- `session-log.jsonl` → keep last 1000 entries
- `learnings.jsonl` → keep last 200 entries
- `anti-patterns.jsonl` → keep last 100 entries
- `decision-journal.jsonl` → keep last 500 entries

Request: $ARGUMENTS
