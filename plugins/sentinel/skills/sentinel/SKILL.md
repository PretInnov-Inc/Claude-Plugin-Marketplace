---
name: sentinel
version: 3.0.0
description: >-
  Use when: user asks to review code, check quality, find bugs, audit security, verify changes before committing,
  or run any code quality check. Works with or without git. Auto-detects scope.
  Triggers on: "review my code", "check my changes", "find bugs", "audit security", "run sentinel",
  "is this safe to commit", "check quality", "run a review", "quick check".
  DO NOT trigger for: reviewing plugin structure (→ ai-validator), style preferences (→ style-engine),
  memory/history questions (→ flow-memory).
argument-hint: "[full|quick|security|quality|tests|<file-path>]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
execution_mode: parallel
---

# Sentinel — Unified Code Review Engine

## What It Does

Sentinel combines the best of 7 code review approaches into one unified system:
- Multi-agent parallel review (from code-review plugin)
- Adaptive confidence scoring (novel — learns your signal/noise preference)
- Security pattern blocking (from security-guidance, expanded to 16 patterns)
- Risk classification and churn detection (from clamper)
- Specialized domain agents (from pr-review-toolkit)
- Non-git support (novel — tracks edits via PostToolUse hooks)

## How To Use

### Slash Commands
- `/sentinel:review` — Full 6-agent review (quality, bugs, errors, security, tests, polish)
- `/sentinel:review quick` — Fast 2-agent check (quality + bugs)
- `/sentinel:review security` — Security-focused review
- `/sentinel:review tests` — Test coverage analysis
- `/sentinel:review quality` — Quality + simplification
- `/sentinel:review src/file.py` — Review specific files
- `/sentinel:quick-check` — Alias for quick mode

### Auto-Detection
Sentinel automatically detects what to review:
1. **Git projects**: Uses `git diff` for changed files
2. **Non-git projects**: Uses the edit log (tracked by PostToolUse hook) to find files modified this session
3. **Explicit files**: Pass file paths as arguments

### Adaptive Thresholds
The confidence threshold starts at 80 and adapts:
- If you say "show more" or "lower threshold" → threshold decreases (more findings)
- If you dismiss findings or say "too noisy" → threshold increases (fewer findings)
- Security scanner starts at 70 (more sensitive by default)
- Each agent has its own threshold

## Agents

| Agent | Model | Focus |
|-------|-------|-------|
| sentinel-reviewer | Sonnet | CLAUDE.md compliance, conventions, code quality |
| bug-hunter | Opus | Logic errors, null handling, race conditions, edge cases |
| error-auditor | Sonnet | Silent failures, empty catches, broad exceptions |
| security-scanner | Opus | OWASP Top 10, data flow analysis, trust boundaries |
| test-analyzer | Haiku | Behavioral test coverage, critical gaps, test quality |
| code-polisher | Haiku | Post-review simplification preserving behavior |

## Hooks (Always Active)

- **PreToolUse**: Layer 1 security patterns + Layer 2 operational gates (TDD, blueprint, destructive commands)
- **PostToolUse**: Edit tracking + output compression
- **SessionStart**: Memory injection + lineage + design-system loading
- **PreCompact/PostCompact**: Lossless learning preservation
- **Stop**: Typed MD learning extraction + lineage update
- **UserPromptSubmit**: Zero-token `>` shortcut routing

## Data Files

- `edit-log.jsonl` — Edit tracking log (the non-git diff)
- `sentinel-config.json` — Thresholds, agent config, review modes, activation gates
- `security-patterns.json` — Extensible security pattern library

## Risk Tiers (v3)

Sentinel auto-classifies each review into GREEN / YELLOW / RED / CRITICAL and routes to the
appropriate agent roster per `sentinel-config.json` risk_gating configuration.
