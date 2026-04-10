---
name: research
description: >-
  Research phase for plugin creation. Searches the internet, GitHub repos, plugin
  marketplaces, and documentation to find existing solutions, best practices, and
  patterns before building a new plugin. Use when asked to research a plugin idea
  or find existing plugins.
version: 1.0.0
argument-hint: "[plugin-concept or topic to research]"
---

# Forge Research Phase

You are conducting the research phase of the Plugin Forge pipeline. Your job is to thoroughly investigate what already exists before any code is written.

## Research Protocol

Given the plugin concept in `$ARGUMENTS`, execute these research steps:

### Step 1: Direct Plugin Search
Use WebSearch with these queries (adapt to the specific concept):
- `claude code plugin <concept> github`
- `claude code skill <concept>`
- `<concept> AI coding assistant plugin 2025 2026`
- `awesome-claude-code <concept>`

### Step 2: Ecosystem Scan
Use WebSearch for broader ecosystem research:
- `<concept> tool CLI open source`
- `<concept> best practices patterns`
- `<concept> implementation approaches`

### Step 3: Deep Dive
For the top 2-3 most relevant results, use WebFetch to:
- Read README files of existing plugins/tools
- Extract architecture patterns
- Identify what works and what doesn't
- Note which Claude Code plugin components they use (hooks, agents, skills, MCP)

### Step 4: Documentation Check
If the plugin concept involves specific technologies, fetch relevant docs:
- Claude Code plugin reference: https://code.claude.com/docs/en/plugins-reference
- Technology-specific docs via context7 MCP or WebFetch

### Step 5: Synthesize & Report

Present findings in this format:

```
═══════════════════════════════════════════
  FORGE RESEARCH REPORT: <concept>
═══════════════════════════════════════════

## Existing Solutions Found
- <name> (<url>) — <what it does, strengths, gaps>
- ...

## Patterns Worth Adopting
- <pattern from existing solutions>
- ...

## Gaps Our Plugin Could Fill
- <what's missing from existing solutions>
- ...

## Recommended Architecture
Based on research:
- Hooks needed: <list>
- Agents recommended: <list>
- Key skills: <list>
- Data to persist: <list>

## Pitfalls to Avoid
- <learned from existing implementations>
- ...

═══════════════════════════════════════════
```

### Step 6: Cache Results

Write each finding to `${CLAUDE_PLUGIN_ROOT}/data/research-cache.jsonl`:
```json
{
  "finding": "<summary of what was found>",
  "source": "<URL or description>",
  "relevance": "high|medium|low",
  "project": "<plugin concept name>",
  "category": "existing-solution|pattern|pitfall|gap|best-practice|documentation",
  "details": "<any additional details worth preserving>",
  "timestamp": "<ISO-8601>"
}
```

## Research Depth

Read `${CLAUDE_PLUGIN_ROOT}/data/forge-config.json` for `thresholds.research_queries_min` and `research_queries_max`. Default: 3 minimum, 12 maximum queries. Adjust depth based on how novel the concept is — well-trodden territory (like linting plugins) needs less research than novel concepts (like AI-to-AI communication plugins).
