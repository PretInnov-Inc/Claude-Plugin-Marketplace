---
description: "Run verification loop — the Clamp. Verifies code changes against project standards, tests, and security."
argument-hint: "[file-path or 'all' or 'last']"
---

You are executing the `/clamp` command — Clamper's core verification loop.

## Behavior Based on Arguments

**`/clamp` (no args)** — Verify the most recently edited files in this session:
1. Check the conversation for files modified via Edit/Write/MultiEdit
2. Collect the last 3-5 modified files
3. Delegate to the `clamper-verifier` agent with those files

**`/clamp <file-path>`** — Verify a specific file:
1. Delegate to `clamper-verifier` agent targeting that specific file
2. Include surrounding context (imports, callers, tests)

**`/clamp all`** — Full project verification:
1. Identify all files modified in this session
2. Delegate to `clamper-verifier` agent with the full list
3. Request a comprehensive report

**`/clamp last`** — Re-verify the last verification's files:
1. Read `${CLAUDE_PLUGIN_ROOT}/data/verification-log.jsonl`
2. Find the most recent verification event
3. Re-run verification on those same files

## Execution

When delegating to `clamper-verifier`, always provide:
- The file paths to verify
- The project's detected stack (from package.json, pyproject.toml, etc.)
- Any recent test results from the conversation
- The current working directory

## After Verification

1. Log the result to `${CLAUDE_PLUGIN_ROOT}/data/verification-log.jsonl`:
   ```json
   {
     "event": "verification_passed|verification_failed",
     "files": ["<paths>"],
     "confidence": <0-100>,
     "issues": ["<if any>"],
     "session_id": "<id>",
     "timestamp": "<iso>"
   }
   ```

2. If confidence < 80: clearly state "FLAGGED FOR HUMAN REVIEW" and explain why

3. If confidence >= 80: report PASS with the score

4. Always end with a one-line summary:
   `Clamped. <N> files verified, confidence <score>/100.`
