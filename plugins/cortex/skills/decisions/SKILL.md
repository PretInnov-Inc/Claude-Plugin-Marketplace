---
description: Query and manage the Cortex decision journal
argument-hint: [project-name or 'all' or 'failures' or 'record <decision>']
---

# Cortex Decisions

Query or record decisions in the Cortex decision journal.

Parse `$ARGUMENTS`:

## "record <decision text>"
Record a new decision. Ask the user for:
- Type: architecture / technology / approach / rejection
- Reasoning: why this was decided
- Project: which project (default: current directory)

Append to `${CLAUDE_PLUGIN_ROOT}/data/decision-journal.jsonl`.

## "update <search terms>"
Find a matching decision and update its outcome to success or failure.

## "failures"
Show all decisions with outcome = "failure". Analyze what went wrong.

## "successes"
Show all decisions with outcome = "success". What patterns are validated?

## "<project-name>"
Show all decisions for that project.

## "all" or no arguments
Show summary: total decisions, breakdown by type and outcome. Then show the last 10 decisions.

## Output Format

```
## Decision Journal

Total: N decisions (S success, F failure, P pending)

### Recent Decisions
| # | Decision | Type | Project | Outcome |
|---|----------|------|---------|---------|
| 1 | ...      | ...  | ...     | ...     |
```

Request: $ARGUMENTS
