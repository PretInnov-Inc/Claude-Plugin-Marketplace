---
name: ecosystem-init
version: 1.0.0
description: "One-command cross-platform agent ecosystem initialization. Analyzes codebase DNA and scaffolds CLAUDE.md, AGENTS.md, subagents, skills, and memory — tailored to the actual project."
triggers:
  - "initialize ecosystem"
  - "set up agent ecosystem"
  - "create CLAUDE.md"
  - "create AGENTS.md"
  - "scaffold project"
  - "init project"
  - "set up agents"
  - "bootstrap project"
  - "create agent config"
---

# Clamper Ecosystem Init Skill

## Purpose

Most CLAUDE.md files are hand-written, generic, and go stale. Most agent ecosystems are either missing or copy-pasted from templates. This skill analyzes the actual codebase and generates an ecosystem that reflects the real project — not a template.

## What Gets Generated

The full cross-platform ecosystem structure:

```
<project-root>/
│
│  ── Cross-Platform Layer (works with ALL agent tools) ──
├── CLAUDE.md                    # Claude Code native rules (the source of truth)
├── AGENTS.md → CLAUDE.md        # Symlink: Codex, Gemini, Copilot, Cursor all read this
├── .agents/
│   └── skills/                  # Open standard skill format
│       └── <project>/SKILL.md   # Project-specific workflow skill
│
│  ── Claude Code Layer (richest implementation) ──
├── .claude/
│   ├── agents/                  # Subagents tailored to this project
│   │   ├── code-reviewer.md     # Knows this project's conventions
│   │   ├── test-writer.md       # Knows this project's test framework
│   │   └── <conditional>.md     # Stack-specific agents
│   ├── skills/ → ../.agents/skills/  # Points to cross-platform skills
│   └── memory/
│       ├── MEMORY.md            # Index
│       └── project-dna.md       # Full DNA extraction results
│
│  ── Cursor Compatibility (if applicable) ──
├── .cursor/
│   └── skills/ → ../.agents/skills/
│
│  ── Tool Config (if applicable) ──
└── .mcp.json                    # MCP server config
```

## Compatibility Matrix

| Generated File | Claude Code | Codex | Gemini CLI | Cursor | Copilot |
|---|---|---|---|---|---|
| CLAUDE.md | Native | — | — | Reads it | — |
| AGENTS.md (symlink) | — | Native | Reads it | Reads it | Reads it |
| .agents/skills/*/SKILL.md | Via symlink | Native | Native | Via symlink | Native |
| .claude/agents/*.md | Native | — | — | Can read | — |
| .claude/memory/ | Native | — | — | — | — |

**Key insight**: By placing skills in `.agents/skills/` and symlinking from `.claude/skills/` and `.cursor/skills/`, the same skill works on 5+ platforms with zero duplication.

## Two Modes of Operation

### Mode 1: Existing Codebase
When the project has code (>3 source files or a manifest file):
1. Run deep DNA extraction (stack, architecture, conventions, fragile zones)
2. Generate all files based on actual findings
3. CLAUDE.md rules come from real code patterns, not templates
4. Subagents reference real test frameworks, real file paths, real conventions

### Mode 2: Brand New Project
When the project is empty or nearly empty:
1. Ask the user 5 questions: name, description, stack, architecture type, constraints
2. Generate a starter ecosystem based on their answers
3. CLAUDE.md contains their stated conventions and constraints
4. Subagents are tailored to their chosen stack
5. Skills provide workflow templates for their architecture type

## CLAUDE.md Quality Standard

A generated CLAUDE.md must meet these criteria:
- **Under 150 lines** — concise, not documentation
- **Every rule has a WHY** — "use pytest (project standard)" not just "use pytest"
- **Actual commands** — from package.json scripts, Makefile targets, not guessed
- **Real fragile zones** — from git analysis, not assumed
- **Real conventions** — from code reading, not templates

Bad CLAUDE.md (generic):
```
## Rules
- Write clean code
- Add tests
- Follow best practices
```

Good CLAUDE.md (specific):
```
## Rules
- Use pytest-django with factory_boy fixtures (see apps/core/tests/factories.py for patterns)
- All views in apps/*/views.py must inherit from LoginRequiredMixin
- Templates use {% block content %} and {% include "partials/_*.html" %} pattern
- HTMX attributes go on the triggering element, not the target
```

## Subagent Quality Standard

Generated subagents must:
- Reference **actual** paths in this project (not generic `/src/tests/`)
- Know the **actual** test framework (not "write tests")
- Use `haiku` model for fast tasks (review), `sonnet` for complex tasks (test writing)
- Have focused tool lists (not "all tools")
- Be under 80 lines of system prompt

## After Init

The `/init` command should suggest:
1. Review CLAUDE.md and tweak rules to your preference
2. Run `/clamp` to verify the current codebase state
3. Run `/dna` for deeper architecture analysis beyond what /init captured
