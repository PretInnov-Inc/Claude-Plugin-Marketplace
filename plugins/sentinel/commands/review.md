---
description: "Full code review using 6 specialized agents with adaptive confidence scoring. Works with or without git."
argument-hint: "[files|mode] — files to review, or mode: full|quick|security|quality|tests"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Agent", "TodoWrite"]
---

# Sentinel Full Review

Run a comprehensive code review using specialized agents, each focusing on a different aspect of code quality. **Works with or without git.**

**Arguments:** "$ARGUMENTS"

## Review Workflow

### Step 1: Detect Scope

Determine what files to review using the scope detector:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks-handlers/scope_detector.py" --session-id "$SESSION_ID"
```

This returns JSON with `mode` (git/file-tracking/explicit) and `files` to review.

**If user specified files in arguments**: pass them as `--explicit-files file1 file2 ...`

**If no files and no git**: Read `${CLAUDE_PLUGIN_ROOT}/data/edit-log.jsonl` to find files edited this session.

**If no files anywhere**: Tell the user "No files to review. Specify files or make some changes first."

### Step 2: Determine Review Mode

Parse arguments for mode keywords:
- **full** (default) — All 6 agents
- **quick** — sentinel-reviewer + bug-hunter only
- **security** — security-scanner + error-auditor only
- **quality** — sentinel-reviewer + code-polisher only
- **tests** — test-analyzer only

### Step 3: Load Adaptive Thresholds

Read `${CLAUDE_PLUGIN_ROOT}/data/sentinel-config.json` to get per-agent confidence thresholds.

Read `${CLAUDE_PLUGIN_ROOT}/data/edit-log.jsonl` to check for adaptive adjustments:
- Count `threshold_lowered` events (user asked for more detail) → lower threshold by decay_rate per event
- Count `threshold_raised` events (user dismissed findings) → raise threshold by decay_rate per event
- Clamp between min_threshold and max_threshold

### Step 4: Launch Review Agents

Based on the mode, launch the appropriate agents. **Launch independent agents in parallel** for speed.

For each agent, provide in the prompt:
1. The file paths to review
2. The scope detection mode (git/file-tracking/explicit)
3. The current adaptive confidence threshold for that agent
4. Whether git is available (for agents that can use git blame/log)

**Full mode agent sequence:**
- **Parallel batch 1** (independent analysis):
  - `sentinel-reviewer` — general quality + CLAUDE.md compliance
  - `bug-hunter` — logic errors, null handling, race conditions
  - `error-auditor` — silent failures, empty catches
  - `security-scanner` — security vulnerabilities
  - `test-analyzer` — test coverage gaps
- **Sequential after batch 1** (uses review results):
  - `code-polisher` — simplification pass (only if other agents found no critical issues)

### Step 5: Aggregate Results

Collect all agent reports and merge into a unified report:

```markdown
# Sentinel Review Report
========================
Scope: [git / file-tracking / explicit] — [N files]
Mode: [full / quick / security / quality / tests]
Confidence thresholds: [per-agent values]

## Critical Issues (must fix)
- [agent-name] [file:line] (confidence: N) — Description

## Important Issues (should fix)
- [agent-name] [file:line] (confidence: N) — Description

## Suggestions (consider)
- [agent-name] [file:line] (confidence: N) — Description

## Strengths
- [what's well-done]

## Test Coverage
- [gaps identified by test-analyzer]

## Security Posture
- [findings from security-scanner]

## Action Plan
1. Fix critical issues first
2. Address important issues
3. Consider suggestions
4. Re-run: /sentinel:review to verify fixes
```

### Step 6: Log Review Outcome

Append to `${CLAUDE_PLUGIN_ROOT}/data/edit-log.jsonl`:

```json
{
  "event": "review_completed",
  "mode": "[full/quick/security/quality/tests]",
  "scope_mode": "[git/file-tracking/explicit]",
  "files_reviewed": ["..."],
  "agents_run": ["..."],
  "issues_found": {"critical": N, "important": N, "suggestions": N},
  "thresholds_used": {"agent": N, ...},
  "timestamp": "ISO"
}
```

## Usage Examples

```
/sentinel:review                    # Full review of all changes
/sentinel:review quick              # Fast review (reviewer + bug-hunter)
/sentinel:review security           # Security-focused review
/sentinel:review src/auth.py        # Review specific file
/sentinel:review tests              # Test coverage analysis only
/sentinel:review quality src/       # Quality + polish for a directory
```

## Adaptive Threshold Interaction

After presenting results, if the user:
- Says "show more" / "lower threshold" / "what else?" → Log `threshold_lowered` event, re-run with threshold - 5
- Dismisses findings / says "too noisy" / "false positive" → Log `threshold_raised` event, threshold + 5 for that agent next time

This makes the system learn the user's signal-to-noise preference over time.
