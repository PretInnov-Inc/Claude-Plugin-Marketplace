---
name: sentinel
version: 1.0.0
description: "Unified code review engine. Use when the user asks to review code, check quality, find bugs, audit security, or verify changes. Works with or without git. Auto-detects scope from git diff or session edit tracking."
triggers:
  - "review my code"
  - "check this code"
  - "find bugs"
  - "code review"
  - "security review"
  - "check for issues"
  - "is this code safe"
  - "review changes"
  - "audit this"
  - "quality check"
  - "does this look right"
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

- **PreToolUse**: Blocks edits containing security vulnerability patterns (16 patterns)
- **PostToolUse**: Tracks all edits for scope detection and risk classification

## Data Files

- `edit-log.jsonl` — Edit tracking log (the non-git diff)
- `sentinel-config.json` — Thresholds, agent config, review modes
- `security-patterns.json` — Extensible security pattern library
