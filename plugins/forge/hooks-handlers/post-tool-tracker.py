#!/usr/bin/env python3
"""Plugin-Forge PostToolUse Hook: Tracks files generated during plugin builds, detects template drift."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
data_dir = plugin_root / "data"

def append_jsonl(filename, entry):
    path = data_dir / filename
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    try:
        hook_input = json.load(sys.stdin)
    except:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Detect if this is a plugin-related file being written
    plugin_indicators = [
        ".claude-plugin", "plugin.json", "SKILL.md", "hooks.json",
        "/agents/", "/skills/", "/hooks/", "/hooks-handlers/",
        "/data/", "/bin/", "/scripts/", "settings.json",
        ".mcp.json", ".lsp.json", "output-styles/"
    ]

    is_plugin_file = any(ind in file_path for ind in plugin_indicators)
    if not is_plugin_file:
        sys.exit(0)

    # Classify the component type
    component_type = "unknown"
    if "plugin.json" in file_path:
        component_type = "manifest"
    elif "SKILL.md" in file_path:
        component_type = "skill"
    elif "/agents/" in file_path and file_path.endswith(".md"):
        component_type = "agent"
    elif "hooks.json" in file_path:
        component_type = "hook-config"
    elif "/hooks-handlers/" in file_path:
        component_type = "hook-handler"
    elif "/data/" in file_path:
        component_type = "data"
    elif "/bin/" in file_path:
        component_type = "bin-tool"
    elif "/scripts/" in file_path:
        component_type = "script"
    elif "settings.json" in file_path:
        component_type = "settings"
    elif ".mcp.json" in file_path:
        component_type = "mcp-config"
    elif ".lsp.json" in file_path:
        component_type = "lsp-config"
    elif "output-styles/" in file_path:
        component_type = "output-style"

    # Log the generated file
    append_jsonl("build-log.jsonl", {
        "event": "file_generated",
        "tool": tool_name,
        "file_path": file_path,
        "component_type": component_type,
        "session_id": session_id,
        "timestamp": now
    })

    # Detect potential issues
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    messages = []

    # Check for hardcoded paths (should use ${CLAUDE_PLUGIN_ROOT})
    if component_type in ("hook-handler", "hook-config", "skill", "agent", "mcp-config"):
        if re.search(r'/Users/|/home/|/Volumes/|C:\\', content):
            messages.append(f"FORGE WARNING: Hardcoded absolute path detected in {os.path.basename(file_path)}. Use ${{CLAUDE_PLUGIN_ROOT}} instead.")

    # Check for missing frontmatter in skills/agents
    if component_type == "skill" and tool_name == "Write":
        if not content.strip().startswith("---"):
            messages.append(f"FORGE WARNING: SKILL.md at {file_path} missing YAML frontmatter. Skills need ---\\ndescription: ...\\n--- at minimum.")

    if component_type == "agent" and tool_name == "Write":
        if not content.strip().startswith("---"):
            messages.append(f"FORGE WARNING: Agent file at {file_path} missing YAML frontmatter. Agents need ---\\nname: ...\\ndescription: ...\\n--- at minimum.")
        elif "tools:" not in content[:500]:
            messages.append(f"FORGE NOTE: Agent {os.path.basename(file_path)} has no explicit tools: field. It will inherit all session tools.")

    # Check for pip dependencies in hook handlers
    if component_type == "hook-handler" and file_path.endswith(".py"):
        non_stdlib = re.findall(r'^(?:import|from)\s+((?!json|os|sys|re|datetime|pathlib|collections|subprocess|shutil|tempfile|hashlib|urllib|io|glob|fnmatch|math|random|string|time|traceback|contextlib|functools|itertools|textwrap|argparse|copy)\w+)', content, re.MULTILINE)
        if non_stdlib:
            messages.append(f"FORGE WARNING: Hook handler imports non-stdlib modules: {', '.join(non_stdlib)}. Hooks should use only Python stdlib to avoid dependency issues.")

    if messages:
        print(json.dumps({"systemMessage": "\n".join(messages)}))

    sys.exit(0)

if __name__ == "__main__":
    main()
