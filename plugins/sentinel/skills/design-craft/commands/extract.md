# Design Craft Command: extract

## Purpose
Reverse-engineer the current codebase to produce `.sentinel/design-system.md`.
Run when a project has existing UI but no documented design system.

## When to Use
- User says "extract design system", "generate design-system.md", "document my UI patterns"
- Starting design-craft work on an existing codebase without a design spec
- After inheriting a codebase with undocumented UI conventions

## Process

### 1. Stack Detection
```bash
# Framework
cat package.json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
deps={**d.get('dependencies',{}),**d.get('devDependencies',{})}
keys=[k for k in deps if any(f in k for f in ['react','vue','svelte','next','nuxt','tailwind','styled','emotion'])]
print(keys)
" 2>/dev/null

# Styling approach
ls tailwind.config.* 2>/dev/null && echo "tailwind"
grep -q "styled-components\|@emotion" package.json 2>/dev/null && echo "css-in-js"
ls src/**/*.module.css 2>/dev/null | head -1 | grep -q . && echo "css-modules"
```

### 2. Token Extraction

**Colors (from CSS variables or Tailwind config):**
```bash
grep -rn "var(--color\|--color-" --include="*.css" --include="*.scss" --include="*.ts" . 2>/dev/null | head -30
cat tailwind.config.* 2>/dev/null | head -50
```

**Spacing:**
```bash
grep -rn "var(--spacing\|--space-" --include="*.css" . 2>/dev/null | head -10
# or extract from Tailwind theme
```

**Typography:**
```bash
grep -rn "font-family\|font-size\|--font-" --include="*.css" . 2>/dev/null | head -20
```

### 3. Component Pattern Extraction
```bash
# Find all component files
find . -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" \) \
  | grep -v node_modules | grep -v ".test." | head -30

# Find variant patterns
grep -rn "variant=\|size=\|color=" --include="*.tsx" --include="*.jsx" . \
  | grep -v node_modules | head -20
```

### 4. Write .sentinel/design-system.md

Output format:
```markdown
---
version: 1.0.0
extracted_from: [project name]
date: [YYYY-MM-DD]
stack: [React/Vue/etc + Tailwind/CSS modules/etc]
---

# Design System

## Color Tokens
| Token | Value | Usage |
|-------|-------|-------|
| [name] | [value] | [primary/secondary/neutral/semantic] |

## Typography
| Token | Value | Usage |
|-------|-------|-------|
| [name] | [value] | [heading/body/mono] |

## Spacing Scale
Base unit: [N]px
| Class/Token | Value |
|-------------|-------|
| [name] | [value] |

## Component Patterns

### [Component Name]
Props API:
- variant: [option1 | option2 | option3]
- size: [sm | md | lg]
- [prop]: [description]

Naming convention: [what convention is used]

### [Component Name]
...

## Conventions
- [Convention 1 — e.g., "Tailwind-first, no inline styles"]
- [Convention 2 — e.g., "Component props use 'variant' not 'type'"]
- [Convention 3]

## Anti-Patterns (found in codebase, avoid going forward)
- [Anti-pattern found — e.g., "Some components use hardcoded #colors instead of tokens"]
```

Write to `.sentinel/design-system.md`. Create `.sentinel/` directory if needed.

## Return Protocol
- **DONE** — `.sentinel/design-system.md` written, [N] tokens extracted, [M] component patterns documented.
- **DONE_WITH_CONCERNS** — Extraction complete but coverage is limited: [specific gaps]
- **NEEDS_CONTEXT** — Cannot extract: [reason — no UI files found, etc.]
