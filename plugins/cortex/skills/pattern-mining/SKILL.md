---
name: pattern-mining
description: >-
  Use this skill when the user asks to "find patterns", "what patterns do you see",
  "analyze my habits", "recurring issues", "what keeps happening", "trends",
  "common mistakes", "frequently used", "most edited files", "technology trends",
  or when you need to mine historical data for actionable insights.
version: 1.0.0
---

# Pattern Mining

Extract actionable patterns from accumulated Cortex data and Claude Code history. Patterns are the raw material for self-optimization.

## Data Sources for Mining

### Cortex Data (plugin-generated)
- `data/tool-usage.jsonl` — Tool invocations with file paths, commands, timestamps
- `data/session-log.jsonl` — Session events with health scores, technologies
- `data/prompt-log.jsonl` — Prompt keywords and sizes
- `data/decision-journal.jsonl` — Decisions with outcomes
- `data/anti-patterns.jsonl` — Known failure patterns
- `data/learnings.jsonl` — Extracted learnings
- `data/patterns.jsonl` — Previously detected patterns

### Claude Code Native Data
- `~/.claude/history.jsonl` — All user prompts across all projects
- `~/.claude/todos/` — Task completion data (304 items across 36 active files)
- `~/.claude/projects/` — Per-project session data
- `~/.claude/stats-cache.json` — Global usage statistics

## Mining Algorithms

### 1. Repetitive Edit Detection
**Input**: tool-usage.jsonl filtered for Edit/Write/MultiEdit
**Algorithm**: Group by file_path, count within sliding window of 20 operations
**Signal**: File edited 5+ times = design hotspot
**Action**: Suggest refactoring, splitting, or rethinking approach

### 2. Failure Clustering
**Input**: anti-patterns.jsonl + session-log entries with health < 40
**Algorithm**: Extract keywords from failure descriptions, cluster by keyword overlap
**Signal**: 3+ failures sharing keywords = systemic issue
**Action**: Create a targeted learning to prevent recurrence

### 3. Technology Affinity
**Input**: session-log.jsonl technology arrays
**Algorithm**: Count co-occurrence of technologies per project
**Signal**: Stable tech stacks (django+htmx+tailwind) vs experimental (mixed stacks)
**Action**: Recommend proven stack combinations, warn about untested combos

### 4. Scope Creep Frequency
**Input**: prompt-log.jsonl word counts + session-log completion ratios
**Algorithm**: Correlate prompt size with completion ratio
**Signal**: Large prompts (>200 words) with low completion = scope issue
**Action**: Establish optimal prompt size range for this user

### 5. Decision Outcome Analysis
**Input**: decision-journal.jsonl with outcomes
**Algorithm**: Group by decision type, calculate success/failure rates
**Signal**: Architecture decisions with high failure rate = area needing more research
**Action**: For high-failure categories, recommend more upfront investigation

### 6. Time-of-Day Productivity
**Input**: session-log.jsonl timestamps + health scores
**Algorithm**: Group sessions by hour, calculate average health
**Signal**: Certain hours consistently produce higher-quality sessions
**Action**: Recommend optimal working hours

### 7. Project Health Trends
**Input**: session-log.jsonl grouped by project
**Algorithm**: Calculate rolling average health score per project
**Signal**: Declining health = project complexity exceeding session capacity
**Action**: Recommend breaking project into phases, using plans

## Mining Process

### Step 1: Extract Raw Data
Read all data files, parse JSONL, build in-memory structures.

### Step 2: Run All Algorithms
Execute each mining algorithm, collect findings.

### Step 3: Rank by Actionability
Score each finding:
- **High**: Directly actionable, clear fix (e.g., "file X is a hotspot — split it")
- **Medium**: Requires behavior change (e.g., "scope down prompts to <150 words")
- **Low**: Informational only (e.g., "most productive at midnight")

### Step 4: Generate Report

```
## Pattern Mining Report

### Critical Patterns (act now)
1. [pattern] — [evidence] — [recommendation]

### Behavioral Patterns (optimize over time)
1. [pattern] — [evidence] — [recommendation]

### Informational Patterns (awareness)
1. [pattern] — [evidence]

### Suggested New Rules
Based on patterns, these rules should be added to Cortex core rules:
1. [rule] — [evidence from N sessions]
```

### Step 5: Auto-Update
If high-confidence patterns are found (5+ occurrences):
- Auto-append to `learnings.jsonl` as new learnings
- Auto-append to `anti-patterns.jsonl` if failure-related
- Update `patterns.jsonl` with the mining results
