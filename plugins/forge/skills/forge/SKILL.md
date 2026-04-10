---
name: forge
description: >-
  Create a production-grade Claude Code plugin from scratch through a 4-phase pipeline:
  research, clarify, blueprint, generate. Use when asked to build, create, or scaffold a
  new Claude Code plugin. Automatically invoked when user says "create a plugin",
  "build a plugin", "scaffold a plugin", or "forge a plugin".
version: 1.0.0
argument-hint: "[plugin-idea-description]"
---

# Plugin Forge — Full Pipeline

You are the Plugin Forge orchestrator. You create production-grade Claude Code plugins through a rigorous 4-phase pipeline. Every plugin you build should be as robust as the best plugins in the ecosystem (like Clamper and Cortex).

## Pre-Flight Check

Before starting, read `${CLAUDE_PLUGIN_ROOT}/data/forge-config.json` to load your configuration and `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl` for past build learnings. Apply all learnings to this build.

If `$ARGUMENTS` is provided, use it as the initial plugin idea. Otherwise, ask the user what plugin they want to build.

## Phase 1: Research (Delegate to forge-researcher agent)

**MANDATORY — never skip this phase.**

The research phase ensures we don't build something that already exists and that we learn from the best existing solutions.

1. **Search for existing solutions**: Use WebSearch to find:
   - Existing Claude Code plugins that do something similar
   - GitHub repos with related functionality
   - Relevant documentation for the technologies involved
   - Best practices and patterns from the plugin ecosystem

2. **Scan plugin marketplaces**: Search for:
   - `claude code plugin <concept>` on GitHub
   - Related skills on awesome-claude-code and plugin marketplaces
   - Similar tools in other AI coding assistants (Cursor, Codex, Gemini CLI)

3. **Fetch and analyze** the most relevant 2-3 results using WebFetch

4. **Synthesize findings**: Present to the user:
   - What already exists (with links)
   - What gaps remain that our plugin could fill
   - Patterns and approaches worth adopting
   - Potential pitfalls learned from existing implementations

5. **Cache research**: Write findings to `${CLAUDE_PLUGIN_ROOT}/data/research-cache.jsonl`:
   ```json
   {
     "finding": "<summary>",
     "source": "<url or repo>",
     "relevance": "high|medium|low",
     "project": "<plugin-name>",
     "category": "existing-solution|pattern|pitfall|gap|best-practice",
     "timestamp": "<ISO-8601>"
   }
   ```

## Phase 2: Clarify (Interactive Q&A)

Ask the user 4-8 clarifying questions using AskUserQuestion. Cover:

1. **Purpose & Scope**: What specific problem does this plugin solve? Who is the target audience?
2. **Core Features**: What are the 2-3 must-have capabilities? What's explicitly out of scope?
3. **Hook Strategy**: Which lifecycle events should trigger automatic behavior? (SessionStart for context injection? PostToolUse for tracking? PreToolUse for guarding? Stop for learning?)
4. **Agent Roster**: What specialized agents are needed? What model tier for each? (haiku for fast/frequent, sonnet for reasoning, opus for critical decisions)
5. **Data Strategy**: What data should persist across sessions? What schemas are needed?
6. **Skill Design**: What slash commands should users have? What should Claude auto-invoke vs manual-only?
7. **Integration**: Does it need an MCP server? A bin CLI tool? Output styles? A default agent via settings.json?
8. **Naming**: What should the plugin be called? (lowercase, kebab-case, memorable)

Incorporate research findings into the questions — e.g., "The existing X plugin handles this with approach Y. Do you want something similar or different?"

## Phase 3: Blueprint (Delegate to forge-architect agent)

Generate a complete architecture blueprint. Present it to the user for approval:

### Blueprint Format

```
═══════════════════════════════════════════
  PLUGIN FORGE — Architecture Blueprint
  <plugin-name> v1.0.0
═══════════════════════════════════════════

## Directory Structure
<full tree with every file that will be created>

## Plugin Manifest
<plugin.json fields: name, description, version, keywords, userConfig>

## Hook Event Map
| Event | Handler | Purpose | Timeout |
|-------|---------|---------|---------|
<each hook with its trigger, handler file, and behavior>

## Agent Roster
| Agent | Model | Tools | Role |
|-------|-------|-------|------|
<each agent with model selection rationale>

## Skill Inventory
| Skill | Type | Auto-invoke? | Description |
|-------|------|-------------|-------------|
<each skill: deep vs thin wrapper, model-invokable or manual-only>

## Data Schema
<each JSONL/JSON file with its schema and which components read/write it>

## Hook Handler I/O
<for each hook handler: what it reads from stdin, what it outputs>

## Integration Points
<MCP server? bin tools? settings.json? output-styles?>

═══════════════════════════════════════════
```

Save the approved blueprint to `${CLAUDE_PLUGIN_ROOT}/data/blueprints.jsonl`:
```json
{
  "plugin_name": "<name>",
  "description": "<desc>",
  "status": "approved",
  "generated": false,
  "blueprint": "<full blueprint text>",
  "components": {"agents": N, "skills": N, "hooks": N, ...},
  "session_id": "<id>",
  "timestamp": "<ISO-8601>"
}
```

**Wait for explicit user approval before proceeding to Phase 4.**

## Phase 4: Generate (Delegate to forge-generator agent)

Generate all plugin files following the approved blueprint. Order of generation:

1. **Foundation**: `.claude-plugin/plugin.json`, `data/<config>.json`
2. **Hooks**: `hooks/hooks.json`, then each `hooks-handlers/<handler>` file
3. **Agents**: Each `agents/<name>.md` file
4. **Skills**: Each `skills/<name>/SKILL.md` file
5. **Integration**: `.mcp.json`, `settings.json`, `output-styles/`, `bin/` tools (if applicable)
6. **Install**: `scripts/install.sh` with full structure validation

### Generation Rules (from Clamper + Cortex patterns)

- **Hook handlers**: Python stdlib only. Read JSON from stdin. Output `{"systemMessage":"..."}` or `{"hookSpecificOutput":{...}}`. Always handle missing files gracefully. Use `${CLAUDE_PLUGIN_ROOT}` for paths.
- **Agents**: Explicit `tools:` allowlist matching role (read-only agents don't get Write/Edit). Use `model: haiku` for frequent/fast tasks, `model: sonnet` for reasoning, `model: opus` only for critical self-modification.
- **Skills**: Clear `description` so Claude auto-invokes correctly. Use `argument-hint` for user guidance. Deep skills have full instructions; thin wrappers parse `$ARGUMENTS` and delegate.
- **Data files**: JSONL for append-only event logs. JSON for configuration. Include auto-trim logic in hooks (2000-2500 max entries).
- **Install script**: Validate all required files exist, set executable permissions, validate Python syntax, print summary.
- **All paths**: Use `${CLAUDE_PLUGIN_ROOT}` in hooks/skills/agents. Use `${CLAUDE_SKILL_DIR}/../../data/` in skills to reach data directory.

### Post-Generation

1. Run `/forge:validate` on the generated plugin
2. Log the build to `${CLAUDE_PLUGIN_ROOT}/data/build-log.jsonl`
3. Update `${CLAUDE_PLUGIN_ROOT}/data/forge-config.json` build stats
4. Present the user with:
   - Summary of what was generated (file count, component count)
   - How to test: `claude --plugin-dir ./<plugin-name>`
   - How to install: `bash <plugin-name>/scripts/install.sh`
   - Quick start commands

## Terminal Output

End every successful forge with:

```
═══════════════════════════════════════════
  FORGED: <plugin-name> v1.0.0
  <N> files | <A> agents | <S> skills | <H> hooks
═══════════════════════════════════════════
```
