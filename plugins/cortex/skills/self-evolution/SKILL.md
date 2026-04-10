---
name: self-evolution
description: >-
  Use this skill when Cortex needs to adapt itself based on user feedback,
  conversation signals, or observed patterns. Triggers when the user says
  "stop warning", "remember this", "cortex should", "don't alert me",
  "adjust cortex", "tune the warnings", "update the rules", "evolve",
  "adapt", or when the user corrects Cortex behavior in any way.
version: 1.0.0
---

# Self-Evolution

Cortex is a living system. It adapts based on three signal sources:

1. **Explicit feedback** — User directly tells Cortex to change ("stop warning about X")
2. **Implicit signals** — User ignores warnings repeatedly, overrides suggestions, or shows frustration
3. **Pattern validation** — Mined patterns confirmed by user behavior or explicit approval

## Signal Detection

### Explicit Feedback Signals
These phrases in user prompts should trigger evolution:

| Signal Pattern | Evolution Action |
|---|---|
| "stop warning about X" / "don't warn me about X" | Suppress that warning category |
| "remember that X" / "always do X" | Add as learning |
| "never do X" / "don't ever X" | Add as anti-pattern |
| "cortex is wrong about X" | Review and correct the rule |
| "this rule is too strict" / "too many warnings" | Increase threshold |
| "this rule is too loose" / "not enough warnings" | Decrease threshold |
| "for this project, X" | Add project-specific override |
| "promote this pattern" / "make this a rule" | Promote pattern to learning |
| "this decision worked" / "that approach failed" | Update decision outcome |

### Implicit Feedback Signals
Detected by hooks and tracked in `user-feedback.jsonl`:

| Signal | Meaning | Evolution |
|---|---|---|
| Same warning shown 5+ times, user never acts on it | Warning is noise | Auto-suppress after 10 occurrences |
| User immediately does what was warned against | Warning is irrelevant to user | Track, suppress after 3 consecutive ignores |
| User asks same question across 3+ sessions | Cortex failed to learn the answer | Promote to active learning |
| User corrects Claude's approach in the same way 3+ times | Recurring correction not captured | Auto-add as anti-pattern |
| Scope warning fires but session completes at 80%+ health | Scope was fine | Increase scope threshold |
| Scope warning fires and session health < 30 | Scope was indeed too large | Reinforce scope warning |

### Pattern Validation Signals
From the pattern-mining results:

| Signal | Evolution |
|---|---|
| Pattern appeared 5+ times with consistent outcome | Auto-promote to learning |
| Pattern appeared but with mixed outcomes | Keep as pattern, flag for review |
| Pattern contradicts existing learning | Flag contradiction, ask user |

## Configuration-Driven Adaptation

All tunable parameters live in `data/cortex-config.json`:

```json
{
  "version": 1,
  "thresholds": {
    "scope_task_threshold": 5,
    "scope_word_threshold": 300,
    "repetitive_edit_threshold": 5,
    "low_health_threshold": 40,
    "auto_suppress_after_ignores": 10,
    "pattern_promotion_threshold": 5
  },
  "suppressed_warnings": [
    {"category": "git-commit", "scope": "project:clamper", "reason": "User wants auto-commit here"}
  ],
  "project_overrides": {
    "tour2tech-pmo": {
      "extra_learnings": ["Use Vanilla JS, never Vue.js"],
      "suppressed_rules": []
    }
  },
  "evolution_stats": {
    "total_evolutions": 0,
    "learnings_added": 0,
    "rules_suppressed": 0,
    "thresholds_tuned": 0,
    "last_evolution": null
  }
}
```

## Evolution Process

### Step 1: Detect Signal
The hooks detect signals and write to `data/user-feedback.jsonl`:

```json
{
  "signal_type": "explicit|implicit|pattern",
  "signal": "User said: stop warning about git commit",
  "context": {"project": "clamper", "warning_category": "git-safety"},
  "session_id": "abc123",
  "timestamp": "ISO-8601"
}
```

### Step 2: Classify Action
Map the signal to an evolution action:
- Is it about a specific warning? → Suppress/tune
- Is it a new preference? → Add learning
- Is it a correction? → Add anti-pattern
- Is it about a threshold? → Tune config
- Is it project-specific? → Add override

### Step 3: Execute via Self-Evolver Agent
The `self-evolver` agent:
1. Reads the signal from user-feedback.jsonl
2. Determines the minimal change needed
3. Prefers config changes (cortex-config.json) over code changes
4. Makes the change
5. Logs to evolution-log.jsonl
6. Reports what was changed

### Step 4: Verify
After any code change: `python3 -m py_compile <file>`
After any config change: validate JSON

### Step 5: Feedback Loop
Next SessionStart loads the updated config, and the new behavior takes effect immediately.

## Auto-Adaptation (No User Intervention Needed)

These adaptations happen automatically based on accumulated data:

### Warning Auto-Suppression
```
IF warning W was shown N times (N >= auto_suppress_after_ignores)
AND user acted against the warning every time
THEN add W to suppressed_warnings with scope=current-project
AND log to evolution-log.jsonl
```

### Learning Auto-Promotion
```
IF pattern P appeared K times (K >= pattern_promotion_threshold)
AND all outcomes were consistent (all success OR all failure)
THEN promote to learning (success) or anti-pattern (failure)
AND mark pattern as promoted
AND log to evolution-log.jsonl
```

### Threshold Auto-Tuning
```
IF scope warnings fire AND session health > 70 (false positive)
  FOR 3 consecutive sessions
THEN increase scope_task_threshold by 2
AND log to evolution-log.jsonl

IF scope warnings DON'T fire AND session health < 30 (missed warning)
  FOR 3 consecutive sessions  
THEN decrease scope_task_threshold by 1
AND log to evolution-log.jsonl
```

### Decision Auto-Closure
```
IF decision D has outcome "pending" for > 30 days
AND the project had 5+ successful sessions since
THEN auto-set outcome to "success" (validated by usage)
AND log to evolution-log.jsonl
```

## Anti-Gaming Rules

To prevent the system from evolving into uselessness:

1. **Core rules are immutable** — The 8 core rules in SessionStart can never be auto-suppressed. Only the user can explicitly ask to remove them via the self-evolver.
2. **Minimum learning count** — Learnings can never drop below 10 entries (the initial seed)
3. **Suppression requires evidence** — At least 5 ignores before auto-suppressing
4. **Evolution rate limit** — Max 3 auto-evolutions per session
5. **Contradiction detection** — If an evolution contradicts an existing rule, flag for user review instead of applying
6. **Rollback support** — Every evolution is logged with `reversible: true/false`. Reversible changes can be undone via `/cortex:evolve undo`
