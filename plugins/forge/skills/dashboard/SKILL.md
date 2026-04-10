---
name: dashboard
description: >-
  View Plugin Forge build history, statistics, and system health.
  Use when asked about forge status, past builds, or plugin generation stats.
version: 1.0.0
argument-hint: "[stats | builds | research | config]"
disable-model-invocation: true
---

# Forge Dashboard

Display Plugin Forge statistics and build history.

## Usage
- `/forge:dashboard` — Full dashboard
- `/forge:dashboard stats` — Quick stats only
- `/forge:dashboard builds` — Build history
- `/forge:dashboard research` — Research cache summary
- `/forge:dashboard config` — Current configuration

## Full Dashboard

Read all data files from `${CLAUDE_PLUGIN_ROOT}/data/` and render:

```
═══════════════════════════════════════════
  PLUGIN FORGE DASHBOARD
═══════════════════════════════════════════

  Build Stats
  ───────────────────────────────────────
  Total builds:     <N>
  Success rate:     <N>%
  Files generated:  <N>
  Agents created:   <N>
  Skills created:   <N>
  Hooks created:    <N>

  Recent Builds
  ───────────────────────────────────────
  <date> │ <plugin-name> │ <status> │ <files> files │ health: <N>/100
  <date> │ <plugin-name> │ <status> │ <files> files │ health: <N>/100
  ...

  Research Cache
  ───────────────────────────────────────
  Total findings:    <N>
  Sources scanned:   <N>
  Categories:        <breakdown>

  Learning System
  ───────────────────────────────────────
  Total learnings:   <N>
  Categories:        <breakdown>
  Last learning:     <date>

  Active Blueprints
  ───────────────────────────────────────
  <name> — <status> — <components>
  ...

  Configuration
  ───────────────────────────────────────
  Research depth:    <min>-<max> queries
  Auto-validate:     <yes/no>
  Default complexity: <value>
  Learning threshold: <N> builds

═══════════════════════════════════════════
```

## Data Sources
- `${CLAUDE_PLUGIN_ROOT}/data/forge-config.json` — stats and config
- `${CLAUDE_PLUGIN_ROOT}/data/build-log.jsonl` — build events
- `${CLAUDE_PLUGIN_ROOT}/data/research-cache.jsonl` — research findings
- `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl` — accumulated learnings
- `${CLAUDE_PLUGIN_ROOT}/data/blueprints.jsonl` — saved blueprints
