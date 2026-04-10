"""Clamper Outcome Store — Persistent outcome pattern database via MCP.

The Cerebellum: stores, queries, and analyzes verification outcomes
to learn what succeeds and what fails across sessions.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("clamper-outcomes")

DATA_DIR = os.environ.get(
    "CLAMPER_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
)


def _read_jsonl(filepath: str, limit: int = 0) -> list[dict]:
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
    return entries[-limit:] if limit else entries


def _append_jsonl(filepath: str, data: dict):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a") as f:
        f.write(json.dumps(data) + "\n")


@mcp.tool
async def record_verification(
    files: list[str],
    confidence: int,
    passed: bool,
    issues: list[str] | None = None,
    project: str = "unknown",
    session_id: str = "unknown"
) -> dict:
    """Record a verification outcome for learning.

    Args:
        files: List of file paths that were verified
        confidence: Confidence score 0-100
        passed: Whether verification passed
        issues: List of issues found (if any)
        project: Project name
        session_id: Current session ID
    """
    record = {
        "event": "verification_passed" if passed else "verification_failed",
        "files": files,
        "confidence": confidence,
        "issues": issues or [],
        "project": project,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    _append_jsonl(os.path.join(DATA_DIR, "verification-log.jsonl"), record)
    _append_jsonl(os.path.join(DATA_DIR, "outcomes.jsonl"), record)

    # Update config stats
    config_path = os.path.join(DATA_DIR, "clamper-config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        stats = config.get("verification_stats", {})
        stats["total_verifications"] = stats.get("total_verifications", 0) + 1
        if passed:
            stats["passed"] = stats.get("passed", 0) + 1
        else:
            stats["failed"] = stats.get("failed", 0) + 1
        if confidence < 80:
            stats["flagged_for_review"] = stats.get("flagged_for_review", 0) + 1
        stats["last_verification"] = record["timestamp"]
        config["verification_stats"] = stats
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    return {"status": "recorded", "event": record["event"], "confidence": confidence}


@mcp.tool
async def query_outcomes(
    project: str | None = None,
    event_type: str | None = None,
    limit: int = 20
) -> list[dict]:
    """Query verification and session outcomes.

    Args:
        project: Filter by project name (optional)
        event_type: Filter by event type: verification_passed, verification_failed, session_end (optional)
        limit: Max results to return
    """
    outcomes = _read_jsonl(os.path.join(DATA_DIR, "outcomes.jsonl"))

    if project:
        outcomes = [o for o in outcomes if o.get("project") == project]
    if event_type:
        outcomes = [o for o in outcomes if o.get("event") == event_type]

    return outcomes[-limit:]


@mcp.tool
async def get_quality_trend(sessions: int = 10) -> dict:
    """Analyze session quality trend over recent sessions.

    Args:
        sessions: Number of recent sessions to analyze
    """
    outcomes = _read_jsonl(os.path.join(DATA_DIR, "outcomes.jsonl"))
    session_ends = [o for o in outcomes if o.get("event") == "session_end"]

    if not session_ends:
        return {"trend": "no_data", "sessions_analyzed": 0}

    recent = session_ends[-sessions:]
    scores = [s.get("quality_score", 0) for s in recent]
    avg = sum(scores) / len(scores) if scores else 0

    # Trend: compare first half vs second half
    mid = len(scores) // 2
    if mid > 0:
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        if second_half > first_half + 5:
            trend = "improving"
        elif second_half < first_half - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Verification stats
    verifications = _read_jsonl(os.path.join(DATA_DIR, "verification-log.jsonl"))
    ver_events = [v for v in verifications if v.get("event") in ("verification_passed", "verification_failed")]
    ver_passed = len([v for v in ver_events if v.get("event") == "verification_passed"])
    ver_total = len(ver_events)

    return {
        "trend": trend,
        "sessions_analyzed": len(recent),
        "average_quality": round(avg, 1),
        "scores": scores,
        "verification_pass_rate": f"{ver_passed}/{ver_total}" if ver_total else "0/0",
        "test_run_rate": f"{sum(1 for s in recent if s.get('tests_run'))}/{len(recent)}"
    }


@mcp.tool
async def get_fragile_file_history(file_path: str) -> dict:
    """Get the verification and churn history for a specific file.

    Args:
        file_path: The file path to look up
    """
    ver_log = _read_jsonl(os.path.join(DATA_DIR, "verification-log.jsonl"))
    dna_cache = _read_jsonl(os.path.join(DATA_DIR, "dna-cache.jsonl"))

    # Edits to this file
    edits = [e for e in ver_log if e.get("file_path") == file_path and e.get("event") == "edit_tracked"]

    # Verifications involving this file
    verifications = [
        e for e in ver_log
        if e.get("event") in ("verification_passed", "verification_failed")
        and file_path in (e.get("files") or [])
    ]

    # DNA patterns for this file
    dna_patterns = [e for e in dna_cache if e.get("file_path") == file_path]

    return {
        "file_path": file_path,
        "total_edits_tracked": len(edits),
        "risk_signals_seen": list(set(
            sig for e in edits for sig in e.get("risk_signals", [])
        )),
        "verifications": len(verifications),
        "verification_pass_rate": (
            f"{sum(1 for v in verifications if v.get('event') == 'verification_passed')}/{len(verifications)}"
            if verifications else "no verifications"
        ),
        "dna_patterns": dna_patterns[-5:],
        "churn_events": len([e for e in ver_log if e.get("event") == "churn_detected" and e.get("file_path") == file_path])
    }
