---
description: "Initialize full cross-platform agent ecosystem for the current project. Analyzes codebase (or asks for context if brand new), then scaffolds CLAUDE.md, AGENTS.md, agents, skills, memory, hooks — everything."
argument-hint: "[--force | --minimal | --dry-run]"
---

You are executing the `/init` command — Clamper's flagship ecosystem initializer. This is the one-command setup that gives any project a complete, intelligent, cross-platform agent ecosystem.

## Phase 0: Pre-Flight Check

1. Check if an ecosystem already exists in the current working directory:
   - Look for: `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.agents/`, `.cursor/`
   - If found AND `$ARGUMENTS` does NOT contain `--force`:
     - Show what already exists
     - Ask: "Ecosystem artifacts already exist. Run `/init --force` to regenerate, or I can enhance what's here."
     - If user says enhance, read existing files and ADD to them rather than overwrite
   - If `--force`: proceed with full regeneration (backup existing first)

2. Check if `--dry-run` is in arguments:
   - If yes: do all analysis but only SHOW what would be created, don't write files

## Phase 1: Codebase Intelligence Gathering

Determine if this is an **existing codebase** or **brand new project**:

### Existing Codebase Detection
Run these checks:
```bash
# Is there meaningful code here?
file_count=$(find . -maxdepth 3 -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.rs" -o -name "*.go" -o -name "*.java" -o -name "*.rb" \) | head -20 | wc -l)
has_git=$(test -d .git && echo "yes" || echo "no")
has_manifest=$(test -f package.json -o -f pyproject.toml -o -f Cargo.toml -o -f go.mod -o -f Gemfile && echo "yes" || echo "no")
```

### If EXISTING codebase (file_count > 3 OR has_manifest = yes):

Delegate to `clamper-scout` agent for deep DNA extraction. Collect:
- **Stack**: Languages, frameworks, build tools, test frameworks
- **Architecture**: Monolith/microservices/monorepo/plugin, layer boundaries
- **Hot files**: Most changed files in recent git history
- **Fragile zones**: High churn + low test coverage
- **Coupling groups**: Files that change together
- **Entry points**: Main files, route definitions, CLI entry points
- **Conventions**: Import style, naming patterns, directory structure patterns
- **Test infrastructure**: Framework, coverage, test:source ratio
- **CI/CD**: GitHub Actions, GitLab CI, Docker, deploy config
- **Existing docs**: README, CONTRIBUTING, API docs

Also read any existing CLAUDE.md, AGENTS.md, .cursorrules for context to preserve.

### If BRAND NEW project (file_count <= 3 AND no manifest):

Ask the user for project context. Present this questionnaire:

```
This looks like a brand new project. I need some context to build the right ecosystem.

1. **Project name**: What's the project called?
2. **What it does**: One-sentence description
3. **Tech stack**: What languages/frameworks will you use?
   (e.g., Django + HTMX + Tailwind, React + TypeScript, Rust CLI, Go microservice)
4. **Architecture**: What kind of project is this?
   - [ ] Web app (frontend + backend)
   - [ ] API / Backend service
   - [ ] CLI tool
   - [ ] Library / Package
   - [ ] Monorepo (multiple packages)
   - [ ] Mobile app
   - [ ] Other: ___
5. **Team size**: Solo / Small team / Large team
6. **Special constraints**: Anything Claude should always know?
   (e.g., "never use ORM, raw SQL only", "must support Python 3.9+", "no external dependencies")

Answer what you can, skip what you don't know yet.
```

Wait for user response before proceeding to Phase 2.

## Phase 2: Ecosystem Generation

Based on the intelligence gathered, generate the following structure:

```
<project-root>/
├── CLAUDE.md                          # Project-aware rules for Claude Code
├── AGENTS.md                          # Cross-platform symlink → CLAUDE.md
│
├── .agents/                           # Cross-platform standard (Codex/Gemini/Copilot)
│   └── skills/
│       └── <project-specific>/SKILL.md
│
├── .claude/
│   ├── agents/                        # Claude-specific subagents
│   │   ├── code-reviewer.md           # Tailored to project's stack
│   │   ├── test-writer.md             # Knows project's test framework
│   │   └── <role-based-on-project>.md
│   ├── skills/ → ../.agents/skills/   # Symlink for Claude compatibility
│   └── memory/
│       └── MEMORY.md                  # Initialized with project DNA
│
├── .cursor/                           # Cursor compatibility (if applicable)
│   └── skills/ → ../.agents/skills/   # Symlink
│
└── .mcp.json                          # MCP server config (if project uses APIs)
```

### File Generation Rules

**CLAUDE.md** — Must contain:
1. **Project identity**: Name, one-line description, stack
2. **Architecture rules**: Derived from actual codebase analysis (not generic)
   - Directory structure explanation with what lives where
   - Import conventions detected from code
   - Naming patterns detected from code
3. **Critical constraints**: Things Claude must ALWAYS know
   - Fragile zones from DNA extraction
   - Technology rejections / preferences
   - Testing requirements
4. **Development workflow**: How to build, test, run, deploy
   - Actual commands from package.json scripts, Makefile targets, etc.
5. **Code conventions**: Derived from codebase, not assumed
   - Detected formatting (tabs/spaces, quotes, semicolons)
   - Error handling patterns used in the codebase
   - State management approach

Example CLAUDE.md generation for a Django project:
```markdown
# Project: MyApp

Django 5 + HTMX + Tailwind + Alpine.js web application.

## Architecture
- `apps/` — Django apps (each self-contained with models, views, templates, tests)
- `templates/` — Shared base templates and partials
- `static/` — Tailwind CSS, Alpine.js, HTMX
- `config/` — Django settings (base, dev, prod)

## Rules
- Always use class-based views, never function-based
- Templates use HTMX for interactivity, NOT JavaScript frameworks
- Tests go in each app's `tests/` directory, use pytest-django
- Never use raw SQL — always Django ORM
- All views must have permission checks

## Fragile Zones
- `apps/payments/models.py` — 12 changes in 50 commits, no tests
- `config/settings/prod.py` — Frequently modified, cascading effects

## Commands
- `make dev` — Start development server
- `make test` — Run pytest with coverage
- `make migrate` — Run database migrations
```

**AGENTS.md** — Create as a symlink to CLAUDE.md:
```bash
ln -sf CLAUDE.md AGENTS.md
```
This gives cross-platform compatibility with Codex, Gemini CLI, Copilot, Cursor.

**Subagents** (.claude/agents/) — Generate 2-4 agents tailored to the project:

Always generate:
- **code-reviewer.md** — Knows the project's stack, conventions, and fragile zones
- **test-writer.md** — Knows the test framework, test patterns, and coverage gaps

Conditionally generate based on stack:
- **api-designer.md** — If project has REST/GraphQL endpoints
- **migration-helper.md** — If project uses database (Django, SQLAlchemy, Prisma)
- **security-auditor.md** — If project handles auth, payments, or user data
- **build-debugger.md** — If project has complex build (webpack, monorepo, Docker)

Each agent's system prompt must reference:
- The actual test framework (`pytest`, `jest`, `cargo test`, etc.)
- The actual file structure (where to find tests, models, routes)
- Project-specific conventions from the DNA analysis

**Skills** (.agents/skills/) — Generate 1-3 skills:
- A project-specific skill that captures the unique workflow (e.g., "django-api-endpoint" that knows how to add a new endpoint in this specific project's structure)
- Only if genuinely useful — don't generate skills for generic tasks

**MEMORY.md** (.claude/memory/) — Initialize with:
```markdown
- [Project DNA](project-dna.md) — Architecture, stack, conventions extracted by Clamper /init
```

And create `project-dna.md` with the full DNA extraction results.

**.mcp.json** — Only generate if the project would benefit from MCP tools:
- If using external APIs → suggest relevant MCP servers
- If using databases → suggest database MCP server
- Don't generate if not needed

## Phase 3: Summary & Next Steps

After generation, display:

```
╔══════════════════════════════════════════════════╗
║          CLAMPER /init COMPLETE                  ║
╠══════════════════════════════════════════════════╣
║ Files Created:                                   ║
║   CLAUDE.md          — project rules             ║
║   AGENTS.md          — cross-platform symlink    ║
║   .claude/agents/    — N subagents               ║
║   .agents/skills/    — N skills                  ║
║   .claude/memory/    — initialized with DNA      ║
║   [.mcp.json]        — if applicable             ║
╠──────────────────────────────────────────────────╣
║ Cross-Platform Compatibility:                    ║
║   Claude Code  — CLAUDE.md + .claude/            ║
║   Codex        — AGENTS.md + .agents/skills/     ║
║   Gemini CLI   — AGENTS.md + .agents/skills/     ║
║   Cursor       — AGENTS.md + .claude/ + .cursor/ ║
║   Copilot      — AGENTS.md + .agents/skills/     ║
╠──────────────────────────────────────────────────╣
║ Next Steps:                                      ║
║   1. Review CLAUDE.md and adjust rules           ║
║   2. Run /clamp to verify current code state     ║
║   3. Run /dna for deep architecture analysis     ║
╚══════════════════════════════════════════════════╝
```

## Minimal Mode (`--minimal`)

If `$ARGUMENTS` contains `--minimal`, generate only:
- CLAUDE.md (essential rules only)
- AGENTS.md (symlink)
- .claude/memory/MEMORY.md

Skip agents, skills, .mcp.json, .cursor/
