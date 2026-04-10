---
description: "Fast single-pass code review. Uses sentinel-reviewer + bug-hunter only. Works with or without git."
argument-hint: "[files] — specific files to check, or leave empty for auto-detect"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Agent", "TodoWrite"]
---

# Sentinel Quick Check

Fast code review using only 2 agents (sentinel-reviewer + bug-hunter) for a rapid quality gate.

**Arguments:** "$ARGUMENTS"

## Workflow

1. **Detect scope** using scope_detector.py (same as full review)
2. **Launch 2 agents in parallel**:
   - `sentinel-reviewer` (Sonnet) — CLAUDE.md compliance + code quality
   - `bug-hunter` (Opus) — logic errors and real bugs
3. **Aggregate** into a brief report
4. **Log** outcome to edit-log.jsonl

## Output Format

```
Sentinel Quick Check
--------------------
Files: [list]
Scope: [git/file-tracking/explicit]

Issues:
  [file:line] (confidence: N) — [description] [fix]

Clean: [files with no issues]

Result: PASS / NEEDS ATTENTION
```

Keep the output concise — this is meant for rapid iteration. Full detail available via `/sentinel:review`.
