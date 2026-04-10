# Claude Code Plugin Structure — Complete Reference

> A comprehensive guide to every file, folder, field, and convention in the Claude Code plugin system.
> Based on official Anthropic documentation (April 2026).

---

## Table of Contents

1. [Overview](#1-overview)
2. [Directory Structure](#2-directory-structure)
3. [.claude-plugin/plugin.json — The Manifest](#3-claude-pluginpluginjson--the-manifest)
4. [skills/ — Agent Skills](#4-skills--agent-skills)
5. [commands/ — Legacy Skills](#5-commands--legacy-skills)
6. [agents/ — Subagents](#6-agents--subagents)
7. [hooks/ — Event Handlers](#7-hooks--event-handlers)
8. [bin/ — Plugin Executables](#8-bin--plugin-executables)
9. [.mcp.json — MCP Servers](#9-mcpjson--mcp-servers)
10. [.lsp.json — LSP Servers](#10-lspjson--lsp-servers)
11. [output-styles/ — Output Formatting](#11-output-styles--output-formatting)
12. [settings.json — Default Settings](#12-settingsjson--default-settings)
13. [scripts/ — Utility Scripts](#13-scripts--utility-scripts)
14. [Other Files](#14-other-files)
15. [Environment Variables](#15-environment-variables)
16. [Plugin Scopes](#16-plugin-scopes)
17. [Plugin Caching and Path Rules](#17-plugin-caching-and-path-rules)
18. [CLI Commands](#18-cli-commands)
19. [Debugging](#19-debugging)
20. [Version Management](#20-version-management)

---

## 1. Overview

A **plugin** is a self-contained directory that extends Claude Code with custom functionality. Plugins can include:

- **Skills** — instructions Claude follows when invoked (slash commands)
- **Agents** — specialized subagents for delegated tasks
- **Hooks** — event handlers that fire automatically on lifecycle events
- **MCP Servers** — external tool integrations via Model Context Protocol
- **LSP Servers** — code intelligence (go-to-definition, diagnostics, references)
- **Executables** — CLI tools added to Claude's PATH
- **Output Styles** — custom response formatting
- **Settings** — default configuration applied on enable

### When to Use a Plugin vs Standalone Config

| Approach | Skill names | Best for |
|---|---|---|
| **Standalone** (`.claude/` directory) | `/hello` | Personal workflows, project-specific, quick experiments |
| **Plugin** (`.claude-plugin/plugin.json`) | `/plugin-name:hello` | Sharing with teams, community distribution, reusable across projects |

Plugin skills are always **namespaced** to prevent conflicts: `/my-plugin:hello` instead of just `/hello`.

---

## 2. Directory Structure

### Complete Layout

```
my-plugin/
├── .claude-plugin/           # Metadata directory
│   └── plugin.json           #   Plugin manifest (ONLY file that goes here)
│
├── skills/                   # Agent Skills (recommended format)
│   ├── code-review/
│   │   ├── SKILL.md          #   Skill definition
│   │   ├── reference.md      #   Optional supporting docs
│   │   └── scripts/          #   Optional co-located scripts
│   └── deploy/
│       └── SKILL.md
│
├── commands/                 # Legacy skills (flat .md files)
│   └── status.md
│
├── agents/                   # Subagent definitions
│   ├── security-reviewer.md
│   └── performance-tester.md
│
├── hooks/                    # Event handlers
│   ├── hooks.json            #   Main hook config
│   └── extra-hooks.json      #   Additional hook files
│
├── output-styles/            # Output style definitions
│   └── terse.md
│
├── bin/                      # Executables added to Bash tool's PATH
│   └── my-tool
│
├── scripts/                  # Utility scripts (conventional, not auto-discovered)
│   ├── format-code.py
│   └── deploy.sh
│
├── .mcp.json                 # MCP server definitions
├── .lsp.json                 # LSP server configurations
├── settings.json             # Default settings (e.g., default agent)
├── LICENSE                   # License file
├── CHANGELOG.md              # Version history
└── README.md                 # Documentation
```

### Critical Rule

> **Never** put `commands/`, `agents/`, `skills/`, `hooks/`, or any other component directory inside `.claude-plugin/`. Only `plugin.json` goes inside `.claude-plugin/`. All other directories must be at the **plugin root** level.

### File Locations Reference

| Component | Default Location | Purpose |
|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | Plugin metadata and configuration (optional) |
| Commands | `commands/` | Skill Markdown files (legacy; use `skills/`) |
| Agents | `agents/` | Subagent Markdown files |
| Skills | `skills/` | Skills with `<name>/SKILL.md` structure |
| Output styles | `output-styles/` | Output style definitions |
| Hooks | `hooks/hooks.json` | Hook configuration |
| MCP servers | `.mcp.json` | MCP server definitions |
| LSP servers | `.lsp.json` | Language server configurations |
| Executables | `bin/` | Added to Bash tool's PATH while plugin is enabled |
| Settings | `settings.json` | Default config applied when plugin is enabled |

---

## 3. .claude-plugin/plugin.json — The Manifest

The manifest defines your plugin's identity and configuration. It is **optional** — if omitted, Claude Code auto-discovers components in default locations and derives the plugin name from the directory name.

### Complete Schema

```json
{
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": ["./custom/commands/special.md"],
  "agents": "./custom/agents/",
  "skills": "./custom/skills/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/",
  "userConfig": {},
  "channels": []
}
```

### Required Fields

Only **one** field is required if you include a manifest:

| Field | Type | Description | Example |
|---|---|---|---|
| `name` | string | Unique identifier (kebab-case, no spaces) | `"deployment-tools"` |

This name is used for namespacing. A skill `deploy` in plugin `my-tools` becomes `/my-tools:deploy`.

### Metadata Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `version` | string | Semantic version | `"2.1.0"` |
| `description` | string | Brief explanation of purpose | `"Deployment automation tools"` |
| `author` | object | `{name, email, url}` | `{"name": "Dev Team"}` |
| `homepage` | string | Documentation URL | `"https://docs.example.com"` |
| `repository` | string | Source code URL | `"https://github.com/user/plugin"` |
| `license` | string | License identifier | `"MIT"`, `"Apache-2.0"` |
| `keywords` | array | Discovery tags | `["deployment", "ci-cd"]` |

### Component Path Fields

| Field | Type | Description |
|---|---|---|
| `commands` | string\|array | Custom command paths (**replaces** default `commands/`) |
| `agents` | string\|array | Custom agent paths (**replaces** default `agents/`) |
| `skills` | string\|array | Custom skill paths (**replaces** default `skills/`) |
| `hooks` | string\|array\|object | Hook config paths or inline config |
| `mcpServers` | string\|array\|object | MCP config paths or inline config |
| `lspServers` | string\|array\|object | LSP config paths or inline config |
| `outputStyles` | string\|array | Custom output style paths (**replaces** default `output-styles/`) |
| `userConfig` | object | User-configurable values prompted at enable time |
| `channels` | array | Channel declarations for message injection |

### Path Behavior Rules

- All paths must be **relative** to the plugin root and start with `./`
- For `commands`, `agents`, `skills`, and `outputStyles`: custom paths **replace** the default directory
- To keep the default AND add more: include the default in your array:
  ```json
  "commands": ["./commands/", "./extras/deploy.md"]
  ```
- Multiple paths can be specified as arrays
- `hooks`, `mcpServers`, and `lspServers` have different merging semantics

### userConfig — User-Prompted Configuration

Declares values that Claude Code prompts the user for when the plugin is enabled. Replaces the need for users to hand-edit `settings.json`.

```json
{
  "userConfig": {
    "api_endpoint": {
      "description": "Your team's API endpoint",
      "sensitive": false
    },
    "api_token": {
      "description": "API authentication token",
      "sensitive": true
    }
  }
}
```

**How values are accessible:**

| Context | Access method |
|---|---|
| MCP/LSP configs, hook commands | `${user_config.KEY}` substitution |
| Skill/agent content | `${user_config.KEY}` (non-sensitive only) |
| Subprocesses | `CLAUDE_PLUGIN_OPTION_<KEY>` environment variable |

**Storage:**

- Non-sensitive values → `settings.json` under `pluginConfigs[<plugin-id>].options`
- Sensitive values → system keychain (or `~/.claude/.credentials.json` as fallback)
- Keychain has ~2 KB total limit — keep sensitive values small

### channels — Message Injection

Lets a plugin declare message channels (Telegram, Slack, Discord style) that inject content into the conversation.

```json
{
  "channels": [
    {
      "server": "telegram",
      "userConfig": {
        "bot_token": { "description": "Telegram bot token", "sensitive": true },
        "owner_id": { "description": "Your Telegram user ID", "sensitive": false }
      }
    }
  ]
}
```

- `server` is **required** and must match a key in the plugin's `mcpServers`
- Per-channel `userConfig` uses the same schema as the top-level field

---

## 4. skills/ — Agent Skills

The **recommended** format for defining slash commands and capabilities.

### Structure

Each skill is a **folder** containing a `SKILL.md` file. The folder name becomes the skill name:

```
skills/
├── code-review/
│   ├── SKILL.md              # Required: skill definition
│   ├── reference.md          # Optional: supporting documentation
│   ├── templates/            # Optional: templates used by the skill
│   └── scripts/              # Optional: co-located helper scripts
└── deploy/
    └── SKILL.md
```

`skills/code-review/SKILL.md` in a plugin named `my-tools` → `/my-tools:code-review`

### SKILL.md Format

```markdown
---
name: code-review
description: Reviews code for best practices and potential issues
user-invocable: true
argument-hint: [file or PR number]
model: sonnet
---

When reviewing code, check for:
1. Code organization and structure
2. Error handling
3. Security concerns
4. Test coverage

Request: $ARGUMENTS
```

### SKILL.md Frontmatter — All Supported Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Skill identifier (defaults to folder name) |
| `description` | string | **Required.** When Claude should use this skill |
| `user-invocable` | boolean | Whether users can invoke via `/name` (default: true for plugins) |
| `disable-model-invocation` | boolean | Prevents Claude from auto-invoking based on context |
| `argument-hint` | string | Placeholder shown in the slash command menu |
| `allowed-tools` | array | Tools this skill is allowed to use |
| `model` | string | Model override (`sonnet`, `opus`, `haiku`) |
| `context` | string | Additional context loading |
| `agent` | string | Run as a specific agent |
| `hooks` | object | Skill-specific hooks |
| `version` | string | Skill version |
| `author` | string | Skill author |
| `license` | string | Skill license |
| `compatibility` | string | Compatibility constraints |
| `compatible-with` | string | Compatible Claude Code versions |
| `tags` | array | Discovery/categorization tags |

### Key Variables in Skill Content

| Variable | Replaced with |
|---|---|
| `$ARGUMENTS` | Text the user typed after the skill name |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin install directory |
| `${CLAUDE_PLUGIN_DATA}` | Persistent data directory |
| `${user_config.KEY}` | User config value (non-sensitive only) |

### Co-located Files

The folder-per-skill structure exists specifically so you can keep supporting files alongside the skill:

```
skills/deploy/
├── SKILL.md                  # Skill instructions
├── reference.md              # Deployment checklist Claude reads
├── scripts/
│   └── validate-config.sh    # Script the skill can invoke
└── templates/
    └── deploy-manifest.yaml  # Template the skill fills in
```

This is the primary advantage over the legacy `commands/` format.

---

## 5. commands/ — Legacy Skills

The older, flat-file format for skills. **Still works, but `skills/` is recommended for new plugins.**

### Structure

```
commands/
├── deploy.md
├── status.md
└── clean.md
```

`commands/deploy.md` → `/my-plugin:deploy`

### Format

Same frontmatter as SKILL.md, but in a flat `.md` file:

```markdown
---
description: Deploy the application
argument-hint: [environment]
---

# Deploy

Deploy to the specified environment.
$ARGUMENTS will contain the target environment.
```

### Differences from skills/

| Feature | `commands/` | `skills/` |
|---|---|---|
| File per skill | Single `.md` | Folder with `SKILL.md` |
| Co-located files | No | Yes (scripts, templates, references) |
| Functionality | Identical | Identical |
| Status | Legacy | Recommended |

---

## 6. agents/ — Subagents

Specialized agents that Claude can delegate tasks to. Each is a Markdown file.

### Structure

```
agents/
├── security-reviewer.md
├── performance-tester.md
└── workspace-janitor.md
```

### Agent .md Format

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities and OWASP top 10 issues
model: sonnet
effort: medium
maxTurns: 20
disallowedTools: Write, Edit
---

You are a security expert. When reviewing code:

1. Check for injection vulnerabilities (SQL, XSS, command)
2. Verify authentication and authorization logic
3. Look for sensitive data exposure
4. Check dependency vulnerabilities

Report findings with severity levels: CRITICAL, HIGH, MEDIUM, LOW.
```

### Agent Frontmatter — All Supported Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `name` | string | Agent identifier | `"security-reviewer"` |
| `description` | string | When Claude should invoke this agent | `"Reviews code for security issues"` |
| `model` | string | Model to use | `"sonnet"`, `"opus"`, `"haiku"` |
| `effort` | string | Reasoning effort level | `"low"`, `"medium"`, `"high"` |
| `maxTurns` | number | Maximum conversation turns | `20` |
| `tools` | array | Allowed tools list | `["Read", "Grep", "Glob"]` |
| `disallowedTools` | array | Blocked tools list | `["Write", "Edit"]` |
| `skills` | array | Skills available to this agent | `["code-review"]` |
| `memory` | string/boolean | Memory access configuration | |
| `background` | boolean | Run in background | `true` |
| `isolation` | string | Only valid value: `"worktree"` | `"worktree"` |

### Security Restrictions

For security reasons, the following fields are **NOT supported** in plugin-shipped agents:

- `hooks` — cannot define hooks
- `mcpServers` — cannot attach MCP servers
- `permissionMode` — cannot change permissions

### Integration

- Agents appear in the `/agents` interface
- Claude can invoke them automatically based on task context
- Users can invoke them manually
- Plugin agents work alongside built-in Claude agents

---

## 7. hooks/ — Event Handlers

Hooks fire automatically on Claude Code lifecycle events. They are the backbone of plugin automation.

### Structure

```
hooks/
├── hooks.json            # Main hook configuration
└── security-hooks.json   # Additional hook files (optional)
```

### hooks.json Format

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-code.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

**Note:** Plugin `hooks.json` wraps everything in `{"hooks": {...}}`. This is the same format as user-defined hooks in `settings.json`.

### All 26 Hook Events

| # | Event | When it fires | Can block? |
|---|---|---|---|
| 1 | `SessionStart` | Session begins or resumes | No |
| 2 | `SessionEnd` | Session terminates | No |
| 3 | `UserPromptSubmit` | User sends a message, before Claude processes it | No |
| 4 | `PreToolUse` | Before a tool call executes | **Yes** |
| 5 | `PostToolUse` | After a tool call succeeds | No |
| 6 | `PostToolUseFailure` | After a tool call fails | No |
| 7 | `PermissionRequest` | When a permission dialog appears | No |
| 8 | `PermissionDenied` | When a tool call is denied. Return `{retry: true}` to allow retry | No |
| 9 | `Stop` | When Claude finishes responding | No |
| 10 | `StopFailure` | Turn ends due to API error (output/exit code ignored) | No |
| 11 | `PreCompact` | Before context compaction | No |
| 12 | `PostCompact` | After context compaction completes | No |
| 13 | `SubagentStart` | When a subagent is spawned | No |
| 14 | `SubagentStop` | When a subagent finishes | No |
| 15 | `TaskCreated` | When a task is created via TaskCreate | No |
| 16 | `TaskCompleted` | When a task is marked as completed | No |
| 17 | `TeammateIdle` | Agent team member going idle | No |
| 18 | `InstructionsLoaded` | CLAUDE.md or `.claude/rules/*.md` loaded into context | No |
| 19 | `ConfigChange` | Config file changes during a session | No |
| 20 | `CwdChanged` | Working directory changes (e.g., `cd` command) | No |
| 21 | `FileChanged` | Watched file changes on disk (`matcher` specifies filenames) | No |
| 22 | `WorktreeCreate` | Worktree being created | No |
| 23 | `WorktreeRemove` | Worktree being removed | No |
| 24 | `Notification` | Claude sends a notification | No |
| 25 | `Elicitation` | MCP server requests user input during a tool call | No |
| 26 | `ElicitationResult` | User responds to an MCP elicitation | No |

### Hook Types

| Type | Description | Example |
|---|---|---|
| `command` | Execute a shell command or script | `"command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh"` |
| `http` | POST event JSON to a URL | `"url": "https://hooks.example.com/event"` |
| `prompt` | Evaluate a prompt with an LLM | Uses `$ARGUMENTS` for context |
| `agent` | Run an agentic verifier with tools | For complex verification tasks |

### Hook Entry Fields

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "script.sh",
      "timeout": 10
    }
  ]
}
```

- `matcher` — regex pattern to filter which tools/files trigger the hook (optional)
- `hooks` — array of hook actions to execute
- `type` — one of `command`, `http`, `prompt`, `agent`
- `command` — shell command to run (for `command` type)
- `timeout` — max execution time in seconds

### Hook Input

Hook commands receive event data as **JSON on stdin**. Use `jq` to extract fields:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npm run lint:fix"
          }
        ]
      }
    ]
  }
}
```

---

## 8. bin/ — Plugin Executables

Files in `bin/` are added to the Bash tool's `PATH` while the plugin is enabled.

### How it Works

```
bin/
└── my-linter
```

Once the plugin is enabled, Claude can run `my-linter file.py` directly in any Bash tool call — no path needed.

### Requirements

- Files must be **executable** (`chmod +x bin/my-linter`)
- Include a proper shebang line (`#!/bin/bash`, `#!/usr/bin/env python3`, etc.)

### Use Cases

- Custom linters or formatters
- Wrapper scripts for complex operations
- Build tools
- Data processing utilities

---

## 9. .mcp.json — MCP Servers

Connect Claude Code with external tools and services via the Model Context Protocol.

### Location

File `.mcp.json` at plugin root, or inline in `plugin.json` under `mcpServers`.

### Format

```json
{
  "mcpServers": {
    "plugin-database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_DATA}/data"
      },
      "cwd": "${CLAUDE_PLUGIN_ROOT}"
    },
    "plugin-api-client": {
      "command": "npx",
      "args": ["@company/mcp-server", "--plugin-mode"]
    }
  }
}
```

### Behavior

- Plugin MCP servers **start automatically** when the plugin is enabled
- Servers appear as standard MCP tools in Claude's toolkit
- Server capabilities integrate seamlessly with Claude's existing tools
- Plugin servers can be configured independently of user MCP servers

### Inline in plugin.json

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/server.js"
    }
  }
}
```

---

## 10. .lsp.json — LSP Servers

Language Server Protocol integration gives Claude real-time code intelligence.

### What LSP Provides

- **Instant diagnostics** — Claude sees errors/warnings immediately after each edit
- **Code navigation** — go to definition, find references, hover information
- **Language awareness** — type information and documentation for symbols

### Location

File `.lsp.json` at plugin root, or inline in `plugin.json` under `lspServers`.

### Format

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  }
}
```

### Required Fields

| Field | Description |
|---|---|
| `command` | The LSP binary to execute (must be in PATH) |
| `extensionToLanguage` | Maps file extensions to language identifiers |

### Optional Fields

| Field | Description |
|---|---|
| `args` | Command-line arguments for the LSP server |
| `transport` | Communication transport: `stdio` (default) or `socket` |
| `env` | Environment variables for the server |
| `initializationOptions` | Options passed during server initialization |
| `settings` | Settings via `workspace/didChangeConfiguration` |
| `workspaceFolder` | Workspace folder path |
| `startupTimeout` | Max time to wait for startup (milliseconds) |
| `shutdownTimeout` | Max time for graceful shutdown (milliseconds) |
| `restartOnCrash` | Auto-restart if server crashes |
| `maxRestarts` | Max restart attempts before giving up |

### Important

> The plugin does NOT bundle the language server binary. Users must install it separately (e.g., `pip install pyright`, `npm install -g typescript-language-server`).

### Available Official LSP Plugins

| Plugin | Language Server | Install |
|---|---|---|
| `pyright-lsp` | Pyright (Python) | `pip install pyright` |
| `typescript-lsp` | TypeScript LS | `npm install -g typescript-language-server typescript` |
| `rust-lsp` | rust-analyzer | See rust-analyzer docs |

---

## 11. output-styles/ — Output Formatting

Custom output styles that change how Claude formats responses.

### Structure

```
output-styles/
└── terse.md
```

### Format

Markdown files that define formatting instructions. These are loaded as system instructions that modify Claude's response style.

### Use Cases

- Concise/terse mode for experienced users
- Verbose/educational mode for learners
- Structured output (always use tables, always use bullet points)
- Domain-specific formatting (medical, legal, technical)

---

## 12. settings.json — Default Settings

Applied when the plugin is enabled. Currently only the `agent` key is supported.

### Format

```json
{
  "agent": "security-reviewer"
}
```

### Behavior

- Setting `agent` activates one of the plugin's custom agents as the **main thread**
- The agent's system prompt, tool restrictions, and model become the defaults
- `settings.json` takes priority over `settings` declared in `plugin.json`
- Unknown keys are silently ignored

### Use Case

Turn a plugin into a **persona** — install the plugin and Claude behaves differently by default (e.g., always acts as a security reviewer).

---

## 13. scripts/ — Utility Scripts

A **conventional** directory for helper scripts. It has no special meaning to Claude Code — nothing is auto-discovered here.

### Purpose

Organizational home for scripts referenced by hooks, agents, or skills:

```
scripts/
├── format-code.py        # Called by PostToolUse hook
├── security-scan.sh      # Called by security-reviewer agent
└── deploy.js             # Called by deploy skill
```

### Referencing Scripts

Always use `${CLAUDE_PLUGIN_ROOT}` to reference scripts:

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-code.py"
}
```

### Alternative

Some plugins use `hooks-handlers/` instead of `scripts/` — the name doesn't matter since it's not auto-discovered. Use whatever makes sense for your project.

---

## 14. Other Files

### LICENSE

Standard license file. Displayed in plugin manager.

### CHANGELOG.md

Version history. Good practice for published plugins.

### README.md

Plugin documentation. Include:
- What the plugin does
- Installation instructions
- Available skills/commands
- Configuration options
- Requirements/prerequisites

---

## 15. Environment Variables

Claude Code provides two variables for referencing plugin paths. Both are substituted inline in skill content, agent content, hook commands, and MCP/LSP configs. Both are also exported as environment variables to subprocesses.

### ${CLAUDE_PLUGIN_ROOT}

**Absolute path to your plugin's installation directory.**

```json
"command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
```

- Use for referencing bundled scripts, binaries, config files
- **Changes when the plugin updates** — files written here don't survive updates

### ${CLAUDE_PLUGIN_DATA}

**Persistent data directory that survives updates.**

Resolves to `~/.claude/plugins/data/{id}/` where `{id}` is the plugin identifier with special characters replaced by `-`.

```json
"env": {
  "NODE_PATH": "${CLAUDE_PLUGIN_DATA}/node_modules"
}
```

- Use for installed dependencies (`node_modules`, Python venvs)
- Use for generated code, caches, databases
- Created automatically on first reference
- Deleted automatically when you uninstall from the last scope (use `--keep-data` to preserve)

### Persistent Data Pattern — Auto-Install Dependencies

A common pattern: install dependencies on first run, re-install when plugin updates change the manifest:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\""
          }
        ]
      }
    ]
  }
}
```

The `diff` exits nonzero when the stored copy is missing or differs, covering both first run and dependency updates.

### Subprocess Environment Variables

| Variable | Available to |
|---|---|
| `CLAUDE_PLUGIN_ROOT` | Hook processes, MCP/LSP server processes |
| `CLAUDE_PLUGIN_DATA` | Hook processes, MCP/LSP server processes |
| `CLAUDE_PLUGIN_OPTION_<KEY>` | All subprocesses (from `userConfig` values) |

---

## 16. Plugin Scopes

When you install a plugin, you choose a **scope** that determines visibility:

| Scope | Settings file | Use case |
|---|---|---|
| `user` | `~/.claude/settings.json` | Personal plugins across all projects (default) |
| `project` | `.claude/settings.json` | Team plugins shared via version control |
| `local` | `.claude/settings.local.json` | Project-specific, gitignored |
| `managed` | Managed settings (read-only) | Organization-enforced plugins |

### Examples

```bash
# Install for yourself (default)
claude plugin install formatter@my-marketplace

# Install for the whole team (committed to git)
claude plugin install formatter@my-marketplace --scope project

# Install just for this project, not committed
claude plugin install formatter@my-marketplace --scope local
```

---

## 17. Plugin Caching and Path Rules

### How Caching Works

Marketplace plugins are **copied** to a local cache (`~/.claude/plugins/cache/`) rather than used in-place. This is for security and verification.

### Path Traversal Limitation

Installed plugins **cannot reference files outside their directory**. Paths like `../shared-utils` won't work after installation because external files aren't copied.

### Workaround: Symlinks

Create symbolic links to external files within your plugin directory:

```bash
# Inside your plugin directory
ln -s /path/to/shared-utils ./shared-utils
```

Symlinked content is copied into the cache during installation.

### --plugin-dir for Development

During development, use `--plugin-dir` to load directly without caching:

```bash
claude --plugin-dir ./my-plugin
```

- When a `--plugin-dir` plugin has the same name as an installed marketplace plugin, the local copy takes precedence
- Use `/reload-plugins` to pick up changes without restarting
- Load multiple: `claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two`

---

## 18. CLI Commands

### plugin install

```bash
claude plugin install <plugin> [--scope user|project|local]
```

### plugin uninstall

```bash
claude plugin uninstall <plugin> [--scope user|project|local] [--keep-data]
```

Aliases: `remove`, `rm`

### plugin enable

```bash
claude plugin enable <plugin> [--scope user|project|local]
```

### plugin disable

```bash
claude plugin disable <plugin> [--scope user|project|local]
```

### plugin update

```bash
claude plugin update <plugin> [--scope user|project|local|managed]
```

### plugin validate

Validates `plugin.json`, skill/agent/command frontmatter, and `hooks/hooks.json` for syntax and schema errors.

### /reload-plugins

Run inside Claude Code to reload all plugins, skills, agents, hooks, MCP servers, and LSP servers without restarting.

---

## 19. Debugging

### Enable Debug Mode

```bash
claude --debug
```

Shows:
- Which plugins are being loaded
- Errors in plugin manifests
- Command, agent, and hook registration
- MCP server initialization

### Common Issues

| Issue | Cause | Solution |
|---|---|---|
| Plugin not loading | Invalid `plugin.json` | Run `claude plugin validate` |
| Commands not appearing | Wrong directory structure | Move components to root, not inside `.claude-plugin/` |
| Hooks not firing | Script not executable | `chmod +x script.sh` |
| MCP server fails | Missing `${CLAUDE_PLUGIN_ROOT}` | Use variable for all plugin paths |
| Path errors | Absolute paths used | All paths must be relative, start with `./` |
| LSP "Executable not found" | Language server not installed | Install the binary separately |

### Hook Troubleshooting Checklist

1. Script is executable: `chmod +x ./scripts/your-script.sh`
2. Shebang line present: `#!/bin/bash` or `#!/usr/bin/env bash`
3. Path uses `${CLAUDE_PLUGIN_ROOT}`: not hardcoded
4. Event name is **case-sensitive**: `PostToolUse`, not `posttooluse`
5. Matcher pattern is correct regex: `"Write|Edit"` for file operations
6. Hook type is valid: `command`, `http`, `prompt`, or `agent`

### MCP Server Troubleshooting

1. Command exists and is executable
2. All paths use `${CLAUDE_PLUGIN_ROOT}`
3. Check `claude --debug` for initialization errors
4. Test server manually outside Claude Code

---

## 20. Version Management

Follow semantic versioning:

```
MAJOR.MINOR.PATCH
```

- **MAJOR** — Breaking changes (incompatible API changes)
- **MINOR** — New features (backward-compatible additions)
- **PATCH** — Bug fixes (backward-compatible fixes)

### Important

> Claude Code uses the version to determine whether to update your plugin. If you change code but don't bump the version, existing users **won't see changes** due to caching.

### Best Practices

- Start at `1.0.0` for first stable release
- Use pre-release versions like `2.0.0-beta.1` for testing
- Document changes in `CHANGELOG.md`
- Version can be set in `plugin.json` or `marketplace.json` (only need one place)

---

## Sources

- [Create plugins — Claude Code Docs](https://code.claude.com/docs/en/plugins)
- [Plugins reference — Claude Code Docs](https://code.claude.com/docs/en/plugins-reference)
- [claude-code/plugins/README.md — GitHub](https://github.com/anthropics/claude-code/blob/main/plugins/README.md)
- [Official Plugin Marketplace](https://claude.com/plugins)
- [Official Plugin Repository](https://github.com/anthropics/claude-plugins-official)
