---
name: project-dna
version: 1.0.0
description: "Deep project DNA extraction — living analysis of git history, architecture, fragile zones, coupling graphs, and test coverage. Goes beyond static CLAUDE.md."
triggers:
  - "analyze this project"
  - "project structure"
  - "what's the architecture"
  - "fragile zones"
  - "what files change together"
  - "test coverage gaps"
  - "project DNA"
  - "hot files"
  - "code coupling"
---

# Clamper Project DNA Skill

## Purpose

CLAUDE.md is static and shallow — a snapshot written once. Project DNA is **alive**: it's extracted from the project's actual git history, dependency graph, test infrastructure, and build system. It reveals what CLAUDE.md can't: which files are fragile, what changes together, where test coverage has gaps, and how the architecture actually works (not just how it was designed).

## DNA Dimensions

### 1. Architecture Fingerprint
- **Stack detection**: Read package.json, pyproject.toml, Cargo.toml, go.mod, Gemfile
- **Pattern recognition**: Monolith vs microservices vs monorepo vs plugin
- **Layer mapping**: Presentation → Business Logic → Data Access → Infrastructure
- **Entry point discovery**: Main files, route definitions, CLI entry points

### 2. Hot Files (High Churn)
Files that change most frequently in recent history signal active development areas or instability:

```bash
git log --oneline -100 --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20
```

Interpretation:
- High churn + high test coverage = active, healthy development
- High churn + low test coverage = **fragile zone** (Clamper's primary alert)
- High churn + many different authors = coordination risk

### 3. Fragile Zones
The intersection of **high churn** and **low test coverage**. These are the files most likely to break silently.

Detection algorithm:
1. Find files changed 5+ times in last 50 commits
2. For each, search for corresponding test file
3. If no test file or test file doesn't import the source: **FRAGILE**

### 4. Coupling Groups
Files that consistently change together reveal hidden dependencies:

```bash
# Co-change analysis from git log
git log --oneline -100 --name-only --pretty=format: | python3 -c "
import sys
from collections import defaultdict, Counter
commits = []
current = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        if current:
            commits.append(current)
            current = []
    else:
        current.append(line)
if current:
    commits.append(current)

pairs = Counter()
for files in commits:
    for i, a in enumerate(files):
        for b in files[i+1:]:
            pair = tuple(sorted([a, b]))
            pairs[pair] += 1

for (a, b), count in pairs.most_common(15):
    if count >= 3:
        print(f'{count}x: {a} <-> {b}')
"
```

### 5. Test Coverage Map
- Ratio of test files to source files per directory
- Modules with zero test files
- Test framework detection (pytest, jest, mocha, cargo test, go test)
- Whether tests actually import and exercise the source they claim to cover

### 6. Dependency Hotspots
Files imported by the most other files — changes here cascade widely:

```bash
# Most-imported files (Python)
grep -rh "^from \|^import " --include="*.py" | sed 's/from //' | sed 's/ import.*//' | sort | uniq -c | sort -rn | head -10

# Most-imported files (TypeScript/JavaScript)
grep -rh "from ['\"]" --include="*.ts" --include="*.tsx" --include="*.js" | sed "s/.*from ['\"]//;s/['\"].*//" | sort | uniq -c | sort -rn | head -10
```

## Cache & Freshness

DNA is cached in `${CLAUDE_SKILL_DIR}/../../data/dna-cache.jsonl` with configurable TTL (default: 24 hours).

Each cache entry:
```json
{
  "project": "<name>",
  "pattern": "<architecture|hot_file|fragile_zone|coupling|test_coverage|dependency_hotspot>",
  "detail": "<finding>",
  "file_path": "<if applicable>",
  "confidence": "<high|medium|low>",
  "timestamp": "<iso>"
}
```

## Integration

- **Session start**: `session-start.sh` reads DNA cache to inject fragile zones and coupling data into context
- **Manual extraction**: `/dna` command triggers full extraction via `clamper-scout` agent
- **Verification boost**: `clamper-verifier` uses DNA data to prioritize checks on fragile zones
- **Learning loop**: `clamper-learner` correlates DNA patterns with verification outcomes
