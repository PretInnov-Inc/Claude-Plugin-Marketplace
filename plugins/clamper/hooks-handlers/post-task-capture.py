#!/usr/bin/env python3
"""Clamper Stop Hook — Outcome capture after task/session completion.

Extracts verification outcomes, project DNA updates, and learning patterns
from the completed session. Feeds the Cerebellum (outcome pattern store).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_clamper_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return os.path.join(plugin_root, "data")
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def append_jsonl(filepath, data):
    with open(filepath, "a") as f:
        f.write(json.dumps(data) + "\n")


def read_jsonl_tail(filepath, n=100):
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


def load_config(data_dir):
    config_path = os.path.join(data_dir, "clamper-config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(data_dir, config):
    config_path = os.path.join(data_dir, "clamper-config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def read_transcript_tail(transcript_path, max_chars=20000):
    """Read the tail of the session transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        with open(transcript_path, "r", errors="replace") as f:
            content = f.read()
        return content[-max_chars:] if len(content) > max_chars else content
    except Exception:
        return ""


def extract_session_outcomes(transcript):
    """Extract verification outcomes and patterns from session transcript."""
    outcomes = {
        "verifications_run": 0,
        "verifications_passed": 0,
        "verifications_failed": 0,
        "tests_run": False,
        "tests_passed": False,
        "files_modified": [],
        "errors_encountered": [],
        "risk_signals_seen": [],
        "churn_files": []
    }

    if not transcript:
        return outcomes

    # Count verification mentions
    clamp_runs = len(re.findall(r"/clamp|clamper.*verif|verification.*(?:pass|fail)", transcript, re.I))
    outcomes["verifications_run"] = clamp_runs

    # Detect test execution
    test_patterns = [
        r"(?:pytest|jest|mocha|cargo test|go test|npm test|yarn test)",
        r"(?:\d+ passed|tests? passed|all tests? pass)",
        r"(?:PASSED|FAILED|ERROR).*test"
    ]
    for pattern in test_patterns:
        if re.search(pattern, transcript, re.I):
            outcomes["tests_run"] = True
            break

    if re.search(r"(?:all )?tests? passed|0 failed|\d+ passed, 0 failed", transcript, re.I):
        outcomes["tests_passed"] = True

    # Extract file paths modified
    file_paths = re.findall(r'file_path["\s:]+([/\w._-]+\.\w+)', transcript[-10000:])
    outcomes["files_modified"] = list(set(file_paths))[:30]

    # Extract errors
    error_lines = re.findall(r'(?:Error|Exception|FAILED|error\[).*', transcript[-10000:])
    outcomes["errors_encountered"] = error_lines[:10]

    # Extract churn warnings
    churn_matches = re.findall(r'CLAMPER CHURN.*?(\S+)\s+has been edited (\d+) times', transcript)
    for file_path, count in churn_matches:
        outcomes["churn_files"].append({"file": file_path, "edits": int(count)})

    # Extract risk signals
    risk_matches = re.findall(r'CLAMPER (?:HIGH|MEDIUM) RISK.*?\[(.*?)\]', transcript)
    for signals in risk_matches:
        outcomes["risk_signals_seen"].extend(s.strip() for s in signals.split(","))

    return outcomes


def calculate_session_quality(outcomes):
    """Score session quality 0-100 based on verification outcomes."""
    score = 60  # baseline

    # Tests run and passed: big positive
    if outcomes["tests_run"]:
        score += 15
        if outcomes["tests_passed"]:
            score += 10

    # Files modified without errors: positive
    files_count = len(outcomes["files_modified"])
    if files_count > 0 and not outcomes["errors_encountered"]:
        score += min(files_count * 2, 15)

    # Errors: negative
    error_count = len(outcomes["errors_encountered"])
    score -= min(error_count * 5, 25)

    # Churn: negative (indicates thrashing)
    churn_count = len(outcomes["churn_files"])
    score -= min(churn_count * 8, 20)

    # High risk signals without verification: negative
    if outcomes["risk_signals_seen"] and outcomes["verifications_run"] == 0:
        score -= 10

    return max(0, min(100, score))


def extract_learnable_patterns(outcomes, session_id, now):
    """Extract patterns worth remembering from this session."""
    patterns = []

    # Churn pattern — files that got thrashed are fragile
    for churn in outcomes["churn_files"]:
        patterns.append({
            "pattern": "file_churn",
            "detail": f"{churn['file']} required {churn['edits']} edits in one session — likely fragile or poorly understood",
            "file_path": churn["file"],
            "session_id": session_id,
            "timestamp": now
        })

    # Risk signal clustering
    if outcomes["risk_signals_seen"]:
        from collections import Counter
        signal_counts = Counter(outcomes["risk_signals_seen"])
        for signal, count in signal_counts.most_common(3):
            if count >= 2:
                patterns.append({
                    "pattern": "recurring_risk",
                    "detail": f"Risk signal '{signal}' appeared {count} times — this session touched sensitive areas repeatedly",
                    "signal": signal,
                    "count": count,
                    "session_id": session_id,
                    "timestamp": now
                })

    # Testing discipline
    if outcomes["files_modified"] and not outcomes["tests_run"]:
        patterns.append({
            "pattern": "untested_changes",
            "detail": f"Modified {len(outcomes['files_modified'])} files without running any tests",
            "files": outcomes["files_modified"][:10],
            "session_id": session_id,
            "timestamp": now
        })

    return patterns


def update_verification_stats(config, outcomes):
    """Update running verification statistics."""
    stats = config.get("verification_stats", {
        "total_verifications": 0, "passed": 0, "failed": 0,
        "flagged_for_review": 0, "last_verification": None
    })
    stats["total_verifications"] += outcomes["verifications_run"]
    stats["passed"] += outcomes["verifications_passed"]
    stats["failed"] += outcomes["verifications_failed"]
    config["verification_stats"] = stats
    return config


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())

    data_dir = get_clamper_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    config = load_config(data_dir)
    now = datetime.now(timezone.utc).isoformat()

    # Read transcript and extract outcomes
    transcript = read_transcript_tail(transcript_path)
    outcomes = extract_session_outcomes(transcript)
    quality_score = calculate_session_quality(outcomes)

    # Record session outcome
    session_record = {
        "event": "session_end",
        "session_id": session_id,
        "project": os.path.basename(cwd),
        "quality_score": quality_score,
        "files_modified": len(outcomes["files_modified"]),
        "errors": len(outcomes["errors_encountered"]),
        "tests_run": outcomes["tests_run"],
        "tests_passed": outcomes["tests_passed"],
        "churn_files": len(outcomes["churn_files"]),
        "verifications_run": outcomes["verifications_run"],
        "timestamp": now
    }
    append_jsonl(os.path.join(data_dir, "outcomes.jsonl"), session_record)

    # Extract and store learnable patterns
    patterns = extract_learnable_patterns(outcomes, session_id, now)
    for pattern in patterns:
        append_jsonl(os.path.join(data_dir, "dna-cache.jsonl"), pattern)

    # Update config stats
    config = update_verification_stats(config, outcomes)
    config["verification_stats"]["last_verification"] = now
    save_config(data_dir, config)

    sys.exit(0)


if __name__ == "__main__":
    main()
