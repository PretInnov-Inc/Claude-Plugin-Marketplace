#!/bin/bash
# Clamper SessionStart Hook — Inject project DNA + verification context
#
# Reads DNA cache, recent verification outcomes, and fragile zones
# to give Claude deep project awareness from the first prompt.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
DATA_DIR="${PLUGIN_ROOT}/data"

# Read session info from stdin
SESSION_INFO=$(python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(json.dumps({
        'session_id': data.get('session_id', 'unknown'),
        'cwd': data.get('cwd', '.')
    }))
except:
    print(json.dumps({'session_id': 'unknown', 'cwd': '.'}))
")

SESSION_ID=$(echo "$SESSION_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")
CWD=$(echo "$SESSION_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['cwd'])")
PROJECT_NAME=$(basename "$CWD")

# Ensure data directory and files exist
mkdir -p "$DATA_DIR"
for f in verification-log.jsonl dna-cache.jsonl outcomes.jsonl; do
    touch "$DATA_DIR/$f"
done

# Log session start
python3 -c "
import json, sys
from datetime import datetime, timezone
record = {
    'event': 'session_start',
    'session_id': '$SESSION_ID',
    'project': '$PROJECT_NAME',
    'cwd': '$CWD',
    'timestamp': datetime.now(timezone.utc).isoformat()
}
with open('$DATA_DIR/outcomes.jsonl', 'a') as f:
    f.write(json.dumps(record) + '\n')
"

# Build intelligence context
CONTEXT=$(python3 << 'PYEOF'
import json
import os

data_dir = os.environ.get("DATA_DIR", "data")
project_name = os.environ.get("PROJECT_NAME", "unknown")

def read_jsonl_tail(filepath, n):
    entries = []
    if not os.path.exists(filepath):
        return entries
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries[-n:]

sections = []

# ── Section 1: Verification History ──
ver_log = read_jsonl_tail(os.path.join(data_dir, "verification-log.jsonl"), 30)
recent_verifications = [e for e in ver_log if e.get("event") in ("verification_passed", "verification_failed")]
if recent_verifications:
    lines = ["## Recent Verification Results"]
    for v in recent_verifications[-10:]:
        status = "PASS" if v.get("event") == "verification_passed" else "FAIL"
        lines.append(f"- [{status}] {v.get('file_path', '?')} — confidence: {v.get('confidence', '?')}%")
    sections.append("\n".join(lines))

# ── Section 2: Fragile Zones (high churn files) ──
dna_cache = read_jsonl_tail(os.path.join(data_dir, "dna-cache.jsonl"), 100)
churn_entries = [e for e in dna_cache if e.get("pattern") == "file_churn"]
if churn_entries:
    lines = ["## Fragile Zones (High Churn)"]
    seen = set()
    for entry in churn_entries[-10:]:
        fp = entry.get("file_path", "?")
        if fp not in seen:
            seen.add(fp)
            lines.append(f"- {fp} — {entry.get('detail', 'frequently edited')}")
    sections.append("\n".join(lines))

# ── Section 3: Recent Session Quality ──
outcomes = read_jsonl_tail(os.path.join(data_dir, "outcomes.jsonl"), 50)
session_ends = [e for e in outcomes if e.get("event") == "session_end"]
if session_ends:
    recent = session_ends[-5:]
    avg_quality = sum(e.get("quality_score", 0) for e in recent) / len(recent)
    lines = [f"## Session Quality (last {len(recent)} sessions, avg: {avg_quality:.0f}/100)"]
    for s in recent:
        proj = s.get("project", "?")
        score = s.get("quality_score", 0)
        icon = "OK" if score >= 70 else "WARN" if score >= 50 else "LOW"
        tests = "tested" if s.get("tests_run") else "untested"
        lines.append(f"- [{icon}] {proj}: {score}/100 ({tests}, {s.get('files_modified', 0)} files)")
    sections.append("\n".join(lines))

# ── Section 4: Project-Specific DNA ──
project_dna = [e for e in dna_cache if e.get("project") == project_name or not e.get("project")]
if project_dna:
    lines = [f"## Project DNA: {project_name}"]
    for entry in project_dna[-8:]:
        pattern = entry.get("pattern", "unknown")
        detail = entry.get("detail", "")
        if detail:
            lines.append(f"- [{pattern}] {detail}")
    sections.append("\n".join(lines))

# ── Section 5: Untested Changes Warning ──
untested = [e for e in dna_cache if e.get("pattern") == "untested_changes"]
if untested:
    last = untested[-1]
    files = last.get("files", [])
    if files:
        sections.append(
            f"## Warning: Untested Changes from Previous Session\n"
            f"Files modified without tests: {', '.join(files[:5])}"
        )

# ── Section 6: Core Clamper Principles ──
sections.append("""## Clamper Core Principles (Always Active)
1. VERIFY before accepting — run /clamp after significant edits
2. Tests are Phase 1, not the last step
3. Repeated edits to the same file = approach problem, not implementation problem
4. Security-sensitive files always warrant verification
5. Config/build file changes cascade — verify downstream effects
6. Track outcomes to learn what succeeds and what fails
7. Deep project DNA > static documentation""")

# ── Section 8: Config State ──
config_path = os.path.join(data_dir, "clamper-config.json")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    stats = config.get("verification_stats", {})
    total = stats.get("total_verifications", 0)
    if total > 0:
        pass_rate = (stats.get("passed", 0) / total * 100) if total else 0
        sections.append(
            f"## Clamper Stats\n"
            f"- Verifications: {total} (pass rate: {pass_rate:.0f}%)\n"
            f"- Flagged for review: {stats.get('flagged_for_review', 0)}"
        )
    suppressed = config.get("suppressed_warnings", [])
    if suppressed:
        sections.append(f"- Suppressed warnings: {', '.join(suppressed)}")

# Output
if sections:
    full_context = "\n\n".join(sections)
    print(full_context)
else:
    print("Clamper active. No historical data yet — outcomes will be tracked from this session.")

PYEOF
)

# Export as hook output
if [ -n "$CONTEXT" ]; then
    python3 -c "
import json, sys
context = sys.stdin.read()
output = {
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': context
    }
}
print(json.dumps(output))
" <<< "$CONTEXT"
fi
