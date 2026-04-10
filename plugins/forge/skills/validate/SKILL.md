---
name: validate
description: >-
  Validate a Claude Code plugin's structure, manifest, hooks, agents, skills,
  data schemas, and paths for correctness and best practices. Use when asked to
  check, validate, or verify a plugin.
version: 1.0.0
argument-hint: "[plugin-directory-path]"
---

# Forge Validate

Validate a Claude Code plugin for correctness and completeness.

## Usage
- `/forge:validate` — validate plugin in current directory
- `/forge:validate <path>` — validate plugin at specified path

## Validation Process

Delegate to the `forge-validator` agent with the target plugin path from `$ARGUMENTS` (or cwd if no arguments).

The validator checks 9 categories:
1. **Structure** — directory layout, plugin.json location
2. **Manifest** — JSON validity, required fields, naming conventions
3. **Hooks** — event names, handler references, timeouts, script validity
4. **Agents** — frontmatter fields, tool restrictions, model selection
5. **Skills** — SKILL.md format, descriptions, naming
6. **Data** — config schema, JSONL emptiness
7. **Paths** — no hardcoded paths, proper variable usage
8. **Security** — no secrets, no eval/exec, proper quoting
9. **Install** — script existence, file coverage, permissions

## Post-Validation

Log validation results to `${CLAUDE_PLUGIN_ROOT}/data/build-log.jsonl`:
```json
{
  "event": "validation",
  "plugin_path": "<path>",
  "plugin_name": "<name>",
  "passed": true|false,
  "checks_passed": N,
  "checks_total": N,
  "critical_issues": N,
  "warnings": N,
  "session_id": "<id>",
  "timestamp": "<ISO-8601>"
}
```
