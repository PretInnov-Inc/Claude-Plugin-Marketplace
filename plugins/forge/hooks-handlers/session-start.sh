#!/bin/bash
# Plugin-Forge SessionStart Hook
# Injects past build learnings, active blueprints, and forge intelligence into session context.
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="$PLUGIN_ROOT/data"

# Read session info from stdin
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
CWD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null || echo "")

# Ensure data files exist
mkdir -p "$DATA_DIR"
for f in build-log.jsonl research-cache.jsonl learnings.jsonl blueprints.jsonl component-templates.jsonl; do
    touch "$DATA_DIR/$f"
done

# Log session start
echo "{\"event\":\"session_start\",\"session_id\":\"$SESSION_ID\",\"cwd\":\"$CWD\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$DATA_DIR/build-log.jsonl"

# Build intelligence context via embedded Python
CONTEXT=$(python3 << 'PYEOF'
import json, os, sys
from pathlib import Path
from datetime import datetime

data_dir = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "data"

def read_jsonl(filename, limit=None):
    path = data_dir / filename
    if not path.exists():
        return []
    lines = path.read_text().strip().split('\n')
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if not obj.get("_init"):
                entries.append(obj)
        except:
            pass
    if limit:
        entries = entries[-limit:]
    return entries

def read_json(filename):
    path = data_dir / filename
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except:
        return {}

sections = []

# Section 1: Recent learnings from past builds
learnings = read_jsonl("learnings.jsonl", limit=15)
if learnings:
    items = []
    for l in learnings:
        cat = l.get("category", "general")
        items.append(f"  - [{cat}] {l.get('learning', '')}")
    sections.append("## Forge Learnings (from past plugin builds)\n" + "\n".join(items))

# Section 2: Recent build history
builds = [b for b in read_jsonl("build-log.jsonl", limit=20) if b.get("event") == "build_complete"]
if builds:
    items = []
    for b in builds[-5:]:
        status = "OK" if b.get("success") else "FAIL"
        items.append(f"  - [{status}] {b.get('plugin_name','?')} — {b.get('files_generated',0)} files, {b.get('components',{})}")
    sections.append("## Recent Builds\n" + "\n".join(items))

# Section 3: Cached research findings (project-relevant)
cwd = os.environ.get("CWD", "")
project = os.path.basename(cwd) if cwd else ""
research = read_jsonl("research-cache.jsonl", limit=10)
if research:
    relevant = [r for r in research if r.get("project", "") == project or r.get("relevance", "") == "universal"]
    if relevant:
        items = [f"  - {r.get('finding', '')}" for r in relevant[-5:]]
        sections.append("## Relevant Research Cache\n" + "\n".join(items))

# Section 4: Active blueprints (in-progress builds)
blueprints = read_jsonl("blueprints.jsonl", limit=5)
active = [bp for bp in blueprints if bp.get("status") == "approved" and not bp.get("generated")]
if active:
    items = [f"  - {bp.get('plugin_name','?')}: {bp.get('description','')}" for bp in active]
    sections.append("## Active Blueprints (approved, not yet generated)\n" + "\n".join(items))

# Section 5: Build stats
config = read_json("forge-config.json")
stats = config.get("build_stats", {})
if stats.get("total_builds", 0) > 0:
    success_rate = round(stats.get("successful_builds", 0) / max(stats["total_builds"], 1) * 100)
    sections.append(f"## Forge Stats\n  - Total builds: {stats['total_builds']} ({success_rate}% success rate)\n  - Files generated: {stats.get('total_files_generated', 0)}\n  - Agents: {stats.get('total_agents_generated', 0)} | Skills: {stats.get('total_skills_generated', 0)} | Hooks: {stats.get('total_hooks_generated', 0)}")

# Section 6: Component templates available
templates = read_jsonl("component-templates.jsonl", limit=50)
if templates:
    categories = set(t.get("component_type", "unknown") for t in templates)
    sections.append(f"## Available Component Templates\n  - {len(templates)} proven templates across: {', '.join(sorted(categories))}")

# Section 7: Core Forge Rules (always injected)
sections.append("""## Forge Core Rules
  1. ALWAYS research before building — never generate a plugin without checking what exists
  2. ALWAYS ask clarifying questions — understand the user's specific needs, not assumptions
  3. ALWAYS generate a blueprint first — get user approval before writing files
  4. Use JSONL for append-only data, JSON for configuration
  5. Hook handlers must use only Python stdlib (no pip dependencies in hooks)
  6. Every agent must have explicit tool restrictions matching its role
  7. Skills must have clear descriptions so Claude knows when to auto-invoke
  8. All paths in hooks/skills/agents must use ${CLAUDE_PLUGIN_ROOT}
  9. Generated plugins must include an install.sh with structure validation
  10. Log every build outcome for the learning loop""")

# Section 8: Plugin spec quick reference
sections.append("""## Plugin Spec Quick Reference
  - Manifest: .claude-plugin/plugin.json (name is the only required field)
  - Skills: skills/<name>/SKILL.md with YAML frontmatter (description, name, allowed-tools, context, model, argument-hint, disable-model-invocation)
  - Agents: agents/<name>.md with YAML frontmatter (name, description, model, tools, disallowedTools, maxTurns, effort, isolation, memory, background, color)
  - Hooks: hooks/hooks.json → hooks-handlers/ scripts. Events: SessionStart, Stop, PreToolUse, PostToolUse, UserPromptSubmit, PreCompact, + 20 more
  - Hook output: {"systemMessage":"..."} for warnings, {"hookSpecificOutput":{"hookEventName":"...","additionalContext":"..."}} for context injection
  - Data: data/ directory with JSONL + JSON files
  - Bin: bin/ executables added to Bash tool PATH
  - Settings: settings.json with {"agent":"<name>"} to set default agent
  - Output styles: output-styles/<name>.md with YAML frontmatter
  - MCP: .mcp.json at plugin root
  - LSP: .lsp.json at plugin root
  - Env vars: ${CLAUDE_PLUGIN_ROOT} (install dir), ${CLAUDE_PLUGIN_DATA} (persistent dir)""")

output = "\n\n".join(sections)
print(output)
PYEOF
)

# Output the hook response
python3 -c "
import json, sys
context = sys.argv[1]
result = {
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context
    }
}
print(json.dumps(result))
" "$CONTEXT"
