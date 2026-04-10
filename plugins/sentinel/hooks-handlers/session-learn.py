#!/usr/bin/env python3
"""
Sentinel Stop Hook — Session Learning Extractor (Category E)

Fires when Claude finishes responding. Analyzes the session transcript
to extract:
  1. Learnings — what worked, what to remember
  2. Anti-patterns — what to avoid in future sessions
  3. Decisions — architectural or technology choices made
  4. Session health score — composite quality metric

Writes all extracted data to sentinel/data/ JSONL files for future
session context injection (session-memory.sh reads these on next start).

This is the primary learning loop that makes Sentinel smarter over time.
Pure stdlib — no pip dependencies.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_plugin_root():
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def get_data_dir():
    data_dir = Path(get_plugin_root()) / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, record: dict):
    """Append a single record to a JSONL file, creating if needed."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def trim_jsonl(path: Path, max_entries: int = 2000, keep_entries: int = 1500):
    """Trim JSONL file to prevent unbounded growth."""
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) > max_entries:
        with open(path, "w", encoding="utf-8") as f:
            for line in lines[-keep_entries:]:
                f.write(line + "\n")


def read_transcript(transcript_path: str, max_chars: int = 20000) -> str:
    """Read the last max_chars of the session transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Take last max_chars for efficiency
        return content[-max_chars:]
    except Exception:
        return ""


def extract_technologies(transcript: str) -> list:
    """Detect technologies and frameworks mentioned in the transcript."""
    tech_patterns = {
        "python": r"\b(python|django|flask|fastapi|pytest|pip|poetry|uv)\b",
        "typescript": r"\b(typescript|tsx|ts-node|vitest|jest)\b",
        "javascript": r"\b(javascript|node\.?js|npm|pnpm|yarn|webpack|vite|esbuild)\b",
        "react": r"\b(react|jsx|nextjs|next\.js|remix|gatsby)\b",
        "vue": r"\b(vue\.?js|nuxt|pinia|vuex)\b",
        "rust": r"\b(rust|cargo|tokio|serde)\b",
        "go": r"\b(golang|go build|go test|goroutine)\b",
        "sql": r"\b(sql|postgres|mysql|sqlite|supabase|prisma|drizzle)\b",
        "docker": r"\b(docker|dockerfile|docker-compose|kubernetes|k8s|helm)\b",
        "airflow": r"\b(airflow|dag|taskflow|astronomer)\b",
        "claude-api": r"\b(anthropic|claude api|agent sdk|mcp server)\b",
    }
    found = []
    transcript_lower = transcript.lower()
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, transcript_lower):
            found.append(tech)
    return found


def detect_errors(transcript: str) -> list:
    """Extract error signals from the transcript."""
    errors = []
    error_rx = [
        (r"(?:Error|ERROR|error):\s*(.{20,150}?)(?:\n|$)", "error"),
        (r"(?:failed|FAILED|Failed)\s+(?:to\s+)?(.{10,100}?)(?:\n|$)", "failure"),
        (r"Traceback \(most recent call last\)", "traceback"),
        (r"SyntaxError|ImportError|ModuleNotFoundError|AttributeError|TypeError|ValueError", "python-error"),
        (r"TypeError|ReferenceError|SyntaxError at .+:\d+", "js-error"),
    ]
    for pattern, category in error_rx:
        matches = re.findall(pattern, transcript[:15000])
        if not matches:
            continue
        for match in matches[:2]:
            clean = (match if isinstance(match, str) else "").strip()[:120]
            if len(clean) > 15:
                errors.append({"type": category, "detail": clean})
    return errors


def extract_decisions(transcript: str) -> list:
    """Look for decision patterns in assistant responses."""
    decisions = []
    decision_patterns = [
        r"(?:decided|choosing|we'll use|I'll use|using|going with)\s+([A-Za-z0-9\-\.]+)\s+(?:instead|over|because|for|as)",
        r"(?:The reason|rationale|because|since)\s+(.{20,100}?)(?:\.|\n)",
        r"(?:pattern|approach|architecture|design):\s*(.{10,80}?)(?:\n|$)",
    ]
    for pattern in decision_patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        for match in matches[:2]:
            clean = match.strip()[:150]
            if len(clean) > 20:
                decisions.append(clean)
    return decisions[:3]  # Cap at 3 per session


def calculate_health_score(transcript: str, errors: list, edit_log_path: Path, session_id: str) -> int:
    """
    Composite session health score (0-100):
    - Errors detected: -5 each (max -30)
    - Session length (reasonable work done): +20
    - Successful tool use (Edit/Write in transcript): +20
    - No repeated failures: +20
    - Coherent conversation (no confusion signals): +20
    - Baseline: 20
    """
    score = 20

    # Penalize errors
    error_penalty = min(len(errors) * 5, 30)
    score -= error_penalty

    # Reward productive session (length of transcript = work done)
    if len(transcript) > 3000:
        score += 20
    elif len(transcript) > 1000:
        score += 10

    # Reward tool use (edits happened)
    if re.search(r'"tool":\s*"(?:Edit|Write|MultiEdit)"', transcript):
        score += 20
    elif "Edit" in transcript or "Write" in transcript:
        score += 10

    # Penalize confusion signals
    confusion_patterns = [
        r"I(?:'m| am) not sure",
        r"I don't (?:know|understand)",
        r"could you clarify",
        r"what do you mean",
        r"I can't find",
        r"doesn't exist",
    ]
    confusion_count = sum(1 for p in confusion_patterns if re.search(p, transcript, re.IGNORECASE))
    score -= min(confusion_count * 5, 20)

    # Check edit log for churn (repeated edits = problem)
    if edit_log_path.exists():
        try:
            with open(edit_log_path) as f:
                entries = [json.loads(l) for l in f if l.strip()]
            session_entries = [e for e in entries[-200:] if e.get("session_id") == session_id]
            churn_events = [e for e in session_entries if e.get("event") == "churn_detected"]
            score -= min(len(churn_events) * 10, 20)
        except Exception:
            pass
    else:
        score += 20  # No churn data = no penalty

    return max(0, min(100, score))


def extract_learnings_from_transcript(transcript: str, technologies: list) -> list:
    """
    Extract specific, actionable learnings from the transcript.
    Looks for:
    - Explicit "remember" / "note that" / "important:" patterns
    - Successful approaches that could repeat
    - Fixed mistakes
    """
    learnings = []

    # Pattern: explicit learning markers
    explicit_patterns = [
        (r"(?:remember|note that|important):\s*(.{20,200}?)(?:\n|$)", "explicit"),
        (r"(?:the (?:key|trick|gotcha|issue|problem) (?:is|was)):\s*(.{20,200}?)(?:\n|$)", "insight"),
        (r"(?:this works because|the reason this works):\s*(.{20,200}?)(?:\n|$)", "insight"),
    ]
    for pattern, cat in explicit_patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        for match in matches[:2]:
            clean = match.strip()[:180]
            if len(clean) > 25:
                learnings.append({"category": cat, "learning": clean, "confidence": "high"})

    # Tech-specific learnings
    if "airflow" in technologies:
        learnings.append({
            "category": "airflow",
            "learning": f"Session worked with Airflow ({', '.join(t for t in technologies if t in ['python', 'airflow'])}). Check DAG structure and test before deploy.",
            "confidence": "medium"
        })

    if "claude-api" in technologies:
        learnings.append({
            "category": "ai-development",
            "learning": "Session involved Claude API / Agent SDK work. Validate tool schemas and test streaming responses.",
            "confidence": "medium"
        })

    return learnings[:5]  # Cap per session


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    stop_reason = hook_input.get("stop_reason", "unknown")

    data_dir = get_data_dir()
    edit_log_path = data_dir / "edit-log.jsonl"
    learnings_path = data_dir / "learnings.jsonl"
    session_log_path = data_dir / "session-log.jsonl"
    anti_patterns_path = data_dir / "anti-patterns.jsonl"

    # Read transcript
    transcript = read_transcript(transcript_path)

    # Extract signals
    technologies = extract_technologies(transcript)
    errors = detect_errors(transcript)
    decisions = extract_decisions(transcript)
    learnings = extract_learnings_from_transcript(transcript, technologies)

    # Calculate health score
    health_score = calculate_health_score(transcript, errors, edit_log_path, session_id)

    ts = now_iso()

    # Write session stop record
    append_jsonl(session_log_path, {
        "event": "session_stop",
        "session_id": session_id,
        "stop_reason": stop_reason,
        "health_score": health_score,
        "technologies": technologies,
        "error_count": len(errors),
        "learnings_extracted": len(learnings),
        "timestamp": ts
    })

    # Write learnings
    for learning in learnings:
        append_jsonl(learnings_path, {
            **learning,
            "session_id": session_id,
            "timestamp": ts
        })

    # Write error-based anti-patterns
    for error in errors[:2]:
        if error["type"] in ("error", "failure"):
            append_jsonl(anti_patterns_path, {
                "pattern": f"Error pattern: {error['detail'][:100]}",
                "reason": "Recurring error detected in session",
                "category": error["type"],
                "session_id": session_id,
                "timestamp": ts
            })

    # Write decisions
    decisions_path = data_dir / "decisions.jsonl"
    for decision in decisions:
        append_jsonl(decisions_path, {
            "decision": decision,
            "outcome": "pending",
            "context": ", ".join(technologies[:3]),
            "session_id": session_id,
            "timestamp": ts
        })

    # Trim files to prevent unbounded growth
    for path in [learnings_path, anti_patterns_path, session_log_path, decisions_path]:
        trim_jsonl(path)

    # Output health warning if very low
    if health_score < 40:
        print(json.dumps({
            "systemMessage": (
                f"SENTINEL: Session health score {health_score}/100 — below threshold. "
                f"Errors detected: {len(errors)}. "
                f"Run /sentinel:flow-memory to review patterns and prevent repeat failures."
            )
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
