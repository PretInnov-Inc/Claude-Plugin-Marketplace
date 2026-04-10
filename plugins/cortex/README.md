# Cortex — Self-Learning Intelligence Layer for Claude Code

> **Claude Code with a brain.**
>
> By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)

---

## What Is Cortex?

Here's the problem: Every time you start a new Claude Code session, Claude forgets everything. It doesn't remember that you hate Vue.js. It doesn't remember that your tests broke last time because of a database migration. It doesn't remember that you prefer Django over Flask. It starts from zero. Every. Single. Time.

**Cortex fixes this.**

Cortex is a self-learning intelligence layer that sits on top of Claude Code and does 6 things:

1. **Captures Learnings** — Every session, Cortex reads the transcript and extracts useful patterns: what technologies were used, what errors occurred, what decisions were made, what files were modified.

2. **Remembers Anti-Patterns** — Things that went wrong. "Don't auto-commit without asking." "Don't use Vue.js for this project." "Don't plan more than 5 tasks per session." These are recorded and warned about.

3. **Tracks Decisions** — When you decide "use Django instead of Flask" or "switch the theme to light mode," Cortex records it with the reasoning. So next time, Claude knows WHY you made that choice.

4. **Injects Context** — At the START of every session, Cortex automatically loads your learnings, anti-patterns, decisions, and session stats into Claude's context. Claude starts smart, not blank.

5. **Guards Against Mistakes** — Before Claude runs a dangerous command (force push, rm -rf, hardcoded secrets), Cortex warns you. It also checks against YOUR specific anti-patterns, not just generic rules.

6. **Evolves Itself** — Over time, Cortex adjusts its own thresholds based on your behavior. If you keep ignoring a warning, it suppresses it. If a pattern appears 5+ times, it promotes it to a permanent learning.

---

## How to Install

### From Our Marketplace (Recommended)

```bash
# Add the marketplace (one-time)
claude plugin marketplace add github:PretInnov-Inc/forge-marketplace

# Install Cortex
claude plugin install cortex@pretinnov-plugins
```

### Local Testing

```bash
git clone https://github.com/PretInnov-Inc/forge-marketplace.git
claude --plugin-dir ./forge-marketplace/plugins/cortex
```

### During Installation, You'll Be Asked:

Cortex has 5 configuration options it asks when you enable it:

| Setting | What It Means | Default |
|---------|--------------|---------|
| `scope_task_threshold` | How many tasks before Cortex warns you about scope creep | 5 |
| `repetitive_edit_threshold` | How many times you edit the same file before Cortex flags it | 5 |
| `auto_evolution` | Should Cortex automatically adjust its own rules? | true |
| `default_output_style` | How Claude formats responses: `learning`, `terse`, or `verbose` | learning |
| `health_alert_threshold` | Session health score below which Cortex alerts you | 40 |

Don't worry about getting these perfect — Cortex adjusts them over time if you enable auto_evolution.

---

## How to Use — Every Command Explained

### `/cortex:cortex` — The Dashboard

**What it does:** Shows you everything Cortex knows — learnings, anti-patterns, decisions, session stats, and health trends.

**How to use it:**
```bash
# Full dashboard
/cortex:cortex
```

**Example output:**
```
═══════════════════════════════════════════
  CORTEX DASHBOARD
═══════════════════════════════════════════

  Sessions: 47 total | Avg health: 68/100
  Learnings: 23 recorded
  Anti-patterns: 8 active
  Decisions: 12 tracked (3 pending)

  Recent Session Health:
    #47: 82/100 ▲  (django project, 4 files modified)
    #46: 55/100 ▼  (scope creep, 2 errors)
    #45: 91/100 ▲  (clean session, tests passed)

  Top Learnings:
    - [scope] Sessions with 5+ tasks complete at 40% rate
    - [testing] Testing is nearly always skipped when it's the last task
    - [stack] Django + HTMX + Tailwind is the validated stack

  Active Anti-Patterns:
    - Don't auto-commit without explicit user request
    - Don't propose SDK approaches without verifying installed packages
    - Don't plan 10+ step tasks in a single session
═══════════════════════════════════════════
```

---

### `/cortex:decisions` — Decision Journal

**What it does:** Records, queries, and manages important decisions you make during coding.

**Why it matters:** Two weeks from now, you won't remember WHY you chose Django over Flask. Cortex remembers for you, and tells Claude about it in future sessions.

**How to use it:**

```bash
# See all decisions for current project
/cortex:decisions

# Record a new decision
/cortex:decisions add Use PostgreSQL instead of SQLite for production

# Search decisions
/cortex:decisions search authentication

# Close a decision (mark outcome as success/failure)
/cortex:decisions close 3 success Worked perfectly in production

# See only pending decisions
/cortex:decisions pending
```

**Example decision entry:**
```json
{
  "decision": "Use Django 6 + Templates + Tailwind + HTMX + Alpine.js",
  "type": "technology",
  "reasoning": "Standardize 60+ projects on a modern, cohesive stack",
  "project": "tour2tech-projects",
  "outcome": "success"
}
```

---

### `/cortex:health` — System Health Check

**What it does:** Checks that everything in Cortex is working properly — data files aren't corrupted, hooks are firing, memory isn't bloated, plugin structure is intact.

**When to use it:** When something seems off, or periodically to make sure Cortex is healthy.

```bash
/cortex:health
```

**Example output:**
```
  Data Integrity:    ✓ All 10 data files valid
  Hooks:             ✓ All 6 hooks configured
  Memory:            ✓ 23 learnings, 8 anti-patterns
  Plugin Structure:  ✓ All files present
  Overall:           HEALTHY
```

---

### `/cortex:evolve` — Self-Evolution Controls

**What it does:** Lets you manage how Cortex adapts itself over time.

**How to use it:**

```bash
# See what evolution actions Cortex has taken
/cortex:evolve status

# Review pending evolution suggestions
/cortex:evolve review

# Apply a suggested evolution
/cortex:evolve apply

# Undo the last evolution
/cortex:evolve undo

# Suppress a specific warning permanently
/cortex:evolve suppress scope-warning

# Manually tune a threshold
/cortex:evolve tune scope_task_threshold 7
```

**How self-evolution works:**

Cortex tracks every warning it fires and every time you ignore it. When a warning is ignored 10+ times, Cortex suggests suppressing it. When a pattern appears 5+ times, Cortex suggests promoting it to a permanent learning. These changes are logged in `evolution-log.jsonl` and can always be undone.

**Safety rails:**
- Core rules (8 hardcoded rules) can NEVER be changed
- Maximum 3 auto-evolutions per session (prevents runaway changes)
- Contradictions are flagged, not applied
- You can always undo any evolution

---

### `/cortex:learn` — Manual Learning

**What it does:** Force-extract learnings from the current session, or manually record a learning.

```bash
# Force-extract learnings from current session transcript
/cortex:learn

# Manually record a specific learning
/cortex:learn record Always run migrations before deploying to staging

# Show all learnings
/cortex:learn show

# Filter by category
/cortex:learn show testing-discipline
```

---

### `/cortex:clean` — Workspace Cleanup

**What it does:** Scans your `.claude/` directory for dead weight — old memory files, stale configs, duplicate entries — and helps you clean up.

```bash
/cortex:clean
```

---

## What Happens Automatically (You Don't Need to Do Anything)

### 1. Session Start — Intelligence Injection

Every time you start a Claude Code session, Cortex automatically:
- Loads your last 15 learnings
- Loads your last 10 anti-patterns
- Loads recent decisions for the current project
- Shows session stats (including your 60% session failure rate reminder)
- Injects 8 core rules that always apply
- Loads any pending user feedback

**You'll never see this happening** — it's injected into Claude's context silently. But Claude will behave differently because of it. For example, if you've told Cortex "don't use Vue.js," Claude will avoid suggesting Vue.js in future sessions.

### 2. Every Message — Scope Detection

Before Claude processes your message, Cortex checks:
- **Scope creep**: If you ask for 5+ distinct tasks in one message, Cortex warns: "This prompt contains 7 distinct tasks. Sessions with 5+ tasks complete at 40% rate. Consider breaking this into smaller sessions."
- **Repetition**: If you've sent 3+ similar messages in a row, Cortex warns: "You may be stuck in a loop — 3 similar prompts detected."
- **Broad language**: If you say "fix everything" or "update all files," Cortex flags it.

### 3. Before Every Tool Use — Anti-Pattern Guard

Before Claude runs a command or edits a file, Cortex checks:
- Is Claude about to `git push` without you asking? → Warning
- Is Claude about to `rm -rf` something? → Warning
- Is Claude about to write secrets into a file? → Warning
- Is this command similar to a past mistake from anti-patterns? → Warning

These are NON-BLOCKING — Cortex warns, but doesn't stop Claude. You decide.

### 4. After Every Tool Use — Usage Tracking

Cortex silently tracks every tool invocation. If the same file is edited 5+ times in a session, it warns: "Repetitive edits detected on src/api/routes.ts (5 times). You might be stuck."

### 5. Before Context Compaction — Memory Preservation

When Claude's context window fills up and gets compacted (compressed), important information can be lost. Cortex detects this and saves:
- Active decisions being discussed
- File paths in context
- Any plans that were in progress

### 6. After Every Claude Response — Learning Extraction

After Claude finishes responding, Cortex reads the transcript tail and extracts:
- Errors and failures
- Technologies used
- Decisions made
- Files modified
- Completion status

It calculates a health score (0-100) and auto-adjusts thresholds if enabled.

---

## The 8 Agents Inside Cortex

| Agent | What It Does | Model | Can Write Files? |
|-------|-------------|-------|-----------------|
| **cortex-advisor** | Default conversational agent. The "face" of Cortex. | sonnet | Yes |
| **memory-curator** | Audits and cleans your memory files across projects | sonnet | Yes |
| **pattern-miner** | Data scientist — finds patterns in your accumulated data | sonnet | No (read-only) |
| **failure-investigator** | Root cause analysis when things go wrong | sonnet | No (read-only) |
| **session-analyst** | Productivity metrics and session analysis | sonnet | No (read-only) |
| **workspace-janitor** | Cleans up dead weight in .claude/ directory | sonnet | No (uses Bash) |
| **decision-tracker** | Records and queries decisions | sonnet | Yes (append-only) |
| **self-evolver** | Modifies Cortex's own rules and thresholds | **opus** | Yes (full access) |

The self-evolver uses the most powerful model (opus) because modifying the plugin itself requires the highest quality reasoning.

---

## Output Styles

Cortex comes with 3 response formatting modes:

| Style | What It Looks Like |
|-------|-------------------|
| **learning** (default) | Educational — explains insights, asks for your input on meaningful decisions |
| **terse** | Minimal — just code, no explanations, no summaries |
| **verbose** | Full transparency — explains every decision, references Cortex data |

Switch styles with:
```bash
/cortex:evolve tune default_output_style terse
```

---

## Data Files (Cortex's Brain)

All data lives in `data/` inside the plugin:

| File | What's In It | Size Limit |
|------|-------------|------------|
| `cortex-config.json` | Thresholds, suppressions, evolution stats | N/A (single file) |
| `learnings.jsonl` | Accumulated insights from past sessions | 200 entries |
| `anti-patterns.jsonl` | Mistakes to avoid | 100 entries |
| `decision-journal.jsonl` | All recorded decisions | 500 entries |
| `patterns.jsonl` | Detected behavioral patterns | 200 entries |
| `session-log.jsonl` | Session start/end events with health scores | 1000 entries |
| `prompt-log.jsonl` | Keywords from your messages (NOT full text — privacy!) | 500 entries |
| `tool-usage.jsonl` | Every tool invocation tracked | 2000 entries |
| `user-feedback.jsonl` | Your corrections and feedback about Cortex | 200 entries |
| `evolution-log.jsonl` | Audit trail of all self-modifications | 500 entries |

**Privacy note:** Cortex NEVER stores your full message text. Only keywords (words 4+ characters) are logged for pattern analysis.

---

## CLI Tool: `cortex-inspect`

When Cortex is enabled, you get a command-line tool you can use from Bash:

```bash
# Inside a Claude Code session, in any Bash command:
cortex-inspect health       # Quick health check
cortex-inspect learnings    # List all learnings
cortex-inspect anti-patterns # List all anti-patterns
cortex-inspect decisions    # List all decisions
cortex-inspect sessions     # Session history
cortex-inspect config       # Current configuration
cortex-inspect stats        # Quick stats summary
cortex-inspect trim         # Trim data files to size limits
cortex-inspect export       # Export all data to cortex-export.json
```

---

## Troubleshooting

**"Cortex keeps warning me about scope creep but I need to do a big task"**
- Adjust the threshold: `/cortex:evolve tune scope_task_threshold 10`
- Or suppress it: `/cortex:evolve suppress scope-warning`

**"I don't see any learnings being captured"**
- Learnings are extracted from the transcript. You need at least one session to complete.
- Run `/cortex:learn` to force-extract from the current session.

**"The session health scores seem wrong"**
- Health is calculated from: files modified, errors, completion signals, test results
- A session where Claude hit errors and didn't complete tasks will score low — that's expected
- Check `/cortex:cortex` for the scoring breakdown

**"I want to reset everything and start fresh"**
- Delete the files in `data/` (keep `cortex-config.json`, delete the .jsonl files)
- Or uninstall and reinstall: `claude plugin uninstall cortex@pretinnov-plugins`

---

## Part of the PretInnov Plugin Ecosystem

Cortex is one of 4 plugins in the [PretInnov Marketplace](../../README.md):

| Plugin | What It Does |
|--------|-------------|
| **[Sentinel](../sentinel/README.md)** | 9-category unified intelligence — code review, AI dev, browser testing, memory, design, docs, infra, DX |
| **[Clamper](../clamper/README.md)** | Code verification, project DNA, ecosystem scaffolding |
| **Cortex** (you are here) | Self-learning intelligence — cross-project patterns, decision tracking, self-evolution |
| **[Forge](../forge/README.md)** | Plugin builder — create full plugins from chat prompts |

**Cortex + Sentinel:** Both track session intelligence but from different angles. Sentinel focuses on code review learnings and per-session health scores. Cortex focuses on cross-project behavioral patterns and self-evolution. They complement each other — Sentinel makes your code better, Cortex makes your workflow better.

---

## License

MIT — By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)
