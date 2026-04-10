#!/bin/bash
# Plugin-Forge Installer
# Meta-plugin that creates production-grade Claude Code plugins.
#
# Usage: bash scripts/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
PLUGIN_NAME="plugin-forge"

echo "═══════════════════════════════════════════"
echo "  PLUGIN FORGE Installer"
echo "  Build plugins from prompts."
echo "═══════════════════════════════════════════"
echo ""

# ── Step 1: Validate plugin structure ──
echo "[1/4] Validating plugin structure..."

required_files=(
    ".claude-plugin/plugin.json"
    "hooks/hooks.json"
    "hooks-handlers/session-start.sh"
    "hooks-handlers/session-stop.py"
    "hooks-handlers/post-tool-tracker.py"
    "hooks-handlers/pre-compact-preserve.py"
    "agents/forge-researcher.md"
    "agents/forge-architect.md"
    "agents/forge-generator.md"
    "agents/forge-validator.md"
    "agents/forge-learner.md"
    "skills/forge/SKILL.md"
    "skills/research/SKILL.md"
    "skills/blueprint/SKILL.md"
    "skills/generate/SKILL.md"
    "skills/validate/SKILL.md"
    "skills/add-component/SKILL.md"
    "skills/learn/SKILL.md"
    "skills/dashboard/SKILL.md"
    "data/forge-config.json"
    "bin/forge-inspect"
)

missing=0
for f in "${required_files[@]}"; do
    if [ ! -f "$PLUGIN_DIR/$f" ]; then
        echo "  MISSING: $f"
        missing=$((missing + 1))
    fi
done

if [ $missing -gt 0 ]; then
    echo "  ERROR: $missing required files missing. Aborting."
    exit 1
fi
echo "  All ${#required_files[@]} required files present."

# ── Step 2: Initialize data files and permissions ──
echo "[2/4] Initializing data files and permissions..."

data_files=(
    "build-log.jsonl"
    "research-cache.jsonl"
    "learnings.jsonl"
    "blueprints.jsonl"
    "component-templates.jsonl"
)
for f in "${data_files[@]}"; do
    touch "$PLUGIN_DIR/data/$f"
done

chmod +x "$PLUGIN_DIR/hooks-handlers/session-start.sh"
chmod +x "$PLUGIN_DIR/hooks-handlers/session-stop.py"
chmod +x "$PLUGIN_DIR/hooks-handlers/post-tool-tracker.py"
chmod +x "$PLUGIN_DIR/hooks-handlers/pre-compact-preserve.py"
chmod +x "$PLUGIN_DIR/bin/forge-inspect"
echo "  Data files ready. Hook handlers and bin tools executable."

# ── Step 3: Validate Python syntax ──
echo "[3/4] Validating Python handlers..."

python_files=(
    "hooks-handlers/session-stop.py"
    "hooks-handlers/post-tool-tracker.py"
    "hooks-handlers/pre-compact-preserve.py"
    "bin/forge-inspect"
)

py_errors=0
for f in "${python_files[@]}"; do
    if ! python3 -c "import py_compile; py_compile.compile('$PLUGIN_DIR/$f', doraise=True)" 2>/dev/null; then
        echo "  SYNTAX ERROR: $f"
        py_errors=$((py_errors + 1))
    fi
done

if [ $py_errors -gt 0 ]; then
    echo "  WARNING: $py_errors files have syntax errors."
else
    echo "  All Python files pass syntax check."
fi

# ── Step 4: Seed component templates ──
echo "[4/4] Checking component templates..."

TEMPLATES_FILE="$PLUGIN_DIR/data/component-templates.jsonl"
if [ ! -s "$TEMPLATES_FILE" ]; then
    echo "  Seeding with proven templates from Clamper + Cortex patterns..."
    cat >> "$TEMPLATES_FILE" << 'TEMPLATES'
{"component_type":"hook-handler","name":"session-start-context-injection","description":"SessionStart hook that reads data files and injects intelligence context via hookSpecificOutput.additionalContext","template":"bash + embedded python pattern","usage_count":2,"avg_health":85,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"hook-handler","name":"post-edit-tracker","description":"PostToolUse hook (Edit|Write|MultiEdit) that tracks file changes, detects churn, and logs risk signals","template":"python stdin parser with risk classification","usage_count":2,"avg_health":80,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"hook-handler","name":"session-stop-learner","description":"Stop hook that reads transcript tail, extracts patterns via regex, calculates health score, writes to multiple data files","template":"python transcript analyzer with scoring algorithm","usage_count":2,"avg_health":82,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"hook-handler","name":"pre-tool-guard","description":"PreToolUse hook that checks tool calls against hardcoded + learned anti-patterns, outputs systemMessage warnings","template":"python rule engine with suppression support","usage_count":1,"avg_health":78,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"hook-handler","name":"prompt-intelligence","description":"UserPromptSubmit hook that detects scope creep, repetitive prompts, and user feedback signals","template":"python keyword extraction with threshold checks","usage_count":1,"avg_health":75,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"hook-handler","name":"pre-compact-preserver","description":"PreCompact hook that saves decisions, blueprint state, and warns about context loss","template":"python transcript scanner with decision extraction","usage_count":2,"avg_health":80,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"agent","name":"read-only-analyst","description":"Sonnet-tier agent with Read, Grep, Glob, Bash tools for analysis without modification","template":"frontmatter: model: sonnet, tools: Read, Grep, Glob, Bash","usage_count":6,"avg_health":82,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"agent","name":"write-capable-generator","description":"Sonnet-tier agent with full tool access for file generation","template":"frontmatter: model: sonnet, tools: Read, Write, Edit, Grep, Glob, Bash","usage_count":4,"avg_health":80,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"agent","name":"fast-validator","description":"Haiku-tier agent for quick validation passes","template":"frontmatter: model: haiku, tools: Read, Grep, Glob, Bash","usage_count":2,"avg_health":85,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"agent","name":"self-modifier","description":"Opus-tier agent with Write/Edit access to plugin files for self-evolution","template":"frontmatter: model: opus, tools: Read, Write, Edit, Grep, Glob, Bash","usage_count":1,"avg_health":78,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"skill","name":"deep-skill-template","description":"Full standalone skill with multi-section instructions, data file references, and output format","template":"YAML frontmatter (name, description, version) + 50-200 line instruction body","usage_count":9,"avg_health":82,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"skill","name":"thin-wrapper-template","description":"Minimal skill that parses $ARGUMENTS and delegates to agents or other skills","template":"YAML frontmatter (description, argument-hint) + 10-30 line routing logic","usage_count":7,"avg_health":80,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"config","name":"standard-config","description":"JSON config with version, thresholds, suppressed_warnings, project_overrides, and stats sections","template":"JSON with hierarchical sections","usage_count":2,"avg_health":82,"timestamp":"2026-04-10T00:00:00Z"}
{"component_type":"install-script","name":"standard-installer","description":"4-step installer: validate structure, init data+permissions, validate Python syntax, print summary","template":"bash with required_files array and py_compile validation","usage_count":2,"avg_health":85,"timestamp":"2026-04-10T00:00:00Z"}
TEMPLATES
    echo "  Seeded 14 component templates."
else
    TEMPLATE_COUNT=$(wc -l < "$TEMPLATES_FILE" | tr -d ' ')
    echo "  $TEMPLATE_COUNT templates already present."
fi

# ── Summary ──
echo ""
echo "═══════════════════════════════════════════"
echo "  PLUGIN FORGE installed successfully!"
echo "═══════════════════════════════════════════"
echo ""
echo "  What's included:"
echo "    5 Subagents  — researcher, architect, generator, validator, learner"
echo "    8 Skills     — forge, research, blueprint, generate, validate, add-component, learn, dashboard"
echo "    4 Hooks      — SessionStart, Stop, PostToolUse, PreCompact"
echo "    1 CLI Tool   — forge-inspect (stats, builds, validate, trim)"
echo "    14 Templates — proven patterns from Clamper + Cortex"
echo ""
echo "  Quick start:"
echo "    /forge                     — Full 4-phase plugin creation pipeline"
echo "    /forge:research <concept>  — Research a plugin idea"
echo "    /forge:blueprint <name>    — Design plugin architecture"
echo "    /forge:generate <name>     — Generate plugin from blueprint"
echo "    /forge:validate <path>     — Validate a plugin"
echo "    /forge:add-component       — Add component to existing plugin"
echo "    /forge:learn               — Mine patterns from past builds"
echo "    /forge:dashboard           — View build stats and history"
echo ""
echo "  Test with:"
echo "    claude --plugin-dir $PLUGIN_DIR"
echo ""
echo "  Forge it."
