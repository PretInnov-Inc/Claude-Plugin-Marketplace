#!/usr/bin/env python3
"""
Cortex PreToolUse Hook — Intelligent Guard + Adaptive Warning System

Applies accumulated wisdom BEFORE tool execution:
1. Checks against known anti-patterns
2. Validates file operations against past mistakes
3. Warns about risky operations based on historical data
4. Checks for common failure patterns learned from 500+ sessions
5. [SELF-ADAPT] Respects suppressed warnings from cortex-config.json
6. [SELF-ADAPT] Tracks which warnings fire for effectiveness analysis
7. [SELF-ADAPT] Skips warnings disabled per-project

Exit 0 = allow, Exit 2 = block (stderr shown to Claude)
"""

import json
import sys
import os
import re
from pathlib import Path

def get_cortex_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return Path(plugin_root) / "data"

def load_anti_patterns(data_dir, limit=50):
    """Load recent anti-patterns for checking."""
    ap_file = data_dir / "anti-patterns.jsonl"
    if not ap_file.exists():
        return []
    patterns = []
    try:
        with open(ap_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        patterns.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return patterns[-limit:]

def load_learnings(data_dir, limit=30):
    """Load recent learnings for rule checking."""
    learn_file = data_dir / "learnings.jsonl"
    if not learn_file.exists():
        return []
    learnings = []
    try:
        with open(learn_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        learnings.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return learnings[-limit:]

def check_hardcoded_rules(tool_name, tool_input):
    """
    Rules extracted from 500+ sessions of real usage data:
    - Auto-commit prevention
    - Dangerous path operations
    - Known footgun patterns
    """
    warnings = []

    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Rule 1: NEVER auto-commit (from agentic project memory)
        if re.search(r"\bgit\s+(commit|push|merge)\b", command) and not tool_input.get("user_approved"):
            warnings.append("Cortex: git commit/push detected. Historical rule: NEVER auto-commit unless user explicitly asks.")

        # Rule 2: Dangerous destructive operations
        if re.search(r"\b(rm\s+-rf|git\s+reset\s+--hard|git\s+push\s+--force|git\s+checkout\s+\.)\b", command):
            warnings.append("Cortex: Destructive operation detected. Verify this is intentional before proceeding.")

        # Rule 3: Moving project directories (fragments context)
        if re.search(r"\b(mv|cp\s+-r)\s+.*(/Volumes/|/Users/)", command):
            warnings.append("Cortex: Moving/copying project directories fragments Claude Code context. Each path creates a separate memory silo.")

        # Rule 4: Pip install without venv (common mistake)
        if re.search(r"\bpip\s+install\b", command) and "venv" not in command and "virtualenv" not in command:
            # Not a warning, just a note
            pass

    elif tool_name in ("Edit", "Write", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "") or tool_input.get("new_string", "")

        # Rule 5: Writing secrets/credentials
        if re.search(r"(api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*['\"][^'\"]{10,}", content, re.IGNORECASE):
            warnings.append("Cortex: Potential secret/credential detected in content. Avoid hardcoding secrets.")

        # Rule 6: Overwriting CLAUDE.md without reading first
        if file_path.endswith("CLAUDE.md") and tool_name == "Write":
            warnings.append("Cortex: Writing to CLAUDE.md — ensure you've read the existing content first to avoid losing instructions.")

        # Rule 7: Modifying settings.json backup
        if "settings.json.backup" in file_path:
            warnings.append("Cortex: Modifying a settings backup file. These should be read-only recovery files.")

    return warnings

def check_against_anti_patterns(tool_name, tool_input, anti_patterns):
    """Check current operation against historically recorded failures."""
    warnings = []
    command = tool_input.get("command", "") if tool_name == "Bash" else ""
    file_path = tool_input.get("file_path", "")

    for ap in anti_patterns:
        what = ap.get("what", "").lower()
        # Simple keyword matching against the operation
        if command and len(what) > 20:
            # Check if the error pattern from a past session matches current command
            keywords = set(re.findall(r'\b\w{4,}\b', what))
            cmd_keywords = set(re.findall(r'\b\w{4,}\b', command.lower()))
            overlap = keywords & cmd_keywords
            if len(overlap) >= 3:
                warnings.append(f"Cortex: Similar operation failed before — {ap.get('what', '')[:100]}")
                break  # One warning is enough

    return warnings

def load_config(data_dir):
    """Load cortex-config.json for suppression rules."""
    config_file = data_dir / "cortex-config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except:
            pass
    return {"suppressed_warnings": [], "project_overrides": {}}


def is_warning_suppressed(config, category, project):
    """Check if a warning is suppressed globally or per-project."""
    for suppression in config.get("suppressed_warnings", []):
        if suppression.get("category") == category:
            scope = suppression.get("scope", "global")
            if scope == "global" or scope == f"project:{project}":
                return True
    # Check project overrides
    overrides = config.get("project_overrides", {}).get(project, {})
    if category in overrides.get("suppressed_rules", []):
        return True
    return False


def append_jsonl(filepath, data):
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except:
        pass


def track_warning(data_dir, category, tool_name, project, now):
    """Track that a warning fired for effectiveness analysis."""
    record = {
        "event": "warning_fired",
        "category": category,
        "tool": tool_name,
        "project": project,
        "timestamp": now,
    }
    append_jsonl(data_dir / "user-feedback.jsonl", record)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    cwd = hook_input.get("cwd", "")
    project = os.path.basename(cwd) if cwd else "unknown"

    data_dir = get_cortex_data_dir()
    config = load_config(data_dir)
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

    # Collect all warnings
    all_warnings = []

    # 1. Check hardcoded rules (from historical analysis) — respecting suppressions
    raw_warnings = check_hardcoded_rules(tool_name, tool_input)
    for w in raw_warnings:
        # Derive category from warning text
        category = "general"
        if "git commit" in w.lower() or "git push" in w.lower():
            category = "git-safety"
        elif "destructive" in w.lower():
            category = "destructive-ops"
        elif "moving" in w.lower() or "copying" in w.lower():
            category = "workspace-management"
        elif "secret" in w.lower() or "credential" in w.lower():
            category = "secret-detection"
        elif "CLAUDE.md" in w:
            category = "claude-md-safety"
        elif "backup" in w.lower():
            category = "backup-safety"

        if not is_warning_suppressed(config, category, project):
            all_warnings.append(w)
            track_warning(data_dir, category, tool_name, project, now)

    # 2. Check against learned anti-patterns (skip disabled ones)
    anti_patterns = load_anti_patterns(data_dir)
    # Filter out disabled anti-patterns
    active_anti_patterns = [ap for ap in anti_patterns if not ap.get("disabled")]
    ap_warnings = check_against_anti_patterns(tool_name, tool_input, active_anti_patterns)
    for w in ap_warnings:
        if not is_warning_suppressed(config, "anti-pattern-match", project):
            all_warnings.append(w)
            track_warning(data_dir, "anti-pattern-match", tool_name, project, now)

    # If we have warnings, output them but DON'T block (exit 0 with systemMessage)
    if all_warnings:
        output = {
            "systemMessage": "\n".join(all_warnings)
        }
        print(json.dumps(output))
        sys.exit(0)

    # No issues found
    sys.exit(0)

if __name__ == "__main__":
    main()
