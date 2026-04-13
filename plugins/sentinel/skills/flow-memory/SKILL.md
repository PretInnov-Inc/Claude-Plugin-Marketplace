---
name: flow-memory
version: 3.0.0
description: >-
  Use when: user asks about session history, accumulated learnings, past decisions, session health,
  or wants to track/forget/query memory. Also use for lineage commands (rollover, resume) and
  typed learning store queries (.sentinel/learnings/).
  Triggers on: "show my learnings", "what have you learned", "track this decision",
  "session history", "show decisions", "memory", "what patterns", "session health",
  "forget this", "remember that", "log this decision", "productivity patterns",
  "rollover session", "resume session", "search learnings", "refresh learnings".
  DO NOT trigger for: capturing a learning RIGHT NOW from conversation (→ session-scribe agent),
  full retrospective analysis (→ memory-warden agent).
argument-hint: "[dashboard|decisions|learnings|health|add|forget|rollover|search|refresh] [details]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
execution_mode: direct
---

# Sentinel Flow Memory — Workflow Intelligence

You manage accumulated session intelligence. All data lives in `${CLAUDE_PLUGIN_ROOT}/data/`.

## Parse Arguments

- (empty) or `dashboard` → Full intelligence dashboard
- `decisions` → Show decision log with outcomes
- `learnings` → Show extracted learnings by category
- `health` → Session health trend analysis
- `add decision [text]` → Log a new architectural decision
- `add learning [text]` → Log a new learning manually
- `add anti-pattern [text]` → Log an anti-pattern to avoid
- `forget [text]` → Remove a learning or anti-pattern matching [text]
- `resolve [n] [success|failure]` → Mark decision #n as succeeded or failed
- `clean` → Remove stale/redundant entries
- `patterns` → Show detected usage patterns

## Data Files

All files in `${CLAUDE_PLUGIN_ROOT}/data/`:

| File | Format | Content |
|---|---|---|
| `learnings.jsonl` | JSONL | `{category, learning, confidence, session_id, timestamp}` |
| `decisions.jsonl` | JSONL | `{decision, outcome, context, session_id, timestamp}` |
| `anti-patterns.jsonl` | JSONL | `{pattern, reason, category, session_id, timestamp}` |
| `session-log.jsonl` | JSONL | `{event, session_id, health_score, technologies, timestamp}` |
| `edit-log.jsonl` | JSONL | `{event, tool, file_path, risk_signals, risk_tier, session_id, timestamp}` |

## Dashboard Format

```
╔══════════════════════════════════════════════╗
║        SENTINEL FLOW MEMORY                  ║
╠══════════════════════════════════════════════╣
║ Sessions Tracked:    [N]                     ║
║ Avg Health Score:    [N]/100                 ║
║ Active Learnings:    [N]                     ║
║ Anti-Patterns:       [N]                     ║
║ Decisions (S/F/P):   [N] ([S] success)       ║
╚══════════════════════════════════════════════╝

## Recent Learnings
[category] [confidence] — [learning text]
...

## Anti-Patterns (avoid these)
AVOID: [pattern] — [reason]
...

## Recent Decisions
✓ [success] / ✗ [failure] / ? [pending] — [decision]
...

## Session Health Trend
[sparkline or description of health over last 10 sessions]

## Most Active Files (from edit log)
[top 5 files by edit frequency]
```

## Adding Records

When user says "remember X" or "track decision X":
1. Parse the intent (is it a decision, learning, or anti-pattern?)
2. Write to the appropriate JSONL file:
```json
{"learning": "X", "category": "user-explicit", "confidence": "high", "session_id": "manual", "timestamp": "ISO8601"}
```
3. Confirm: "Logged to Sentinel memory. Will appear in next session context."

## Cleaning Memory

When user says "forget X" or `/sentinel:flow-memory forget X`:
1. Read the relevant JSONL
2. Find lines matching X (substring or semantic match)
3. Rewrite the file excluding matched lines
4. Report what was removed

## Typed Learning Store (v3)

`.sentinel/learnings/<category>/` holds structured Markdown learning files. Two tracks:
- **knowledge** track: `applies_when` + `insight` fields — browsable best practices
- **bug** track: `symptoms` + `root_cause` + `prevention` fields — error pattern library

Commands:
- `search [query]` → `grep -r "query" .sentinel/learnings/` then read top matches
- `refresh` → Run `bin/sentinel-refresh` to apply 5-outcome maintenance (keep/update/consolidate/replace/delete)
- `add knowledge [text]` → Write a new knowledge MD via `bin/sentinel-learn knowledge`
- `add bug [symptom]` → Write a new bug MD via `bin/sentinel-learn bug`

## Lineage Commands (v3)

- `rollover` → Fork to new session: run `sentinel-status --trigger rollover`
- `resume` → Print handoff context for next session: run `sentinel-status --trigger resume`
- `lineage` → Show `.sentinel/lineage/<username>.json` ancestor chain

## Agent Delegation

Launch `memory-warden` agent for:
- Complex pattern analysis across hundreds of sessions
- Deduplication and consolidation of JSONL learnings
- Generating a structured memory-index.md summary
- Analyzing decision outcomes for systematic lessons

For simple read/write operations (add, forget, show), do it directly without an agent.
For typed store operations (search, refresh, add knowledge/bug), use CLI tools or grep directly.
