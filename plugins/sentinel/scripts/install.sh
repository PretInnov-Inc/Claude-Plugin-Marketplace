#!/usr/bin/env bash
# Sentinel Plugin v2.1 — Install & Full Validation Script
# Validates all 52 components: 21 agents, 9 skills, 6 hook handlers,
# 3 output styles, 2 commands, 6 data files, 3 config files, 1 manifest.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
ERRORS=0

echo "═══════════════════════════════════════════════════"
echo "  Sentinel v2.1 — Plugin Installation & Validation"
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

# ─── Agents (21) ─────────────────────────────────────────────────────────────
echo "▸ Agents (21)"
for agent in \
    sentinel-reviewer bug-hunter error-auditor security-scanner test-analyzer code-polisher \
    ai-architect ai-builder ai-validator \
    style-conductor \
    web-pilot a11y-auditor \
    memory-warden session-scribe \
    ui-architect style-writer \
    doc-writer content-strategist \
    pipeline-builder data-profiler \
    workspace-curator; do
    check_file "agents/${agent}.md"
done
echo ""

# ─── Skills (9) ──────────────────────────────────────────────────────────────
echo "▸ Skills (9)"
for skill in sentinel ai-forge style-engine browser-pilot flow-memory design-craft doc-engine infra-ops dx-meta; do
    check_file "skills/${skill}/SKILL.md"
done
echo ""

# ─── Commands (2) ────────────────────────────────────────────────────────────
echo "▸ Commands"
check_file "commands/review.md"
check_file "commands/quick-check.md"
echo ""

# ─── Hook Handlers (6) ───────────────────────────────────────────────────────
echo "▸ Hook Handlers"
check_file "hooks-handlers/pre-edit-security.py"
check_file "hooks-handlers/post-edit-tracker.py"
check_file "hooks-handlers/session-learn.py"
check_file "hooks-handlers/session-memory.sh"
check_file "hooks-handlers/output-mode.sh"
check_file "hooks-handlers/post-compact-inject.py"
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
echo ""

# ─── bin/ CLI Tools ──────────────────────────────────────────────────────────
echo "▸ CLI Tools (bin/)"
check_file "bin/sentinel-status"
check_file "bin/sentinel-report"
check_file "bin/sentinel-reset"
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
    "hooks-handlers/scope_detector.py"; do
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
    echo "  Status: SUCCESS — all components validated"
    echo ""
    echo "  9 Categories:"
    echo "    A. Code Review    /sentinel:review [full|quick|security|quality|tests]"
    echo "    B. AI Dev Toolkit /sentinel:ai-forge [build|research|blueprint|validate]"
    echo "    C. Output Styles  /sentinel:style-engine [focused|learning|verbose]"
    echo "    D. Browser & A11y /sentinel:browser-pilot [--flow|--a11y|--screenshot]"
    echo "    E. Flow Memory    /sentinel:flow-memory [dashboard|add|decisions|clean]"
    echo "    F. Frontend Design/sentinel:design-craft [component|system|audit]"
    echo "    G. Documentation  /sentinel:doc-engine [readme|api|guide|seo]"
    echo "    H. Infrastructure /sentinel:infra-ops [dag|dbt|query|lineage|profile]"
    echo "    I. DX & Meta      /sentinel:dx-meta [claude-md|hooks|setup|analyze]"
    echo ""
    echo "  CLI Tools (available in Bash):"
    echo "    sentinel-status   Print health score and recent learnings"
    echo "    sentinel-report   Formatted session history markdown"
    echo "    sentinel-reset    Archive and clear data files"
    echo ""
    echo "  Always-active Hooks:"
    echo "    PreToolUse    Security pattern blocking (16 patterns)"
    echo "    PostToolUse   Edit tracking + risk classification + churn detection"
    echo "    SessionStart  Memory context + output style injection"
    echo "    PreCompact    Learning extraction before transcript compaction"
    echo "    PostCompact   Memory re-injection after compaction"
    echo "    Stop          Full session learning extraction"
    echo ""
    echo "  Quick check: /sentinel:quick-check"
else
    echo "  Status: $ERRORS ERROR(S) FOUND"
    echo "  Fix the issues above and re-run: bash scripts/install.sh"
    exit 1
fi
echo "═══════════════════════════════════════════════════"
