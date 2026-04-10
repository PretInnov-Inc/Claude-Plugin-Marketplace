---
name: blueprint
description: >-
  Architecture blueprint phase for plugin creation. Designs the complete plugin
  structure including directory tree, data schemas, hook event map, agent roster,
  and skill inventory. Use after research and clarification phases are complete.
version: 1.0.0
argument-hint: "[plugin-name]"
---

# Forge Blueprint Phase

You are the architecture phase of the Plugin Forge pipeline. Design a complete, production-grade plugin blueprint for user approval.

## Prerequisites

Before blueprinting, ensure:
1. Research findings exist in `${CLAUDE_PLUGIN_ROOT}/data/research-cache.jsonl` for this concept
2. User requirements have been clarified (purpose, scope, features, constraints)

If either is missing, inform the user and suggest running `/forge:research` or the clarification step first.

## Blueprint Design Process

### 1. Plugin Identity
- **Name**: lowercase, kebab-case, max 20 chars. Must be unique and descriptive.
- **Version**: Always start at 1.0.0
- **Description**: One sentence, < 100 chars, explains the "what" and "why"
- **Keywords**: 5-8 tags for discoverability

### 2. Directory Structure Design
Map out every file that will be created. Follow the standard plugin layout:

```
<plugin-name>/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── hooks-handlers/
│   ├── <handler-1>.sh or .py
│   └── ...
├── skills/
│   ├── <skill-1>/SKILL.md
│   └── ...
├── agents/
│   ├── <agent-1>.md
│   └── ...
├── data/
│   ├── <config>.json
│   └── <log>.jsonl
├── bin/                      (if needed)
│   └── <cli-tool>
├── scripts/
│   └── install.sh
└── settings.json             (if a default agent is needed)
```

### 3. Hook Event Map

For each hook, specify:

| Event | Matcher | Handler File | Language | Purpose | Stdin Fields Used | Stdout Format | Timeout |
|-------|---------|-------------|----------|---------|-------------------|---------------|---------|

**Common patterns from proven plugins:**
- `SessionStart` → inject accumulated intelligence as `additionalContext`
- `PostToolUse` with matcher `Edit|Write|MultiEdit` → track file changes, detect patterns
- `PreToolUse` with matcher for dangerous tools → guard against known anti-patterns
- `Stop` → extract session learnings from transcript, update stats
- `UserPromptSubmit` → scope detection, repetition warnings
- `PreCompact` → preserve critical context before compaction

### 4. Agent Roster Design

For each agent, specify:
- **Name**: `<plugin>-<role>` naming convention
- **Model**: haiku (fast/frequent), sonnet (reasoning), opus (critical/self-modifying)
- **Tools**: Explicit allowlist. Read-only agents: `Read, Grep, Glob, Bash`. Write agents add: `Write, Edit`.
- **Color**: Optional, for visual distinction in multi-agent output
- **Role description**: What this agent does and when Claude should invoke it

**Proven agent archetypes:**
- **Verifier/Validator**: haiku, read-only, runs frequently
- **Analyst/Scout**: sonnet, read-only, deeper reasoning
- **Generator/Architect**: sonnet, write access, creates files
- **Learner/Miner**: sonnet, read-only, pattern extraction from data
- **Evolver**: opus, full write access, self-modification (use sparingly)

### 5. Skill Inventory Design

For each skill:
- **Name**: kebab-case folder name
- **Type**: "deep" (full standalone instructions) or "thin" (wrapper that delegates)
- **Auto-invoke**: Should Claude use this automatically, or manual `/command` only?
- **Frontmatter fields**: description, argument-hint, disable-model-invocation, allowed-tools, context

### 6. Data Schema Design

For each data file:
- **Format**: JSONL (append-only logs) or JSON (configuration)
- **Schema**: All fields with types
- **Writers**: Which hooks/agents/skills write to it
- **Readers**: Which hooks/agents/skills read from it
- **Trim rules**: Max entries before auto-trim

**Design principles:**
- One config JSON file for thresholds, suppression lists, and running stats
- Separate JSONL files per concern (don't mix event types in one file)
- Privacy by design: log keywords/metadata, not full content
- Every JSONL entry needs a `timestamp` field
- Include `session_id` for cross-session analysis

### 7. Integration Points

Determine if the plugin needs:
- **MCP server** (.mcp.json): Only if external tool integration is needed
- **bin/ tools**: Standalone CLI for data inspection without Claude
- **settings.json**: Only if a default agent should take over the session
- **output-styles/**: Only if the plugin changes how Claude formats responses
- **userConfig**: Values the user must provide at enable time (API keys, preferences)

## Blueprint Output Format

Present the complete blueprint using box-drawing:

```
═══════════════════════════════════════════
  PLUGIN FORGE — Architecture Blueprint
  <plugin-name> v1.0.0
═══════════════════════════════════════════

## Purpose
<one paragraph>

## Directory Structure
<full annotated tree>

## Plugin Manifest (plugin.json)
<key fields and values>

## Hook Event Map
<table>

## Agent Roster
<table with model/tools/role>

## Skill Inventory
<table with type/auto-invoke/description>

## Data Schemas
<each file with full field listing>

## Integration
<MCP/bin/settings/output-styles/userConfig details>

## Install Script Checklist
<files to validate, permissions to set>

═══════════════════════════════════════════
  Waiting for your approval to proceed to generation.
═══════════════════════════════════════════
```

## Save Blueprint

After presenting, save to `${CLAUDE_PLUGIN_ROOT}/data/blueprints.jsonl`:
```json
{
  "plugin_name": "<name>",
  "description": "<description>",
  "status": "pending",
  "generated": false,
  "directory_structure": "<tree>",
  "components": {
    "agents": <count>,
    "skills": <count>,
    "hooks": <count>,
    "hook_handlers": <count>,
    "data_files": <count>,
    "bin_tools": <count>
  },
  "blueprint_text": "<full blueprint>",
  "research_findings_count": <how many research entries were used>,
  "session_id": "<id>",
  "timestamp": "<ISO-8601>"
}
```

When the user approves, update the blueprint status to `"approved"` and proceed to `/forge:generate`.
