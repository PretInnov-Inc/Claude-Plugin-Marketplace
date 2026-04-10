---
description: "Extract deep project DNA — architecture, fragile zones, coupling graphs, test coverage gaps."
argument-hint: "[project-path or 'refresh' or 'fragile' or 'coupling']"
---

You are executing the `/dna` command — Clamper's deep project DNA extraction.

## Behavior Based on Arguments

**`/dna` (no args)** — Full DNA extraction for current project:
1. Delegate to `clamper-scout` agent targeting the current working directory
2. Request complete DNA report: architecture, hot files, fragile zones, coupling, tests, build

**`/dna <path>`** — Extract DNA for a specific project:
1. Delegate to `clamper-scout` agent targeting the specified path
2. Same full report

**`/dna refresh`** — Force re-extraction (bypass cache):
1. Clear project-specific entries from `${CLAUDE_PLUGIN_ROOT}/data/dna-cache.jsonl`
2. Run full extraction
3. Cache new results

**`/dna fragile`** — Show only fragile zones:
1. Either read from cache or run targeted extraction
2. Output: files with high churn + low test coverage
3. Format as actionable list: "These files need tests or refactoring"

**`/dna coupling`** — Show only coupling groups:
1. Either read from cache or run targeted extraction
2. Output: files that change together
3. Format as dependency map

## Caching

DNA results are cached in `${CLAUDE_PLUGIN_ROOT}/data/dna-cache.jsonl` with TTL from `clamper-config.json` (`dna_cache_ttl_hours`, default 24h).

Cache format:
```json
{
  "project": "<name>",
  "pattern": "<architecture|fragile_zone|coupling|test_coverage|dependency>",
  "detail": "<finding>",
  "file_path": "<if applicable>",
  "timestamp": "<iso>"
}
```

Check cache freshness before running extraction. If cache is fresh, use it. If stale, re-extract.

## After Extraction

1. Cache all findings to `dna-cache.jsonl`
2. Update `clamper-config.json` dna_stats
3. Display the DNA report in the structured format defined by clamper-scout

Always end with:
`DNA extracted. <N> hot files, <M> fragile zones, <K> coupling groups identified.`
