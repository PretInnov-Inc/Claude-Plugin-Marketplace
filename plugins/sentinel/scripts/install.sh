#!/usr/bin/env bash
set -euo pipefail

# Sentinel Plugin — Install & Validation Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Sentinel Plugin Installation ==="
echo "Plugin root: $PLUGIN_ROOT"
echo ""

# Validate plugin structure
ERRORS=0

check_file() {
    if [ ! -f "$PLUGIN_ROOT/$1" ]; then
        echo "  MISSING: $1"
        ERRORS=$((ERRORS + 1))
    else
        echo "  OK: $1"
    fi
}

check_dir() {
    if [ ! -d "$PLUGIN_ROOT/$1" ]; then
        echo "  MISSING: $1/"
        ERRORS=$((ERRORS + 1))
    else
        echo "  OK: $1/"
    fi
}

echo "Checking structure..."
check_file ".claude-plugin/plugin.json"
check_dir "agents"
check_dir "commands"
check_dir "skills/sentinel"
check_dir "hooks"
check_dir "hooks-handlers"
check_dir "data"
echo ""

echo "Checking agents..."
for agent in sentinel-reviewer bug-hunter error-auditor security-scanner test-analyzer code-polisher; do
    check_file "agents/${agent}.md"
done
echo ""

echo "Checking hooks..."
check_file "hooks/hooks.json"
check_file "hooks-handlers/pre-edit-security.py"
check_file "hooks-handlers/post-edit-tracker.py"
check_file "hooks-handlers/scope_detector.py"
echo ""

echo "Checking commands..."
check_file "commands/review.md"
check_file "commands/quick-check.md"
echo ""

echo "Checking skills..."
check_file "skills/sentinel/SKILL.md"
echo ""

echo "Checking data..."
check_file "data/sentinel-config.json"
check_file "data/security-patterns.json"
echo ""

# Validate JSON files
echo "Validating JSON..."
for json_file in .claude-plugin/plugin.json data/sentinel-config.json data/security-patterns.json hooks/hooks.json; do
    if [ -f "$PLUGIN_ROOT/$json_file" ]; then
        if python3 -c "import json; json.load(open('$PLUGIN_ROOT/$json_file'))" 2>/dev/null; then
            echo "  VALID: $json_file"
        else
            echo "  INVALID JSON: $json_file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# Validate Python scripts
echo "Validating Python syntax..."
for py_file in hooks-handlers/pre-edit-security.py hooks-handlers/post-edit-tracker.py hooks-handlers/scope_detector.py; do
    if [ -f "$PLUGIN_ROOT/$py_file" ]; then
        if python3 -c "import py_compile; py_compile.compile('$PLUGIN_ROOT/$py_file', doraise=True)" 2>/dev/null; then
            echo "  VALID: $py_file"
        else
            echo "  SYNTAX ERROR: $py_file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# Make scripts executable
echo "Setting permissions..."
chmod +x "$PLUGIN_ROOT/hooks-handlers/"*.py 2>/dev/null || true
chmod +x "$PLUGIN_ROOT/scripts/install.sh" 2>/dev/null || true
echo "  Done"
echo ""

# Initialize data directory
echo "Initializing data directory..."
mkdir -p "$PLUGIN_ROOT/data"
touch "$PLUGIN_ROOT/data/edit-log.jsonl"
echo "  Created edit-log.jsonl"
echo ""

# Check Python availability
echo "Checking runtime..."
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  Python: $PYTHON_VERSION"
else
    echo "  WARNING: python3 not found. Hooks require Python 3."
    ERRORS=$((ERRORS + 1))
fi

# Check git availability (optional)
if command -v git &>/dev/null; then
    GIT_VERSION=$(git --version 2>&1)
    echo "  Git: $GIT_VERSION (git-aware mode available)"
else
    echo "  Git: not found (file-tracking mode will be used)"
fi
echo ""

# Summary
echo "=== Installation Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "Status: SUCCESS"
    echo "All components validated."
    echo ""
    echo "Usage:"
    echo "  /sentinel:review          Full 6-agent review"
    echo "  /sentinel:review quick    Fast 2-agent check"
    echo "  /sentinel:review security Security-focused review"
    echo "  /sentinel:quick-check     Alias for quick mode"
    echo ""
    echo "Hooks (always active):"
    echo "  PreToolUse  — Security pattern blocking (16 patterns)"
    echo "  PostToolUse — Edit tracking + risk classification"
else
    echo "Status: $ERRORS ERROR(S) FOUND"
    echo "Please fix the issues above and re-run install.sh"
    exit 1
fi
