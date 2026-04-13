#!/usr/bin/env python3
"""
Sentinel SessionStart Hook — Lineage Manager (v3)

Fires at every session start. Manages the session lineage chain:
  - Records current session in lineage file
  - Checks context usage % (via hook_input) against graduated trigger thresholds
  - Warns at 75%, offers rollover at 85%, logs hard-fork readiness at 95%
  - In team_mode: per-user lineage files (gitignored), shared typed learnings

Lineage file location: .sentinel/lineage/<username>.json (team) or .sentinel/lineage.json (solo)

Output: systemMessage warnings for context stage thresholds.
        additionalContext injection if design-system.md exists.

Pure stdlib — no pip dependencies.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def load_config():
    config_path = Path(get_plugin_root()) / "data" / "sentinel-config.json"
    defaults = {
        "memory": {
            "lineage": {
                "enabled": True,
                "path": ".sentinel/lineage/",
                "rollover_trigger": "graduated",
                "stages": {
                    "warn_at_pct": 75,
                    "offer_at_pct": 85,
                    "hard_fork_at_pct": 95
                },
                "respect_busy_state": True,
                "team_mode": "per_user"
            }
        },
        "design_system": {
            "enabled": True,
            "path": ".sentinel/design-system.md",
            "auto_load_on_session_start": True
        }
    }
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            if "memory" in cfg and "lineage" in cfg["memory"]:
                defaults["memory"]["lineage"].update(cfg["memory"]["lineage"])
            if "design_system" in cfg:
                defaults["design_system"].update(cfg["design_system"])
        except Exception:
            pass
    return defaults


def get_lineage_path(cfg: dict) -> Path:
    """Return the lineage file path (per-user or shared)."""
    lineage_dir = cfg["memory"]["lineage"].get("path", ".sentinel/lineage/")
    # Resolve relative to cwd (project root)
    base = Path(lineage_dir)
    team_mode = cfg["memory"]["lineage"].get("team_mode", "per_user")

    if team_mode == "per_user":
        username = os.environ.get("USER", os.environ.get("USERNAME", "default"))
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{username}.json"
    else:
        base.parent.mkdir(parents=True, exist_ok=True)
        return base.parent / "lineage.json"


def load_lineage(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"current_session": None, "ancestors": []}


def save_lineage(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        pass


def ensure_gitignore(lineage_dir_path: Path):
    """Ensure .sentinel/lineage/ is gitignored."""
    sentinel_dir = lineage_dir_path.parent
    gitignore = sentinel_dir / ".gitignore"
    try:
        sentinel_dir.mkdir(parents=True, exist_ok=True)
        existing = gitignore.read_text() if gitignore.exists() else ""
        lines_to_add = []
        if "lineage/" not in existing:
            lines_to_add.append("lineage/")
        if "lineage.json" not in existing:
            lines_to_add.append("lineage.json")
        if lines_to_add:
            with open(gitignore, "a") as f:
                f.write("\n".join(lines_to_add) + "\n")
    except Exception:
        pass


def load_design_system(cfg: dict) -> str:
    """Load .sentinel/design-system.md if it exists and auto_load is enabled."""
    ds_cfg = cfg.get("design_system", {})
    if not ds_cfg.get("enabled", True) or not ds_cfg.get("auto_load_on_session_start", True):
        return ""
    ds_path = Path(ds_cfg.get("path", ".sentinel/design-system.md"))
    if not ds_path.exists():
        return ""
    try:
        content = ds_path.read_text(encoding="utf-8")
        # Truncate if too large (> 3000 chars)
        if len(content) > 3000:
            content = content[:3000] + "\n... [design-system.md truncated]"
        return content
    except Exception:
        return ""


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cfg = load_config()
    lineage_cfg = cfg["memory"]["lineage"]

    if not lineage_cfg.get("enabled", True):
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    ts = datetime.now(timezone.utc).isoformat()

    # Get lineage path + ensure .gitignore
    lineage_path = get_lineage_path(cfg)
    ensure_gitignore(lineage_path.parent)

    # Load existing lineage
    lineage = load_lineage(lineage_path)

    # Record this session
    lineage["current_session"] = session_id
    lineage["last_seen"] = ts

    # Persist
    save_lineage(lineage_path, lineage)

    messages = []
    context_parts = []

    # Check context % from hook_input (if provided by Claude Code)
    context_pct = hook_input.get("context_usage_pct", None)
    trigger = lineage_cfg.get("rollover_trigger", "graduated")

    if trigger == "graduated" and context_pct is not None:
        stages = lineage_cfg.get("stages", {
            "warn_at_pct": 75,
            "offer_at_pct": 85,
            "hard_fork_at_pct": 95
        })
        warn_at = stages.get("warn_at_pct", 75)
        offer_at = stages.get("offer_at_pct", 85)
        hard_at = stages.get("hard_fork_at_pct", 95)

        ancestor_count = len(lineage.get("ancestors", []))

        if context_pct >= hard_at:
            messages.append(
                f"SENTINEL LINEAGE [AUTO-FORK READY]: Context at {context_pct}%. "
                f"Type >rollover to fork this session and preserve lineage. "
                f"Ancestors in chain: {ancestor_count}."
            )
        elif context_pct >= offer_at:
            messages.append(
                f"SENTINEL LINEAGE [ROLLOVER OFFER]: Context at {context_pct}%. "
                f"Recommend forking at a natural break. Type >rollover when ready."
            )
        elif context_pct >= warn_at:
            messages.append(
                f"SENTINEL LINEAGE [HEADS-UP]: Context at {context_pct}%. "
                f"Consider >rollover at your next natural stopping point."
            )

    # Inject ancestor list if lineage exists
    ancestors = lineage.get("ancestors", [])
    if ancestors:
        ancestor_summary = "\n".join(
            f"  [{i+1}] {a.get('session', 'unknown')} — {a.get('forked_at', 'unknown')}"
            for i, a in enumerate(ancestors[-5:])  # last 5 ancestors
        )
        context_parts.append(
            f"## Sentinel Session Lineage\n"
            f"Ancestor sessions (read them for full context on prior work):\n{ancestor_summary}\n"
            f"Use Bash(cat <path>) to read ancestor transcripts on demand."
        )

    # Load design system
    design_system = load_design_system(cfg)
    if design_system:
        context_parts.append(
            f"## Active Design System (.sentinel/design-system.md)\n{design_system}"
        )

    output = {}

    if messages:
        output["systemMessage"] = "\n\n".join(messages)

    if context_parts:
        output["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(context_parts)
        }

    if output:
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
