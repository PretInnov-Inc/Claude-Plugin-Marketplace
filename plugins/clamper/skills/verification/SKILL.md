---
name: verification
version: 1.0.0
description: "Clamper verification loop — proof-of-work quality gate for code changes. The thing Claude Code is missing."
triggers:
  - "verify this"
  - "check this code"
  - "is this correct"
  - "run verification"
  - "clamp this"
  - "proof of work"
  - "quality check"
  - "does this look right"
---

# Clamper Verification Skill

## Purpose

Claude Code generates code but doesn't verify its own output. Clamper's verification loop ("The Clamp") fills this gap with a structured proof-of-work process that catches issues before they compound.

## Verification Framework

### Risk Classification

Every code change falls into one of four risk tiers:

| Tier | Risk | Examples | Verification Level |
|------|------|----------|-------------------|
| 1 | Low | Comments, docs, formatting | Style check only |
| 2 | Medium | Business logic, new functions | Tests + imports + style |
| 3 | High | Auth, security, config, build | Full verification + security scan |
| 4 | Critical | Database migrations, API changes, deployments | Full + human review required |

### 5-Step Verification Protocol

**Step 1: Scope** — What changed and what could break?
- List modified files
- Map import/dependency chain from each file
- Identify downstream consumers

**Step 2: Correctness** — Does the code do what it claims?
- Read the actual code (never assume)
- Verify imports resolve to real exports: `grep -r "export.*functionName" --include="*.ts"`
- Check types match (if typed language)
- Verify error paths are handled

**Step 3: Tests** — Does evidence support correctness?
- Run relevant test suite
- If no tests exist, FLAG as coverage gap
- Check test assertions actually test the changed behavior (not just "it doesn't throw")

**Step 4: Security** — Is it safe?
- Hardcoded secrets: `grep -rn "api_key\|secret\|password\|token" <file>`
- SQL injection: raw string concatenation in queries
- XSS: unsanitized user input in HTML output
- Command injection: user input in shell commands
- Auth bypass: removed or weakened permission checks

**Step 5: Score** — Confidence rating 0-100:

| Score | Meaning | Action |
|-------|---------|--------|
| 90-100 | All checks pass, tests green | Accept |
| 80-89 | Minor style issues, tests pass | Accept with notes |
| 60-79 | Missing tests or minor concerns | Flag for review |
| 40-59 | Failing tests or security concerns | Reject, fix required |
| 0-39 | Critical issues found | Reject, immediate fix |

### Common Verification Failures (from historical data)

1. **Import ghosts** (~30% of failures): Code imports a function that doesn't exist in the target module. Always grep for the actual export.

2. **Untested paths** (~25%): New code added without corresponding tests. The "tests pass" signal is meaningless if tests don't cover the change.

3. **Config cascade** (~20%): Changing package.json, tsconfig, or pyproject.toml without checking downstream effects. Build may break in ways not caught by unit tests.

4. **Security blindspots** (~15%): Auth-adjacent code changes that don't get security review. Any file with "auth", "session", "token", "permission" in the path needs extra scrutiny.

5. **Type drift** (~10%): In TypeScript/Python projects, changes that break type contracts caught only at runtime.

## Data Files

Verification results are stored in `${CLAUDE_SKILL_DIR}/../../data/verification-log.jsonl`.

## Integration

- **Hook trigger**: PostToolUse on Edit/Write/MultiEdit fires `post-edit-verify.py` which detects risk signals
- **Manual trigger**: `/clamp` command runs full verification via `clamper-verifier` agent
- **Session capture**: Stop hook captures verification outcomes for pattern learning
