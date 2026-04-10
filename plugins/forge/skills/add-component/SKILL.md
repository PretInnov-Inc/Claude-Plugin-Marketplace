---
name: add-component
description: >-
  Add a new component (hook, agent, skill, MCP server, bin tool, or output style)
  to an existing Claude Code plugin. Use when asked to extend, enhance, or add
  functionality to a plugin that already exists.
version: 1.0.0
argument-hint: "<component-type> [plugin-path]"
---

# Forge Add Component

Add a new component to an existing Claude Code plugin.

## Usage
- `/forge:add-component hook <plugin-path>` — add a new hook + handler
- `/forge:add-component agent <plugin-path>` — add a new agent
- `/forge:add-component skill <plugin-path>` — add a new skill
- `/forge:add-component mcp <plugin-path>` — add MCP server config
- `/forge:add-component bin <plugin-path>` — add a bin tool
- `/forge:add-component output-style <plugin-path>` — add an output style

Parse `$ARGUMENTS` to extract the component type and optional plugin path (default: cwd).

## Process

1. **Read the existing plugin**: Read `plugin.json` to understand the plugin's current structure
2. **Understand context**: Read existing hooks, agents, skills to understand naming conventions and patterns
3. **Ask what's needed**: Use AskUserQuestion to understand:
   - What the new component should do
   - For hooks: which event, what behavior
   - For agents: role, model tier, tool access
   - For skills: deep vs thin, auto-invoke vs manual
4. **Research** (quick): Run 1-2 WebSearch queries for best practices specific to this component type
5. **Generate**: Write the new component file(s) following the plugin's existing conventions
6. **Update manifest**: If needed, update plugin.json (e.g., add hook file reference)
7. **Update install script**: Add the new file to the required files list in install.sh
8. **Validate**: Run a quick validation pass on the new component

## Component Templates

Reference `${CLAUDE_PLUGIN_ROOT}/data/component-templates.jsonl` for proven patterns.

Use templates from the `/forge:generate` skill for the specific component type:
- Hook handlers: Python stdlib only, stdin JSON, stdout JSON
- Agents: YAML frontmatter with name, description, model, tools, color
- Skills: YAML frontmatter with description, argument-hint, version
- MCP: .mcp.json format with server configurations
- Bin tools: Python executable with argparse, data dir resolution
- Output styles: YAML frontmatter with name, description, formatting rules
