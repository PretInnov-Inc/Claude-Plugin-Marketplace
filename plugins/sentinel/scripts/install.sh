#!/usr/bin/env bash
# Sentinel Plugin v3.0 — Install & Full Validation Script
# Validates all 68 components: 24 agents, 11 skills, 9 hook handlers,
# 3 output styles, 2 commands, 6 data files, 3 config files, 1 manifest,
# 6 CLI tools, 2 data templates, 3 new bin utilities.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
ERRORS=0

echo "═══════════════════════════════════════════════════"
echo "  Sentinel v3.0 — Plugin Installation & Validation"
echo "═══════════════════════════════════════════════════"
echo "Plugin root: $PLUGIN_ROOT"
echo ""

check_file() {
    local label="${2:-$1}"
    if [ ! -f "$PLUGIN_ROOT/$1" ]; then
        echo "  MISSING: $label"
        ERRORS=$((ERRORS + 1))
    else
        echo "  OK:      $label"
    fi
}

check_dir() {
    if [ ! -d "$PLUGIN_ROOT/$1" ]; then
        echo "  MISSING: $1/"
        ERRORS=$((ERRORS + 1))
    else
        echo "  OK:      $1/"
    fi
}

# ─── Manifest ───────────────────────────────────────────────────────────────
echo "▸ Manifest"
check_file ".claude-plugin/plugin.json"
echo ""

# ─── Directories ─────────────────────────────────────────────────────────────
echo "▸ Directories"
for dir in agents commands skills hooks hooks-handlers data output-styles scripts bin; do
    check_dir "$dir"
done
echo ""

# ─── Agents (24) ─────────────────────────────────────────────────────────────
echo "▸ Agents (24)"
for agent in \
    sentinel-reviewer bug-hunter error-auditor security-scanner test-analyzer code-polisher \
    ai-architect ai-builder ai-validator \
    style-conductor \
    web-pilot a11y-auditor \
    memory-warden session-scribe \
    ui-architect style-writer \
    doc-writer content-strategist \
    pipeline-builder data-profiler \
    workspace-curator \
    design-auditor sentinel-auditor risk-gatekeeper; do
    check_file "agents/${agent}.md"
done
echo ""

# ─── Skills (11) ─────────────────────────────────────────────────────────────
echo "▸ Skills (11)"
for skill in sentinel ai-forge style-engine browser-pilot flow-memory design-craft doc-engine infra-ops dx-meta sentinel-doctor sentinel-audit; do
    check_file "skills/${skill}/SKILL.md"
done
echo ""

# ─── Commands (2) ────────────────────────────────────────────────────────────
echo "▸ Commands"
check_file "commands/review.md"
check_file "commands/quick-check.md"
echo ""

# ─── Hook Handlers (9) ───────────────────────────────────────────────────────
echo "▸ Hook Handlers (9)"
check_file "hooks-handlers/pre-edit-security.py"
check_file "hooks-handlers/post-edit-tracker.py"
check_file "hooks-handlers/session-learn.py"
check_file "hooks-handlers/session-memory.sh"
check_file "hooks-handlers/output-mode.sh"
check_file "hooks-handlers/post-compact-inject.py"
check_file "hooks-handlers/output-compressor.py"
check_file "hooks-handlers/prompt-router.py"
check_file "hooks-handlers/lineage-manager.py"
echo ""

# ─── Utility Scripts (referenced by commands) ────────────────────────────────
echo "▸ Utilities"
check_file "hooks-handlers/scope_detector.py"
echo ""

# ─── Hooks Config ────────────────────────────────────────────────────────────
echo "▸ Hooks"
check_file "hooks/hooks.json"
echo ""

# ─── Output Styles (3) ───────────────────────────────────────────────────────
echo "▸ Output Styles"
check_file "output-styles/focused.md"
check_file "output-styles/learning.md"
check_file "output-styles/verbose.md"
echo ""

# ─── Data / Config Files ─────────────────────────────────────────────────────
echo "▸ Data & Config"
check_file "data/sentinel-config.json"
check_file "data/security-patterns.json"
check_file "data/design-system-template.md"
check_file "data/sentinel-gitignore-template"
echo ""

# ─── bin/ CLI Tools ──────────────────────────────────────────────────────────
echo "▸ CLI Tools (bin/)"
check_file "bin/sentinel-status"
check_file "bin/sentinel-report"
check_file "bin/sentinel-reset"
check_file "bin/sentinel-doctor"
check_file "bin/sentinel-refresh"
check_file "bin/sentinel-learn"
echo ""

# ─── JSON Validation ─────────────────────────────────────────────────────────
echo "▸ JSON Syntax"
for json_file in \
    ".claude-plugin/plugin.json" \
    "data/sentinel-config.json" \
    "data/security-patterns.json" \
    "hooks/hooks.json"; do
    if [ -f "$PLUGIN_ROOT/$json_file" ]; then
        if python3 -c "import json; json.load(open('$PLUGIN_ROOT/$json_file'))" 2>/dev/null; then
            echo "  VALID:   $json_file"
        else
            echo "  INVALID: $json_file  ← JSON parse error"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# ─── Python Syntax ───────────────────────────────────────────────────────────
echo "▸ Python Syntax"
for py_file in \
    "hooks-handlers/pre-edit-security.py" \
    "hooks-handlers/post-edit-tracker.py" \
    "hooks-handlers/session-learn.py" \
    "hooks-handlers/post-compact-inject.py" \
    "hooks-handlers/scope_detector.py" \
    "hooks-handlers/output-compressor.py" \
    "hooks-handlers/prompt-router.py" \
    "hooks-handlers/lineage-manager.py" \
    "bin/sentinel-doctor" \
    "bin/sentinel-refresh" \
    "bin/sentinel-learn"; do
    if [ -f "$PLUGIN_ROOT/$py_file" ]; then
        if python3 -c "import py_compile; py_compile.compile('$PLUGIN_ROOT/$py_file', doraise=True)" 2>/dev/null; then
            echo "  VALID:   $py_file"
        else
            echo "  SYNTAX ERROR: $py_file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# ─── Bash Syntax ─────────────────────────────────────────────────────────────
echo "▸ Bash Syntax"
for sh_file in \
    "hooks-handlers/session-memory.sh" \
    "hooks-handlers/output-mode.sh"; do
    if [ -f "$PLUGIN_ROOT/$sh_file" ]; then
        if bash -n "$PLUGIN_ROOT/$sh_file" 2>/dev/null; then
            echo "  VALID:   $sh_file"
        else
            echo "  SYNTAX ERROR: $sh_file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# ─── MCP Server Nesting Check ────────────────────────────────────────────────
# There is no mechanism to nest one plugin's MCP server inside another's.
# Claude Code registers MCP servers at the plugin root level only.
# If a companion plugin with its own .mcp.json is found nested inside this
# plugin directory, it will silently fail — the nested server never registers.
# This check detects that early and tells the user how to fix it.
echo "▸ MCP Server Nesting Check"
NESTED_MCP=$(find "$PLUGIN_ROOT" -mindepth 2 -name ".mcp.json" 2>/dev/null || true)
if [ -n "$NESTED_MCP" ]; then
    echo ""
    echo "  WARNING: Nested MCP server(s) detected inside this plugin:"
    while IFS= read -r mcp_path; do
        nested_plugin_dir=$(dirname "$mcp_path")
        nested_plugin_name=$(basename "$nested_plugin_dir")
        echo "    $mcp_path"
        echo ""
        echo "  PROBLEM: There is no mechanism to nest one plugin's MCP server"
        echo "           inside another's. Claude Code only registers .mcp.json"
        echo "           at the plugin root level — '$nested_plugin_name' will"
        echo "           never load its MCP server from this location."
        echo ""
        echo "  FIX: Install '$nested_plugin_name' as a sibling plugin instead:"
        echo "    mv \"$nested_plugin_dir\" \"$(dirname "$PLUGIN_ROOT")/$nested_plugin_name\""
        echo "    claude --plugin-dir \"$(dirname "$PLUGIN_ROOT")/$nested_plugin_name\""
        echo ""
    done <<< "$NESTED_MCP"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK:      no nested MCP servers found"
fi
echo ""

# ─── Runtime Checks ──────────────────────────────────────────────────────────
echo "▸ Runtime"
if command -v python3 &>/dev/null; then
    echo "  Python:  $(python3 --version 2>&1)"
else
    echo "  MISSING: python3  ← hooks require Python 3"
    ERRORS=$((ERRORS + 1))
fi
if command -v git &>/dev/null; then
    echo "  Git:     $(git --version 2>&1 | head -1) (git-aware scope detection available)"
else
    echo "  Git:     not found (file-tracking mode will be used)"
fi
echo ""

# ─── Permissions ─────────────────────────────────────────────────────────────
echo "▸ Setting Permissions"
chmod +x "$PLUGIN_ROOT/hooks-handlers/"*.py 2>/dev/null || true
chmod +x "$PLUGIN_ROOT/hooks-handlers/"*.sh 2>/dev/null || true
chmod +x "$PLUGIN_ROOT/bin/"* 2>/dev/null || true
chmod +x "$PLUGIN_ROOT/scripts/install.sh" 2>/dev/null || true
echo "  Done"
echo ""

# ─── Data Directory Init ─────────────────────────────────────────────────────
echo "▸ Initializing Data Files"
mkdir -p "$PLUGIN_ROOT/data"
for f in edit-log.jsonl learnings.jsonl decisions.jsonl anti-patterns.jsonl session-log.jsonl; do
    touch "$PLUGIN_ROOT/data/$f"
    echo "  Initialized: data/$f"
done
echo ""

# ─── Summary ─────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo "  Status: SUCCESS — all 68 components validated"
    echo ""
    echo "  11 Skills:"
    echo "    A. Code Review    /sentinel:review [full|quick|security|quality|tests]"
    echo "    B. AI Dev Toolkit /sentinel:ai-forge [build|research|blueprint|validate]"
    echo "    C. Output Styles  /sentinel:style-engine [focused|learning|verbose]"
    echo "    D. Browser & A11y /sentinel:browser-pilot [--flow|--a11y|--screenshot]"
    echo "    E. Flow Memory    /sentinel:flow-memory [dashboard|add|decisions|rollover]"
    echo "    F. Frontend Design/sentinel:design-craft [extract|audit-design|critique]"
    echo "    G. Documentation  /sentinel:doc-engine [readme|api|guide|seo]"
    echo "    H. Infrastructure /sentinel:infra-ops [dag|dbt|query|lineage|profile]"
    echo "    I. DX & Meta      /sentinel:dx-meta [claude-md|hooks|setup|analyze]"
    echo "    J. Health Diag    /sentinel:sentinel-doctor [--full|--quick|--hooks|--config]"
    echo "    K. Plugin Audit   /sentinel:sentinel-audit [skills|agents|hooks|all]"
    echo ""
    echo "  6 CLI Tools (available in Bash):"
    echo "    sentinel-status   Print health score and recent learnings"
    echo "    sentinel-report   Formatted session history markdown"
    echo "    sentinel-reset    Archive and clear data files"
    echo "    sentinel-doctor   Full plugin health diagnostic (exit 0/1/2)"
    echo "    sentinel-refresh  5-outcome maintenance for .sentinel/learnings/"
    echo "    sentinel-learn    Write typed learning entries (knowledge|bug)"
    echo ""
    echo "  7 Always-active Hooks:"
    echo "    PreToolUse        Security blocking (Layer 1: 16 patterns, Layer 2: TDD/blueprint/destructive gates)"
    echo "    PostToolUse       Edit tracking + risk classification + output compression"
    echo "    UserPromptSubmit  Zero-token routing (>review/>rollover/>doctor shortcuts)"
    echo "    SessionStart      Memory context + output style + lineage chain injection"
    echo "    PreCompact        Learning extraction before transcript compaction"
    echo "    PostCompact       Memory re-injection after compaction"
    echo "    Stop              Full session learning extraction + lineage stop event"
    echo ""
    echo "  24 Agents — 3 new in v3:"
    echo "    design-auditor    Detects UI drift against .sentinel/design-system.md"
    echo "    sentinel-auditor  120-point rubric for agents/skills/hooks quality"
    echo "    risk-gatekeeper   5-axis risk matrix with hard human gate for CRITICAL tier"
    echo ""
    echo "  Quick check: /sentinel:quick-check"
else
    echo "  Status: $ERRORS ERROR(S) FOUND"
    echo "  Fix the issues above and re-run: bash scripts/install.sh"
    exit 1
fi
echo "═══════════════════════════════════════════════════"
