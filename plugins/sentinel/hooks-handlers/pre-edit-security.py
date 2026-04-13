#!/usr/bin/env python3
"""Sentinel PreToolUse Hook — Security + Layer 2 Hard Gates (v3)

Fires BEFORE Edit/Write/MultiEdit/Bash. Two layers of enforcement:

Layer 1 — Security Pattern Blocker:
  Matches file paths and content against security-patterns.json.
  Blocks the edit with exit code 2 on critical/high matches.

Layer 2 — Operational Hard Gates (configurable via sentinel-config.json):
  - destructive_commands: Block rm -rf, git push --force, DROP TABLE, etc.
  - tdd_enforcement: Block src/ writes when no test file exists for module.
  - blueprint_gate: Block ai-builder writes without .sentinel/blueprints/<slug>.approved

Session-scoped dedup (warn once per file+rule per session).
Pure stdlib — no pip dependencies.
"""

import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__)))


def get_data_dir():
    return os.path.join(get_plugin_root(), "data")


def load_patterns():
    """Load security patterns from external JSON file."""
    patterns_file = os.path.join(get_data_dir(), "security-patterns.json")
    if os.path.exists(patterns_file):
        try:
            with open(patterns_file, "r") as f:
                data = json.load(f)
                return data.get("patterns", [])
        except (json.JSONDecodeError, IOError):
            pass
    return []


def load_activation_config():
    """Load activation.hard_hooks config from sentinel-config.json."""
    config_path = os.path.join(get_data_dir(), "sentinel-config.json")
    defaults = {
        "security_patterns": "block",
        "destructive_commands": "block",
        "tdd_enforcement": "off",
        "blueprint_gate": "warn"
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
            hard_hooks = cfg.get("activation", {}).get("hard_hooks", {})
            defaults.update(hard_hooks)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def get_state_file(session_id):
    """Session-specific state file to track which warnings have been shown."""
    state_dir = os.path.expanduser("~/.claude")
    return os.path.join(state_dir, f"sentinel_security_state_{session_id}.json")


def cleanup_old_state_files():
    """Remove state files older than 7 days."""
    try:
        state_dir = os.path.expanduser("~/.claude")
        if not os.path.exists(state_dir):
            return
        cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        for fname in os.listdir(state_dir):
            if fname.startswith("sentinel_security_state_") and fname.endswith(".json"):
                fpath = os.path.join(state_dir, fname)
                try:
                    if os.path.getmtime(fpath) < cutoff:
                        os.remove(fpath)
                except OSError:
                    pass
    except Exception:
        pass


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_state(session_id, shown_warnings):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown_warnings), f)
    except IOError:
        pass


def extract_content(tool_name, tool_input):
    """Extract content to scan from tool input."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(edit.get("new_string", "") for edit in edits)
    elif tool_name == "Bash":
        return tool_input.get("command", "")
    return ""


def check_patterns(file_path, content, patterns):
    """Layer 1: Check file path and content against security patterns. Returns first match."""
    path_lower = file_path.lower()

    for pattern in patterns:
        if not pattern.get("enabled", True):
            continue

        # Path-based patterns
        path_patterns = pattern.get("path_patterns", [])
        for pp in path_patterns:
            if pp in path_lower:
                return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")

        # Content substring patterns
        substrings = pattern.get("substrings", [])
        if content:
            for sub in substrings:
                if sub in content:
                    return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")

        # Content regex patterns
        regex_patterns = pattern.get("regex", [])
        if content and regex_patterns:
            for rx in regex_patterns:
                try:
                    if re.search(rx, content):
                        return pattern["id"], pattern.get("severity", "high"), pattern.get("reminder", "")
                except re.error:
                    continue

    return None, None, None


# ─── Layer 2: Operational Hard Gates ─────────────────────────────────────────

# Destructive command signatures: (display_name, regex_pattern)
DESTRUCTIVE_PATTERNS = [
    ("rm -rf",          r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+--recursive\s+--force\b'),
    ("git push --force",r'\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b'),
    ("git reset --hard",r'\bgit\s+reset\s+--hard\b'),
    ("DROP TABLE",      r'\bDROP\s+TABLE\b'),
    ("DROP DATABASE",   r'\bDROP\s+DATABASE\b'),
    ("git clean -f",    r'\bgit\s+clean\s+.*-f\b'),
    ("chmod 777",       r'\bchmod\s+777\b'),
    ("truncate table",  r'\bTRUNCATE\s+TABLE\b'),
]


def check_destructive_commands(tool_name, tool_input, mode):
    """
    Layer 2a: Block destructive Bash commands.
    mode: 'block' (exit 2) | 'warn' | 'off'
    Returns (matched_name, guidance) or (None, None).
    """
    if mode == "off":
        return None, None
    if tool_name != "Bash":
        return None, None

    command = tool_input.get("command", "")
    if not command:
        return None, None

    for name, pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            guidance = (
                f"Destructive command detected: `{name}`\n"
                f"Command: {command[:200]}\n"
                f"If intentional, confirm with user before proceeding. "
                f"For git operations, prefer safer alternatives (--force-with-lease instead of --force)."
            )
            return name, guidance

    return None, None


def check_tdd_gate(file_path, tool_name, mode):
    """
    Layer 2b: Require test files alongside src/ module writes.
    mode: 'block' | 'warn' | 'off'
    Returns (True_if_violation, guidance) or (False, None).
    """
    if mode == "off":
        return False, None
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return False, None
    if not file_path:
        return False, None

    fp = Path(file_path)
    fp_str = str(fp)

    # Only enforce on src/ paths (not tests, not config)
    src_indicators = ["/src/", "\\src\\", "/lib/", "\\lib\\", "/app/", "\\app\\"]
    if not any(ind in fp_str for ind in src_indicators):
        return False, None

    # Skip if already a test file
    name_lower = fp.stem.lower()
    if any(x in name_lower for x in ["test", "spec", "__test__", "_test"]):
        return False, None

    # Look for sibling test file
    test_dirs = ["tests", "test", "__tests__", "spec"]
    test_suffixes = [".test", ".spec", "_test", "_spec"]

    # Check same directory
    parent = fp.parent
    for suffix in test_suffixes:
        test_candidate = parent / f"{fp.stem}{suffix}{fp.suffix}"
        if test_candidate.exists():
            return False, None

    # Check common test directory siblings
    for test_dir in test_dirs:
        # e.g., src/foo.py → tests/test_foo.py
        test_root = parent.parent / test_dir
        if test_root.exists():
            for suffix in test_suffixes:
                test_candidate = test_root / f"{fp.stem}{suffix}{fp.suffix}"
                alt_candidate = test_root / f"test_{fp.stem}{fp.suffix}"
                if test_candidate.exists() or alt_candidate.exists():
                    return False, None

    guidance = (
        f"TDD gate: No test file found for `{fp.name}`\n"
        f"Expected a test sibling (e.g., `{fp.stem}.test{fp.suffix}` or `test_{fp.stem}{fp.suffix}`).\n"
        f"Write the test first, then implement. "
        f"Override: set tdd_enforcement to 'warn' in sentinel-config.json."
    )
    return True, guidance


def check_blueprint_gate(file_path, tool_name, mode):
    """
    Layer 2c: Block ai-builder writes without an approved blueprint.
    Approved blueprints live at .sentinel/blueprints/<slug>.approved
    mode: 'block' | 'warn' | 'off'
    Returns (True_if_violation, guidance) or (False, None).
    """
    if mode == "off":
        return False, None
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return False, None

    # Only enforce when writing into a plugin/agent directory (heuristic)
    # ai-builder typically creates files under agents/, skills/, hooks-handlers/, bin/
    blueprint_targets = ["/agents/", "/skills/", "/hooks-handlers/", "/hooks/", "/bin/", "/commands/"]
    fp_str = str(file_path)
    if not any(t in fp_str for t in blueprint_targets):
        return False, None

    # Look for any approved blueprint in .sentinel/blueprints/
    blueprints_dir = Path(".sentinel/blueprints")
    if blueprints_dir.exists():
        approved = list(blueprints_dir.glob("*.approved"))
        if approved:
            return False, None  # At least one blueprint approved

    guidance = (
        f"Blueprint gate: Writing to `{file_path}` without an approved blueprint.\n"
        f"Expected: `.sentinel/blueprints/<feature-slug>.approved` must exist.\n"
        f"Run `/ai-forge` to create and approve a blueprint first. "
        f"Override: set blueprint_gate to 'off' in sentinel-config.json."
    )
    return True, guidance


def emit_block(message):
    """Print blocking message and exit 2."""
    print(f"SENTINEL [BLOCKED] {message}", file=sys.stderr)
    sys.exit(2)


def emit_warn(message):
    """Print warning message (non-blocking)."""
    output = {
        "systemMessage": f"SENTINEL [WARN] {message}"
    }
    print(json.dumps(output))


def main():
    # Periodically clean up (5% chance)
    if random.random() < 0.05:
        cleanup_old_state_files()

    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "default")

    valid_tools = ("Edit", "Write", "MultiEdit", "Bash")
    if tool_name not in valid_tools:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    content = extract_content(tool_name, tool_input)

    activation = load_activation_config()

    # ── Layer 2a: Destructive command gate ────────────────────────────────────
    destr_mode = activation.get("destructive_commands", "block")
    if destr_mode != "off":
        matched_name, guidance = check_destructive_commands(tool_name, tool_input, destr_mode)
        if matched_name:
            if destr_mode == "block":
                emit_block(guidance)
            else:
                emit_warn(guidance)

    # ── Layer 2b: TDD enforcement gate ───────────────────────────────────────
    tdd_mode = activation.get("tdd_enforcement", "off")
    if tdd_mode != "off" and file_path:
        violated, guidance = check_tdd_gate(file_path, tool_name, tdd_mode)
        if violated:
            if tdd_mode == "block":
                emit_block(guidance)
            else:
                emit_warn(guidance)

    # ── Layer 2c: Blueprint gate ──────────────────────────────────────────────
    bp_mode = activation.get("blueprint_gate", "warn")
    if bp_mode != "off" and file_path:
        violated, guidance = check_blueprint_gate(file_path, tool_name, bp_mode)
        if violated:
            if bp_mode == "block":
                emit_block(guidance)
            else:
                emit_warn(guidance)

    # ── Layer 1: Security pattern check ──────────────────────────────────────
    if tool_name in ("Edit", "Write", "MultiEdit") and file_path:
        sec_mode = activation.get("security_patterns", "block")
        if sec_mode != "off":
            patterns = load_patterns()
            rule_id, severity, reminder = check_patterns(file_path, content, patterns)

            if rule_id and reminder:
                warning_key = f"{file_path}::{rule_id}"
                shown = load_state(session_id)

                if warning_key not in shown:
                    shown.add(warning_key)
                    save_state(session_id, shown)

                    severity_label = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM"}.get(
                        severity, "WARNING"
                    )
                    message = f"SENTINEL [{severity_label}] {reminder}"
                    print(message, file=sys.stderr)

                    if severity in ("critical", "high") and sec_mode == "block":
                        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
