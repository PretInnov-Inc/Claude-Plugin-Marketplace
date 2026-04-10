---
description: "Clamper dashboard — verification stats, DNA status, ecosystem health, and session quality."
argument-hint: "[dashboard | stats | config | learn]"
---

You are executing the `/clamper` command — the Clamper intelligence dashboard.

## Behavior Based on Arguments

**`/clamper` or `/clamper dashboard` (no args)** — Full dashboard:

Read all data files from `${CLAUDE_PLUGIN_ROOT}/data/` and render:

```
╔══════════════════════════════════════════════════╗
║              CLAMPER DASHBOARD                   ║
╠══════════════════════════════════════════════════╣
║ Verification                                     ║
║   Total: <N>  Pass: <N>  Fail: <N>  Review: <N> ║
║   Pass Rate: <N>%                                ║
║   Last: <timestamp>                              ║
╠──────────────────────────────────────────────────╣
║ Project DNA                                      ║
║   Projects Analyzed: <N>                         ║
║   Fragile Zones: <N>                             ║
║   Last Extraction: <timestamp>                   ║
╠──────────────────────────────────────────────────╣
║ Session Quality                                  ║
║   Avg Score: <N>/100 (last 10 sessions)          ║
║   Trend: <improving|stable|declining>            ║
║   Tests Run: <N>% of sessions                    ║
╠──────────────────────────────────────────────────╣
║ Ecosystem                                        ║
║   Projects Initialized: <N>                      ║
║   Last Init: <timestamp>                         ║
╚══════════════════════════════════════════════════╝
```

Data sources:
- `clamper-config.json` — stats and thresholds
- `verification-log.jsonl` — verification events
- `outcomes.jsonl` — session quality scores
- `dna-cache.jsonl` — DNA findings

**`/clamper stats`** — Quick stats only:
- Read `clamper-config.json` and show verification_stats, dna_stats, init_stats
- Show last 5 session quality scores from `outcomes.jsonl`

**`/clamper config`** — Show current configuration:
- Display all thresholds from `clamper-config.json`
- Show suppressed warnings
- Show project overrides

**`/clamper learn`** — Trigger learning analysis:
1. Delegate to `clamper-learner` agent
2. Analyze all outcome data for patterns
3. Display learning report with promotable patterns

## Reading Data Files

For each JSONL file, read and parse line by line:
```python
import json
entries = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line.strip()))
```

Count events by type, calculate averages, detect trends (compare last 5 vs previous 5 session quality scores).

## Trend Detection

- **Improving**: last 5 avg > previous 5 avg by 5+ points
- **Declining**: last 5 avg < previous 5 avg by 5+ points
- **Stable**: within 5 points
