#!/usr/bin/env python3
"""
Sentinel UserPromptSubmit Hook — Zero-Token Prompt Router (v3)

Intercepts prompts starting with '>' (configurable prefix).
Blocks the prompt from reaching the model (zero LLM cost) and routes
it directly to the appropriate CLI tool or injects routing instructions.

Supported routes (see sentinel-config.json prompt_routing.routes):
  >review   → Full sentinel review pipeline
  >quick    → Quick 2-agent check
  >security → Security-focused scan
  >rollover → Fork session, update lineage
  >doctor   → Unified health check
  >refresh  → Run sentinel-refresh maintenance
  >resume   → Print session handoff instructions

Non-prefixed prompts pass through unchanged (exit 0, no output).

Pure stdlib — no pip dependencies.
"""

import json
import os
import sys
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def load_config():
    config_path = Path(get_plugin_root()) / "data" / "sentinel-config.json"
    defaults = {
        "prompt_routing": {
            "enabled": True,
            "prefix": ">",
            "routes": {
                "review":   "Run /sentinel full review pipeline on current changes",
                "quick":    "Run /sentinel quick — 2-agent check only",
                "security": "Run /sentinel security — security-focused scan",
                "rollover": "Fork this session: run sentinel-status --trigger rollover",
                "doctor":   "Run sentinel-doctor to check plugin health",
                "refresh":  "Run sentinel-refresh --auto to maintain typed learning store",
                "resume":   "Print session handoff: run sentinel-status --trigger resume"
            }
        }
    }
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            if "prompt_routing" in cfg:
                defaults["prompt_routing"].update(cfg["prompt_routing"])
        except Exception:
            pass
    return defaults["prompt_routing"]


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cfg = load_config()
    if not cfg.get("enabled", True):
        sys.exit(0)

    prompt = hook_input.get("prompt", "").strip()
    prefix = cfg.get("prefix", ">")

    if not prompt.startswith(prefix):
        sys.exit(0)

    # Extract command (everything after prefix, lowercased, strip whitespace)
    command = prompt[len(prefix):].strip().lower()
    routes = cfg.get("routes", {})

    if command not in routes:
        # Unknown >command — let it pass through to model
        sys.exit(0)

    route_instruction = routes[command]

    # Block the raw prompt (exit 2 would reject it; use systemMessage pattern instead)
    # We inject a routing directive so the model executes the right action
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                f"[SENTINEL ROUTER] User shortcut: >{command}\n"
                f"Execute immediately: {route_instruction}\n"
                f"Do not ask for clarification — route directly."
            )
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
