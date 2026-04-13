#!/usr/bin/env python3
"""
Sentinel PostToolUse Hook — Output Compressor (Category E / v3)

Fires after every Edit/Write/MultiEdit (debounced — every Nth call).
If the tool result output exceeds threshold_chars, compresses it:
  - JSON tool results: extract key fields only
  - Log output: truncate with summary
  - HTML: strip tags, keep text
  - General: first+last 200 chars + "... [N chars compressed]"

Logs savings to data/compression.jsonl. Claims ~7k tokens/session.

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
    return Path(get_plugin_root()) / "data"


def load_config():
    config_path = get_data_dir() / "sentinel-config.json"
    defaults = {
        "compression": {
            "enabled": True,
            "threshold_chars": 3000,
            "debounce_every_n_calls": 3,
            "log_savings": True
        }
    }
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            defaults["compression"].update(cfg.get("compression", {}))
        except Exception:
            pass
    return defaults["compression"]


def get_call_counter_path(session_id: str) -> Path:
    state_dir = Path(os.path.expanduser("~/.claude"))
    state_dir.mkdir(exist_ok=True)
    return state_dir / f"sentinel_compress_counter_{session_id}.json"


def get_and_increment_counter(session_id: str, reset_every: int) -> int:
    """Returns counter before increment. Resets at reset_every."""
    path = get_call_counter_path(session_id)
    count = 0
    if path.exists():
        try:
            count = int(json.loads(path.read_text()).get("count", 0))
        except Exception:
            count = 0
    new_count = (count + 1) % reset_every
    try:
        path.write_text(json.dumps({"count": new_count, "updated": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass
    return count


def compress_json(content: str, max_chars: int) -> tuple[str, int]:
    """Try to parse as JSON and extract a summary."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            summary = f"[JSON array: {len(data)} items. First: {json.dumps(data[0])[:200] if data else 'empty'}]"
        elif isinstance(data, dict):
            keys = list(data.keys())
            summary = f"[JSON object: keys={keys[:10]}, {len(content)} chars total]"
        else:
            summary = f"[JSON value: {str(data)[:200]}]"
        return summary, len(content) - len(summary)
    except Exception:
        return content[:max_chars] + f"\n... [{len(content) - max_chars} chars compressed]", len(content) - max_chars


def compress_html(content: str, max_chars: int) -> tuple[str, int]:
    """Strip HTML tags and return text only."""
    text = re.sub(r'<[^>]+>', '', content)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_chars:
        return text, len(content) - len(text)
    compressed = text[:max_chars] + f"\n... [HTML stripped, {len(content)} raw chars]"
    return compressed, len(content) - len(compressed)


def compress_log(content: str, max_chars: int) -> tuple[str, int]:
    """Keep first and last N lines of log output."""
    lines = content.split('\n')
    if len(lines) <= 20:
        return content, 0
    kept = lines[:10] + [f"... [{len(lines) - 20} lines omitted] ..."] + lines[-10:]
    compressed = '\n'.join(kept)
    return compressed, len(content) - len(compressed)


def compress_content(content: str, threshold: int) -> tuple[str, int]:
    """Detect content type and compress appropriately."""
    if len(content) <= threshold:
        return content, 0

    stripped = content.lstrip()

    # JSON
    if stripped.startswith(('{', '[')):
        return compress_json(content, threshold)

    # HTML
    if stripped.lower().startswith('<!doctype') or stripped.startswith('<html') or '<body' in stripped[:200]:
        return compress_html(content, threshold)

    # Log-like (many short lines with timestamps or level markers)
    lines = content.split('\n')
    if len(lines) > 20 and any(
        re.search(r'\d{2}:\d{2}|\b(INFO|DEBUG|ERROR|WARN|WARNING)\b', l)
        for l in lines[:5]
    ):
        return compress_log(content, threshold)

    # Generic: first+last
    half = threshold // 2
    compressed = content[:half] + f"\n... [{len(content) - threshold} chars compressed] ...\n" + content[-half:]
    return compressed, len(content) - len(compressed)


def log_savings(data_dir: Path, session_id: str, original: int, compressed_to: int, saved: int):
    log_path = data_dir / "compression.jsonl"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "event": "compression",
                "session_id": session_id,
                "original_chars": original,
                "compressed_chars": compressed_to,
                "saved_chars": saved,
                "saved_pct": round(saved / original * 100, 1) if original else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }) + "\n")
    except Exception:
        pass


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cfg = load_config()
    if not cfg.get("enabled", True):
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    debounce = cfg.get("debounce_every_n_calls", 3)
    threshold = cfg.get("threshold_chars", 3000)

    # Debounce: only compress every Nth call
    counter = get_and_increment_counter(session_id, debounce)
    if counter != 0:
        sys.exit(0)

    # Get tool output from hook input
    tool_result = hook_input.get("tool_response", {})
    if not isinstance(tool_result, dict):
        sys.exit(0)

    content = tool_result.get("content", "")
    if not isinstance(content, str):
        # Handle list of content blocks
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") for c in content if isinstance(c, dict)
            )
        else:
            sys.exit(0)

    if len(content) <= threshold:
        sys.exit(0)

    original_len = len(content)
    compressed, saved = compress_content(content, threshold)

    if saved <= 0:
        sys.exit(0)

    # Log savings
    data_dir = get_data_dir()
    data_dir.mkdir(exist_ok=True)
    if cfg.get("log_savings", True):
        log_savings(data_dir, session_id, original_len, len(compressed), saved)

    # Return compressed content as additionalContext
    savings_pct = round(saved / original_len * 100, 1)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[SENTINEL COMPRESSOR: {original_len:,} → {len(compressed):,} chars, "
                f"{savings_pct}% saved]\n\n{compressed}"
            )
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
