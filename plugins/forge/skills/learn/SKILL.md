---
name: learn
description: >-
  Extract learnings from past plugin builds or manually record a learning.
  Use when asked about build patterns, past mistakes, or to review what
  the forge has learned.
version: 1.0.0
argument-hint: "[mine | record <learning> | show | clear]"
---

# Forge Learn

Manage the Plugin Forge's learning system.

## Usage
- `/forge:learn` or `/forge:learn mine` — Mine patterns from build history (delegate to forge-learner)
- `/forge:learn record <text>` — Manually record a learning
- `/forge:learn show` — Display all current learnings
- `/forge:learn show <category>` — Filter learnings by category
- `/forge:learn clear` — Clear all learnings (with confirmation)

## Categories
- `build-quality` — What makes a plugin build succeed or fail
- `component-design` — Best patterns for hooks, agents, skills
- `research-strategy` — What research approaches work best
- `process` — Pipeline process improvements
- `scope-management` — Avoiding over/under-engineering

## Manual Recording

When `$ARGUMENTS` starts with "record", extract the learning text and write to `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl`:
```json
{
  "learning": "<the text after 'record'>",
  "category": "<infer from content, or ask>",
  "source": "manual",
  "timestamp": "<ISO-8601>"
}
```

## Pattern Mining

When `$ARGUMENTS` is empty or "mine", delegate to the `forge-learner` agent to analyze all data files and extract patterns.

## Show Learnings

Read `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl` and display in formatted table:
```
═══════════════════════════════════════════
  FORGE LEARNINGS (<N> total)
═══════════════════════════════════════════

  [build-quality] <learning>
    Source: <source> | <timestamp>

  [component-design] <learning>
    Source: <source> | <timestamp>
  ...
═══════════════════════════════════════════
```
