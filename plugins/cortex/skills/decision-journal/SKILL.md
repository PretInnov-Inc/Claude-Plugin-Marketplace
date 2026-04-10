---
name: decision-journal
description: >-
  Use this skill when the user asks to "track a decision", "what did we decide",
  "decision history", "why did we choose", "record this choice", "what worked",
  "what failed", "mark decision as success", "mark decision as failure",
  "review past decisions", or when a significant architectural or design
  decision is being made that should be recorded for future reference.
version: 1.0.0
---

# Decision Journal

A persistent record of decisions made across all projects and sessions. Decisions are the most valuable memory — they capture WHY something was done, not just WHAT.

## Why Track Decisions

From analysis of 500+ sessions:
- Memory's greatest value is storing **decisions and preferences**, not code patterns
- The most useful memories are corrections ("don't do X") and non-obvious constraints
- Without a journal, the same bad decisions get repeated across sessions
- Plans are the most valuable persistent artifact — decisions power those plans

## Decision Structure

Each decision record contains:

```json
{
  "decision": "Use Vanilla JS instead of Vue for Tour2Tech PMO",
  "type": "user_correction|architecture|technology|approach|rejection",
  "reasoning": "User explicitly rejected Vue.js framework for this project",
  "alternatives_considered": ["Vue.js", "React"],
  "project": "tour2tech-pmo",
  "outcome": "pending|success|failure",
  "outcome_notes": "Completed 188 modules successfully with Vanilla JS",
  "session_id": "abc123",
  "timestamp": "2026-03-15T10:30:00Z"
}
```

## Recording Decisions

### When to Record (auto-detected by hooks)
The Stop hook auto-extracts decisions from user corrections ("don't", "instead", "prefer"). But you should also MANUALLY record:

1. **Architecture decisions** — "Use Django + HTMX instead of React SPA"
2. **Technology rejections** — "No Vue.js for this project"
3. **Approach selections** — "Bundled PR over many small ones"
4. **Constraint declarations** — "Never auto-commit without asking"
5. **Trade-off resolutions** — "Prioritize security over ergonomics for auth middleware"

### How to Record
Append to `${CLAUDE_SKILL_DIR}/../../data/decision-journal.jsonl`:

```python
import json
from datetime import datetime, timezone

record = {
    "decision": "...",
    "type": "architecture",
    "reasoning": "...",
    "project": "project-name",
    "outcome": "pending",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

with open(journal_path, "a") as f:
    f.write(json.dumps(record) + "\n")
```

## Querying Decisions

### By Project
```bash
grep -i "project-name" data/decision-journal.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    icon = {'success':'OK','failure':'FAIL','pending':'?'}.get(d.get('outcome','?'),'?')
    print(f'[{icon}] {d[\"decision\"][:80]} ({d.get(\"type\",\"\")})')
"
```

### By Outcome
- Find all failures: `grep '"outcome":"failure"' decision-journal.jsonl`
- Find all successes: `grep '"outcome":"success"' decision-journal.jsonl`
- Find pending: `grep '"outcome":"pending"' decision-journal.jsonl`

### By Type
- Corrections: `grep '"type":"user_correction"' decision-journal.jsonl`
- Architecture: `grep '"type":"architecture"' decision-journal.jsonl`
- Rejections: `grep '"type":"rejection"' decision-journal.jsonl`

## Updating Outcomes

When a decision's outcome becomes clear, update it:

1. Read the journal file
2. Find the matching decision by content and timestamp
3. Update the `outcome` field to "success" or "failure"
4. Add `outcome_notes` explaining why

## Decision Patterns to Watch

| Pattern | Signal | Action |
|---|---|---|
| Same rejection repeated | User keeps having to say "don't do X" | Promote to anti-pattern |
| Decision followed by failure | Approach didn't work | Record as lesson learned |
| Decision across multiple projects | Universal preference | Promote to core rule |
| Contradictory decisions | Different choices for same problem | Flag for user review |

## Integration with Anti-Patterns

When a decision leads to failure:
1. Record the failure outcome in the journal
2. Auto-create an anti-pattern entry: `{"what": "...", "why": "Failed in project X — ..."}`
3. The anti-pattern gets injected via SessionStart hook into future sessions

When a decision leads to success:
1. Record the success outcome
2. Consider promoting to a learning: `{"learning": "...", "category": "validated-approach"}`
3. Successful patterns reinforce future recommendations
