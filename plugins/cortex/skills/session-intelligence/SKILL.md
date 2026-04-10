---
name: session-intelligence
description: >-
  Use this skill when the user asks to "analyze my sessions", "show session stats",
  "how productive was I", "session health", "what did I accomplish", "review my history",
  "how am I using Claude Code", "usage patterns", or when you need to understand
  the user's working patterns to provide better assistance.
version: 1.0.0
---

# Session Intelligence

Analyze Claude Code session data to extract productivity insights, detect patterns, and provide actionable recommendations.

## Data Sources

Session intelligence draws from these Cortex data files (all in `${CLAUDE_SKILL_DIR}/../../data/`):

1. **session-log.jsonl** — Session start/end events with health scores, completion ratios, technologies used
2. **tool-usage.jsonl** — Every tool invocation with file paths, commands, timestamps
3. **prompt-log.jsonl** — Prompt keywords and word counts (not full content)
4. **learnings.jsonl** — Auto-extracted learnings from past sessions
5. **patterns.jsonl** — Detected patterns (repetitive edits, tech usage, etc.)

Also reference the global Claude Code data:
- `~/.claude/projects/` — Per-project session history
- `~/.claude/stats-cache.json` — Global usage statistics

## Analysis Process

### Step 1: Load Session Data
Read `${CLAUDE_SKILL_DIR}/../../data/session-log.jsonl` and compute:
- Total sessions tracked by Cortex
- Average health score across sessions
- Health score trend (improving or declining?)
- Most active projects (by session count)
- Completion ratio distribution

### Step 2: Productivity Analysis
From the session log, calculate:
- **Sessions per day** (group by date)
- **Health score by project** (which projects have the healthiest sessions?)
- **Time-of-day patterns** (when do you start sessions?)
- **Technology frequency** (what tech stacks are most used?)
- **Failure rate** (sessions with health < 40)

### Step 3: Tool Usage Patterns
Read `tool-usage.jsonl` and analyze:
- Most used tools (Edit vs Write vs Bash vs Read)
- Files edited most frequently (potential hotspots)
- Average edits per session
- Bash command categories (git, npm, python, etc.)

### Step 4: Scope Management Score
From `prompt-log.jsonl`:
- Average prompt word count (shorter = more focused)
- How often scope warnings fired
- Trend: getting more focused or more scattered?

### Step 5: Generate Report

Output a structured report:

```
## Session Intelligence Report

### Overview
- Total Cortex-tracked sessions: N
- Average health score: N/100
- Health trend: [improving/declining/stable]

### Productivity Hotspots
- Most productive project: [name] (avg health: N)
- Least productive project: [name] (avg health: N)
- Peak productivity hours: [time range]

### Tool Patterns
- Primary tool: [name] (N% of usage)
- Hotspot files: [files edited 5+ times]
- Bash categories: [git N%, npm N%, python N%]

### Scope Management
- Average prompt size: N words
- Scope warnings triggered: N times
- Completion ratio: N%

### Recommendations
1. [Based on data]
2. [Based on patterns]
3. [Based on failures]
```

## Recommendations Engine

Generate recommendations based on these rules:

| Signal | Recommendation |
|---|---|
| Health < 50 average | "Sessions are struggling. Consider smaller, more focused tasks." |
| Same file edited 5+ times | "File X is a hotspot. Consider refactoring or splitting it." |
| Completion ratio < 0.4 | "You're completing less than 40% of planned work. Scope down aggressively." |
| High Bash usage | "Heavy shell usage. Consider creating custom commands for repeated operations." |
| Single project dominates | "Project X dominates sessions. Consider dedicated focus blocks." |
| Low Read vs Write ratio | "Writing more than reading. Read-first approach prevents rework." |
