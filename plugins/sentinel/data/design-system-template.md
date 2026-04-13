---
version: 1.0.0
extracted_from: "[PROJECT NAME]"
date: "[YYYY-MM-DD]"
stack: "[React|Vue|Svelte|vanilla] + [Tailwind|styled-components|CSS modules|vanilla CSS]"
---

# Design System

> Copy this file to `.sentinel/design-system.md` in your project and fill in the sections.
> Or run `/design-craft extract` to auto-generate it from your codebase.
>
> This file is loaded at every session start by the lineage-manager hook,
> making your design system context always available to ui-architect and style-writer.

## Color Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary-500` | `#3b82f6` | Primary interactive elements |
| `--color-primary-600` | `#2563eb` | Primary hover state |
| `--color-neutral-100` | `#f3f4f6` | Background surfaces |
| `--color-neutral-900` | `#111827` | Primary text |
| `--color-success` | `#10b981` | Success states |
| `--color-warning` | `#f59e0b` | Warning states |
| `--color-error` | `#ef4444` | Error states |

*Or Tailwind class names if using Tailwind:*

| Purpose | Tailwind Class | Value |
|---------|----------------|-------|
| Primary | `bg-blue-500` | `#3b82f6` |
| Primary text | `text-blue-600` | `#2563eb` |

## Typography

| Token | Value | Usage |
|-------|-------|-------|
| Font family (body) | `Inter, system-ui, sans-serif` | Body text |
| Font family (mono) | `JetBrains Mono, monospace` | Code |
| Base size | `1rem (16px)` | Body |
| Scale xs | `0.75rem` | Captions |
| Scale sm | `0.875rem` | Labels, metadata |
| Scale md | `1rem` | Body |
| Scale lg | `1.125rem` | Subheadings |
| Scale xl | `1.25rem` | Headings |
| Scale 2xl | `1.5rem` | Section titles |
| Scale 3xl | `1.875rem` | Page titles |

## Spacing Scale

Base unit: `4px` (0.25rem)

| Token | Value | Tailwind |
|-------|-------|---------|
| 1 | `4px` | `p-1` |
| 2 | `8px` | `p-2` |
| 3 | `12px` | `p-3` |
| 4 | `16px` | `p-4` |
| 6 | `24px` | `p-6` |
| 8 | `32px` | `p-8` |
| 12 | `48px` | `p-12` |
| 16 | `64px` | `p-16` |

## Component Patterns

### Button

Props API:
- `variant`: `primary` | `secondary` | `ghost` | `destructive`
- `size`: `sm` | `md` | `lg`
- `loading`: `boolean` (shows spinner, disables button)
- `disabled`: `boolean`

Naming convention: functional variants (`primary`, `secondary`) not color-based (`blue`, `gray`)

### Input

Props API:
- `type`: standard HTML input types
- `label`: string (always required — no unlabeled inputs)
- `error`: string (shows error state)
- `hint`: string (helper text below input)

### Card

Props API:
- `padding`: `sm` | `md` | `lg` (default: `md`)
- `variant`: `default` | `bordered` | `elevated`

### Badge

Props API:
- `variant`: `default` | `success` | `warning` | `error` | `info`
- `size`: `sm` | `md`

## Conventions

- **Semantic HTML first**: use `<button>` for buttons, `<a>` for links, never `<div>` with onClick
- **Token-first styling**: always use design tokens, never raw values (`#3b82f6`, `12px`)
- **Variant naming**: use functional names (`primary`, `destructive`) not visual names (`blue`, `red`)
- **Mobile-first responsive**: all components work at 320px minimum width
- **Focus visible**: every interactive element has a visible focus ring (never `outline: none`)
- **Loading states**: every async action has a loading state

## Anti-Patterns (avoid)

- Hardcoded color values (`#hexcode`, `rgb()`) — use tokens
- Inline styles except for truly dynamic values (not for spacing, color, typography)
- `div` elements with click handlers for interactive functionality
- Color-only error states (must also have text or icons)
- Custom button styles that don't use the Button component API

## Breakpoints

| Name | Value | Usage |
|------|-------|-------|
| sm | `640px` | Large phones |
| md | `768px` | Tablets |
| lg | `1024px` | Laptops |
| xl | `1280px` | Desktops |
| 2xl | `1536px` | Large screens |
