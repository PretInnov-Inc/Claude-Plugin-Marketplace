# Clamper — Code Verification & Project DNA Plugin

> **Clip it, Clamp it.**
>
> By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)

---

## What Is Clamper?

Imagine you're coding with Claude, and it edits a file. How do you know the edit was safe? How do you know it didn't break something? How do you know which files in your project are fragile and need extra care?

**That's what Clamper does.**

Clamper is a Claude Code plugin that adds three things Claude doesn't have by default:

1. **A Verification Loop** — After Claude edits your code, Clamper automatically checks if the edit was risky (did it touch security files? config files? was it a huge deletion?). You can also manually run a deep verification with `/clamper:clamp`.

2. **Project DNA Extraction** — Clamper scans your entire project and figures out: which files change the most (hot files), which files are fragile (lots of changes but no tests), which files always change together (coupling), and what your tech stack looks like.

3. **One-Command Ecosystem Init** — Run `/clamper:init` on ANY project and Clamper creates a complete agent setup: CLAUDE.md rules file, custom subagents, skills, and memory — tailored to YOUR project's actual code, not generic templates.

---

## How to Install

### Option 1: From Our Marketplace (Recommended)

If you haven't added our marketplace yet:
```bash
claude plugin marketplace add github:PretInnov-Inc/forge-marketplace
```

Then install Clamper:
```bash
claude plugin install clamper@pretinnov-plugins
```

### Option 2: Direct Install (Standalone)

```bash
claude plugin add github:PretInnov-Inc/forge-marketplace --path plugins/clamper
```

### Option 3: Local Testing (For Developers)

```bash
git clone https://github.com/PretInnov-Inc/forge-marketplace.git
claude --plugin-dir ./forge-marketplace/plugins/clamper
```

### After Installing

Run the install script to validate everything is set up correctly:
```bash
bash clamper/scripts/install.sh
```

You should see:
```
═══════════════════════════════════════════
  CLAMPER installed successfully!
═══════════════════════════════════════════
  4 Subagents  — verifier, scout, learner, architect
  4 Commands   — /init, /clamp, /dna, /clamper
  3 Skills     — ecosystem-init, verification, project-dna
  3 Hooks      — SessionStart, PostToolUse, Stop
```

---

## How to Use — Every Command Explained

### `/clamper:init` — Set Up Your Project (Start Here!)

**What it does:** Scans your project, understands the tech stack, architecture, and conventions, then generates a complete agent ecosystem tailored to YOUR project.

**When to use it:** Run this ONCE when you start working on a new project with Claude Code.

**How to use it:**

```bash
# Just run it — Clamper figures out everything automatically
/clamper:init

# Force regenerate (if you already ran it before)
/clamper:init --force

# Just see what it would create, without writing files
/clamper:init --dry-run

# Create only the essentials (CLAUDE.md + AGENTS.md + MEMORY.md)
/clamper:init --minimal
```

**What happens step by step:**

1. Clamper checks if your project already has agent config files (CLAUDE.md, .claude/, etc.)
2. If it's an existing project with code, Clamper's **Scout agent** analyzes your codebase:
   - Reads package.json / pyproject.toml / Cargo.toml to detect your stack
   - Runs `git log` to find hot files and code coupling
   - Scans for test coverage gaps
   - Maps your architecture
3. If it's a brand new project, Clamper asks you 6 questions (name, description, stack, etc.)
4. Clamper's **Architect agent** generates:
   - `CLAUDE.md` — Project-specific rules (under 150 lines, not generic fluff)
   - `AGENTS.md` — Symlink to CLAUDE.md for cross-platform compatibility
   - `.claude/agents/` — 2-4 custom subagents (always code-reviewer + test-writer, plus conditional ones like api-designer or security-auditor)
   - `.claude/skills/` — Project-specific skills
   - `.claude/memory/` — Memory system with project DNA

**Example output:**
```
═══════════════════════════════════════════
  CLAMPER INIT — my-web-app
═══════════════════════════════════════════
  
  Created:
    CLAUDE.md              (128 lines, tailored to Next.js + TypeScript)
    AGENTS.md              (symlink → CLAUDE.md)
    .claude/agents/
      code-reviewer.md     (TypeScript-focused review agent)
      test-writer.md       (Jest + React Testing Library agent)
      api-designer.md      (REST API design agent — detected Express routes)
    .claude/skills/
      project-review/SKILL.md
    .claude/memory/
      MEMORY.md
      project-dna.md

  Compatible with: Claude Code, Cursor, Codex CLI, Gemini CLI
═══════════════════════════════════════════
```

---

### `/clamper:clamp` — Verify Your Code Changes

**What it does:** Checks your recently edited files for correctness, test coverage, security issues, and gives you a confidence score from 0-100.

**When to use it:** After you've made changes and want to make sure nothing is broken before committing.

**How to use it:**

```bash
# Verify the last 3-5 files you edited
/clamper:clamp

# Verify a specific file
/clamper:clamp src/auth/login.ts

# Verify ALL files you changed in this session
/clamper:clamp all

# Re-run the last verification
/clamper:clamp last
```

**What happens behind the scenes:**

Clamper's **Verifier agent** (runs on the fast haiku model for speed) does a 5-step check:

1. **Reads your modified files** — Understands what changed
2. **Checks project standards** — Are you following the conventions in CLAUDE.md?
3. **Runs tests** — If tests exist, runs them to make sure they pass
4. **Security scan** — Looks for hardcoded secrets, SQL injection risks, XSS vulnerabilities
5. **Scores and reports** — Gives you a confidence score

**Example output:**
```
═══════════════════════════════════════════
  CLAMPER VERIFICATION REPORT
═══════════════════════════════════════════

  Files verified: src/auth/login.ts, src/auth/session.ts
  
  Checks:
    [PASS] Code compiles without errors
    [PASS] Follows project TypeScript conventions
    [WARN] No test file found for session.ts
    [PASS] No hardcoded secrets detected
    [PASS] Input validation present on login route

  Confidence: 82/100
  Status: MINOR ISSUES — consider adding tests for session.ts

  Clamped. 2 files verified, confidence 82/100.
═══════════════════════════════════════════
```

**What do the confidence scores mean?**
- **90-100**: Clean — everything looks great
- **70-89**: Minor issues — small things to fix but nothing dangerous
- **50-69**: Concerns — you should review these carefully
- **Below 50**: Significant problems — FLAGGED FOR HUMAN REVIEW

---

### `/clamper:dna` — Understand Your Project's DNA

**What it does:** Deep-scans your entire project and tells you everything about its structure: which files are hot (changed a lot), which are fragile (changed a lot but have no tests), which files always change together, and what your tech stack looks like.

**When to use it:** When you're new to a codebase, or when you want to know where the risky parts are.

**How to use it:**

```bash
# Full DNA extraction of current project
/clamper:dna

# Scan a specific path
/clamper:dna /path/to/other/project

# Clear the cache and re-scan from scratch
/clamper:dna refresh

# Show only fragile zones (high-risk files)
/clamper:dna fragile

# Show only files that change together
/clamper:dna coupling
```

**What you get:**

```
═══════════════════════════════════════════
  PROJECT DNA — my-web-app
═══════════════════════════════════════════

  Hot Files (changed most in last 100 commits):
    src/api/routes.ts          — 23 changes
    src/components/Dashboard.tsx — 18 changes
    src/utils/helpers.ts        — 15 changes

  Fragile Zones (lots of changes + NO tests):
    ⚠️ src/api/routes.ts       — 23 changes, NO test file
    ⚠️ src/utils/helpers.ts    — 15 changes, NO test file

  Coupling Groups (files that always change together):
    src/api/routes.ts ↔ src/types/api.ts (co-changed 12 times)
    src/components/Dashboard.tsx ↔ src/hooks/useDashboard.ts (co-changed 8 times)

  Test Coverage Map:
    src/components/ — 67% files have tests
    src/api/        — 20% files have tests  ⚠️
    src/utils/      — 0% files have tests   ⚠️

  DNA extracted. 3 hot files, 2 fragile zones, 2 coupling groups identified.
═══════════════════════════════════════════
```

**Why this matters:** If Claude is about to edit `src/api/routes.ts` and Clamper knows it's a fragile zone with no tests, it can warn you to be extra careful.

---

### `/clamper:clamper` — View the Dashboard

**What it does:** Shows you a summary of all Clamper activity — verification history, quality trends, project DNA, and configuration.

**How to use it:**

```bash
# Full dashboard
/clamper:clamper

# Quick stats only
/clamper:clamper stats

# View configuration (thresholds, suppressed warnings)
/clamper:clamper config

# Trigger a learning cycle (find patterns in past sessions)
/clamper:clamper learn
```

**Example dashboard:**
```
═══════════════════════════════════════════
  CLAMPER DASHBOARD
═══════════════════════════════════════════

  Verifications: 47 total | 89% pass rate
  Flagged:       5 files flagged for human review
  
  Session Quality (last 5 sessions):
    Session 1: 85/100 ▲
    Session 2: 72/100 ▼
    Session 3: 91/100 ▲
    Session 4: 88/100 ▲
    Session 5: 79/100 ▼
  
  Trend: STABLE (avg 83/100)
  
  Fragile Zones: 2 files need attention
  Hot Files: 3 files with high churn
═══════════════════════════════════════════
```

---

## What Happens Automatically (Hooks)

You don't need to run any commands for these — they happen on their own:

### 1. Session Start — Context Injection
Every time you start a new Claude Code session, Clamper automatically loads:
- Your recent verification results
- Known fragile zones
- Past session quality scores
- Project DNA

This means Claude STARTS every session already knowing where the risky parts of your code are.

### 2. After Every Edit — Risk Detection
Every time Claude edits a file (Write, Edit, or MultiEdit), Clamper checks:
- Is this a test file? (risk: you might break tests)
- Is this a config file? (risk: could affect the whole project)
- Is this a security-related file? (auth, login, permissions, etc.)
- Was it a huge edit? (100+ lines changed)
- Was it mostly deletions? (deleting more than adding)
- Has this file been edited 5+ times? (churn warning)

If it detects risk, you'll see a warning message like:
```
⚠️ CLAMPER HIGH RISK: Security-sensitive file modified (src/auth/login.ts)
   Signals: [security-sensitive-file, config-file-modification]
   Consider running /clamp to verify.
```

### 3. Session End — Outcome Capture
When your session ends, Clamper reads the transcript and:
- Counts how many files were modified
- Checks if tests were run and passed
- Detects errors and warnings
- Calculates a quality score (0-100)
- Saves everything so the NEXT session can learn from this one

---

## The 4 Agents Inside Clamper

| Agent | What It Does | Speed |
|-------|-------------|-------|
| **clamper-verifier** | The verification engine. Reads files, checks standards, runs tests, scores confidence. | Fast (haiku) |
| **clamper-scout** | The DNA extractor. Analyzes git history, maps architecture, finds fragile zones. | Thorough (sonnet) |
| **clamper-learner** | The pattern miner. Reads past data to find what works and what keeps failing. | Thorough (sonnet) |
| **clamper-architect** | The ecosystem builder. Generates CLAUDE.md, agents, skills tailored to your project. | Thorough (sonnet) |

---

## Data Files (Where Clamper Stores Its Knowledge)

All data lives in the `data/` folder inside the plugin:

| File | What's In It |
|------|-------------|
| `clamper-config.json` | Configuration: thresholds, suppressed warnings, stats |
| `verification-log.jsonl` | Every edit tracked + every verification result |
| `dna-cache.jsonl` | Project architecture, fragile zones, coupling maps |
| `outcomes.jsonl` | Session-level quality scores and summaries |

These files grow over time. Clamper automatically trims them when they get too big (keeps last 2000 entries).

---

## Optional: MCP Server

Clamper includes an optional MCP (Model Context Protocol) server that provides 8 tools for programmatic access to DNA and verification data. Install it with:

```bash
bash scripts/install.sh --with-mcp
```

This requires Python 3.10+ and installs via pip.

---

## Troubleshooting

**"Command not found" when I type /clamper:clamp**
- Make sure the plugin is installed: check `/help` for the command list
- Try `/reload-plugins` to refresh

**Verification always says "No files to verify"**
- You need to have edited files in the current session first
- Try `/clamper:clamp src/some-file.ts` with a specific file

**DNA scan says "Not a git repository"**
- Clamper needs git history for DNA extraction. Run `git init` first.

**Hook warnings are annoying**
- Use `/clamper:clamper config` to see your thresholds
- You can suppress specific warnings by editing `data/clamper-config.json`

---

## Part of the PretInnov Plugin Ecosystem

Clamper is one of 4 plugins in the [PretInnov Marketplace](../../README.md):

| Plugin | What It Does |
|--------|-------------|
| **[Sentinel](../sentinel/README.md)** | 9-category unified intelligence — code review, AI dev, browser testing, memory, design, docs, infra, DX |
| **Clamper** (you are here) | Code verification, project DNA, ecosystem scaffolding |
| **[Cortex](../cortex/README.md)** | Self-learning intelligence — cross-project patterns, decision tracking, self-evolution |
| **[Forge](../forge/README.md)** | Plugin builder — create full plugins from chat prompts |

**Clamper + Sentinel:** Sentinel's PreToolUse hook blocks dangerous edits before they happen. Clamper's verification loop checks code quality after. Together: prevention + verification. Sentinel handles the multi-agent code review, Clamper handles project DNA extraction and ecosystem initialization.

---

## License

MIT — By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)
