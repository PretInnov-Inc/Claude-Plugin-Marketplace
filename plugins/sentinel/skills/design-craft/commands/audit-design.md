# Design Craft Command: audit-design

## Purpose
Check for drift between `.sentinel/design-system.md` (spec) and current codebase (reality).
Delegates to `design-auditor` agent for systematic file-by-file comparison.

## When to Use
- User says "audit design drift", "check design consistency", "are we drifting from the spec?"
- After a sprint of UI work to catch inconsistencies before they spread
- Periodically as a maintenance task on design-heavy projects

## Process

### 1. Verify Spec Exists
```bash
cat .sentinel/design-system.md 2>/dev/null | head -5
```
If missing: "No design-system.md found. Run `/design-craft extract` first."

### 2. Find Recently Changed UI Files
```bash
# Git projects
git diff --name-only HEAD~10..HEAD 2>/dev/null | grep -E "\.(tsx|jsx|vue|css|scss)$"

# Or all UI files if no git
find . -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.css" \
  | grep -v node_modules | head -30
```

### 3. Launch design-auditor

Pass the agent:
- The full `.sentinel/design-system.md` content
- The list of UI files to check
- Instruction to produce the drift report with CRITICAL/WARNING/PASSED classification

### 4. After Agent Returns

Present the drift report. If drift is found:
- Offer to fix violations (route to style-writer with specific files + the spec)
- Offer to update the spec if the drift is intentional (route to update `.sentinel/design-system.md`)

## Return Protocol
- **DONE** — Audit complete, [N] files clean.
- **DONE_WITH_CONCERNS** — [N] drift violations found. See report above.
- **NEEDS_CONTEXT** — No design-system.md or no UI files found.
