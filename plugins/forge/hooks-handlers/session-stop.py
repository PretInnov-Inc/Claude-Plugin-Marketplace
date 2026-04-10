#!/usr/bin/env python3
"""Plugin-Forge Stop Hook: Captures build outcomes, extracts learnings from plugin generation sessions."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
data_dir = plugin_root / "data"

def read_json(filename):
    path = data_dir / filename
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except:
        return {}

def write_json(filename, data):
    path = data_dir / filename
    path.write_text(json.dumps(data, indent=2) + "\n")

def append_jsonl(filename, entry):
    path = data_dir / filename
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def trim_jsonl(filename, max_entries):
    path = data_dir / filename
    if not path.exists():
        return
    lines = path.read_text().strip().split("\n")
    if len(lines) > max_entries:
        path.write_text("\n".join(lines[-int(max_entries * 0.8):]) + "\n")

def main():
    try:
        hook_input = json.load(sys.stdin)
    except:
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")
    project = os.path.basename(cwd) if cwd else "unknown"
    now = datetime.now(timezone.utc).isoformat()

    # Read transcript tail
    transcript = ""
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, "r") as f:
                content = f.read()
                transcript = content[-30000:]  # Last 30K chars
        except:
            pass

    if not transcript:
        sys.exit(0)

    # Detect if this was a forge/plugin-building session
    forge_signals = [
        r'/forge',
        r'plugin\.json',
        r'SKILL\.md',
        r'hooks\.json',
        r'\.claude-plugin',
        r'plugin-forge|plugin.forge',
        r'generate.*plugin|create.*plugin|build.*plugin|scaffold.*plugin',
        r'blueprint|forge-architect|forge-generator',
    ]
    forge_activity = sum(1 for pat in forge_signals if re.search(pat, transcript, re.IGNORECASE))

    if forge_activity < 2:
        sys.exit(0)  # Not a forge-relevant session, skip

    # Extract build details
    plugins_mentioned = set(re.findall(r'plugin[_-]?(?:name|id)[":\s]+["\']?(\w[\w-]+)', transcript, re.IGNORECASE))
    files_written = set(re.findall(r'(?:File created|Written to|Wrote)[^"]*"([^"]+)"', transcript))
    files_written.update(re.findall(r'(?:Write|Edit).*?file_path[":\s]+["\']([^"\']+)', transcript))

    # Count component types generated
    agents_generated = len([f for f in files_written if '/agents/' in f and f.endswith('.md')])
    skills_generated = len([f for f in files_written if 'SKILL.md' in f])
    hooks_generated = len([f for f in files_written if 'hooks.json' in f or '/hooks-handlers/' in f])
    hook_handlers = len([f for f in files_written if '/hooks-handlers/' in f and (f.endswith('.py') or f.endswith('.sh'))])

    # Detect errors
    errors = re.findall(r'(?:Error|FAILED|error\[|Exception|failed to).*', transcript, re.IGNORECASE)
    error_count = len(errors)

    # Detect validation
    validation_run = bool(re.search(r'forge.*validate|validate.*plugin|plugin.*valid', transcript, re.IGNORECASE))
    validation_passed = bool(re.search(r'validation.*pass|all.*files.*present|structure.*valid', transcript, re.IGNORECASE))

    # Detect research phase
    research_done = bool(re.search(r'WebSearch|WebFetch|research.*phase|searching.*for|found.*existing', transcript, re.IGNORECASE))
    repos_scanned = len(re.findall(r'github\.com/[\w-]+/[\w-]+', transcript))

    # Calculate build health score
    health = 50
    health += min(len(files_written) * 2, 20)  # Files generated
    health += 10 if research_done else 0
    health += 10 if validation_run else 0
    health += 5 if validation_passed else 0
    health -= min(error_count * 5, 25)
    health -= 10 if not research_done and forge_activity > 3 else 0  # Penalty for skipping research
    health = max(0, min(100, health))

    success = health >= 60 and error_count < 3

    # Log build completion
    build_entry = {
        "event": "build_complete",
        "session_id": session_id,
        "project": project,
        "plugin_name": list(plugins_mentioned)[0] if plugins_mentioned else "unknown",
        "success": success,
        "health_score": health,
        "files_generated": len(files_written),
        "components": {
            "agents": agents_generated,
            "skills": skills_generated,
            "hooks": hooks_generated,
            "hook_handlers": hook_handlers
        },
        "research_done": research_done,
        "repos_scanned": repos_scanned,
        "validation_run": validation_run,
        "validation_passed": validation_passed,
        "error_count": error_count,
        "timestamp": now
    }
    append_jsonl("build-log.jsonl", build_entry)

    # Extract learnings
    if health < 40:
        append_jsonl("learnings.jsonl", {
            "learning": f"Low-health build ({health}/100) for {build_entry['plugin_name']}. Errors: {error_count}. Research: {'yes' if research_done else 'SKIPPED'}.",
            "category": "build-quality",
            "source": "auto-extraction",
            "build_health": health,
            "timestamp": now
        })

    if not research_done and forge_activity > 3:
        append_jsonl("learnings.jsonl", {
            "learning": "Plugin was built without research phase. Enforce research-first workflow.",
            "category": "process-violation",
            "source": "auto-extraction",
            "timestamp": now
        })

    if agents_generated > 6:
        append_jsonl("learnings.jsonl", {
            "learning": f"Generated {agents_generated} agents — consider if all are necessary. Past builds show 3-5 agents is the sweet spot.",
            "category": "scope-management",
            "source": "auto-extraction",
            "timestamp": now
        })

    if skills_generated > 0 and hooks_generated == 0:
        append_jsonl("learnings.jsonl", {
            "learning": "Plugin has skills but no hooks. Most robust plugins use hooks for automatic behavior (SessionStart context injection, PostToolUse tracking).",
            "category": "completeness",
            "source": "auto-extraction",
            "timestamp": now
        })

    # Update build stats in config
    config = read_json("forge-config.json")
    stats = config.get("build_stats", {})
    stats["total_builds"] = stats.get("total_builds", 0) + 1
    if success:
        stats["successful_builds"] = stats.get("successful_builds", 0) + 1
    else:
        stats["failed_builds"] = stats.get("failed_builds", 0) + 1
    stats["total_files_generated"] = stats.get("total_files_generated", 0) + len(files_written)
    stats["total_agents_generated"] = stats.get("total_agents_generated", 0) + agents_generated
    stats["total_skills_generated"] = stats.get("total_skills_generated", 0) + skills_generated
    stats["total_hooks_generated"] = stats.get("total_hooks_generated", 0) + hooks_generated
    if plugins_mentioned:
        generated = stats.get("plugins_generated", [])
        generated.extend(list(plugins_mentioned))
        stats["plugins_generated"] = list(set(generated))[-20:]  # Keep last 20
    stats["last_build"] = now
    config["build_stats"] = stats

    research_stats = config.get("research_stats", {})
    if research_done:
        research_stats["total_searches"] = research_stats.get("total_searches", 0) + 1
        research_stats["total_repos_scanned"] = research_stats.get("total_repos_scanned", 0) + repos_scanned
        research_stats["last_research"] = now
    config["research_stats"] = research_stats

    write_json("forge-config.json", config)

    # Trim data files
    trim_jsonl("build-log.jsonl", 1000)
    trim_jsonl("learnings.jsonl", 200)
    trim_jsonl("research-cache.jsonl", 500)

    sys.exit(0)

if __name__ == "__main__":
    main()
