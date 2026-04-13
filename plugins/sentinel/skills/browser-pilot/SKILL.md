---
name: browser-pilot
version: 2.0.0
description: >-
  Use when: user wants to test a live web app, automate browser interactions, audit accessibility,
  take screenshots, or test user flows. Requires a running web server (localhost or URL).
  Triggers on: "test my web app", "automate browser", "check accessibility", "WCAG audit",
  "test the UI", "screenshot", "fill form", "test login flow", "a11y check", "browser test".
  DO NOT trigger for: reviewing source code (→ sentinel), building UI (→ design-craft),
  writing Playwright tests for CI (write them inline). Will fail if no server is running.
argument-hint: "[url or description] [--a11y|--flow|--screenshot|--audit]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
execution_mode: parallel
---

# Sentinel Browser Pilot — Web Testing & Automation

You orchestrate web browser testing using Playwright (via MCP) and accessibility auditing.

## Parse Arguments

`$ARGUMENTS` format: `[target] [mode]`

**Targets:**
- URL (http/https) → Test that specific URL
- `localhost:[port]` → Test local dev server
- File path → Read the path to find the app's URL or launch instructions

**Modes (flags):**
- `--a11y` or `a11y` → Accessibility audit only (WCAG 2.1 AA)
- `--flow` or `flow` → User flow automation (forms, navigation, interactions)
- `--screenshot` → Capture screenshots of key states
- `--audit` → Full audit: functionality + a11y + performance signals
- (no flag) → Default: quick smoke test + screenshot

## Mode Routing

### Quick Smoke Test (default)
Launch `web-pilot` agent to:
1. Navigate to the target
2. Check page loads without console errors
3. Take a screenshot
4. Test basic interactions (click primary CTAs, fill visible forms)
5. Report any broken elements or JS errors

### Accessibility Audit (`--a11y`)
Launch `a11y-auditor` agent to:
1. Navigate to target
2. Analyze DOM structure (headings hierarchy, ARIA labels, roles)
3. Check color contrast (textual description of issues)
4. Test keyboard navigation flow
5. Check form labels, alt text, focus indicators
6. Report WCAG 2.1 AA violations with severity and remediation

### User Flow Automation (`--flow`)
Launch `web-pilot` agent with flow instructions:
1. Parse the description for specific flow steps
2. Execute each step (navigate, fill, click, assert)
3. Screenshot each state
4. Report pass/fail per step

### Full Audit (`--audit`)
Launch both `web-pilot` + `a11y-auditor` in parallel:
1. web-pilot: functionality, console errors, network failures, form testing
2. a11y-auditor: WCAG compliance, keyboard nav, screen reader support
3. Combine reports with severity-sorted findings

## MCP Tool Reference (Playwright)

The Playwright MCP server provides these tools (use them directly):
- `playwright__browser_navigate` — go to URL
- `playwright__browser_snapshot` — get accessibility tree
- `playwright__browser_take_screenshot` — capture visual state
- `playwright__browser_click` — click element by selector/description
- `playwright__browser_fill_form` — fill form fields
- `playwright__browser_type` — type into element
- `playwright__browser_press_key` — keyboard interactions
- `playwright__browser_evaluate` — run JavaScript
- `playwright__browser_console_messages` — get console output
- `playwright__browser_network_requests` — get network log
- `playwright__browser_wait_for` — wait for condition

## Report Format

```
SENTINEL BROWSER PILOT
======================
Target: [url]
Mode: [mode]
Browser: Chromium (via Playwright MCP)

RESULTS:

CRITICAL (must fix):
  [description] — [location/selector]
  Impact: [who is affected]
  Fix: [specific remediation]

WARNINGS (should fix):
  [description]

PASSED:
  ✓ [what worked correctly]

Screenshots: [list of states captured]

Summary: [N critical, M warnings, P passed]
```
