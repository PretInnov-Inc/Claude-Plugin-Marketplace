# Claude-Plugin-Marketplace — Developer Instructions

This file is the authoritative operating manual for Claude working in this repository.
**Read every section before making any change.** These rules exist because we hit each
of these failure modes in production and had to diagnose them the hard way.

---

## 1. How Claude Code discovers plugins — the full chain

Claude Code does NOT scan directories. It follows a strict resolution chain:

```
marketplace.json          ← controls /plugin UI "available" count
  └── plugin.json         ← controls what components Claude Code loads
        ├── "skills"      ← without this key, 0 skills are registered
        ├── "hooks"       ← without this key, 0 hook events fire
        └── "agents"      ← (auto-discovered from agents/ if skills declared)
```

**Root failure mode (hit in production):** Sentinel had skills/ and hooks-handlers/ directories
with correct files, but `plugin.json` had no `"skills"` or `"hooks"` keys. Claude Code loaded
the plugin with zero skills and zero hooks. The fix is in the manifest, not the files.

### Files Claude Code reads at load time

| File | Purpose | Consequence if wrong |
|---|---|---|
| `.claude-plugin/marketplace.json` | Index for `/plugin` UI | Plugin invisible or wrong "available" count |
| `plugins/<name>/.claude-plugin/plugin.json` | Component declarations | Skills/hooks silently missing |
| `plugins/<name>/hooks/hooks.json` | Hook event routing | Hooks never fire |
| `plugins/<name>/skills/<skill>/SKILL.md` | Skill prompt + metadata | Skill not invokable |

---

## 2. The two caches you must understand

Claude Code maintains **two separate caches**. They are NOT automatically kept in sync:

```
~/.claude/plugins/marketplaces/pretinnov-plugins/   ← marketplace cache (what /plugin list reads)
~/.claude/plugins/cache/pretinnov-plugins/<name>/<version>/  ← install cache (what Claude Code loads at runtime)
```

**Root failure mode (hit in production):** We fixed `plugin.json` manifests in the local source
and marketplace cache, but Claude Code was still loading stale copies from the install cache
because the version string hadn't changed — Claude Code had no reason to re-copy.

### When each cache updates

| Cache | Updates when |
|---|---|
| Marketplace cache | `/plugin update-marketplaces` or `autoUpdate: true` on session start |
| Install cache | Only when `version` in `marketplace.json` + `plugin.json` **both** increase |

**Rule: the only way to push changes to end users is to bump the version.**

---

## 3. Mandatory checks before ANY change

Before editing any file in this repo, run the audit:

```bash
python3 - <<'EOF'
import json, os

ROOT = '/Volumes/Mac/autonomous/Claude-Plugin-Marketplace'
ALLOWED_TYPES = {"string", "number", "boolean", "directory", "file"}
ALLOWED_USER_CONFIG_KEYS = {"title", "description", "type", "sensitive"}

mj = json.load(open(f'{ROOT}/.claude-plugin/marketplace.json'))
mj_plugins = {p['name']: p['version'] for p in mj['plugins']}
print(f"marketplace.json v{mj['version']} — {len(mj_plugins)} plugins listed\n")

all_ok = True
for name in sorted(os.listdir(f'{ROOT}/plugins')):
    pj_path = f'{ROOT}/plugins/{name}/.claude-plugin/plugin.json'
    if not os.path.exists(pj_path):
        print(f"  ❌ {name}: MISSING plugin.json"); all_ok = False; continue
    pj = json.load(open(pj_path))
    errs = []

    # --- Identity & registry ---
    if name not in mj_plugins:
        errs.append("MISSING from marketplace.json")
    elif mj_plugins[name] != pj.get('version'):
        errs.append(f"version mismatch: marketplace={mj_plugins[name]} plugin.json={pj.get('version')}")
    if 'skills' not in pj:        errs.append("MISSING required key: skills")
    if 'homepage' not in pj:      errs.append("MISSING required key: homepage")
    author = pj.get('author', {})
    if author.get('name') != 'Siddharth Gupta' or 'PretInnov-Inc' not in author.get('url', ''):
        errs.append(f"WRONG author: {author}")

    # --- Forbidden: hooks declaration causes duplicate-load ---
    if pj.get('hooks') == './hooks/hooks.json':
        errs.append('FORBIDDEN: "hooks": "./hooks/hooks.json" (causes duplicate-load — auto-loaded)')

    # --- userConfig schema ---
    for k, cfg in pj.get('userConfig', {}).items():
        if 'title' not in cfg:           errs.append(f"userConfig.{k}: missing 'title'")
        if cfg.get('type') not in ALLOWED_TYPES:
            errs.append(f"userConfig.{k}: invalid type '{cfg.get('type')}' (allowed: {ALLOWED_TYPES})")
        for unknown in set(cfg) - ALLOWED_USER_CONFIG_KEYS:
            errs.append(f"userConfig.{k}: forbidden key '{unknown}' (only title/description/type/sensitive allowed)")

    # --- hooks.json format must be record (object), not array ---
    hj_path = f'{ROOT}/plugins/{name}/hooks/hooks.json'
    if os.path.exists(hj_path):
        hj = json.load(open(hj_path))
        if isinstance(hj.get('hooks'), list):
            errs.append("hooks.json uses array format — must be record keyed by event name")

    if errs:
        all_ok = False
        print(f"  ❌ {name} v{pj.get('version','?')}")
        for e in errs: print(f"       {e}")
    else:
        print(f"  ✅ {name} v{pj['version']}")

print()
print("ALL OK — safe to commit." if all_ok else "ERRORS — fix before committing.")
EOF
```

All plugins must show `✅` before you commit or push.

---

## 4. Required fields in every plugin.json

Every `plugins/<name>/.claude-plugin/plugin.json` MUST have ALL of these:

```json
{
  "name": "<plugin-name>",
  "version": "<semver>",
  "description": "<one-line description>",
  "author": {
    "name": "Siddharth Gupta",
    "url": "https://github.com/PretInnov-Inc"
  },
  "homepage": "https://github.com/PretInnov-Inc/forge-marketplace/tree/main/plugins/<name>",
  "license": "MIT",
  "skills": ["./skills"]
}
```

**Author format is strict.** Never use `"GuptaJi"`, a plugin name, or omit the `url`.
The `skills` key is a load-time declaration — missing it = invisible skills.

### CRITICAL: Do NOT declare `"hooks": "./hooks/hooks.json"`

The standard `hooks/hooks.json` file is **auto-loaded by Claude Code**. Declaring it
in `plugin.json` causes a "Duplicate hooks file detected" error and the plugin's
hooks fail to register entirely.

The `manifest.hooks` field is ONLY for *additional* hook files beyond the default.
Since we never have additional hook files, never declare `hooks` in plugin.json.

**Wrong (causes duplicate-load error):**
```json
{ "skills": ["./skills"], "hooks": "./hooks/hooks.json" }
```

**Right (default hooks.json auto-loaded):**
```json
{ "skills": ["./skills"] }
```

### CRITICAL: `userConfig` schema — strictly limited

Each entry in `userConfig` may ONLY contain these 4 keys:

| Key | Required | Type |
|---|---|---|
| `title` | YES | string |
| `description` | YES | string |
| `type` | YES | one of `"string"`, `"number"`, `"boolean"`, `"directory"`, `"file"` |
| `sensitive` | YES | boolean |

**Forbidden keys** (will cause manifest validation to fail):
- `enum` — put allowed values in the `description` text instead
- `default` — put default value in the `description` text instead
- `minimum` / `maximum` — put range in the `description` text instead

**Forbidden type values:**
- `integer` — use `"number"` instead

**Wrong (Sentinel v3.0.0 — failed validation):**
```json
"churn_threshold": {
  "type": "integer", "default": 5, "minimum": 1, "maximum": 50,
  "description": "Number of edits..."
}
```

**Right (Sentinel v3.1.1 — passes validation):**
```json
"churn_threshold": {
  "title": "Churn Threshold",
  "description": "Number of edits to the same file before churn warning fires. Default: 5.",
  "type": "number",
  "sensitive": false
}
```

---

## 5. Required fields in marketplace.json

`/.claude-plugin/marketplace.json` is the root index. Every plugin directory under `plugins/`
MUST have a corresponding entry here. Missing = plugin doesn't appear in `/plugin` UI.

```json
{
  "name": "<plugin-name>",
  "source": "./plugins/<name>",
  "version": "<must match plugin.json exactly>",
  "description": "<accurate, current description>",
  "author": { "name": "Siddharth Gupta" },
  "category": "<code-quality|intelligence|plugin-development|search>"
}
```

**Version must match `plugin.json` exactly.** Mismatch causes confusion in the UI and
may prevent Claude Code from correctly resolving the install path.

---

## 5b. hooks.json format — record, not array

Claude Code expects `hooks/hooks.json` to use the **nested record format** keyed by event name.
The flat array format will fail with `Invalid input: expected record, received array`.

**Wrong (codebase-radar v1.0.0 — failed):**
```json
{
  "hooks": [
    {"event": "SessionStart", "handler": "hooks-handlers/session-start.py", "timeout": 20000}
  ]
}
```

**Right (the canonical format):**
```json
{
  "description": "Plugin lifecycle hooks: ...",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks-handlers/session-start.py",
            "timeout": 20
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks-handlers/post-tool.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Notes:
- `hooks` is a **record** (object), keys are event names (`SessionStart`, `PostToolUse`, `PreToolUse`, `Stop`, `UserPromptSubmit`, `PreCompact`, etc.)
- Each event maps to an **array of hook groups**, each with optional `matcher` regex and a nested `hooks` array
- Each entry has `type: "command"`, `command` (with `${CLAUDE_PLUGIN_ROOT}`), and `timeout` in **seconds** (not milliseconds)
- Use `python3 ${CLAUDE_PLUGIN_ROOT}/hooks-handlers/<file>.py` — never a bare relative path

## 6. Adding a new plugin — checklist

When adding a new plugin, ALL of the following must happen together:

- [ ] Create `plugins/<name>/` directory with full structure (skills/, hooks/, hooks-handlers/, agents/, data/, bin/)
- [ ] Write `plugins/<name>/.claude-plugin/plugin.json` with ALL required fields (section 4)
- [ ] Add entry to `.claude-plugin/marketplace.json` (section 5)
- [ ] Write `plugins/<name>/hooks/hooks.json` (even if minimal — empty `{"hooks":[]}` is valid)
- [ ] Write at least one skill in `plugins/<name>/skills/<skill>/SKILL.md`
- [ ] Add to ALL ecosystem cross-reference tables in every plugin's README.md
- [ ] Add to install/update/uninstall commands in the root README.md
- [ ] Run `bash scripts/sync-plugins.sh` to push into local Claude caches
- [ ] Bump marketplace.json version (minor bump: x.Y.z → x.Y+1.0)

---

## 7. Updating an existing plugin — version bump rules

| What changed | Version bump | Example |
|---|---|---|
| Bug fix, manifest field added/corrected | Patch | `1.0.1` → `1.0.2` |
| New skill, agent, or hook added | Minor | `1.0.x` → `1.1.0` |
| Breaking change (new required config, removed skill) | Major | `1.x.y` → `2.0.0` |

**Always bump in both places:**
1. `plugins/<name>/.claude-plugin/plugin.json` — the `"version"` field
2. `.claude-plugin/marketplace.json` — the matching plugin entry's `"version"` field

Then run `bash scripts/sync-plugins.sh` to propagate locally.

---

## 8. Current plugin registry (ground truth as of 2026-04-13)

| Plugin | Version | Skills | Agents | Hook Events | Handlers | bin |
|---|---|---|---|---|---|---|
| clamper | 1.1.3 | 3 | 4 | 3 | 2 | 0 |
| codebase-radar | 1.0.2 | 4 | 2 | 4 | 4 | 3 |
| cortex | 1.0.3 | 12 | 8 | 6 | 5 | 1 |
| forge | 1.0.3 | 8 | 5 | 4 | 3 | 2 |
| sentinel | 3.1.1 | 12 | 24 | 7 | 8 | 6 |

**Total: 5 plugins, 39 skills, 43 agents, 24 hook events, 22 handlers, 12 bin tools**

When you add a component (skill, agent, handler), update this table.

---

## 9. sync-plugins.sh — when and how to use it

`scripts/sync-plugins.sh` syncs local source → marketplace cache → install cache.

```bash
# Dry-run first to see what will change
bash scripts/sync-plugins.sh --dry-run

# Apply when satisfied
bash scripts/sync-plugins.sh
```

Run this after EVERY change before restarting Claude Code. It handles:
- Updating `marketplace.json` in the local Claude cache
- rsyncing each plugin's files into the marketplace cache
- Installing new versions into the install cache and registering them

**Data files are excluded from sync** (`data/*.jsonl`, `data/*-cache.*`) to preserve
runtime state (learnings, session logs, decision journals). Never wipe these.

---

## 10. Why end users get stale plugins — and how to prevent it

`autoUpdate: true` in the marketplace config means Claude Code re-fetches the repo index
on session start. But it only re-installs a plugin when the version number increases.

**If you change a hook handler, skill, or agent without bumping the version:**
- Your marketplace cache shows the new file
- End users' install cache still has the old file
- Claude Code loads the old file (no indication anything changed)

**Fix: always bump version before pushing to GitHub.** The version bump is the update signal.

**Never push to GitHub without:**
1. Bumping `plugin.json` version
2. Bumping matching entry in `marketplace.json`
3. Running `bash scripts/sync-plugins.sh`
4. Running the audit from section 3 (all OK)

---

## 11. Install cache anatomy — where Claude Code loads from

```
~/.claude/plugins/
  installed_plugins.json                    ← registry: which plugins are installed at what version
  marketplaces/pretinnov-plugins/
    .claude-plugin/marketplace.json         ← index read by /plugin UI (available count)
    plugins/<name>/                         ← marketplace cache (updated by /plugin update-marketplaces)
  cache/pretinnov-plugins/
    <name>/<version>/                       ← INSTALL CACHE — Claude Code loads from here at runtime
      .claude-plugin/plugin.json            ← if missing skills/hooks here, they don't load
      skills/
      hooks/
      hooks-handlers/
      agents/
```

**When Claude Code can't see your hooks/skills after fixing plugin.json:**
The fix must be applied to `cache/pretinnov-plugins/<name>/<version>/.claude-plugin/plugin.json`,
not just the source. The fastest fix: bump the version so Claude Code creates a fresh install cache entry.

---

## 11b. Errors you will see in `/doctor` and what they mean

Run `/doctor` after any plugin change to catch issues. Common errors:

| Error message | Root cause | Fix |
|---|---|---|
| `Duplicate hooks file detected: ./hooks/hooks.json` | `plugin.json` declares `"hooks": "./hooks/hooks.json"` (auto-loaded) | Remove the `hooks` key from `plugin.json` |
| `Hook load failed: Invalid input: expected record, received array` | `hooks/hooks.json` uses flat `[...]` array | Convert to nested record format keyed by event (see section 5b) |
| `userConfig.X.title: Invalid input: expected string, received undefined` | Missing `title` in a userConfig entry | Add `"title": "..."` to every userConfig entry |
| `userConfig.X: Unrecognized key: "enum"` | `enum` not allowed in userConfig | Remove `enum`, document allowed values in `description` |
| `userConfig.X: Unrecognized keys: "minimum", "maximum"` | Range constraints not allowed | Remove, document range in `description` |
| `userConfig.X.type: Invalid option: expected one of "string"\|"number"\|"boolean"\|"directory"\|"file"` | Used `integer` or other invalid type | Use `"number"` for ints |
| `Unknown skill: <name>` | Skill name in user invocation doesn't match any `name:` field in any SKILL.md frontmatter | Either rename the skill in SKILL.md, or create a thin alias skill (e.g. `skills/<short-name>/SKILL.md` that delegates) |
| Plugin shows in `/plugin` but skills/hooks missing | Install cache stale (version not bumped) | Bump `version` in both `plugin.json` and `marketplace.json`, run `sync-plugins.sh` |

## 12. Debugging checklist — "Claude Code can't see my plugin changes"

Work through this in order:

1. **Is the plugin in marketplace.json?**
   ```bash
   python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); print([p['name'] for p in d['plugins']])"
   ```

2. **Does plugin.json have skills and hooks keys?**
   ```bash
   python3 -c "import json; d=json.load(open('plugins/<name>/.claude-plugin/plugin.json')); print('skills' in d, 'hooks' in d)"
   ```

3. **Is the install cache version stale?**
   ```bash
   # installed version
   python3 -c "import json; d=json.load(open('~/.claude/plugins/installed_plugins.json')); print(d['plugins'].get('<name>@pretinnov-plugins'))"
   # vs source version
   python3 -c "import json; print(json.load(open('plugins/<name>/.claude-plugin/plugin.json'))['version'])"
   ```

4. **Does the install cache plugin.json have skills/hooks?**
   ```bash
   cat ~/.claude/plugins/cache/pretinnov-plugins/<name>/<version>/.claude-plugin/plugin.json
   ```

5. **Did you run sync-plugins.sh after making changes?**

6. **Did you restart Claude Code after syncing?** (Required for hook/skill registration)

---

## 13. Repository structure

```
Claude-Plugin-Marketplace/
  .claude-plugin/
    marketplace.json          ← ROOT INDEX — add every plugin here
  plugins/
    clamper/                  ← 3 skills, 4 agents, 3 hook events
    codebase-radar/           ← 4 skills, 2 agents, 4 hook events
    cortex/                   ← 12 skills, 8 agents, 6 hook events
    forge/                    ← 8 skills, 5 agents, 4 hook events
    sentinel/                 ← 11 skills, 24 agents, 7 hook events (v3)
  scripts/
    sync-plugins.sh           ← run after every change
  README.md
  CLAUDE.md                   ← this file
```

Each plugin follows this internal structure:
```
plugins/<name>/
  .claude-plugin/
    plugin.json               ← MUST have skills, hooks, homepage, author
  skills/<skill>/SKILL.md
  agents/<agent>.md
  hooks/hooks.json
  hooks-handlers/<handler>.py
  bin/<cli-tool>
  data/
  output-styles/              ← (optional)
  commands/                   ← (optional)
  scripts/install.sh
  README.md
```
