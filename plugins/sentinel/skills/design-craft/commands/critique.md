# Design Craft Command: critique

## Purpose
Post-implementation critique of newly written UI components against the design-system spec.
Run immediately after style-writer finishes to catch spec violations before they land.

## When to Use
- Automatically after style-writer implements components
- User says "critique this component", "check this against the spec", "post-build review"

## Process

### 1. Identify Recently Implemented Files
```bash
# From git
git diff --name-only HEAD 2>/dev/null | grep -E "\.(tsx|jsx|vue|css|scss)$"

# Or files explicitly passed
```

### 2. Load the Spec
```bash
cat .sentinel/design-system.md 2>/dev/null
```

### 3. Compare Implementation vs Spec

For each implemented file, check:

**Token adherence** (same as audit-design):
- Hardcoded colors instead of tokens?
- Raw spacing values instead of scale?
- Direct font values instead of typography tokens?

**Component API contract:**
- Does the implementation match the prop API in the spec?
- Are all required variants implemented?
- Are there additional variants not in the spec (spec drift)?

**Accessibility (quick check):**
- Interactive elements use semantic HTML?
- ARIA attributes where needed?
- Focus styles present?

**Pattern conformance:**
- Does the component follow the naming conventions in the spec?
- Is the file structure consistent with existing components?

### 4. Critique Report

```
DESIGN CRAFT CRITIQUE
=====================
Implementation: [component or file list]
Spec: .sentinel/design-system.md

SPEC VIOLATIONS (must fix):
  [file:line] — [violation + spec reference]
  Fix: [specific change]

MISSING VARIANTS (spec requires these):
  [variant name] — not implemented

EXTRA VARIANTS (not in spec — add to spec or remove):
  [variant name]

ACCESSIBILITY GAPS:
  [file:line] — [issue]

CONFORMING:
  ✓ [what matches the spec]

VERDICT: [APPROVED | NEEDS_FIXES | SPEC_UPDATE_NEEDED]
```

If NEEDS_FIXES: route to style-writer with specific file + fix list
If SPEC_UPDATE_NEEDED: ask user if the new variant should be added to spec, then update `.sentinel/design-system.md`

## Return Protocol
- **DONE** — Component approved, matches spec.
- **DONE_WITH_CONCERNS** — [N] violations found. Must fix before merging.
- **NEEDS_CONTEXT** — No spec file or no implemented files to critique.
