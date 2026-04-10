---
name: style-engine
version: 2.0.0
description: >-
  Output Style Manager. Use when the user wants to change how Claude responds — switch to
  minimal/focused mode, educational/learning mode, or detailed/verbose mode. Also use when
  the user says "be more concise", "explain more", "teach me", "just give me the code",
  "more detail", "stop explaining", "switch to learning mode", "use focused mode".
  Consolidates learning-output-style, explanatory-output-style, cortex output-styles.
argument-hint: "[focused|learning|verbose] or describe desired style"
allowed-tools: Read, Write, Edit, Glob, Bash, TodoWrite, Agent
---

# Sentinel Style Engine — Output Style Manager

You manage the active output style for this Sentinel installation. Style changes take effect on the NEXT session start (the SessionStart hook injects the active style).

## Parse Arguments

`$ARGUMENTS` can be:
- `focused` / `minimal` / `concise` / `code-first` → Switch to focused style
- `learning` / `educational` / `teach` / `explain` → Switch to learning style
- `verbose` / `detailed` / `full` → Switch to verbose style
- `status` / `current` / (empty) → Show current style + preview
- `reset` → Reset to default (focused)

## Actions

### Show Current Style
Read `${CLAUDE_PLUGIN_ROOT}/data/sentinel-config.json` and extract `output_style.active`.
Display:
```
SENTINEL STYLE ENGINE
=====================
Active style: [name] — [description]
Available styles: focused | learning | verbose
Takes effect: on next session start

Style preview:
[first 3-4 lines of the style's rules]

To change: /sentinel:style-engine [focused|learning|verbose]
```

### Switch Style
1. Read `${CLAUDE_PLUGIN_ROOT}/data/sentinel-config.json`
2. Update `output_style.active` to the requested style
3. Write the config back
4. Confirm the change:
```
SENTINEL STYLE ENGINE
=====================
✓ Style changed: [old] → [new]
Takes effect: next session start (/restart to apply now)

[new style] means:
[2-3 bullet summary of what changes]
```

## Style Summaries

**focused** (default):
- Code-first, no preamble, no trailing summaries
- One-line status at milestones only
- Break silence only for errors or explicit questions

**learning**:
- ★ Insight blocks before/after significant code
- Invite user contributions for trade-off decisions
- Explain the "why" behind architectural choices

**verbose**:
- Explain every decision with alternatives considered
- Connect changes to the broader codebase
- Full context for errors and design decisions
- Best for onboarding, documentation, or pair-programming

## Agent Delegation

Launch `style-conductor` agent only if:
- The user wants a CUSTOM style not in the three defaults
- The user wants to preview a style interactively before switching

For standard switches, do it directly without launching an agent.
