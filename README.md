# PretInnov Plugins — Claude Code Plugin Marketplace

> **By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)**

Three production-grade plugins that make Claude Code smarter, safer, and capable of building its own extensions.

---

## What's Inside?

| Plugin | What It Does | One-Liner |
|--------|-------------|-----------|
| **Clamper** | Verifies your code, maps your project DNA, and scaffolds full agent ecosystems | *"Clip it, Clamp it."* |
| **Cortex** | Remembers what worked and what failed across ALL your sessions, then uses that knowledge automatically | *"Claude Code with a brain."* |
| **Forge** | Creates entire plugins from a simple chat prompt — researches, asks questions, designs, and generates everything | *"Build plugins by talking."* |

---

## How to Install (Step by Step)

### What You Need First

- **Claude Code** installed on your machine. If you don't have it yet, go to [claude.ai/code](https://claude.ai/code) and follow the install instructions.
- That's it. No other software needed.

### Step 1: Add This Marketplace

This tells Claude Code "hey, there's a plugin store at this GitHub repo." You only do this once.

**Option A — Using the Terminal (CLI):**

Open your terminal and type:
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

Just type this as a message:
```
/plugin marketplace add github:PretInnov-Inc/forge-marketplace
```

### Step 2: Install the Plugins You Want

Now you can install any (or all) of the 3 plugins:

```bash
# Install all three:
claude plugin install clamper@pretinnov-plugins
claude plugin install cortex@pretinnov-plugins
claude plugin install forge@pretinnov-plugins
```

Or from inside a Claude Code session:
```
/plugin install clamper@pretinnov-plugins
/plugin install cortex@pretinnov-plugins
/plugin install forge@pretinnov-plugins
```

### Step 3: Verify They're Installed

Type `/help` inside Claude Code — you should see the new commands listed under their plugin namespaces.

---

## Quick Start for Each Plugin

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

---

## Updating Plugins

When we release new versions, update like this:

```bash
# Update the marketplace catalog first
claude plugin marketplace update pretinnov-plugins

# Then update individual plugins
claude plugin update clamper@pretinnov-plugins
claude plugin update cortex@pretinnov-plugins
claude plugin update forge@pretinnov-plugins
```

---

## Uninstalling

```bash
claude plugin uninstall clamper@pretinnov-plugins
claude plugin uninstall cortex@pretinnov-plugins
claude plugin uninstall forge@pretinnov-plugins

# Remove the marketplace entirely
claude plugin marketplace remove pretinnov-plugins
```

---

## Each Plugin Has Its Own Detailed README

- [Clamper README](./plugins/clamper/README.md) — Full guide with screenshots-style examples
- [Cortex README](./plugins/cortex/README.md) — Full guide with every command explained
- [Forge README](./plugins/forge/README.md) — Full guide for building plugins from chat

---

## License

MIT — Use it, modify it, share it. No restrictions.

## Author

**Siddharth Gupta** — [PretInnov Technologies](https://github.com/PretInnov-Inc)
