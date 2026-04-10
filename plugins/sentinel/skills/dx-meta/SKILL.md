---
name: dx-meta
version: 2.0.0
description: >-
  Developer experience and meta-tooling. Use when the user wants to improve their CLAUDE.md,
  set up automation hooks, analyze Claude Code usage, set up a project from scratch, create
  recurring loops, analyze codebase setup, manage permissions, or configure automation behaviors.
  Consolidates hookify, claude-code-setup, claude-md-management, security-guidance, developer-growth-analysis,
  playground plugins. Triggers on: "improve CLAUDE.md", "set up hooks", "automate when X",
  "configure my project", "claude setup", "analyze my usage", "create a hook rule",
  "prevent me from doing X", "set up permissions", "recurring task", "grow as developer".
argument-hint: "[claude-md|hooks|setup|automation|analyze|permissions|loop] [details]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
---

# Sentinel DX Meta — Developer Experience & Meta-Tooling

You configure and optimize the development environment, Claude Code setup, and project automation.

## Parse Arguments

`$ARGUMENTS` format: `[scope] [description]`

**Scopes:**
- `claude-md` / `improve` → Audit and improve CLAUDE.md files
- `hooks [description]` → Create hook rules to prevent/automate behaviors
- `setup` → Full project setup analysis and recommendations
- `automation [when X do Y]` → Convert natural language to hook configuration
- `analyze` → Analyze Claude Code usage patterns and give growth recommendations
- `permissions` → Review and optimize settings.json permissions
- `loop [interval] [command]` → Set up recurring task loop
- (empty) → Run full DX health check

## Routing

### CLAUDE.md Improvement
Launch `workspace-curator` to:
1. Read all CLAUDE.md files in the project hierarchy
2. Audit: completeness, clarity, contradictions, missing sections
3. Check against project reality (does CLAUDE.md match actual code patterns?)
4. Rewrite or append improvements with user approval

### Hook Creation
Translate natural language automation requests to hook configurations:

User: "Prevent me from committing to main"
→ Create PreToolUse hook on `Bash(git commit*)` matching `--branch main`

User: "Always run tests after editing Python files"  
→ Create PostToolUse hook on `Edit|Write` matching `*.py` running `python -m pytest`

User: "Warn me before deleting files"
→ Create PreToolUse hook on `Bash(rm*)` with warning message

Output format for hook creation:
```json
// hooks/hooks.json entry:
{
  "PreToolUse": [{
    "matcher": "Bash(git*)",
    "hooks": [{
      "type": "command",
      "command": "python3 '${CLAUDE_PLUGIN_ROOT}/hooks-handlers/[handler].py'",
      "timeout": 5
    }]
  }]
}
```
Always write both the hooks.json entry AND the handler script.

### Project Setup Analysis
Launch `workspace-curator` to:
1. Scan project structure (Glob key config files)
2. Check: CLAUDE.md exists? .gitignore complete? linting configured? CI/CD set up?
3. Detect stack (package.json, pyproject.toml, etc.)
4. Generate prioritized setup recommendations

### Usage Analysis (Developer Growth)
Read from `${CLAUDE_PLUGIN_ROOT}/data/`:
- `session-log.jsonl` → Session frequency, health trends, technologies
- `edit-log.jsonl` → Files edited most, risk patterns
- `learnings.jsonl` → Accumulated learnings by category

Generate developer growth report:
```
SENTINEL DX ANALYSIS
====================
Sessions this week: [N] | Avg health: [N]/100
Most-edited files: [list — potential hotspots]
Technologies used: [list]
Risk events: [N high-risk edits]
Top anti-patterns hit: [list]

Growth opportunities:
  1. [specific actionable advice]
  2. [specific actionable advice]
```

### Permissions Audit
Read `~/.claude/settings.json` and project `.claude/settings.json`:
1. List all `allow` permissions — are any too broad?
2. Check `defaultMode` — is it appropriate?
3. Suggest tightening over-permissive rules
4. Suggest adding missing commonly-needed permissions

## Hook Handler Template

Every hook handler must:
- Use only Python stdlib (no pip)
- Read input from `sys.stdin` as JSON
- Output to stdout: `{"systemMessage": "..."}` or `{"hookSpecificOutput": {...}}`
- Block with `sys.exit(2)` for critical issues
- Never crash silently — wrap in try/except

```python
#!/usr/bin/env python3
import json, sys, os

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)
    
    # Your logic here
    tool_name = hook_input.get("tool_name", "")
    
    # Example: warn
    print(json.dumps({"systemMessage": "Warning: ..."}))
    sys.exit(0)

if __name__ == "__main__":
    main()
```
