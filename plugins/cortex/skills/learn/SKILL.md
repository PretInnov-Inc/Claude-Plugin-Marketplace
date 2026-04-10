---
description: Force-extract learnings from the current session into Cortex
argument-hint: [learning to record]
---

# Cortex Learn

Manually record a learning or force-extract learnings from the current conversation.

## If Arguments Provided

Record `$ARGUMENTS` as a manual learning. Append to `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl`:

```json
{
  "learning": "$ARGUMENTS",
  "category": "manual",
  "source": "user",
  "timestamp": "current ISO-8601"
}
```

Confirm what was saved.

## If No Arguments

Analyze the current conversation and extract:
1. Any user corrections ("don't do X", "instead use Y")
2. Any decisions made (technology choices, approach selections)
3. Any failures encountered and their causes
4. Any successful patterns worth remembering

For each extracted item, append to the appropriate Cortex data file:
- Corrections → `anti-patterns.jsonl`
- Decisions → `decision-journal.jsonl`
- Failures → `anti-patterns.jsonl`
- Successes → `learnings.jsonl`

Report what was extracted and saved.

Request: $ARGUMENTS
