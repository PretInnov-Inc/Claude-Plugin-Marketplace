---
name: failure-forensics
description: >-
  Use this skill when the user asks to "analyze failures", "why did this fail",
  "what went wrong", "debug this pattern", "recurring errors", "investigate failures",
  "failure analysis", "post-mortem", "root cause", "what keeps breaking",
  or when you need to understand why past sessions or tasks failed.
version: 1.0.0
---

# Failure Forensics

Systematic investigation of failures across sessions, projects, and operations. Every failure is a learning opportunity — this skill ensures no failure goes uninvestigated.

## Failure Data Sources

1. **anti-patterns.jsonl** — Recorded failures from past sessions
2. **session-log.jsonl** — Sessions with health scores < 40
3. **decision-journal.jsonl** — Decisions with outcome "failure"
4. **tool-usage.jsonl** — Tool operations that preceded failures
5. **learnings.jsonl** — Lessons already extracted from failures

## Failure Categories (from 500+ sessions analysis)

### Category 1: Scope Failures (~40%)
**Symptom**: Low completion ratio, many pending todos, session ends with work unfinished
**Root Cause**: Over-ambitious planning, too many tasks in one session
**Historical Evidence**: Todo completion rate is 40%. 60% of multi-phase plans never complete.
**Prevention**: 
- Cap tasks at 4-5 per session
- Put testing in Phase 1
- Create plans for multi-session work instead of trying to do everything

### Category 2: Approach Failures (~25%)
**Symptom**: Same file edited 5+ times, multiple retries of similar operations
**Root Cause**: Wrong initial approach, not enough upfront research
**Historical Evidence**: Repetitive edit pattern detected in tool-usage data
**Prevention**:
- Read before writing (check Read:Write ratio)
- Verify SDK exports/types before proposing approaches
- Research existing patterns before creating new ones

### Category 3: Context Failures (~15%)
**Symptom**: Asking for information that was in a previous session, redoing work
**Root Cause**: Project directory moved (fragments context), compaction lost critical info
**Historical Evidence**: Internal-Tracker split across 3 paths = 3 separate memory silos
**Prevention**:
- Never move project directories
- Create plans for important decisions (persists across sessions)
- Use Cortex decision journal to capture important choices

### Category 4: Integration Failures (~10%)
**Symptom**: Code works in isolation but breaks when combined, test failures
**Root Cause**: Testing deferred to end, incomplete understanding of system
**Historical Evidence**: Testing is almost always the last and most-skipped step
**Prevention**:
- Test FIRST (Phase 1, not last)
- Run existing tests before making changes
- Verify against actual installed code, not assumed APIs

### Category 5: Configuration Failures (~10%)
**Symptom**: Environment issues, wrong model, missing dependencies
**Root Cause**: Configuration drift, missing setup steps
**Historical Evidence**: Chrome extension connection failures (65 debug logs), model routing issues
**Prevention**:
- Pre-approve common commands in settings.json
- Use CCS proxy for model routing when needed
- Document configuration in CLAUDE.md

## Investigation Process

### Step 1: Identify the Failure
Read the failure data and classify:
- When did it happen? (timestamp)
- What project? (project field)
- What category? (match against categories above)
- What was the immediate trigger? (error message, tool failure, etc.)

### Step 2: Trace the Causal Chain
For each failure, work backwards:
1. What was the last successful operation?
2. What changed between success and failure?
3. Were there warning signs (scope warnings, repetitive edits)?
4. Was this failure seen before? (check anti-patterns)

### Step 3: Extract Root Cause
Distinguish between:
- **Proximate cause**: The immediate trigger (e.g., "test failed")
- **Root cause**: The underlying issue (e.g., "approached without reading existing tests")
- **Systemic cause**: The pattern that enables this (e.g., "testing always deferred")

### Step 4: Generate Prevention Rules
For each root cause, create:
1. A **learning** for `learnings.jsonl`
2. An **anti-pattern** for `anti-patterns.jsonl` (if not already recorded)
3. A **decision** for `decision-journal.jsonl` (if applicable)

### Step 5: Report

```
## Failure Forensics Report

### Failure: [description]
- **When**: [date/session]
- **Project**: [name]
- **Category**: [scope/approach/context/integration/configuration]
- **Proximate Cause**: [what triggered it]
- **Root Cause**: [why it happened]
- **Systemic Cause**: [what pattern enables it]
- **Already Known**: [yes/no — was this in anti-patterns?]
- **Prevention Rule**: [new rule added to Cortex]
- **Status**: [mitigated/unresolved/recurring]
```

## Recurring Failure Detection

A failure is **recurring** if:
- Same error keyword appears 3+ times in anti-patterns
- Same project has 3+ low-health sessions
- Same decision type has 3+ failure outcomes

For recurring failures:
1. ESCALATE to the user — this isn't a one-off, it's a systematic problem
2. Recommend structural changes (not just behavioral)
3. Consider whether the approach itself needs to change
