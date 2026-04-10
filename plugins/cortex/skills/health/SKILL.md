---
description: Full health check of the .claude/ ecosystem and Cortex intelligence layer
argument-hint: [deep]
---

# Cortex Health Check

Run a comprehensive health check of the entire Claude Code ecosystem.

## Standard Health Check

### 1. Cortex Data Integrity
Check all data files in `${CLAUDE_PLUGIN_ROOT}/data/`:
- Do all .jsonl files contain valid JSON per line?
- Are timestamps in chronological order?
- Are there any corrupt entries?
- File sizes (are any growing too large?)

### 2. Hook Health
Verify all Cortex hooks are functional:
- Check that `session-start.sh` is executable
- Check that all Python hook scripts exist and have valid syntax: `python3 -m py_compile <script>`
- Verify `hooks.json` is valid JSON

### 3. Memory Health
Scan `~/.claude/projects/*/memory/`:
- Count projects with memories
- Check for broken MEMORY.md references
- Detect fragmented projects (same project at multiple paths)
- Report stale memories (referencing files/functions that no longer exist)

### 4. Plugin Health
Check Cortex plugin structure:
- Verify `.claude-plugin/plugin.json` is valid
- Count skills, agents, commands
- Check all agent/skill/command files have valid frontmatter

### 5. Workspace Metrics
Report on .claude/ directory:
- Total size
- Largest subdirectories
- Dead weight estimate (from workspace-hygiene analysis)

### 6. Intelligence Metrics
From Cortex data:
- Total learnings active
- Total anti-patterns tracked
- Total decisions logged
- Average session health (last 10 sessions)
- Trend direction

## Deep Health Check (if `$ARGUMENTS` = "deep")

Additionally:
- Read `~/.claude/stats-cache.json` for global usage stats
- Analyze `~/.claude/history.jsonl` for prompt pattern evolution
- Cross-reference decisions with anti-patterns for contradictions
- Check for orphaned sessions (in projects/ but no matching session-env)

## Output Format

```
╔══════════════════════════════════════════╗
║           CORTEX HEALTH CHECK            ║
╠══════════════════════════════════════════╣

## Data Integrity: [PASS/WARN/FAIL]
- learnings.jsonl: OK (N entries, N KB)
- anti-patterns.jsonl: OK (N entries, N KB)
...

## Hook Health: [PASS/WARN/FAIL]
- session-start.sh: [executable/not executable]
- session-stop.py: [valid syntax/syntax error]
...

## Memory Health: [PASS/WARN/FAIL]
- Projects with memory: N/49
- Fragmented projects: N
- Stale memories: N

## Workspace: [CLEAN/NEEDS CLEANUP]
- Total .claude/ size: N MB
- Dead weight: N MB (N% of total)
- Recommendation: [run /cortex:clean if > 20%]

## Intelligence: [ACTIVE/DEGRADED/EMPTY]
- Learnings: N
- Anti-patterns: N
- Decisions: N (S/F/P)
- Health trend: [improving/declining/stable]

Overall: [HEALTHY/ATTENTION NEEDED/CRITICAL]
╚══════════════════════════════════════════╝
```

Request: $ARGUMENTS
