#!/bin/bash
# codebase-radar install script
# Sets up the plugin venv, installs dependencies, validates all files, and initializes data.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-${HOME}/.local/share/claude-plugins/codebase-radar}"
VENV_DIR="${PLUGIN_DATA}/venv"
REQUIREMENTS="${PLUGIN_ROOT}/mcp/requirements.txt"

echo ""
echo "codebase-radar Installation"
echo "================================================="
echo "Plugin root:  ${PLUGIN_ROOT}"
echo "Plugin data:  ${PLUGIN_DATA}"
echo "Venv:         ${VENV_DIR}"
echo "================================================="
echo ""

# -------------------------------------------------------
# Step 1: Check Python 3.10+
# -------------------------------------------------------
echo "[1/6] Checking Python version..."

PYTHON_BIN=$(command -v python3 || true)
if [ -z "${PYTHON_BIN}" ]; then
    echo "ERROR: python3 not found in PATH."
    echo "Install Python 3.10+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$("${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$("${PYTHON_BIN}" -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$("${PYTHON_BIN}" -c "import sys; print(sys.version_info.minor)")

if [ "${PYTHON_MAJOR}" -lt 3 ] || { [ "${PYTHON_MAJOR}" -eq 3 ] && [ "${PYTHON_MINOR}" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ is required. Found: ${PYTHON_VERSION}"
    echo "Install Python 3.10+ from https://python.org"
    exit 1
fi

echo "    Python ${PYTHON_VERSION} found at ${PYTHON_BIN} — OK"

# -------------------------------------------------------
# Step 2: Create plugin data directories
# -------------------------------------------------------
echo ""
echo "[2/6] Creating plugin data directories..."

mkdir -p "${PLUGIN_DATA}"
mkdir -p "${PLUGIN_DATA}/lancedb"
echo "    ${PLUGIN_DATA} — OK"
echo "    ${PLUGIN_DATA}/lancedb — OK"

# -------------------------------------------------------
# Step 3: Create virtualenv and install dependencies
# -------------------------------------------------------
echo ""
echo "[3/6] Creating virtualenv and installing dependencies..."

if [ ! -d "${VENV_DIR}" ]; then
    echo "    Creating venv at ${VENV_DIR}..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
    echo "    Venv already exists at ${VENV_DIR} — skipping creation"
fi

VENV_PIP="${VENV_DIR}/bin/pip"
VENV_PYTHON="${VENV_DIR}/bin/python3"

echo "    Upgrading pip..."
"${VENV_PIP}" install --quiet --upgrade pip

echo "    Installing from ${REQUIREMENTS}..."
"${VENV_PIP}" install --quiet -r "${REQUIREMENTS}"
echo "    Dependencies installed — OK"

# -------------------------------------------------------
# Step 4: Validate all 25 plugin files
# -------------------------------------------------------
echo ""
echo "[4/6] Validating plugin file structure..."

REQUIRED_FILES=(
    ".claude-plugin/plugin.json"
    "hooks/hooks.json"
    "hooks-handlers/session-start.py"
    "hooks-handlers/post-tool-reindex.py"
    "hooks-handlers/pre-tool-suggest.py"
    "hooks-handlers/session-stop.py"
    "skills/radar/SKILL.md"
    "skills/radar-search/SKILL.md"
    "skills/radar-index/SKILL.md"
    "skills/radar-config/SKILL.md"
    "agents/radar-explorer.md"
    "agents/radar-indexer.md"
    "mcp/requirements.txt"
    "mcp/server.py"
    "mcp/embedder.py"
    "mcp/chunker.py"
    "mcp/indexer.py"
    "mcp/searcher.py"
    "mcp/state.py"
    "data/config.json"
    "data/index-state.json"
    ".mcp.json"
    "bin/radar-status"
    "bin/radar-reset"
    "scripts/install.sh"
)

MISSING_FILES=0
for rel_path in "${REQUIRED_FILES[@]}"; do
    full_path="${PLUGIN_ROOT}/${rel_path}"
    if [ -f "${full_path}" ]; then
        echo "    [OK] ${rel_path}"
    else
        echo "    [MISSING] ${rel_path}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ "${MISSING_FILES}" -gt 0 ]; then
    echo ""
    echo "ERROR: ${MISSING_FILES} required file(s) are missing."
    echo "Re-generate the plugin or check the plugin root: ${PLUGIN_ROOT}"
    exit 1
fi

echo "    All 25 files present — OK"

# -------------------------------------------------------
# Step 5: Set permissions on executables
# -------------------------------------------------------
echo ""
echo "[5/6] Setting executable permissions..."

chmod +x "${PLUGIN_ROOT}/hooks-handlers/session-start.py"
chmod +x "${PLUGIN_ROOT}/hooks-handlers/post-tool-reindex.py"
chmod +x "${PLUGIN_ROOT}/hooks-handlers/pre-tool-suggest.py"
chmod +x "${PLUGIN_ROOT}/hooks-handlers/session-stop.py"
chmod +x "${PLUGIN_ROOT}/mcp/server.py"
chmod +x "${PLUGIN_ROOT}/bin/radar-status"
chmod +x "${PLUGIN_ROOT}/bin/radar-reset"
chmod +x "${PLUGIN_ROOT}/scripts/install.sh"

echo "    Hook handlers — chmod +x OK"
echo "    MCP server — chmod +x OK"
echo "    Bin tools — chmod +x OK"

# -------------------------------------------------------
# Step 6: Initialize data files
# -------------------------------------------------------
echo ""
echo "[6a/6] Initializing config.json..."

CONFIG_DEST="${PLUGIN_DATA}/config.json"
if [ ! -f "${CONFIG_DEST}" ]; then
    cp "${PLUGIN_ROOT}/data/config.json" "${CONFIG_DEST}"
    echo "    Wrote default config.json to ${CONFIG_DEST}"
else
    echo "    config.json already exists — skipping"
fi

echo "[6b/6] Initializing index-state.json..."

STATE_DEST="${PLUGIN_DATA}/index-state.json"
if [ ! -f "${STATE_DEST}" ]; then
    cp "${PLUGIN_ROOT}/data/index-state.json" "${STATE_DEST}"
    echo "    Wrote default index-state.json to ${STATE_DEST}"
else
    echo "    index-state.json already exists — skipping"
fi

# -------------------------------------------------------
# Validate Python syntax of hook handlers
# -------------------------------------------------------
echo ""
echo "[+] Validating Python syntax of hook handlers..."

PY_FILES=(
    "hooks-handlers/session-start.py"
    "hooks-handlers/post-tool-reindex.py"
    "hooks-handlers/pre-tool-suggest.py"
    "hooks-handlers/session-stop.py"
)

SYNTAX_ERRORS=0
for rel_path in "${PY_FILES[@]}"; do
    full_path="${PLUGIN_ROOT}/${rel_path}"
    if "${PYTHON_BIN}" -m py_compile "${full_path}" 2>/dev/null; then
        echo "    [OK] ${rel_path}"
    else
        echo "    [SYNTAX ERROR] ${rel_path}"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ "${SYNTAX_ERRORS}" -gt 0 ]; then
    echo "WARNING: ${SYNTAX_ERRORS} hook handler(s) have syntax errors."
fi

# -------------------------------------------------------
# Test MCP server imports
# -------------------------------------------------------
echo ""
echo "[+] Testing MCP server imports..."

"${VENV_PYTHON}" -c "
import lancedb
import sentence_transformers
import tree_sitter
import mcp
print('All MCP imports OK')
" && echo "    lancedb, sentence_transformers, tree_sitter, mcp — OK" || {
    echo "    WARNING: Some MCP imports failed. Check the output above."
    echo "    Try: ${VENV_PIP} install -r ${REQUIREMENTS}"
}

# -------------------------------------------------------
# Completion summary
# -------------------------------------------------------
echo ""
echo "================================================="
echo "codebase-radar Installation Complete"
echo "================================================="
echo ""
echo "Components installed:"
echo "  Hooks:          4 (SessionStart, PostToolUse, PreToolUse, Stop)"
echo "  Skills:         4 (/radar, /radar:search, /radar:index, /radar:config)"
echo "  Agents:         2 (radar-explorer, radar-indexer)"
echo "  MCP modules:    6 (server, embedder, chunker, indexer, searcher, state)"
echo "  Bin tools:      2 (radar-status, radar-reset)"
echo "  Total files:   25"
echo ""
echo "Quick start:"
echo "  1. Open a Claude Code session in your project directory"
echo "  2. Run: /radar:index"
echo "     (Builds the semantic search index — takes a few minutes first time)"
echo "  3. Run: /radar:search <your query>"
echo "     (Semantic hybrid search across your codebase)"
echo "  4. Run: /radar"
echo "     (Check index status and health)"
echo ""
echo "CLI tools (can be added to PATH):"
echo "  ${PLUGIN_ROOT}/bin/radar-status   — Show index status"
echo "  ${PLUGIN_ROOT}/bin/radar-reset    — Clear index for a project"
echo ""
echo "Data stored at: ${PLUGIN_DATA}"
echo "LanceDB index:  ${PLUGIN_DATA}/lancedb/"
echo "Search logs:    ${PLUGIN_DATA}/search-log.jsonl"
echo ""
echo "Embedding model: all-MiniLM-L6-v2 (local, no API key required)"
echo "To use OpenAI or VoyageAI embeddings, run: /radar:config"
echo ""
