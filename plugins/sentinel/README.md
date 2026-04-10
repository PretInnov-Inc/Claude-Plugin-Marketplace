# Sentinel — 9-Category Unified Intelligence for Claude Code

> **One plugin to rule them all.**
>
> By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)

---

## What Is Sentinel?

Most Claude Code setups end up with 15-40 plugins installed — each doing one thing, overlapping with three others, and fighting for context window space. Every SessionStart hook from every plugin injects text, eating up tokens. Every PostToolUse hook from every plugin fires, adding latency. It becomes chaos.

**Sentinel replaces all of that with one unified system.**

Sentinel consolidates 40+ standalone plugins into 9 organized categories, with 21 specialized agents, 9 slash-command skills, 6 lifecycle hooks, 3 CLI tools, and 3 output styles — all sharing one data store, one config file, and one coherent architecture.

### The 9 Categories

| # | Category | What It Covers |
|---|----------|---------------|
| **A** | AI Development Toolkit | Build plugins, agents, skills, MCP servers, Agent SDK apps |
| **B** | Code Quality & Review | Multi-agent parallel review with adaptive confidence scoring |
| **C** | Output Style Management | Switch between focused/learning/verbose response modes |
| **D** | Browser & Web Testing | Playwright automation, WCAG 2.1 AA accessibility audits |
| **E** | Workflow Intelligence | Session memory, decision tracking, accumulated learnings |
| **F** | Frontend & Design | Design systems, component blueprints, brand guidelines |
| **G** | Documentation & Content | READMEs, API docs, SEO content, tracking plans |
| **H** | Infrastructure & Data | Airflow DAGs, dbt models, data lineage, warehouse queries |
| **I** | DX & Meta Tools | CLAUDE.md improvement, hook creation, project setup analysis |

---

## How to Install

### From Our Marketplace (Recommended)

```bash
# Add the marketplace (one-time)
claude plugin marketplace add github:PretInnov-Inc/forge-marketplace

# Install Sentinel
claude plugin install sentinel@pretinnov-plugins
```

### Local Testing

```bash
git clone https://github.com/PretInnov-Inc/forge-marketplace.git
claude --plugin-dir ./forge-marketplace/plugins/sentinel
```

### After Installing

Run the install script to validate all 57 components:
```bash
bash sentinel/scripts/install.sh
```

You should see:
```
Status: SUCCESS - all components validated

  21 Agents     - sentinel-reviewer, bug-hunter, security-scanner, + 18 more
   9 Skills     - sentinel, ai-forge, browser-pilot, design-craft, doc-engine,
                  dx-meta, flow-memory, infra-ops, style-engine
   2 Commands   - review, quick-check
   6 Hook Events - PreToolUse, PostToolUse, SessionStart, PreCompact, PostCompact, Stop
   3 Output Styles - focused, learning, verbose
   3 CLI Tools  - sentinel-status, sentinel-report, sentinel-reset
```

---

## How to Use — Every Category Explained

### Category B: Code Review (Start Here!)

This is what most people use first. Sentinel reviews your code using up to 6 specialized agents in parallel.

```bash
# Full 6-agent review of all changes
/sentinel
/sentinel:review

# Fast 2-agent check (reviewer + bug-hunter only)
/sentinel quick
/sentinel:quick-check

# Security-focused scan (OWASP Top 10, data flow analysis)
/sentinel security

# Test coverage analysis
/sentinel tests

# Quality + simplification pass
/sentinel quality

# Review a specific file
/sentinel src/auth/login.py
```

**What happens behind the scenes (full mode):**

1. **Scope detection** — Sentinel checks if you're in a git repo. If yes, it uses `git diff`. If no, it reads the edit log (tracked by PostToolUse hooks) to find files you modified this session. This is why Sentinel works on ANY project, not just git repos.

2. **Parallel agent launch** — 5 agents run simultaneously:

| Agent | Model | What It Checks |
|-------|-------|---------------|
| sentinel-reviewer | Sonnet | CLAUDE.md compliance, naming conventions, code organization |
| bug-hunter | Opus | Logic errors, null handling, race conditions, off-by-one errors |
| error-auditor | Sonnet | Silent failures, empty catches, broad exceptions, swallowed errors |
| security-scanner | Opus | SQL injection, XSS, hardcoded secrets, IDOR, trust boundary analysis |
| test-analyzer | Haiku | Behavioral test coverage gaps, brittle tests, missing edge cases |

3. **Sequential polish** — If no critical issues found, `code-polisher` (Haiku) does a simplification pass.

4. **Adaptive thresholds** — Each agent has a confidence threshold (default 80, security starts at 70). If you say "show more," it decreases. If you dismiss findings as noise, it increases. The system learns your signal-to-noise preference over time.

**Example output:**
```
SENTINEL REVIEW REPORT
======================
Scope: git — 3 files
Mode: full
Confidence thresholds: reviewer=80, bugs=80, security=70

CRITICAL (90-100):
  security-scanner src/api/auth.py:47 (confidence: 95)
    SQL string concatenation with user input
    Fix: Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

IMPORTANT (80-89):
  bug-hunter src/utils/parse.py:23 (confidence: 85)
    IndexError when input list is empty — data[0] accessed without guard
    Fix: Add `if not data: return None` before accessing data[0]

PASSED:
  - CLAUDE.md compliance (all conventions followed)
  - Error handling (all catches are specific, none empty)
  - Test coverage (auth module at 80% behavioral coverage)

Summary: 2 issues found, 1 file clean
```

---

### Category A: AI Development Toolkit

Build Claude Code plugins, agents, skills, MCP servers, and Agent SDK apps.

```bash
# Build a complete plugin (research -> blueprint -> build -> validate)
/sentinel:ai-forge plugin "monitoring dashboard"

# Design a single agent
/sentinel:ai-forge agent "code reviewer for Python"

# Create a skill
/sentinel:ai-forge skill "database migration helper"

# Create a hook handler
/sentinel:ai-forge hook "warn before deleting files"

# Design an MCP server
/sentinel:ai-forge mcp "GitHub issue tracker"

# Architecture only (no code generation)
/sentinel:ai-forge blueprint "testing automation plugin"

# Validate an existing plugin
/sentinel:ai-forge validate ./my-plugin
```

**The pipeline:**
1. `ai-architect` (Opus) — Researches what exists, designs the blueprint
2. User approves the blueprint
3. `ai-builder` (Sonnet) — Implements every file in correct order
4. `ai-validator` (Haiku) — Checks structure, frontmatter, stdlib compliance

---

### Category C: Output Style

Control how Claude formats its responses.

```bash
# Switch to minimal, code-first mode
/sentinel:style-engine focused

# Switch to educational mode with insights
/sentinel:style-engine learning

# Switch to full explanation mode
/sentinel:style-engine verbose

# See current style
/sentinel:style-engine status
```

**What each style does:**

| Style | Behavior |
|-------|----------|
| **focused** (default) | Code-first. No preamble, no trailing summaries. Errors get full detail, everything else stays brief. |
| **learning** | Educational insights before/after code. Invites user contributions for meaningful trade-off decisions. |
| **verbose** | Explains every decision with alternatives considered. Connects changes to the broader codebase. Best for onboarding. |

Style changes take effect on the next session start (the SessionStart hook reads the active style from config and injects it).

Want a custom style? Ask `style-conductor` to create one:
```bash
# This launches the style-conductor agent to design a custom style
/sentinel:style-engine pair-programming
```

---

### Category D: Browser Testing

Test web apps using Playwright (via MCP) and audit accessibility.

```bash
# Quick smoke test (page loads? console errors? basic interactions?)
/sentinel:browser-pilot http://localhost:3000

# WCAG 2.1 AA accessibility audit
/sentinel:browser-pilot http://localhost:3000 --a11y

# Automate a user flow (login, form fill, navigation)
/sentinel:browser-pilot http://localhost:3000 --flow

# Full audit (functionality + accessibility + performance signals)
/sentinel:browser-pilot http://localhost:3000 --audit
```

**Agents:**
- `web-pilot` (Sonnet) — Browser automation, form testing, console error checking
- `a11y-auditor` (Haiku) — WCAG compliance: heading hierarchy, ARIA, keyboard nav, contrast, labels

**Requires:** Playwright MCP server running (`mcp__plugin_playwright_playwright__*` tools available).

---

### Category E: Workflow Intelligence

Session memory, decision tracking, and accumulated learnings.

```bash
# Full intelligence dashboard
/sentinel:flow-memory

# View decision journal with outcomes
/sentinel:flow-memory decisions

# View extracted learnings by category
/sentinel:flow-memory learnings

# Session health trend analysis
/sentinel:flow-memory health

# Log a decision manually
/sentinel:flow-memory add decision "Chose SQLite for deployment simplicity"

# Log a learning manually
/sentinel:flow-memory add learning "pnpm workspaces hoist peer deps differently than npm"

# Log an anti-pattern
/sentinel:flow-memory add anti-pattern "Don't auto-commit without asking"

# Remove a stale entry
/sentinel:flow-memory forget "Vue.js"

# Mark decision #3 as successful
/sentinel:flow-memory resolve 3 success

# Deep pattern analysis (launches memory-warden agent)
/sentinel:flow-memory patterns
```

**CLI tools** (available in Bash after install):
```bash
sentinel-status                 # Health score bar + recent learnings
sentinel-status --json          # Machine-readable JSON output
sentinel-report --last 10       # Markdown table of last 10 sessions
sentinel-reset --confirm        # Archive data to data/archive/ and clear
sentinel-reset --archive-only   # Archive without clearing
```

**How memory works:**
1. **Stop hook** extracts learnings, decisions, and anti-patterns from every session transcript
2. **SessionStart hook** injects the accumulated wisdom into Claude's context
3. **PreCompact hook** extracts learnings before context is truncated
4. **PostCompact hook** re-injects memory after compaction

This creates a lossless memory pipeline — Claude never forgets what it learned, even in multi-hour sessions that auto-compact.

---

### Category F: Frontend Design

Design systems, component blueprints, brand guidelines.

```bash
# Build a single UI component matching your existing stack
/sentinel:design-craft component Button

# Full design system audit + token architecture
/sentinel:design-craft system

# Extract brand guidelines from existing UI
/sentinel:design-craft brand

# Implement a full page
/sentinel:design-craft page "landing page with hero and CTA"

# Audit existing UI for consistency
/sentinel:design-craft audit
```

**Agents:**
- `ui-architect` (Opus) — Design-only. Audits existing patterns, defines token architecture, component inventory. Never writes implementation code.
- `style-writer` (Sonnet) — Implementation. Takes blueprints and writes production components matching your stack (React/Vue/Svelte, Tailwind/CSS-in-JS/vanilla CSS).

---

### Category G: Documentation & Content

READMEs, API references, guides, SEO content, tracking plans.

```bash
# Generate README from source code
/sentinel:doc-engine readme

# Auto-generate API reference from exports
/sentinel:doc-engine api src/

# Write a how-to guide
/sentinel:doc-engine guide "setting up authentication"

# SEO content strategy + optimized article
/sentinel:doc-engine seo "serverless database architecture"

# Full content strategy with 90-day roadmap
/sentinel:doc-engine strategy

# Long-form blog post
/sentinel:doc-engine content "why we switched from REST to GraphQL"
```

**Agents:**
- `doc-writer` (Sonnet) — Reads actual source code, never invents API behavior
- `content-strategist` (Opus) — Keyword research, competitor analysis, on-page SEO
- `data-profiler` (Haiku) — SQL profiling queries, data freshness checks, tracking plans

---

### Category H: Infrastructure & Data

Airflow DAGs, dbt models, data pipelines, tracking instrumentation.

```bash
# Build an Airflow DAG
/sentinel:infra-ops dag "ETL from Postgres to BigQuery daily"

# Create a dbt model with schema tests
/sentinel:infra-ops dbt "daily user activity aggregation"

# General pipeline design
/sentinel:infra-ops pipeline "real-time event processing"

# Warehouse query
/sentinel:infra-ops query "top 10 users by revenue this month"

# Trace data lineage
/sentinel:infra-ops lineage orders_daily

# Product analytics tracking plan
/sentinel:infra-ops tracking "checkout flow"

# Data profiling (row counts, nulls, distributions)
/sentinel:infra-ops profile users

# Check data freshness against SLA
/sentinel:infra-ops freshness orders --sla 2h
```

**Agent:** `pipeline-builder` (Sonnet) — Detects Airflow version automatically, uses TaskFlow API, includes proper retry/error handling, writes test files alongside DAGs.

---

### Category I: DX & Meta Tools

CLAUDE.md improvement, hook creation, project setup, usage analysis.

```bash
# Audit and improve CLAUDE.md files
/sentinel:dx-meta claude-md

# Create automation hooks from natural language
/sentinel:dx-meta hooks "prevent pushing to main"
/sentinel:dx-meta hooks "run tests after editing Python files"
/sentinel:dx-meta hooks "warn before deleting files"

# Full project setup analysis
/sentinel:dx-meta setup

# Developer growth report from session data
/sentinel:dx-meta analyze

# Permissions audit
/sentinel:dx-meta permissions
```

---

## What Happens Automatically (Hooks)

You don't need to run any commands for these — they fire on their own:

| When | Hook | Handler | What Happens |
|------|------|---------|-------------|
| Session start | SessionStart | `session-memory.sh` | Loads accumulated learnings, anti-patterns, decisions, and session health into Claude's context |
| Session start | SessionStart | `output-mode.sh` | Injects the active output style (focused/learning/verbose) |
| Before edit | PreToolUse | `pre-edit-security.py` | Scans for 16 security patterns (SQL injection, hardcoded secrets, eval, etc.). Blocks on critical/high severity. |
| After edit | PostToolUse | `post-edit-tracker.py` | Logs every edit to `edit-log.jsonl`. Classifies risk (4 tiers). Detects churn (5+ edits to same file). |
| Before compaction | PreCompact | `session-learn.py` | Extracts learnings from transcript before context is truncated |
| After compaction | PostCompact | `post-compact-inject.py` | Re-injects memory context with halved limits to save space |
| Session end | Stop | `session-learn.py` | Extracts learnings, decisions, anti-patterns. Calculates health score (0-100). |

### Security Patterns (16 built-in, extensible)

The PreToolUse hook checks every Edit/Write against `data/security-patterns.json`:
- SQL injection (string concatenation in queries)
- Hardcoded secrets (API keys, passwords in source)
- Unsafe eval/exec with user input
- XSS (innerHTML with unsanitized data)
- Command injection (shell commands with user input)
- Path traversal (unsanitized file paths)
- Weak crypto (MD5, SHA1 for passwords)
- And 9 more...

Add your own patterns by editing `data/security-patterns.json`.

---

## The 21 Agents

| Agent | Model | Category | Role | Can Write? |
|-------|-------|----------|------|-----------|
| sentinel-reviewer | Sonnet | B | Code quality + CLAUDE.md compliance | No |
| bug-hunter | Opus | B | Logic errors, null handling, race conditions | No |
| error-auditor | Sonnet | B | Silent failures, empty catches | No |
| security-scanner | Opus | B | OWASP Top 10, trust boundary analysis | No |
| test-analyzer | Haiku | B | Behavioral test coverage gaps | No |
| code-polisher | Haiku | B | Post-review simplification | Yes |
| ai-architect | Opus | A | Plugin/agent system design | No |
| ai-builder | Sonnet | A | Implementation engine | Yes |
| ai-validator | Haiku | A | Structure validation | No |
| style-conductor | Haiku | C | Output style management + custom styles | Yes |
| style-writer | Sonnet | F | Frontend UI implementation | Yes |
| web-pilot | Sonnet | D | Playwright browser automation | Yes |
| a11y-auditor | Haiku | D | WCAG 2.1 AA compliance checking | Yes |
| memory-warden | Sonnet | E | Session intelligence analysis + dedup | Yes |
| session-scribe | Haiku | E | Quick manual memory capture | Yes |
| workspace-curator | Sonnet | E/I | CLAUDE.md + hook creation + DX | Yes |
| ui-architect | Opus | F | Design system architecture | No |
| doc-writer | Sonnet | G | Technical documentation | Yes |
| content-strategist | Opus | G | SEO + content strategy | Yes |
| data-profiler | Haiku | G/H | Data quality + tracking plans | Yes |
| pipeline-builder | Sonnet | H | Airflow DAGs + dbt models | Yes |

**Model tiers:**
- **Opus** (4 agents) — Deep reasoning for critical analysis (bugs, security, architecture, content strategy)
- **Sonnet** (10 agents) — Balanced reasoning for implementation and review
- **Haiku** (7 agents) — Fast execution for frequent/simple tasks (all have `maxTurns` limits)

---

## Configuration

All settings live in `data/sentinel-config.json`. Key sections:

### User-Tunable Settings (via plugin.json userConfig)

| Setting | Default | What It Controls |
|---------|---------|-----------------|
| `output_style` | `"focused"` | Active response style |
| `churn_threshold` | `5` | Edits to same file before churn warning |
| `confidence_threshold` | `80` | Review agent confidence threshold (lower = more findings) |
| `memory_enabled` | `true` | Whether to inject past learnings at session start |
| `a11y_wcag_level` | `"AA"` | WCAG conformance level for accessibility audits |

### Per-Agent Confidence Thresholds

```json
{
  "adaptive_confidence": {
    "per_agent": {
      "sentinel-reviewer": 80,
      "bug-hunter": 80,
      "security-scanner": 70,
      "code-polisher": 85
    }
  }
}
```

### Review Modes

```json
{
  "review_modes": {
    "full": ["sentinel-reviewer", "bug-hunter", "error-auditor", "security-scanner", "test-analyzer", "code-polisher"],
    "quick": ["sentinel-reviewer", "bug-hunter"],
    "security": ["security-scanner", "error-auditor"],
    "quality": ["sentinel-reviewer", "code-polisher"],
    "tests": ["test-analyzer"]
  }
}
```

---

## Data Files

All data lives in `data/`:

| File | Format | What's In It | Auto-Trimmed |
|------|--------|-------------|-------------|
| `sentinel-config.json` | JSON | Master config (thresholds, modes, agent settings) | No |
| `security-patterns.json` | JSON | 16 extensible security patterns | No |
| `learnings.jsonl` | JSONL | Extracted learnings from sessions | Yes (2000 max) |
| `decisions.jsonl` | JSONL | Decision journal with outcomes | Yes (2000 max) |
| `anti-patterns.jsonl` | JSONL | Patterns to avoid | Yes (2000 max) |
| `session-log.jsonl` | JSONL | Session health history | Yes (2000 max) |
| `edit-log.jsonl` | JSONL | Every edit tracked (the non-git diff) | Yes (3000 max) |

All JSONL files are automatically trimmed to prevent unbounded growth. When a file exceeds the max, older entries are removed (keeping the most recent 1500-2000).

---

## Works Without Git

Most review tools break without git. Sentinel doesn't.

**With git:** Uses `git diff` for changed files, `git status` for untracked files.

**Without git:** Uses the `edit-log.jsonl` (populated by the PostToolUse hook) to track which files were modified this session. Every Edit/Write is logged with file path, risk signals, and timestamp.

Both modes produce the same output format, so all downstream agents work identically. The `scope_detector.py` utility handles this automatically.

---

## Compatibility with Other PretInnov Plugins

Sentinel works standalone or alongside the other marketplace plugins:

| Combo | What You Get |
|-------|-------------|
| **Sentinel alone** | Everything. All 9 categories work independently. |
| **Sentinel + Clamper** | Sentinel blocks dangerous edits before they happen (PreToolUse), Clamper verifies code quality after (verification loop). Sentinel reviews code, Clamper maps project DNA. |
| **Sentinel + Cortex** | Both track session intelligence. Sentinel focuses on code review learnings and health scores. Cortex focuses on cross-project patterns and self-evolution. |
| **Sentinel + Forge** | Sentinel's `ai-architect`/`ai-builder`/`ai-validator` agents power the same pipeline Forge uses. Use `/sentinel:ai-forge` for integrated builds or `/forge` for the standalone pipeline. |

---

## Troubleshooting

**"No files to review" when I run /sentinel**
- In a git repo: make sure you have uncommitted changes (`git diff` must show something)
- Without git: edit some files first — the PostToolUse hook needs to log at least one edit
- Or specify files directly: `/sentinel src/file.py`

**"Session memory seems empty"**
- Memory accumulates over sessions. First session will have nothing.
- Run `sentinel-status` to check if data files have content
- Ensure `memory_enabled` is `true` in config

**"Security hook keeps blocking my edit"**
- The block is intentional for critical/high severity patterns
- Review the pattern: check `data/security-patterns.json`
- If it's a false positive, disable that specific pattern (`"enabled": false`)

**"Churn warning is annoying"**
- Increase the threshold: edit `data/sentinel-config.json`, set `churn_threshold` to 8 or 10
- Or via userConfig: `churn_threshold: 10`

**"Output style didn't change"**
- Style changes take effect on the NEXT session start
- The SessionStart hook reads the config and injects the style
- Run `/restart` or start a new session

---

## License

MIT — By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)
