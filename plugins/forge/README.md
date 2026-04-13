# Forge — Build Claude Code Plugins by Talking

> **Build plugins from prompts.**
>
> By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)

---

## What Is Forge?

You know how Claude can build apps for you by chatting? **Forge does the same thing, but for Claude Code plugins.**

Instead of manually creating 20+ files with the exact right YAML frontmatter, JSON schemas, hook configurations, agent definitions, and skill files — you just say:

> "/forge I want a plugin that automatically runs my tests after every code edit and tracks which tests break most often"

And Forge will:
1. **Research** — Search the internet for existing testing plugins, scan GitHub for similar solutions, check what already exists
2. **Ask Questions** — "Should it run tests after every edit or only when you ask? Should it track flaky tests? What test framework do you use?"
3. **Design** — Create a complete architecture blueprint with directory tree, hook event map, agent roster, data schemas
4. **Generate** — Write every single file: manifest, hooks, handlers, agents, skills, data config, install script

The result is a fully functional, production-grade plugin that follows all the same patterns as Clamper and Cortex (two real-world plugins that Forge was trained on).

---

## How to Install

### From Our Marketplace (Recommended)

```bash
# Add the marketplace (one-time)
claude plugin marketplace add github:PretInnov-Inc/forge-marketplace

# Install Forge
claude plugin install forge@pretinnov-plugins
```

### Local Testing

```bash
git clone https://github.com/PretInnov-Inc/forge-marketplace.git
claude --plugin-dir ./forge-marketplace/plugins/forge
```

### After Installing

Run the installer to validate and seed templates:
```bash
bash forge/scripts/install.sh
```

You'll see:
```
═══════════════════════════════════════════
  PLUGIN FORGE installed successfully!
═══════════════════════════════════════════
  5 Subagents  — researcher, architect, generator, validator, learner
  8 Skills     — forge, research, blueprint, generate, validate, add-component, learn, dashboard
  4 Hooks      — SessionStart, Stop, PostToolUse, PreCompact
  1 CLI Tool   — forge-inspect
  14 Templates — proven patterns from Clamper + Cortex
```

---

## How to Use — The Main Command

### `/forge` — Create a Plugin (Full Pipeline)

This is the main command. It runs all 4 phases automatically.

```bash
/forge I want a plugin that tracks code complexity and warns when functions get too complex
```

**Here's what happens, step by step:**

---

#### Phase 1: Research (Automatic)

Forge searches the internet for existing solutions:

```
═══════════════════════════════════════════
  FORGE RESEARCH REPORT: code-complexity
═══════════════════════════════════════════

  Existing Solutions Found:
  - complexity-tracker-plugin (github.com/...) — Basic, only counts lines
  - code-metrics-skill (awesome-claude-code) — Single skill, no hooks

  Gaps Our Plugin Could Fill:
  - No existing plugin tracks complexity OVER TIME
  - No existing plugin warns DURING editing (via PostToolUse hook)
  - No existing plugin breaks down by function/method

  Patterns Worth Adopting:
  - Use radon (Python) or escomplex (JS) for complexity calculation
  - Track trends in JSONL, not just current state

═══════════════════════════════════════════
```

#### Phase 2: Clarify (Interactive)

Forge asks you 4-8 questions to understand exactly what you need:

```
Questions:
1. Which languages should it support? (Python, JavaScript, TypeScript, all?)
2. Should it warn during editing (automatic) or only when you ask (manual)?
3. What complexity threshold triggers a warning? (cyclomatic complexity > 10?)
4. Should it track trends over time, or just show current state?
5. Do you need a dashboard to visualize complexity trends?
```

You answer each question, and Forge uses your answers to design the plugin.

#### Phase 3: Blueprint (Architecture Design)

Forge designs the complete architecture and shows it to you for approval:

```
═══════════════════════════════════════════
  PLUGIN FORGE — Architecture Blueprint
  complexity-tracker v1.0.0
═══════════════════════════════════════════

  Directory Structure:
  complexity-tracker/
  ├── .claude-plugin/plugin.json
  ├── hooks/hooks.json
  ├── hooks-handlers/
  │   ├── session-start.sh        (inject past complexity data)
  │   └── post-edit-complexity.py  (calculate complexity after edits)
  ├── agents/
  │   ├── complexity-analyzer.md   (deep analysis agent)
  │   └── complexity-advisor.md    (recommendations agent)
  ├── skills/
  │   ├── complexity/SKILL.md      (main command)
  │   ├── trends/SKILL.md          (trend analysis)
  │   └── refactor/SKILL.md        (refactoring suggestions)
  ├── data/
  │   ├── complexity-config.json
  │   └── complexity-log.jsonl
  └── scripts/install.sh

  Hook Event Map:
  | Event       | Handler                  | Purpose              |
  |-------------|--------------------------|----------------------|
  | SessionStart| session-start.sh         | Inject complexity data|
  | PostToolUse | post-edit-complexity.py  | Check after edits    |

  Agent Roster:
  | Agent               | Model  | Tools              |
  |---------------------|--------|--------------------|
  | complexity-analyzer | sonnet | Read,Grep,Glob,Bash|
  | complexity-advisor  | haiku  | Read,Grep,Glob     |

  Waiting for your approval to proceed.
═══════════════════════════════════════════
```

You review it, maybe ask for changes, then approve.

#### Phase 4: Generate (Code Writing)

Forge writes every file. You'll see them being created one by one:

```
  Creating .claude-plugin/plugin.json... ✓
  Creating hooks/hooks.json... ✓
  Creating hooks-handlers/session-start.sh... ✓
  Creating hooks-handlers/post-edit-complexity.py... ✓
  Creating agents/complexity-analyzer.md... ✓
  Creating agents/complexity-advisor.md... ✓
  Creating skills/complexity/SKILL.md... ✓
  Creating skills/trends/SKILL.md... ✓
  Creating skills/refactor/SKILL.md... ✓
  Creating data/complexity-config.json... ✓
  Creating scripts/install.sh... ✓

═══════════════════════════════════════════
  FORGED: complexity-tracker v1.0.0
  11 files | 2 agents | 3 skills | 2 hooks
═══════════════════════════════════════════

  Quick start:
    claude --plugin-dir ./complexity-tracker

  Available commands:
    /complexity-tracker:complexity   — Analyze current complexity
    /complexity-tracker:trends       — View complexity trends
    /complexity-tracker:refactor     — Get refactoring suggestions
═══════════════════════════════════════════
```

**That's it.** You now have a fully functional plugin, created from a single chat prompt.

---

## Other Commands

### `/forge:research <concept>` — Research Only

Just want to know what exists before committing to building something?

```bash
/forge:research testing automation for python projects
```

This runs Phase 1 only — searches the internet, scans GitHub, reports findings. No code is written.

---

### `/forge:blueprint <name>` — Design Only

Already know what you want but want to design the architecture before generating?

```bash
/forge:blueprint my-testing-plugin
```

This runs Phase 3 only — creates the architecture blueprint for your approval.

---

### `/forge:generate <name>` — Generate Only

Already have an approved blueprint? Skip straight to code generation:

```bash
/forge:generate my-testing-plugin
```

This runs Phase 4 only — reads the approved blueprint from Forge's data and writes all files.

---

### `/forge:validate <path>` — Validate a Plugin

Built a plugin (manually or with Forge) and want to check it's correct?

```bash
# Validate a plugin in the current directory
/forge:validate

# Validate a plugin at a specific path
/forge:validate ./my-plugin
```

This checks 9 categories:
- Structure, Manifest, Hooks, Agents, Skills, Data, Paths, Security, Install Script

```
═══════════════════════════════════════════
  FORGE VALIDATION REPORT: my-plugin
═══════════════════════════════════════════

  Structure:    ✓ PASS
  Manifest:     ✓ PASS
  Hooks:        ✓ PASS
  Agents:       ✓ PASS (2 agents)
  Skills:       ✓ PASS (3 skills)
  Data:         ✓ PASS
  Paths:        ✓ PASS
  Security:     ✓ PASS
  Install:      ✓ PASS

  Overall: PASS — 0 issues found
═══════════════════════════════════════════
```

---

### `/forge:add-component <type> <plugin-path>` — Add to Existing Plugin

Already have a plugin and want to add a new hook, agent, or skill?

```bash
# Add a new hook to an existing plugin
/forge:add-component hook ./my-plugin

# Add a new agent
/forge:add-component agent ./my-plugin

# Add a new skill
/forge:add-component skill ./my-plugin

# Add MCP server config
/forge:add-component mcp ./my-plugin

# Add a bin tool
/forge:add-component bin ./my-plugin
```

Forge will:
1. Read your existing plugin structure
2. Ask what the new component should do
3. Generate it following your plugin's conventions
4. Update the manifest and install script

---

### `/forge:learn` — Mine Past Build Patterns

```bash
# Mine patterns from all past builds
/forge:learn

# Manually record a learning
/forge:learn record Hook handlers should always handle missing data files gracefully

# Show all learnings
/forge:learn show
```

---

### `/forge:dashboard` — Build History & Stats

```bash
/forge:dashboard
```

```
═══════════════════════════════════════════
  PLUGIN FORGE DASHBOARD
═══════════════════════════════════════════

  Build Stats:
    Total builds:     12
    Success rate:     83%
    Files generated:  247
    Agents created:   31
    Skills created:   42

  Recent Builds:
    2026-04-10 | OK   | complexity-tracker | 11 files | health: 85/100
    2026-04-08 | OK   | deploy-helper      | 15 files | health: 92/100
    2026-04-05 | FAIL | mcp-bridge         |  3 files | health: 35/100

  Learning System:
    23 learnings | 14 seeded templates

═══════════════════════════════════════════
```

---

## What Happens Automatically (Hooks)

### 1. Session Start — Loads Build Intelligence
Every session, Forge injects:
- Past build learnings (what worked, what failed)
- Recent build history
- Active blueprints waiting for generation
- Component templates for reference

### 2. After Every File Write — Quality Checks
When you're building a plugin (even manually), Forge watches and warns:
- "You're writing a SKILL.md without frontmatter"
- "This hook handler imports a non-stdlib module"
- "Hardcoded absolute path detected — use ${CLAUDE_PLUGIN_ROOT}"

### 3. Session End — Outcome Capture
After a build session, Forge captures:
- How many files were generated
- Whether research was done
- Whether validation passed
- Health score for the build

### 4. Before Compaction — Blueprint Preservation
If Claude's context is about to be compacted during a build, Forge saves:
- Which phase you're in
- Active plugin name
- What's already been generated

---

## The 5 Agents Inside Forge

| Agent | What It Does | Model | Writes Files? |
|-------|-------------|-------|--------------|
| **forge-researcher** | Searches internet, scans GitHub, finds existing solutions | sonnet | No |
| **forge-architect** | Designs plugin blueprints with full schemas and rationale | sonnet | No |
| **forge-generator** | Writes all plugin files based on approved blueprints | sonnet | Yes |
| **forge-validator** | Checks plugins for 9 categories of correctness | haiku (fast) | No |
| **forge-learner** | Mines build history for patterns, promotes learnings | sonnet | Yes (data only) |

---

## The Learning Loop

Forge gets BETTER at building plugins over time:

```
Build #1 → Forge generates a plugin → Outcome captured
Build #2 → Past learnings injected → Forge avoids past mistakes
Build #3 → Patterns promoted → Templates refined
Build #10 → Forge knows your preferences → Builds match your style
```

14 component templates are pre-seeded from analyzing Clamper and Cortex (two production plugins). As you build more, Forge adds your own patterns to its template library.

---

## CLI Tool: `forge-inspect`

Available in any Bash command when Forge is enabled:

```bash
forge-inspect stats       # Build statistics
forge-inspect builds      # Recent build history
forge-inspect learnings   # All accumulated learnings
forge-inspect research    # Research cache
forge-inspect blueprints  # Saved blueprints
forge-inspect config      # Current configuration
forge-inspect trim        # Trim data files to size limits
forge-inspect validate ./my-plugin  # Quick validation
```

---

## Troubleshooting

**"Research phase didn't find anything useful"**
- Try a more specific concept description
- Run `/forge:research` separately with different search terms
- Some concepts are very new — no existing solutions is actually good news

**"Blueprint seems too complex for what I need"**
- Tell Forge: "Make it simpler — I only need 1 hook and 2 skills"
- You can edit the blueprint before approving it

**"Generated files have issues"**
- Run `/forge:validate ./my-plugin` to see specific problems
- Most issues are minor (missing frontmatter fields, wrong path format)

**"I want to modify a generated plugin"**
- Just edit the files directly — they're regular files
- Use `/forge:add-component` to add new pieces
- Re-run `/forge:validate` after changes

---

## Part of the PretInnov Plugin Ecosystem

Forge is one of 5 plugins in the [PretInnov Marketplace](../../README.md):

| Plugin | What It Does |
|--------|-------------|
| **[Sentinel](../sentinel/README.md)** | 9-category unified intelligence — code review, AI dev, browser testing, memory, design, docs, infra, DX |
| **[Clamper](../clamper/README.md)** | Code verification, project DNA, ecosystem scaffolding |
| **[Cortex](../cortex/README.md)** | Self-learning intelligence — cross-project patterns, decision tracking, self-evolution |
| **Forge** (you are here) | Plugin builder — create full plugins from chat prompts |
| **[codebase-radar](../codebase-radar/README.md)** | Hybrid semantic + BM25 search via LanceDB — find code by meaning, auto-reindex as you edit |

**Forge + Sentinel:** Sentinel includes its own AI development toolkit (`/sentinel:ai-forge`) powered by 3 dedicated agents (ai-architect, ai-builder, ai-validator). When both plugins are installed, you can use either `/forge` (standalone pipeline with 5 agents) or `/sentinel:ai-forge` (integrated with Sentinel's data store and learnings). Forge is the specialist; Sentinel's ai-forge is the generalist that shares context with the other 8 categories.

**Forge + codebase-radar:** When building a new plugin, use `/radar:search` to find how existing plugins in the codebase implement patterns before Forge generates new code. Research phase gets richer context, generated code matches conventions better.

---

## License

MIT — By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)
