#!/usr/bin/env python3
"""Plugin-Forge PreCompact Hook: Preserves blueprint state and build context before context compaction."""
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

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    now = datetime.now(timezone.utc).isoformat()

    transcript = ""
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, "r") as f:
                transcript = f.read()[-20000:]
        except:
            pass

    if not transcript:
        sys.exit(0)

    # Extract blueprint info from context
    blueprint_mentions = re.findall(r'blueprint.*?(?:approved|pending|generated|rejected)', transcript, re.IGNORECASE)
    plugin_names = set(re.findall(r'plugin[_-]?name[":\s]+["\']?(\w[\w-]+)', transcript, re.IGNORECASE))
    active_phase = "unknown"
    for phase in ["generate", "blueprint", "clarify", "research"]:
        if re.search(rf'phase.*{phase}|{phase}.*phase|/forge:{phase}', transcript, re.IGNORECASE):
            active_phase = phase
            break

    # Count files already generated in this session
    files_in_context = len(re.findall(r'File created|Written to|file_path', transcript))

    # Preserve state
    append_jsonl("build-log.jsonl", {
        "event": "pre_compact",
        "session_id": session_id,
        "active_phase": active_phase,
        "plugin_names": list(plugin_names),
        "files_in_context": files_in_context,
        "blueprint_status": blueprint_mentions[-1] if blueprint_mentions else "none",
        "timestamp": now
    })

    # Warn Claude about context loss
    warnings = []
    if active_phase in ("generate", "blueprint"):
        warnings.append(f"FORGE: Context compaction during {active_phase} phase. After compaction, re-read the blueprint from data/blueprints.jsonl and any partially generated files before continuing.")

    if plugin_names:
        warnings.append(f"FORGE: Active build for: {', '.join(plugin_names)}. Check data/build-log.jsonl for file_generated events to know what's already been written.")

    if warnings:
        print(json.dumps({"systemMessage": "\n".join(warnings)}))

    sys.exit(0)

if __name__ == "__main__":
    main()
