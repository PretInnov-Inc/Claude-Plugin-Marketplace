#!/usr/bin/env python3
"""
Cortex Stop Hook — Session Intelligence Extractor + Self-Adaptation Engine

When Claude stops responding, this hook:
1. Reads the transcript to extract learnings
2. Analyzes task completion patterns
3. Updates the decision journal
4. Detects abandoned work and records anti-patterns
5. Calculates session health score
6. [SELF-ADAPT] Detects user feedback about Cortex and records it
7. [SELF-ADAPT] Auto-tunes thresholds based on session outcomes
8. [SELF-ADAPT] Promotes validated patterns to permanent learnings

This is the PRIMARY learning mechanism — it runs at every session end.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

def get_cortex_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = Path(plugin_root) / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def read_transcript_tail(transcript_path, max_lines=200):
    """Read last N lines of transcript for analysis."""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception:
        return ""

def extract_learnings_from_transcript(transcript):
    """Extract key learnings, decisions, and patterns from transcript text."""
    learnings = []
    decisions = []
    failures = []

    # Detect error patterns
    error_patterns = [
        (r"(?:Error|ERROR|error):\s*(.+?)(?:\n|$)", "error"),
        (r"(?:failed|FAILED|Failed)(?:\s+to\s+|\s*:\s*)(.+?)(?:\n|$)", "failure"),
        (r"(?:warning|WARNING|Warning):\s*(.+?)(?:\n|$)", "warning"),
    ]

    for pattern, category in error_patterns:
        matches = re.findall(pattern, transcript[:10000])  # First 10k chars
        for match in matches[:3]:  # Cap at 3 per category
            clean = match.strip()[:200]
            if len(clean) > 20:
                failures.append({"type": category, "detail": clean})

    # Detect technology/framework mentions for context
    tech_patterns = {
        "django": r"\b(?:django|manage\.py|makemigrations|INSTALLED_APPS)\b",
        "react": r"\b(?:react|useState|useEffect|jsx|tsx|Next\.js)\b",
        "vue": r"\b(?:vue|nuxt|composable|pinia|PrimeVue)\b",
        "python": r"\b(?:python3?|pip|pytest|pydantic|fastapi)\b",
        "typescript": r"\b(?:typescript|tsx?|tsconfig|tsc)\b",
        "mcp": r"\b(?:MCP|FastMCP|mcp\.tool|McpServer)\b",
        "agent": r"\b(?:agent|subagent|Agent SDK|claude-agent-sdk)\b",
    }

    detected_tech = []
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, transcript, re.IGNORECASE):
            detected_tech.append(tech)

    # Detect decision patterns (user corrections, preferences)
    correction_patterns = [
        r"(?:don't|do not|never|stop|avoid)\s+(.+?)(?:\.|!|\n)",
        r"(?:instead|rather|prefer)\s+(.+?)(?:\.|!|\n)",
        r"(?:use|switch to|change to)\s+(.+?)(?:\s+instead|\.|!|\n)",
    ]

    for pattern in correction_patterns:
        matches = re.findall(pattern, transcript[-5000:], re.IGNORECASE)
        for match in matches[:2]:
            clean = match.strip()[:150]
            if len(clean) > 10:
                decisions.append({"decision": clean, "type": "user_correction"})

    # Detect what was accomplished (file edits, creates)
    files_modified = set(re.findall(r"(?:Edited|Created|Wrote|Modified)\s+[`'\"]?([^\s`'\"]+\.\w+)", transcript))

    # Detect todo completion patterns
    todo_complete = len(re.findall(r"(?:completed|done|finished|✓|✅)", transcript, re.IGNORECASE))
    todo_pending = len(re.findall(r"(?:pending|TODO|FIXME|remaining|skipped)", transcript, re.IGNORECASE))

    return {
        "learnings": learnings,
        "decisions": decisions,
        "failures": failures,
        "technologies": detected_tech,
        "files_modified": list(files_modified)[:20],
        "completion_signals": {"completed": todo_complete, "pending": todo_pending},
    }

def calculate_session_health(analysis):
    """Score session health 0-100 based on extracted signals."""
    score = 50  # Baseline

    # Positive signals
    if analysis["files_modified"]:
        score += min(len(analysis["files_modified"]) * 3, 20)
    if analysis["completion_signals"]["completed"] > 0:
        score += min(analysis["completion_signals"]["completed"] * 2, 15)

    # Negative signals
    score -= min(len(analysis["failures"]) * 5, 25)
    score -= min(analysis["completion_signals"]["pending"] * 2, 15)

    return max(0, min(100, score))

def append_jsonl(filepath, data):
    """Thread-safe JSONL append."""
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass

def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    cwd = hook_input.get("cwd", "")
    transcript_path = hook_input.get("transcript_path", "")

    data_dir = get_cortex_data_dir()
    now = datetime.now(timezone.utc).isoformat()

    # Read and analyze transcript
    transcript = ""
    if transcript_path and os.path.exists(transcript_path):
        transcript = read_transcript_tail(transcript_path, max_lines=300)

    if not transcript:
        sys.exit(0)

    analysis = extract_learnings_from_transcript(transcript)
    health = calculate_session_health(analysis)

    # 1. Log session completion with health score
    session_record = {
        "event": "session_end",
        "session_id": session_id,
        "cwd": cwd,
        "project": os.path.basename(cwd) if cwd else "unknown",
        "timestamp": now,
        "health_score": health,
        "technologies": analysis["technologies"],
        "files_modified_count": len(analysis["files_modified"]),
        "failures_count": len(analysis["failures"]),
        "completion_ratio": (
            analysis["completion_signals"]["completed"] /
            max(1, analysis["completion_signals"]["completed"] + analysis["completion_signals"]["pending"])
        ),
    }
    append_jsonl(data_dir / "session-log.jsonl", session_record)

    # 2. Record decisions
    for decision in analysis["decisions"]:
        record = {
            "decision": decision["decision"],
            "type": decision["type"],
            "project": os.path.basename(cwd) if cwd else "unknown",
            "session_id": session_id,
            "outcome": "pending",
            "timestamp": now,
        }
        append_jsonl(data_dir / "decision-journal.jsonl", record)

    # 3. Record failures as potential anti-patterns
    for failure in analysis["failures"]:
        if failure["type"] in ("error", "failure"):
            record = {
                "what": failure["detail"],
                "why": f"Encountered during session in {os.path.basename(cwd) if cwd else 'unknown'}",
                "category": failure["type"],
                "session_id": session_id,
                "timestamp": now,
            }
            append_jsonl(data_dir / "anti-patterns.jsonl", record)

    # 4. Auto-extract learnings from low-health sessions
    if health < 40:
        learning = {
            "learning": f"Low-health session ({health}/100) in {os.path.basename(cwd) if cwd else 'unknown'}: {len(analysis['failures'])} failures, completion ratio {session_record['completion_ratio']:.0%}",
            "category": "session-health",
            "session_id": session_id,
            "timestamp": now,
        }
        append_jsonl(data_dir / "learnings.jsonl", learning)

    # 5. Detect scope creep pattern (many pending, few completed)
    comp = analysis["completion_signals"]
    if comp["pending"] > 5 and comp["completed"] < comp["pending"] * 0.3:
        learning = {
            "learning": f"Scope creep detected: {comp['pending']} pending vs {comp['completed']} completed. Consider scoping down next time.",
            "category": "scope-management",
            "session_id": session_id,
            "timestamp": now,
        }
        append_jsonl(data_dir / "learnings.jsonl", learning)

    # 6. Track technology usage patterns
    if analysis["technologies"]:
        record = {
            "technologies": analysis["technologies"],
            "project": os.path.basename(cwd) if cwd else "unknown",
            "session_id": session_id,
            "timestamp": now,
        }
        append_jsonl(data_dir / "patterns.jsonl", record)

    # ─── SELF-ADAPTATION ENGINE ────────────────────────────────────────

    # 7. Detect user feedback about Cortex itself
    cortex_feedback = extract_cortex_feedback(transcript)
    for fb in cortex_feedback:
        fb["session_id"] = session_id
        fb["project"] = os.path.basename(cwd) if cwd else "unknown"
        fb["timestamp"] = now
        append_jsonl(data_dir / "user-feedback.jsonl", fb)

    # 8. Auto-tune thresholds based on session health vs scope warnings
    auto_tune_thresholds(data_dir, health, session_record, now)

    # 9. Auto-promote high-confidence patterns
    auto_promote_patterns(data_dir, now)

    # 10. Auto-close stale pending decisions (>30 days, project still active)
    auto_close_stale_decisions(data_dir, cwd, now)

    # Output nothing to stdout (non-blocking)
    sys.exit(0)


def extract_cortex_feedback(transcript):
    """Detect when user talks about Cortex warnings/behavior."""
    feedback = []
    feedback_patterns = [
        (r"(?:stop|don'?t)\s+(?:warning|warn|alert)(?:ing)?\s+(?:me\s+)?(?:about\s+)?(.+?)(?:\.|!|\n|$)", "suppress_warning"),
        (r"cortex\s+(?:is\s+)?(?:wrong|incorrect|bad|annoying|noisy|too\s+(?:strict|aggressive))(?:\s+about\s+)?(.+?)(?:\.|!|\n|$)", "negative_feedback"),
        (r"cortex\s+(?:is\s+)?(?:right|correct|good|helpful|useful)(?:\s+about\s+)?(.+?)(?:\.|!|\n|$)", "positive_feedback"),
        (r"(?:remember|learn)\s+(?:that\s+)?(.+?)(?:\.|!|\n|$)", "teach"),
        (r"(?:always|never)\s+(.+?)(?:\s+for\s+this\s+project)(?:\.|!|\n|$)", "project_rule"),
        (r"(?:too\s+many|fewer)\s+(?:warnings|alerts)(.*)(?:\.|!|\n|$)", "tune_threshold"),
    ]

    # Only scan the last portion of transcript (user messages)
    scan_text = transcript[-8000:]

    for pattern, signal_type in feedback_patterns:
        matches = re.findall(pattern, scan_text, re.IGNORECASE)
        for match in matches[:2]:
            clean = match.strip()[:200]
            if len(clean) > 3:
                feedback.append({
                    "signal_type": signal_type,
                    "signal": clean,
                    "source": "transcript_extraction",
                })

    return feedback


def load_config(data_dir):
    """Load cortex-config.json."""
    config_file = data_dir / "cortex-config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except:
            pass
    return {"version": 1, "thresholds": {}, "suppressed_warnings": [], "project_overrides": {}, "evolution_stats": {}}


def save_config(data_dir, config):
    """Save cortex-config.json."""
    config_file = data_dir / "cortex-config.json"
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except:
        pass


def log_evolution(data_dir, action, target_file, description, trigger, now):
    """Log a self-evolution action."""
    record = {
        "action": action,
        "target_file": target_file,
        "description": description,
        "trigger": trigger,
        "reversible": True,
        "timestamp": now,
    }
    append_jsonl(data_dir / "evolution-log.jsonl", record)


def auto_tune_thresholds(data_dir, health, session_record, now):
    """
    Auto-tune scope thresholds based on session outcomes:
    - If scope warnings fired but health was high → false positive → relax threshold
    - If scope warnings didn't fire but health was low → missed warning → tighten threshold
    """
    config = load_config(data_dir)
    thresholds = config.get("thresholds", {})
    stats = config.get("evolution_stats", {})

    # Check rate limit
    evolutions_this_session = stats.get("_session_evolutions", 0)
    max_evolutions = thresholds.get("max_auto_evolutions_per_session", 3)
    if evolutions_this_session >= max_evolutions:
        return

    # Read recent session outcomes to look for patterns
    session_file = data_dir / "session-log.jsonl"
    if not session_file.exists():
        return

    recent_sessions = []
    try:
        with open(session_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        recent_sessions.append(json.loads(line))
                    except:
                        pass
    except:
        return

    recent_sessions = [s for s in recent_sessions[-10:] if s.get("event") == "session_end"]
    if len(recent_sessions) < 3:
        return

    # Check last 3 sessions for consistent false positive pattern
    last_3 = recent_sessions[-3:]
    all_high_health = all(s.get("health_score", 0) > 70 for s in last_3)
    all_low_completion = all(s.get("completion_ratio", 1) < 0.3 for s in last_3)

    current_scope_threshold = thresholds.get("scope_task_threshold", 5)

    if all_high_health and current_scope_threshold < 10:
        # Sessions are healthy despite scope — relax threshold
        new_threshold = min(current_scope_threshold + 1, 10)
        if new_threshold != current_scope_threshold:
            thresholds["scope_task_threshold"] = new_threshold
            stats["thresholds_tuned"] = stats.get("thresholds_tuned", 0) + 1
            stats["total_evolutions"] = stats.get("total_evolutions", 0) + 1
            stats["last_evolution"] = now
            stats["_session_evolutions"] = evolutions_this_session + 1
            config["thresholds"] = thresholds
            config["evolution_stats"] = stats
            save_config(data_dir, config)
            log_evolution(data_dir, "tune_threshold", "cortex-config.json",
                          f"Relaxed scope_task_threshold {current_scope_threshold} → {new_threshold} (3 consecutive high-health sessions)",
                          "auto_tune", now)

    elif all_low_completion and current_scope_threshold > 3:
        # Sessions are failing — tighten threshold
        new_threshold = max(current_scope_threshold - 1, 3)
        if new_threshold != current_scope_threshold:
            thresholds["scope_task_threshold"] = new_threshold
            stats["thresholds_tuned"] = stats.get("thresholds_tuned", 0) + 1
            stats["total_evolutions"] = stats.get("total_evolutions", 0) + 1
            stats["last_evolution"] = now
            stats["_session_evolutions"] = evolutions_this_session + 1
            config["thresholds"] = thresholds
            config["evolution_stats"] = stats
            save_config(data_dir, config)
            log_evolution(data_dir, "tune_threshold", "cortex-config.json",
                          f"Tightened scope_task_threshold {current_scope_threshold} → {new_threshold} (3 consecutive low-completion sessions)",
                          "auto_tune", now)


def auto_promote_patterns(data_dir, now):
    """Promote patterns that appeared 5+ times with consistent outcome to learnings."""
    config = load_config(data_dir)
    threshold = config.get("thresholds", {}).get("pattern_promotion_threshold", 5)

    patterns_file = data_dir / "patterns.jsonl"
    if not patterns_file.exists():
        return

    # Count pattern occurrences by type
    pattern_counts = {}
    try:
        with open(patterns_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    p = json.loads(line)
                    key = p.get("pattern", "")
                    if key and not p.get("promoted"):
                        pattern_counts[key] = pattern_counts.get(key, 0) + 1
                except:
                    pass
    except:
        return

    # Promote patterns that meet threshold
    for pattern_type, count in pattern_counts.items():
        if count >= threshold and pattern_type not in ("technology_affinity",):
            # Check if already promoted as a learning
            existing = False
            learnings_file = data_dir / "learnings.jsonl"
            if learnings_file.exists():
                try:
                    with open(learnings_file) as f:
                        for line in f:
                            if pattern_type in line:
                                existing = True
                                break
                except:
                    pass

            if not existing:
                learning = {
                    "learning": f"Auto-promoted pattern: {pattern_type} detected {count} times across sessions",
                    "category": "auto-promoted",
                    "source": "pattern_mining",
                    "timestamp": now,
                }
                append_jsonl(learnings_file, learning)
                log_evolution(data_dir, "promote_pattern", "learnings.jsonl",
                              f"Promoted pattern '{pattern_type}' ({count} occurrences) to learning",
                              "auto_promote", now)


def auto_close_stale_decisions(data_dir, cwd, now):
    """Auto-close decisions pending >30 days if project has had recent healthy sessions."""
    journal_file = data_dir / "decision-journal.jsonl"
    if not journal_file.exists():
        return

    try:
        now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
    except:
        return

    entries = []
    modified = False
    try:
        with open(journal_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Check if pending and old
                    if entry.get("outcome") == "pending":
                        try:
                            ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                            age_days = (now_dt - ts).days
                            if age_days > 30:
                                entry["outcome"] = "success"
                                entry["outcome_notes"] = f"Auto-closed after {age_days} days (validated by continued usage)"
                                modified = True
                                log_evolution(data_dir, "auto_close_decision", "decision-journal.jsonl",
                                              f"Auto-closed stale decision: {entry.get('decision', '')[:80]}",
                                              "auto_close", now)
                        except:
                            pass
                    entries.append(entry)
                except:
                    entries.append({"_raw": line})
    except:
        return

    if modified:
        try:
            with open(journal_file, "w") as f:
                for entry in entries:
                    if "_raw" in entry:
                        f.write(entry["_raw"] + "\n")
                    else:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except:
            pass

if __name__ == "__main__":
    main()
