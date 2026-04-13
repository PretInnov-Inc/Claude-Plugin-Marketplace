# PretInnov Plugins — Claude Code Plugin Marketplace

> **By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)**

Four production-grade plugins that make Claude Code smarter, safer, self-improving, and capable of building its own extensions.

---

## What's Inside?

| Plugin | Version | What It Does | One-Liner |
|--------|---------|-------------|-----------|
| **Sentinel** | v3.0.0 | 9-category unified intelligence — code review, AI dev toolkit, browser testing, workflow memory, frontend design, docs, infra, and DX tools in one plugin | *"One plugin to rule them all."* |
| **Clamper** | v1.1.1 | Verifies your code, maps your project DNA, and scaffolds full agent ecosystems | *"Clip it, Clamp it."* |
| **Cortex** | v1.0.1 | Remembers what worked and what failed across ALL your sessions, then uses that knowledge automatically | *"Claude Code with a brain."* |
| **Forge** | v1.0.1 | Creates entire plugins from a simple chat prompt — researches, asks questions, designs, and generates everything | *"Build plugins by talking."* |
| **codebase-radar** | v1.0.0 | Hybrid semantic + BM25 search via LanceDB — auto-indexes on session start, finds code by meaning not just keywords | *"Stop burning tokens on Grep."* |

### Sentinel at a Glance

Sentinel v3 is the flagship plugin — it consolidates 40+ standalone plugins into 9 organized categories with 24 specialized agents:

| Category | Skill | Agents | What It Covers |
|----------|-------|--------|----------------|
| **A. AI Development** | `/sentinel:ai-forge` | ai-architect, ai-builder, ai-validator | Build plugins, agents, skills, MCP servers, Agent SDK apps |
| **B. Code Quality** | `/sentinel:review` | sentinel-reviewer, bug-hunter, error-auditor, security-scanner, test-analyzer, code-polisher | Multi-agent parallel review with adaptive confidence scoring |
| **C. Output Style** | `/sentinel:style-engine` | style-conductor, style-writer | Switch between focused/learning/verbose modes, create custom styles |
| **D. Browser Testing** | `/sentinel:browser-pilot` | web-pilot, a11y-auditor | Playwright automation, WCAG 2.1 AA accessibility audits |
| **E. Workflow Memory** | `/sentinel:flow-memory` | memory-warden, session-scribe, workspace-curator | Session intelligence, typed learning store, lineage chaining |
| **F. Frontend Design** | `/sentinel:design-craft` | ui-architect, style-writer, design-auditor | Design systems, component blueprints, drift detection against spec |
| **G. Documentation** | `/sentinel:doc-engine` | doc-writer, content-strategist, data-profiler | READMEs, API docs, SEO content, tracking plans |
| **H. Infrastructure** | `/sentinel:infra-ops` | pipeline-builder | Airflow DAGs, dbt models, data lineage, warehouse queries |
| **I. DX / Meta Tools** | `/sentinel:dx-meta` | — | CLAUDE.md improvement, hook creation, project setup, usage analysis |
| **v3 New** | `sentinel-doctor` / `sentinel-audit` | sentinel-auditor, risk-gatekeeper | 120-point plugin rubric, 5-axis risk matrix with CRITICAL hard gate |

**24 agents** | **11 skills** | **7 hook events** | **6 CLI tools** | **3 output styles**

---

## How to Install

### What You Need First

- **Claude Code** installed on your machine. If you don't have it yet, go to [claude.ai/code](https://claude.ai/code) and follow the install instructions.
- That's it. No other software needed.

### Step 1: Add This Marketplace

This tells Claude Code "hey, there's a plugin store at this GitHub repo." You only do this once.

**Option A — Using the Terminal (CLI):**

```bash
claude plugin marketplace add github:PretInnov-Inc/forge-marketplace
```

**Option B — Using the Desktop App:**

1. Open Claude Code desktop app
2. Go to **Settings** (gear icon)
3. Click **Plugins**
4. Click **Add Marketplace**
5. Type in: `PretInnov-Inc/forge-marketplace`
6. Click **Add**

**Option C — From inside a Claude Code chat session:**

```
/plugin marketplace add github:PretInnov-Inc/forge-marketplace
```

### Step 2: Install the Plugins You Want

```bash
# The flagship — covers 9 categories of developer tooling:
claude plugin install sentinel@pretinnov-plugins

# Supporting plugins:
claude plugin install clamper@pretinnov-plugins
claude plugin install cortex@pretinnov-plugins
claude plugin install forge@pretinnov-plugins

# Semantic codebase search (requires Python 3.10+, ~2GB disk for model):
claude plugin install codebase-radar@pretinnov-plugins
```

Or from inside a Claude Code session:
```
/plugin install sentinel@pretinnov-plugins
/plugin install clamper@pretinnov-plugins
/plugin install cortex@pretinnov-plugins
/plugin install forge@pretinnov-plugins
/plugin install codebase-radar@pretinnov-plugins
```

### Step 3: Verify They're Installed

Type `/help` inside Claude Code — you should see the new commands listed under their plugin namespaces.

---

## Quick Start for Each Plugin

### Sentinel — Unified Intelligence (9 Categories)

```bash
# Code Review (Category B)
/sentinel                       # Full 6-agent review of all changes
/sentinel quick                 # Fast 2-agent check (reviewer + bug-hunter)
/sentinel security              # Security-focused scan (OWASP Top 10)
/sentinel tests                 # Test coverage analysis
/sentinel src/auth.py           # Review a specific file

# AI Development (Category A)
/sentinel:ai-forge plugin "monitoring dashboard"   # Build a new plugin
/sentinel:ai-forge agent "code reviewer"           # Create a single agent
/sentinel:ai-forge validate ./my-plugin            # Validate plugin structure

# Output Style (Category C)
/sentinel:style-engine focused    # Minimal, code-first responses
/sentinel:style-engine learning   # Educational insights + interactive contributions
/sentinel:style-engine verbose    # Detailed explanations for everything

# Browser Testing (Category D)
/sentinel:browser-pilot http://localhost:3000          # Quick smoke test
/sentinel:browser-pilot http://localhost:3000 --a11y   # WCAG accessibility audit
/sentinel:browser-pilot http://localhost:3000 --flow   # Automate user flows

# Workflow Memory (Category E)
/sentinel:flow-memory                # Full intelligence dashboard
/sentinel:flow-memory decisions      # View decision journal
/sentinel:flow-memory health         # Session health trends
/sentinel:flow-memory add decision "Chose SQLite for deployment simplicity"

# Frontend Design (Category F)
/sentinel:design-craft component Button     # Build a UI component
/sentinel:design-craft system               # Full design system audit + blueprint
/sentinel:design-craft brand                # Extract brand guidelines from existing UI

# Documentation (Category G)
/sentinel:doc-engine readme              # Generate README from source code
/sentinel:doc-engine api src/            # Auto-generate API reference
/sentinel:doc-engine seo "serverless"    # SEO content strategy + article

# Infrastructure (Category H)
/sentinel:infra-ops dag "ETL from Postgres to BigQuery"   # Build an Airflow DAG
/sentinel:infra-ops dbt "daily user aggregation"          # Create dbt model
/sentinel:infra-ops tracking "checkout flow"              # Product tracking plan

# DX / Meta Tools (Category I)
/sentinel:dx-meta claude-md      # Audit and improve CLAUDE.md
/sentinel:dx-meta hooks          # Create automation hooks from natural language
/sentinel:dx-meta setup          # Full project setup analysis
/sentinel:dx-meta analyze        # Developer growth report from session data
```

**CLI tools** (available in Bash after install):
```bash
sentinel-status                 # Health score + recent learnings
sentinel-report --last 10       # Markdown session history report
sentinel-reset --confirm        # Archive and clear accumulated data
sentinel-doctor                 # Full plugin health diagnostic (exit 0/1/2)
sentinel-doctor --quick         # 30-second config + hooks check
sentinel-refresh --auto         # Maintain typed learning store (5-outcome model)
sentinel-learn knowledge "..."  # Manually add knowledge entry
sentinel-learn bug "..."        # Manually add bug entry with root cause
```

### Clamper — Code Quality Guardian

```bash
/clamper:init           # Set up your project with agents, skills, and rules
/clamper:clamp          # Check if your recent code changes are safe
/clamper:dna            # Analyze your project structure, hot files, fragile zones
/clamper:clamper        # View the Clamper dashboard with stats
```

### Cortex — Self-Learning Intelligence

```bash
/cortex:cortex          # View what Cortex has learned about you
/cortex:decisions       # Track important decisions you've made
/cortex:health          # Check system health
/cortex:evolve          # Let Cortex adapt its rules based on your feedback
```

### Forge — Plugin Builder

```bash
/forge                  # Create a new plugin (full guided process)
/forge:research <idea>  # Research if a plugin idea already exists
/forge:validate <path>  # Check if a plugin is correctly built
/forge:dashboard        # View your build history
```

### codebase-radar — Hybrid Semantic Search

```bash
# Index your project on first use
/radar:index                                    # Build/refresh the semantic index
/radar:search "how does auth work"              # Natural language code search
/radar:search "database connection pooling"     # Find by concept, not keyword
/radar:search "retry logic with backoff"        # Cross-language concept search

# Status and config
/radar                                          # Index status + health
/radar:config                                   # View/change search settings
```

**CLI tools** (available in Bash after install):
```bash
radar-status                 # Index health for current project
radar-reset                  # Clear index and rebuild
```

---

## How Sentinel's Hooks Work (Automatic Behavior)

Sentinel v3 runs 7 lifecycle hooks — no slash commands needed, they fire automatically:

| When | What Happens | Why It Matters |
|------|-------------|----------------|
| **Session Start** | Injects accumulated learnings, anti-patterns, decisions, and session lineage into Claude's context | Claude starts every session knowing what worked and what to avoid |
| **Session Start** | Injects the active output style (focused/learning/verbose) | Consistent response behavior without manual setup |
| **Before Edit/Write** | Layer 1: scans for 16 security patterns. Layer 2: TDD gate, blueprint gate, destructive command blocking | Blocks dangerous code AND enforces operational safety — all configurable block/warn/off |
| **After Edit/Write** | Logs every edit, classifies risk (GREEN/YELLOW/RED/CRITICAL), detects churn, compresses large outputs | Warns when you're stuck in a loop; saves ~7k tokens/session via output compression |
| **User Message** | Intercepts `>review`, `>rollover`, `>doctor` shortcuts — zero LLM cost routing | Instant command shortcuts without burning any tokens |
| **Before Compaction** | Extracts learnings from the transcript, writes to both JSONL and typed `.sentinel/learnings/` store | Nothing is lost when long sessions auto-compact |
| **After Compaction** | Re-injects memory context into the new context window | Claude continues with full accumulated wisdom, not a blank slate |

---

## Architecture Overview

```
Claude-Plugin-Marketplace/
  plugins/
    sentinel/                    # Flagship — 9-category unified intelligence (v3.0)
      .claude-plugin/
        plugin.json              # Manifest (v3.0.0)
      agents/                    # 24 specialized agents
        sentinel-reviewer.md     #   Sonnet — code quality + CLAUDE.md compliance
        bug-hunter.md            #   Opus — deep logic error detection
        security-scanner.md      #   Opus — OWASP Top 10 analysis
        error-auditor.md         #   Sonnet — silent failure detection
        test-analyzer.md         #   Haiku — behavioral test coverage
        code-polisher.md         #   Haiku — post-review simplification
        ai-architect.md          #   Opus — plugin/agent system design (HARD-GATE)
        ai-builder.md            #   Sonnet — implementation engine (blueprint gate)
        ai-validator.md          #   Haiku — structure validation
        web-pilot.md             #   Sonnet — Playwright browser automation
        a11y-auditor.md          #   Haiku — WCAG 2.1 AA compliance
        memory-warden.md         #   Sonnet — session intelligence curator
        session-scribe.md        #   Haiku — quick memory capture
        workspace-curator.md     #   Sonnet — DX + CLAUDE.md management
        ui-architect.md          #   Opus — design system architecture
        style-writer.md          #   Sonnet — frontend implementation
        style-conductor.md       #   Haiku — output style management
        doc-writer.md            #   Sonnet — technical documentation
        content-strategist.md    #   Opus — SEO + content strategy
        data-profiler.md         #   Haiku — data quality + tracking
        pipeline-builder.md      #   Sonnet — Airflow/dbt/infra
        design-auditor.md        #   Haiku — UI drift vs .sentinel/design-system.md [NEW v3]
        sentinel-auditor.md      #   Sonnet — 120-point agent/skill/hook rubric [NEW v3]
        risk-gatekeeper.md       #   Opus — 5-axis risk matrix + CRITICAL hard gate [NEW v3]
      skills/                    # 11 slash-command skills
        sentinel/SKILL.md        #   /sentinel — unified code review
        ai-forge/SKILL.md        #   /sentinel:ai-forge — AI dev toolkit
        browser-pilot/SKILL.md   #   /sentinel:browser-pilot — web testing
        design-craft/SKILL.md    #   /sentinel:design-craft — frontend design
        doc-engine/SKILL.md      #   /sentinel:doc-engine — documentation
        dx-meta/SKILL.md         #   /sentinel:dx-meta — DX tools
        flow-memory/SKILL.md     #   /sentinel:flow-memory — session memory + lineage
        infra-ops/SKILL.md       #   /sentinel:infra-ops — infrastructure
        style-engine/SKILL.md    #   /sentinel:style-engine — output style
        sentinel-doctor/SKILL.md #   /sentinel:sentinel-doctor — health diagnostic [NEW v3]
        sentinel-audit/SKILL.md  #   /sentinel:sentinel-audit — plugin quality audit [NEW v3]
      commands/                  # 2 command aliases
        review.md                #   /sentinel:review — full review workflow
        quick-check.md           #   /sentinel:quick-check — fast review
      hooks/
        hooks.json               # 7 lifecycle events configured
      hooks-handlers/            # 9 handlers (pure stdlib, no pip)
        pre-edit-security.py     #   PreToolUse — Layer 1 security + Layer 2 gates
        post-edit-tracker.py     #   PostToolUse — edit log + churn + risk
        session-memory.sh        #   SessionStart — memory + lineage injection
        output-mode.sh           #   SessionStart — style injection
        session-learn.py         #   Stop + PreCompact — dual-store learning extraction
        post-compact-inject.py   #   PostCompact — memory re-injection
        output-compressor.py     #   PostToolUse — debounced output compression [NEW v3]
        prompt-router.py         #   UserPromptSubmit — zero-token >shortcuts [NEW v3]
        lineage-manager.py       #   SessionStart — per-user lineage chaining [NEW v3]
      output-styles/             # 3 response modes
        focused.md               #   Code-first, minimal
        learning.md              #   Educational + interactive
        verbose.md               #   Full explanations
      bin/                       # 6 CLI tools (added to Bash PATH)
        sentinel-status          #   Health score + learnings
        sentinel-report          #   Markdown session report
        sentinel-reset           #   Archive + clear data
        sentinel-doctor          #   Full plugin health diagnostic (exit 0/1/2) [NEW v3]
        sentinel-refresh         #   5-outcome typed learning store maintenance [NEW v3]
        sentinel-learn           #   Manual learning entry writer (knowledge|bug) [NEW v3]
      data/                      # Persistent data store
        sentinel-config.json     #   Master config (thresholds, agents, modes, gates)
        security-patterns.json   #   16 extensible security patterns
        design-system-template.md #  Template for .sentinel/design-system.md [NEW v3]
        sentinel-gitignore-template # Template for .sentinel/.gitignore [NEW v3]
        learnings.jsonl          #   Accumulated learnings (JSONL — fast read)
        decisions.jsonl          #   Decision journal (JSONL)
        anti-patterns.jsonl      #   Patterns to avoid (JSONL)
        session-log.jsonl        #   Session health history (JSONL)
        edit-log.jsonl           #   Edit tracking log (JSONL)
      settings.json              # Default agent: sentinel-reviewer
      scripts/
        install.sh               # Validates all 68 v3 components

    clamper/                     # Code verification + project DNA
      agents/                    # 4 agents
      skills/                    # 3 skills
      ...

    cortex/                      # Self-learning intelligence
      agents/                    # 8 agents
      skills/                    # 12 skills
      ...

    forge/                       # Plugin builder (meta-plugin)
      agents/                    # 5 agents
      skills/                    # 8 skills
      ...

    codebase-radar/              # Hybrid semantic + BM25 search via LanceDB
      .mcp.json                  # MCP server registration
      agents/                    # 2 agents (radar-explorer, radar-indexer)
      skills/                    # 4 skills (radar, radar-search, radar-index, radar-config)
      hooks-handlers/            # 4 handlers (session-start, post-tool-reindex, pre-tool-suggest, session-stop)
      bin/                       # 2 CLI tools (radar-status, radar-reset)
      data/                      # config.json, index-state.json, search-log.jsonl
      ...
```

---

## Plugin Compatibility

All five plugins can run independently or together. When co-installed:

- **Sentinel + Forge**: Sentinel's `ai-architect` / `ai-builder` / `ai-validator` agents power the same pipeline Forge uses, giving you a unified AI development experience
- **Sentinel + Cortex**: Both track session intelligence — Sentinel focuses on code review learnings and session health, Cortex focuses on cross-project patterns and self-evolution
- **Sentinel + Clamper**: Sentinel's `pre-edit-security.py` hook complements Clamper's verification loop — security blocking happens before the edit, verification after
- **codebase-radar + Sentinel**: `radar-explorer` pairs naturally with `sentinel-reviewer` — semantic search surfaces the right code context before review agents analyze it
- **codebase-radar + Clamper**: radar-explorer finds code by concept; Clamper maps fragile zones by git history. Together: the deepest codebase understanding available
- **codebase-radar + Cortex**: Cortex tracks what decisions were made; codebase-radar makes the code itself semantically searchable. Session intelligence meets semantic search

---

## Updating Plugins

When we release new versions:

```bash
# Update the marketplace catalog first
claude plugin marketplace update pretinnov-plugins

# Then update individual plugins
claude plugin update sentinel@pretinnov-plugins
claude plugin update clamper@pretinnov-plugins
claude plugin update cortex@pretinnov-plugins
claude plugin update forge@pretinnov-plugins
claude plugin update codebase-radar@pretinnov-plugins
```

---

## Uninstalling

```bash
claude plugin uninstall sentinel@pretinnov-plugins
claude plugin uninstall clamper@pretinnov-plugins
claude plugin uninstall cortex@pretinnov-plugins
claude plugin uninstall forge@pretinnov-plugins
claude plugin uninstall codebase-radar@pretinnov-plugins

# Remove the marketplace entirely
claude plugin marketplace remove pretinnov-plugins
```

---

## Each Plugin Has Its Own Detailed README

- [Sentinel README](./plugins/sentinel/README.md) — Full guide with all 9 categories, 24 agents, 7 hooks, and v3 typed learning store
- [Clamper README](./plugins/clamper/README.md) — Full guide with verification workflow and project DNA extraction
- [Cortex README](./plugins/cortex/README.md) — Full guide with every command, self-evolution, and cross-project learning
- [Forge README](./plugins/forge/README.md) — Full guide for building plugins from chat prompts
- [codebase-radar README](./plugins/codebase-radar/README.md) — Full guide for hybrid semantic search, LanceDB setup, and MCP tools

---

## License

MIT — Use it, modify it, share it. No restrictions.

## Author

**Siddharth Gupta** — [PretInnov Technologies](https://github.com/PretInnov-Inc)
