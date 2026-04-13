---
name: sentinel-audit
version: 3.0.0
description: >-
  Use when: user wants to evaluate the quality of Sentinel's own skills, agents, or hook handlers
  using the 120-point rubric. "Audit sentinel", "check skill quality", "are my agents well-designed",
  "evaluate sentinel's skill descriptions".
  DO NOT trigger for: checking if sentinel is running (→ sentinel-doctor), reviewing application code (→ sentinel),
  validating plugin file structure (→ ai-validator within ai-forge).
argument-hint: "[skills|agents|hooks|all] [specific-name]"
allowed-tools: Read, Glob, Grep, Bash, TodoWrite, Agent
execution_mode: direct
---

# Sentinel Audit — Self-Evaluation Skill

You run a quality audit on Sentinel's own components using the sentinel-auditor agent.

## Parse Arguments

- (empty) or `all` → Audit all skills + agents
- `skills` → Skills only
- `agents` → Agents only  
- `hooks` → Hook handler quality only
- `skills [name]` → Specific skill SKILL.md
- `agents [name]` → Specific agent .md

## Routing

Launch `sentinel-auditor` agent with the scope from `$ARGUMENTS`.

Provide the agent:
1. The file paths to audit (Glob them before launching)
2. The scope (skills/agents/hooks/all)
3. Instruction to use the 120-point rubric and produce the full report

## Pre-Agent File Collection

```bash
# Collect files before launching agent
ls "${CLAUDE_PLUGIN_ROOT}/skills/"*/SKILL.md
ls "${CLAUDE_PLUGIN_ROOT}/agents/"*.md | grep -v ".gitkeep"
```

## After Agent Returns

Present the agent's report to the user and suggest:
1. Highest-priority fixes (score < 60)
2. Offer to implement the fixes inline or via agent

## Example Interaction

```
/sentinel:sentinel-audit agents sentinel-reviewer

→ Launches sentinel-auditor targeting agents/sentinel-reviewer.md
→ Returns 120-point score with dimension breakdown
→ Reports: "Trigger Precision: 12/15 — PASS, Negative Triggers: 15/15 — PASS, ..."
→ Suggests fixes for any dimensions < 8/15
```
