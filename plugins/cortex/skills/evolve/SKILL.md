---
description: "Trigger Cortex self-evolution: process feedback, tune thresholds, promote patterns"
argument-hint: "review, apply, undo, status, suppress, tune"
---

# Cortex Evolve

Self-modify the Cortex plugin based on accumulated feedback and patterns.

Parse `$ARGUMENTS`:

## "review" or no arguments
Review pending evolution actions:
1. Read `${CLAUDE_PLUGIN_ROOT}/data/user-feedback.jsonl` — show unprocessed feedback
2. Read `${CLAUDE_PLUGIN_ROOT}/data/evolution-log.jsonl` — show recent evolutions
3. Read `${CLAUDE_PLUGIN_ROOT}/data/cortex-config.json` — show current thresholds and suppressions
4. Analyze patterns.jsonl for promotion candidates (5+ occurrences)
5. Present a summary of what could be evolved and ask user for approval

## "apply"
Process ALL pending user feedback:
1. Read user-feedback.jsonl
2. For each `suppress_warning` signal → add to cortex-config.json suppressed_warnings
3. For each `teach` signal → add to learnings.jsonl
4. For each `project_rule` signal → add to cortex-config.json project_overrides
5. For each `tune_threshold` signal → adjust cortex-config.json thresholds
6. For each `negative_feedback` → review the relevant rule and suggest modification
7. Log ALL changes to evolution-log.jsonl
8. Clear processed entries from user-feedback.jsonl

## "undo"
Show the last 5 evolution actions from evolution-log.jsonl.
Ask which to undo. Reverse the change (only if `reversible: true`).

## "status"
Show evolution statistics:
- Total self-evolutions performed
- Learnings added by evolution
- Rules suppressed
- Thresholds tuned
- Current active suppressions
- Current project overrides

## "suppress <category>"
Manually suppress a warning category. Categories:
git-safety, destructive-ops, workspace-management, secret-detection,
claude-md-safety, backup-safety, scope-management, repetitive-editing,
anti-pattern-match, repetition-detection

Ask if global or project-specific. Add to cortex-config.json. Log to evolution-log.jsonl.

## "tune <param> <value>"
Manually tune a threshold parameter:
- scope_task_threshold (default: 5, range: 3-15)
- scope_word_threshold (default: 300, range: 100-1000)
- repetitive_edit_threshold (default: 5, range: 3-20)
- low_health_threshold (default: 40, range: 20-70)
- auto_suppress_after_ignores (default: 10, range: 3-50)
- pattern_promotion_threshold (default: 5, range: 3-20)

Update cortex-config.json. Log to evolution-log.jsonl.

## Important

Use the `self-evolver` agent for complex evolution actions that require modifying hook scripts.
For simple config changes, modify cortex-config.json directly.
ALWAYS log every change to evolution-log.jsonl.

Request: $ARGUMENTS
