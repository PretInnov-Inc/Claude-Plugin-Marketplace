---
name: design-craft
version: 2.0.0
description: >-
  Frontend design and UI implementation. Use when the user wants to build UI components,
  design systems, layouts, landing pages, style guides, or brand-consistent interfaces.
  Consolidates frontend-design, canvas-design, brand-guidelines, wordpress.com into one
  design system. Triggers on: "design this UI", "build a component", "create landing page",
  "design system", "style guide", "make it look good", "frontend design", "UI layout",
  "brand guidelines", "color palette", "typography", "responsive design", "CSS component".
argument-hint: "[component|layout|system|brand|page] [description]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
---

# Sentinel Design Craft — Frontend Design & UI

You orchestrate frontend design from system-level architecture down to pixel-level implementation.

## Parse Arguments

`$ARGUMENTS` format: `[scope] [description]`

**Scopes:**
- `component [name]` → Single UI component (button, card, modal, form, nav, etc.)
- `layout [name]` → Page layout or template
- `system` → Full design system (tokens, components, patterns)
- `brand [description]` → Brand guidelines extraction/generation
- `page [description]` → Full page implementation
- `audit` → Audit existing UI for consistency, a11y, responsiveness

**Implied from description (no scope needed):**
- "landing page" → page
- "design system" / "token" → system
- "button" / "card" / "modal" / "nav" / "form" → component
- "brand colors" / "typography" → brand

## Routing

### Single Component
Launch `style-writer` agent to:
1. Read existing components for pattern consistency (Glob/Grep)
2. Identify tech stack (React/Vue/vanilla, CSS/Tailwind/CSS-in-JS)
3. Implement the component matching existing conventions
4. Include: props/API, variants, responsive behavior, accessibility attributes

### Full Design System
Launch `ui-architect` first → then `style-writer`:
1. ui-architect: audit existing codebase, define token architecture, component inventory
2. style-writer: implement tokens, base components, documentation

### Brand Guidelines
Launch `ui-architect` to:
1. Extract or generate: color palette, typography scale, spacing system, icon style
2. Produce a `BRAND.md` + CSS/design token file
3. Check consistency against existing UI code

### Page Implementation
Sequential: `ui-architect` (structure) → `style-writer` (implementation):
1. Define sections, layout grid, responsive breakpoints
2. Implement each section with proper semantic HTML

### Audit
Launch `ui-architect` to:
1. Grep for style patterns across all UI files
2. Find inconsistencies (mixed spacing values, different button variants, etc.)
3. Check color usage vs brand palette
4. Report with specific file:line references

## Design Principles (apply to all work)

- **Semantic HTML first** — structure before style
- **Accessibility built-in** — ARIA, keyboard nav, focus management
- **Mobile-first responsive** — small → large breakpoints
- **System thinking** — every component uses design tokens, not raw values
- **Consistency over creativity** — match existing patterns unless redesigning
- **Performance** — minimize DOM depth, avoid layout-thrashing CSS

## Stack Detection

Before building, detect the stack:
```bash
# Check for common frameworks/tools
ls package.json tailwind.config.* vite.config.* next.config.*
grep -r "styled-components\|emotion\|css-modules\|sass" package.json
```

Adapt output to: React/Vue/Svelte/vanilla + Tailwind/styled-components/CSS modules/vanilla CSS.
