#!/usr/bin/env bash
# Cortex SessionStart Hook
# Loads intelligence context, checks stale memories, injects learnings
# Runs at every session start to prime Claude with accumulated wisdom

set -euo pipefail

CORTEX_DATA="${CLAUDE_PLUGIN_ROOT}/data"
CORTEX_JOURNAL="${CORTEX_DATA}/decision-journal.jsonl"
CORTEX_PATTERNS="${CORTEX_DATA}/patterns.jsonl"
CORTEX_LEARNINGS="${CORTEX_DATA}/learnings.jsonl"
CORTEX_SESSION_LOG="${CORTEX_DATA}/session-log.jsonl"
CORTEX_ANTI_PATTERNS="${CORTEX_DATA}/anti-patterns.jsonl"

# Read hook input from stdin
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo "unknown")
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")

# Ensure data directory exists
mkdir -p "$CORTEX_DATA"

# Initialize files if missing
for f in "$CORTEX_JOURNAL" "$CORTEX_PATTERNS" "$CORTEX_LEARNINGS" "$CORTEX_SESSION_LOG" "$CORTEX_ANTI_PATTERNS"; do
  [ -f "$f" ] || touch "$f"
done

# Log session start
echo "{\"event\":\"session_start\",\"session_id\":\"$SESSION_ID\",\"cwd\":\"$CWD\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$CORTEX_SESSION_LOG"

# Build intelligence context via Python for safe JSON handling
python3 << 'PYEOF'
import json, os, sys
from pathlib import Path

data_dir = os.environ.get("CORTEX_DATA", "")
if not data_dir:
    sys.exit(0)
data_dir = Path(data_dir)
cwd = os.environ.get("CWD", "")

sections = []

# 1. Load recent learnings (last 15)
learnings_file = data_dir / "learnings.jsonl"
if learnings_file.exists():
    items = []
    with open(learnings_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                cat = d.get("category", "general")
                msg = d.get("learning", "")
                if msg:
                    items.append(f"  [{cat}] {msg}")
            except:
                pass
    if items:
        sections.append("## Cortex: Active Learnings (from past sessions)\n" + "\n".join(items[-15:]))

# 2. Load anti-patterns (things to AVOID)
ap_file = data_dir / "anti-patterns.jsonl"
if ap_file.exists():
    items = []
    with open(ap_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                what = d.get("what", "")
                why = d.get("why", "")
                if what:
                    entry = f"  AVOID: {what}"
                    if why:
                        entry += f" (Reason: {why})"
                    items.append(entry)
            except:
                pass
    if items:
        sections.append("## Cortex: Anti-Patterns (mistakes to avoid)\n" + "\n".join(items[-10:]))

# 3. Load recent decisions relevant to current project
if cwd:
    project_name = os.path.basename(cwd)
    journal_file = data_dir / "decision-journal.jsonl"
    if journal_file.exists():
        items = []
        with open(journal_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if project_name.lower() in d.get("project", "").lower():
                        decision = d.get("decision", "")
                        outcome = d.get("outcome", "pending")
                        if decision:
                            icon = "OK" if outcome == "success" else ("FAIL" if outcome == "failure" else "?")
                            items.append(f"  [{icon}] {decision}")
                except:
                    pass
        if items:
            sections.append(f"## Cortex: Past Decisions for {project_name}\n" + "\n".join(items[-5:]))

# 4. Session stats
session_count = 0
session_file = data_dir / "session-log.jsonl"
if session_file.exists():
    with open(session_file) as f:
        session_count = sum(1 for line in f if line.strip())

learning_count = 0
if learnings_file.exists():
    with open(learnings_file) as f:
        learning_count = sum(1 for line in f if line.strip())

ap_count = 0
if ap_file.exists():
    with open(ap_file) as f:
        ap_count = sum(1 for line in f if line.strip())

sections.append(f"""## Cortex: Session Intelligence
  Total tracked sessions: {session_count}
  Active learnings: {learning_count}
  Anti-patterns tracked: {ap_count}
  REMEMBER: Multi-phase tasks fail ~60% of the time. Scope down aggressively. Test FIRST, not last.""")

# 5. Core rules (always injected)
sections.append("""## Cortex: Core Rules (always active)
  1. NEVER auto-commit or auto-push unless explicitly asked
  2. ALWAYS verify SDK exports/types against installed code before proposing approaches
  3. Store DECISIONS not code patterns in memory — corrections and constraints are most valuable
  4. Plans are the most valuable artifact — create them for multi-session work
  5. Moving project directories fragments context — warn if detected
  6. Testing should be Phase 1, not the last step
  7. If a 10-step plan exists, expect to finish 4 steps. Scope accordingly.
  8. Security warnings are domain-blind — accept architectural necessities without repeated warnings""")

# 6. Self-evolution status
config_file = data_dir / "cortex-config.json"
if config_file.exists():
    try:
        with open(config_file) as f:
            config = json.load(f)
        stats = config.get("evolution_stats", {})
        total_evolutions = stats.get("total_evolutions", 0)
        last_evolution = stats.get("last_evolution", "never")
        thresholds = config.get("thresholds", {})
        suppressed = config.get("suppressed_warnings", [])
        overrides = config.get("project_overrides", {})

        evo_lines = [f"  Total self-evolutions: {total_evolutions}"]
        evo_lines.append(f"  Last evolution: {last_evolution}")
        evo_lines.append(f"  Scope task threshold: {thresholds.get('scope_task_threshold', 5)}")
        evo_lines.append(f"  Repetitive edit threshold: {thresholds.get('repetitive_edit_threshold', 5)}")
        if suppressed:
            evo_lines.append(f"  Suppressed warnings: {len(suppressed)} active")
            for s in suppressed[-3:]:
                evo_lines.append(f"    - {s.get('category', '?')} ({s.get('scope', 'global')}): {s.get('reason', '')}")
        if cwd:
            proj = os.path.basename(cwd)
            if proj in overrides:
                ov = overrides[proj]
                if ov.get("extra_learnings"):
                    for el in ov["extra_learnings"]:
                        evo_lines.append(f"  [PROJECT RULE] {el}")
                if ov.get("suppressed_rules"):
                    evo_lines.append(f"  Suppressed for this project: {', '.join(ov['suppressed_rules'])}")

        sections.append("## Cortex: Self-Evolution State\n" + "\n".join(evo_lines))

        # 7. Inject project-specific extra learnings
        if cwd:
            proj = os.path.basename(cwd)
            if proj in overrides and overrides[proj].get("extra_learnings"):
                proj_lines = [f"  - {l}" for l in overrides[proj]["extra_learnings"]]
                sections.append(f"## Cortex: Project-Specific Rules for {proj}\n" + "\n".join(proj_lines))

    except Exception:
        pass

# 8. Pending user feedback to process
feedback_file = data_dir / "user-feedback.jsonl"
if feedback_file.exists():
    try:
        with open(feedback_file) as f:
            lines = f.readlines()
        recent_fb = []
        for line in lines[-5:]:
            line = line.strip()
            if not line:
                continue
            try:
                fb = json.loads(line)
                if fb.get("signal_type") in ("suppress_warning", "negative_feedback", "directive", "teach", "project_rule", "tune_threshold"):
                    recent_fb.append(f"  [{fb['signal_type']}] {fb.get('signal', '')}")
            except:
                pass
        if recent_fb:
            sections.append("## Cortex: Pending User Feedback (process with self-evolver agent)\n" + "\n".join(recent_fb))
    except:
        pass

context = "\n\n".join(sections)
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))
PYEOF
