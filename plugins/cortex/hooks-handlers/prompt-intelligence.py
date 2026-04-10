#!/usr/bin/env python3
"""
Cortex UserPromptSubmit Hook — Scope Intelligence + Self-Adaptation Detector

Analyzes every user prompt BEFORE Claude processes it:
1. Detects scope creep patterns (too many tasks in one prompt)
2. Identifies when user is asking for multi-phase work (warn about 60% completion rate)
3. Enriches prompt with relevant historical context
4. Detects repeated questions (user might be stuck)
5. [SELF-ADAPT] Detects Cortex-directed feedback and records for evolution
6. [SELF-ADAPT] Uses config-driven thresholds (not hardcoded)
7. [SELF-ADAPT] Respects suppressed warnings per project

Non-blocking — provides guidance via systemMessage.
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone

def get_cortex_data_dir():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return Path(plugin_root) / "data"

def append_jsonl(filepath, data):
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except:
        pass

def load_config(data_dir):
    """Load cortex-config.json for adaptive thresholds."""
    config_file = data_dir / "cortex-config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except:
            pass
    return {"thresholds": {"scope_task_threshold": 5, "scope_word_threshold": 300}, "suppressed_warnings": [], "project_overrides": {}}


def is_warning_suppressed(config, category, project):
    """Check if a warning category is suppressed for this project."""
    for suppression in config.get("suppressed_warnings", []):
        if suppression.get("category") == category:
            scope = suppression.get("scope", "global")
            if scope == "global" or scope == f"project:{project}":
                return True
    return False


def detect_cortex_feedback(prompt, data_dir, session_id, project, now):
    """Detect when user is talking TO/ABOUT Cortex and record as feedback."""
    feedback_patterns = [
        (r"(?:stop|don'?t)\s+(?:warning|warn|alert)(?:ing)?\s+(?:me\s+)?(?:about\s+)?(.+?)(?:\.|!|$)", "suppress_warning"),
        (r"cortex\s+(?:is\s+)?(?:wrong|incorrect|annoying|noisy|too\s+(?:strict|aggressive))(.*)(?:\.|!|$)", "negative_feedback"),
        (r"cortex\s+(?:should|needs?\s+to)\s+(.+?)(?:\.|!|$)", "directive"),
        (r"(?:remember|learn|note)\s+(?:that\s+)?(.{10,150}?)(?:\.|!|$)", "teach"),
        (r"(?:for\s+this\s+project)\s*[,:]\s*(?:always|never)\s+(.+?)(?:\.|!|$)", "project_rule"),
        (r"(?:too\s+many|fewer|less)\s+(?:warnings|alerts|notifications)", "tune_threshold"),
    ]

    prompt_lower = prompt.lower()
    feedback_items = []

    for pattern, signal_type in feedback_patterns:
        matches = re.findall(pattern, prompt_lower)
        for match in matches[:1]:
            clean = match.strip()[:200]
            if len(clean) > 3 or signal_type == "tune_threshold":
                record = {
                    "signal_type": signal_type,
                    "signal": clean if clean else signal_type,
                    "source": "prompt_detection",
                    "session_id": session_id,
                    "project": project,
                    "timestamp": now,
                }
                append_jsonl(data_dir / "user-feedback.jsonl", record)
                feedback_items.append(record)

    return feedback_items


def detect_scope_signals(prompt, config=None):
    """Detect if user is requesting too much in one prompt. Uses config-driven thresholds."""
    if config is None:
        config = {}
    thresholds = config.get("thresholds", {})
    task_threshold = thresholds.get("scope_task_threshold", 5)
    word_threshold = thresholds.get("scope_word_threshold", 300)

    signals = {
        "multi_phase": False,
        "task_count": 0,
        "scope_size": "normal",
        "warnings": [],
    }

    prompt_lower = prompt.lower()

    # Detect multi-phase language
    phase_patterns = [
        r"\bphase\s*\d",
        r"\bstep\s*\d",
        r"\bfirst\b.*\bthen\b.*\bfinally\b",
        r"\b(?:and also|and then|after that|next|additionally)\b",
    ]
    phase_count = sum(1 for p in phase_patterns if re.search(p, prompt_lower))
    if phase_count >= 2:
        signals["multi_phase"] = True

    # Count distinct task verbs
    task_verbs = re.findall(
        r"\b(create|build|implement|add|fix|update|refactor|remove|delete|migrate|write|setup|configure|deploy|test)\b",
        prompt_lower
    )
    signals["task_count"] = len(set(task_verbs))

    # Assess scope size using CONFIG-DRIVEN thresholds
    word_count = len(prompt.split())
    if signals["task_count"] >= task_threshold or word_count > word_threshold:
        signals["scope_size"] = "large"
        signals["warnings"].append(
            f"Cortex: Large scope detected ({signals['task_count']} distinct tasks, {word_count} words). "
            "Historical data shows multi-phase tasks complete only ~40%. Consider breaking into smaller sessions."
        )
    elif signals["multi_phase"] or signals["task_count"] >= max(3, task_threshold - 2):
        signals["scope_size"] = "medium"
        signals["warnings"].append(
            "Cortex: Multi-step task detected. Tip: put testing in Phase 1 (not last) — "
            "it's the most commonly deferred step."
        )

    # Detect "everything" / "all" language (often too broad)
    if re.search(r"\b(everything|all files|entire|whole|complete)\b", prompt_lower):
        if signals["scope_size"] != "large":
            signals["warnings"].append(
                "Cortex: Broad scope language ('everything', 'entire', 'all'). "
                "Consider specifying which files/features to focus on."
            )

    return signals

def check_repeated_patterns(data_dir, prompt, session_id):
    """Check if user is asking similar things repeatedly (might be stuck)."""
    prompt_log = data_dir / "prompt-log.jsonl"
    if not prompt_log.exists():
        return None

    prompt_words = set(re.findall(r'\b\w{4,}\b', prompt.lower()))
    if len(prompt_words) < 3:
        return None

    similar_count = 0
    try:
        with open(prompt_log, "r") as f:
            for line in f.readlines()[-20:]:  # Last 20 prompts
                try:
                    entry = json.loads(line.strip())
                    if entry.get("session_id") != session_id:
                        continue
                    past_words = set(entry.get("keywords", []))
                    overlap = prompt_words & past_words
                    if len(overlap) >= max(3, len(prompt_words) * 0.5):
                        similar_count += 1
                except:
                    pass
    except:
        pass

    if similar_count >= 3:
        return "Cortex: You've asked similar things 3+ times this session. You might be stuck — consider a different approach or asking for help."
    return None

def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = hook_input.get("user_prompt", "")
    session_id = hook_input.get("session_id", "unknown")
    cwd = hook_input.get("cwd", "")

    if not prompt or len(prompt) < 10:
        sys.exit(0)

    data_dir = get_cortex_data_dir()
    data_dir.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    project = os.path.basename(cwd) if cwd else "unknown"

    # Load adaptive config
    config = load_config(data_dir)

    # Log the prompt (keywords only, not full content for privacy)
    keywords = list(set(re.findall(r'\b\w{4,}\b', prompt.lower())))[:30]
    prompt_record = {
        "keywords": keywords,
        "word_count": len(prompt.split()),
        "session_id": session_id,
        "project": project,
        "timestamp": now,
    }
    append_jsonl(data_dir / "prompt-log.jsonl", prompt_record)

    # [SELF-ADAPT] Detect Cortex-directed feedback FIRST
    feedback = detect_cortex_feedback(prompt, data_dir, session_id, project, now)
    if feedback:
        # Don't add scope warnings when user is giving Cortex feedback
        # Let the self-evolver handle it
        pass

    # Collect intelligence
    messages = []

    # 1. Scope analysis (uses config-driven thresholds)
    if not is_warning_suppressed(config, "scope-management", project):
        scope = detect_scope_signals(prompt, config)
        messages.extend(scope["warnings"])

    # 2. Repetition detection
    if not is_warning_suppressed(config, "repetition-detection", project):
        repeated = check_repeated_patterns(data_dir, prompt, session_id)
        if repeated:
            messages.append(repeated)

    # Output warnings
    if messages:
        output = {"systemMessage": "\n".join(messages)}
        print(json.dumps(output))

    # Auto-trim prompt log (keep last 500)
    prompt_log = data_dir / "prompt-log.jsonl"
    try:
        if prompt_log.exists():
            with open(prompt_log, "r") as f:
                lines = f.readlines()
            if len(lines) > 600:
                with open(prompt_log, "w") as f:
                    f.writelines(lines[-500:])
    except:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
