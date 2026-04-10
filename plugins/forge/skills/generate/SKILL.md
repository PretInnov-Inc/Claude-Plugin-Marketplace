---
name: generate
description: >-
  Generation phase for plugin creation. Writes all plugin files based on an
  approved blueprint. Creates manifest, hooks, handlers, agents, skills, data
  schemas, bin tools, and install script. Use after blueprint approval.
version: 1.0.0
argument-hint: "[plugin-name]"
---

# Forge Generation Phase

You are the code generation engine of the Plugin Forge pipeline. Write all plugin files based on the approved blueprint.

## Prerequisites

1. Read the approved blueprint from `${CLAUDE_PLUGIN_ROOT}/data/blueprints.jsonl` — find the most recent entry with `"status": "approved"` and `"generated": false`
2. Read learnings from `${CLAUDE_PLUGIN_ROOT}/data/learnings.jsonl` — apply all relevant patterns
3. Read component templates from `${CLAUDE_PLUGIN_ROOT}/data/component-templates.jsonl` — use proven patterns

If no approved blueprint exists, inform the user and suggest running `/forge` or `/forge:blueprint` first.

## Generation Order

Generate files in this specific order to ensure dependencies are satisfied:

### Step 1: Foundation
Create the plugin directory in the current working directory:

```
mkdir -p <plugin-name>/{.claude-plugin,hooks,hooks-handlers,skills,agents,data,scripts}
```

Then generate:
1. `.claude-plugin/plugin.json` — The manifest
2. `data/<plugin-name>-config.json` — The configuration file

### Step 2: Hook System
1. `hooks/hooks.json` — Event routing configuration
2. Each `hooks-handlers/<handler>.py` or `.sh` file

### Step 3: Agents
Each `agents/<name>.md` file with proper frontmatter

### Step 4: Skills
Each `skills/<name>/SKILL.md` with proper frontmatter. Create the skill subdirectory first.

### Step 5: Integration (if applicable)
- `.mcp.json` — MCP server configuration
- `settings.json` — Default agent setting
- `output-styles/<name>.md` — Response formatting
- `bin/<tool>` — CLI executables

### Step 6: Install Script
`scripts/install.sh` — Structure validation and setup

## Generation Templates

### plugin.json Template
```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<from blueprint>",
  "author": { "name": "<user>", "url": "<url>" },
  "keywords": ["<from blueprint>"],
  "license": "MIT",
  "skills": ["./skills"],
  "hooks": "./hooks/hooks.json"
}
```
Add `"outputStyles"`, `"userConfig"` only if the blueprint specifies them.

### hooks.json Template
```json
{
  "description": "<plugin description> lifecycle hooks.",
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<regex if needed>",
        "hooks": [
          {
            "type": "command",
            "command": "<python3|bash> ${CLAUDE_PLUGIN_ROOT}/hooks-handlers/<handler>",
            "timeout": <seconds>
          }
        ]
      }
    ]
  }
}
```

### Hook Handler Template (Python)
```python
#!/usr/bin/env python3
"""<Plugin> <Event> Hook: <purpose>."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
data_dir = plugin_root / "data"

def append_jsonl(filename, entry):
    path = data_dir / filename
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    try:
        hook_input = json.load(sys.stdin)
    except:
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    # ... handler logic ...

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Hook Handler Template (Bash — for SessionStart)
```bash
#!/bin/bash
set -euo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="$PLUGIN_ROOT/data"

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo "unknown")

# Ensure data files exist
mkdir -p "$DATA_DIR"
# ... touch files ...

# Build context via embedded Python
CONTEXT=$(python3 << 'PYEOF'
# ... read data files, build context sections ...
PYEOF
)

python3 -c "
import json, sys
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))
" "$CONTEXT"
```

### Agent Template
```markdown
---
name: <plugin>-<role>
description: <when Claude should invoke this agent — be specific>
model: <haiku|sonnet|opus>
tools: <Read, Grep, Glob, Bash> or <Read, Write, Edit, Grep, Glob, Bash>
color: <blue|magenta|red|cyan|yellow|green>
---

<System prompt: role, expertise, constraints, output format>
```

### Skill Template (Deep)
```markdown
---
name: <skill-name>
description: >-
  <multi-line description of what the skill does and when Claude should use it>
version: 1.0.0
argument-hint: "[options]"
---

# <Skill Title>

<Full instructions for how to execute this skill>

## Data References
- Config: `${CLAUDE_PLUGIN_ROOT}/data/<config>.json`
- Log: `${CLAUDE_PLUGIN_ROOT}/data/<log>.jsonl`
```

### Skill Template (Thin Wrapper)
```markdown
---
description: <one-line purpose>
argument-hint: [options]
---

# <Command>

Parse `$ARGUMENTS` and route:
- No args: <default behavior>
- `<subcommand>`: <behavior>
- `<flag>`: <behavior>

Data path: `${CLAUDE_PLUGIN_ROOT}/data/`
```

### Install Script Template
```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
PLUGIN_NAME="<name>"

echo "═══════════════════════════════════════════"
echo "  $PLUGIN_NAME Plugin Installer"
echo "═══════════════════════════════════════════"

# Step 1: Validate structure
required_files=( <list of all files> )
missing=0
for f in "${required_files[@]}"; do
    [ ! -f "$PLUGIN_DIR/$f" ] && echo "  MISSING: $f" && missing=$((missing + 1))
done
[ $missing -gt 0 ] && echo "  ERROR: $missing files missing." && exit 1

# Step 2: Initialize data + permissions
for f in <jsonl files>; do touch "$PLUGIN_DIR/data/$f"; done
chmod +x "$PLUGIN_DIR/hooks-handlers/"*.py "$PLUGIN_DIR/hooks-handlers/"*.sh 2>/dev/null || true
[ -d "$PLUGIN_DIR/bin" ] && chmod +x "$PLUGIN_DIR/bin/"* 2>/dev/null || true

# Step 3: Validate Python
for f in "$PLUGIN_DIR/hooks-handlers/"*.py; do
    python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null || echo "  SYNTAX ERROR: $f"
done

# Summary
echo "  $PLUGIN_NAME installed successfully!"
echo "  Test with: claude --plugin-dir $PLUGIN_DIR"
```

## Quality Checks During Generation

For every file you write, verify:
1. **No hardcoded paths** — all paths use `${CLAUDE_PLUGIN_ROOT}`
2. **Proper frontmatter** — all .md files start with `---` block
3. **Consistent naming** — agents: `<plugin>-<role>.md`, skills: `<name>/SKILL.md`
4. **Tool restrictions match role** — read-only agents don't have Write/Edit
5. **Hook handlers use stdlib only** — no pip imports
6. **JSONL schemas have timestamps** — every entry needs a timestamp field
7. **Data files have trim logic** — hooks should auto-trim when files exceed limits

## Post-Generation

1. Update the blueprint status in `${CLAUDE_PLUGIN_ROOT}/data/blueprints.jsonl` to `"generated": true`
2. Log the build to `${CLAUDE_PLUGIN_ROOT}/data/build-log.jsonl`
3. Run `/forge:validate <plugin-name>` if auto_validate is enabled
4. Present the summary:

```
═══════════════════════════════════════════
  FORGED: <plugin-name> v1.0.0
  <N> files | <A> agents | <S> skills | <H> hooks
═══════════════════════════════════════════

  Quick start:
    claude --plugin-dir ./<plugin-name>
    bash <plugin-name>/scripts/install.sh

  Available commands:
    /<plugin-name>:<skill-1>  — <description>
    /<plugin-name>:<skill-2>  — <description>
    ...
═══════════════════════════════════════════
```
