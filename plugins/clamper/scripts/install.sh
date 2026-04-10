#!/bin/bash
# Clamper Plugin Installer
# Clip it, Clamp it — verification loop, deep project DNA, and one-command ecosystem init.
#
# Usage: bash scripts/install.sh [--with-mcp]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
PLUGIN_NAME="clamper"

echo "═══════════════════════════════════════════"
echo "  CLAMPER Plugin Installer"
echo "  Clip it, Clamp it."
echo "═══════════════════════════════════════════"
echo ""

# Parse arguments
INSTALL_MCP=false
for arg in "$@"; do
    case $arg in
        --with-mcp) INSTALL_MCP=true ;;
        --help|-h)
            echo "Usage: bash scripts/install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-mcp   Install the FastMCP server (requires Python 3.10+)"
            echo "  --help       Show this help"
            exit 0
            ;;
    esac
done

# ── Step 1: Validate plugin structure ──
echo "[1/4] Validating plugin structure..."

required_files=(
    ".claude-plugin/plugin.json"
    "hooks/hooks.json"
    "hooks-handlers/post-edit-verify.py"
    "hooks-handlers/post-task-capture.py"
    "hooks-handlers/session-start.sh"
    "agents/clamper-verifier.md"
    "agents/clamper-scout.md"
    "agents/clamper-learner.md"
    "agents/clamper-architect.md"
    "commands/clamp.md"
    "commands/dna.md"
    "commands/init.md"
    "commands/clamper.md"
    "skills/verification/SKILL.md"
    "skills/project-dna/SKILL.md"
    "skills/ecosystem-init/SKILL.md"
    "data/clamper-config.json"
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
    "verification-log.jsonl"
    "dna-cache.jsonl"
    "outcomes.jsonl"
)
for f in "${data_files[@]}"; do
    touch "$PLUGIN_DIR/data/$f"
done

chmod +x "$PLUGIN_DIR/hooks-handlers/session-start.sh"
chmod +x "$PLUGIN_DIR/hooks-handlers/post-edit-verify.py"
chmod +x "$PLUGIN_DIR/hooks-handlers/post-task-capture.py"
echo "  Data files ready. Hook handlers executable."

# ── Step 3: Validate Python syntax ──
echo "[3/4] Validating Python handlers..."

python_files=(
    "hooks-handlers/post-edit-verify.py"
    "hooks-handlers/post-task-capture.py"
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
    echo "  All Python handlers pass syntax check."
fi

# ── Step 4: Install MCP server (optional) ──
if [ "$INSTALL_MCP" = true ]; then
    echo "[4/4] Installing Clamper MCP server..."

    if ! command -v python3 &>/dev/null; then
        echo "  ERROR: Python 3 not found."
        exit 1
    fi

    cd "$PLUGIN_DIR/mcp-server"
    pip3 install -e . --quiet 2>/dev/null || pip3 install -e .
    cd "$PLUGIN_DIR"

    echo "  MCP server installed."
    echo ""
    echo "  Add to settings.json:"
    echo "    \"mcpServers\": {"
    echo "      \"clamper\": {"
    echo "        \"command\": \"python3\","
    echo "        \"args\": [\"-m\", \"clamper_mcp.server\"],"
    echo "        \"cwd\": \"$PLUGIN_DIR/mcp-server\""
    echo "      }"
    echo "    }"
else
    echo "[4/4] Skipping MCP server (use --with-mcp to install)."
fi

# ── Summary ──
echo ""
echo "═══════════════════════════════════════════"
echo "  CLAMPER installed successfully!"
echo "═══════════════════════════════════════════"
echo ""
echo "  What's included:"
echo "    4 Subagents  — verifier, scout, learner, architect"
echo "    4 Commands   — /init, /clamp, /dna, /clamper"
echo "    3 Skills     — ecosystem-init, verification, project-dna"
echo "    3 Hooks      — SessionStart, PostToolUse, Stop"
if [ "$INSTALL_MCP" = true ]; then
echo "    1 MCP Server — dna_analyzer, outcome_store"
fi
echo ""
echo "  Quick start:"
echo "    /init        — Initialize full ecosystem for any project"
echo "    /clamp       — Verify recent code changes"
echo "    /dna         — Extract deep project DNA"
echo "    /clamper     — View intelligence dashboard"
echo ""
echo "  Clip it, Clamp it."
