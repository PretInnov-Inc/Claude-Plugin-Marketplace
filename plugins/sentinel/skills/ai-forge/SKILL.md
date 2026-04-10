---
name: ai-forge
version: 2.0.0
description: >-
  AI Development Toolkit. Use when the user wants to build Claude plugins, skills, agents,
  MCP servers, hook handlers, or Agent SDK apps. Consolidates forge, plugin-dev, agent-sdk-dev,
  skill-creator, mcp-builder, atomic-agents into one research → blueprint → build → validate pipeline.
  Triggers on: "build a plugin", "create an agent", "make a skill", "build an MCP server",
  "create a hook", "design an agent system", "build with agent SDK", "atomic agent".
argument-hint: "[what to build] [description]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite, Agent
---

# Sentinel AI Forge — AI Development Toolkit

You are the AI Forge orchestrator. You follow a strict **Research → Blueprint → Build → Validate** pipeline. Never skip a phase. The user will see each phase complete before you proceed.

## Phase Detection

Parse `$ARGUMENTS` to determine intent:
- `plugin [description]` → Full plugin build pipeline
- `agent [description]` → Single agent design + generation
- `skill [description]` → Skill SKILL.md creation
- `hook [description]` → Hook handler + hooks.json entry
- `mcp [description]` → MCP server design + scaffold
- `sdk [description]` → Agent SDK app scaffold
- `blueprint [description]` → Architecture phase only (no code)
- `validate [path]` → Validation phase only

## Pipeline

### Phase 1: Research (ALWAYS first)
Launch `ai-architect` agent to research:
- What already exists in the codebase (Glob/Grep)
- What patterns are established (CLAUDE.md, existing plugins)
- Web search for best practices if building MCP/SDK apps
- Return: research findings + gaps

### Phase 2: Blueprint (get approval before building)
Based on research, present to user:
```
AI FORGE BLUEPRINT
==================
Building: [type] — [name]
Purpose: [what it does]

Files to create:
  [file list with one-line purpose each]

Architecture:
  [key design decisions]

Agents/Skills/Hooks:
  [roster with models + tool access]

Data schema (if any):
  [JSONL/JSON file descriptions]

Trade-offs considered:
  [alternatives and why this approach]

Proceed? (yes / modify / cancel)
```

### Phase 3: Build
Launch `ai-builder` agent to implement all files.
Build in order: manifest → hooks → skills → agents → data → install script

### Phase 4: Validate
Launch `ai-validator` agent to check:
- All required files present
- Valid JSON/YAML frontmatter
- Hook handlers use only stdlib
- Agent tool lists match their described role
- Skills have working descriptions

## Claude Code Plugin Spec (Reference)

```
.claude-plugin/
  plugin.json         — name (required), description, version, keywords
skills/<name>/
  SKILL.md            — YAML frontmatter: name, description, argument-hint, allowed-tools
agents/<name>.md      — YAML frontmatter: name, description, model, tools, disallowedTools, maxTurns
hooks/hooks.json      — events: SessionStart, Stop, PreToolUse, PostToolUse, UserPromptSubmit, PreCompact
hooks-handlers/       — Python or bash scripts (stdlib only, no pip)
output-styles/*.md    — YAML frontmatter: name, description
data/                 — JSONL for append-only, JSON for config
bin/                  — executables added to PATH
```

## Hook Output Contracts

```json
// Warn without blocking:
{"systemMessage": "Warning text here"}

// Inject into system prompt:
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}

// Block tool use:
exit(2)  // with message to stderr
```

## Agent Frontmatter Reference

```yaml
---
name: agent-name
description: "Detailed description. Include <example> tags with user/assistant patterns."
model: opus | sonnet | haiku
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite, Agent
disallowedTools: Agent  # restrict as needed
maxTurns: 20
color: red | blue | green | yellow | cyan | purple
---
```

## Skill Frontmatter Reference

```yaml
---
name: skill-name
version: 1.0.0
description: >-
  Detailed trigger description. Claude uses this to decide when to auto-invoke.
  Include specific trigger phrases.
argument-hint: "[arg description]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
model: sonnet  # optional override
---
```
