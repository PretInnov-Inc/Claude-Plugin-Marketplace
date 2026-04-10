---
name: workspace-hygiene
description: >-
  Use this skill when the user asks to "clean up", "optimize workspace", "free disk space",
  "remove dead files", "consolidate", "hygiene", "maintenance", "declutter",
  "clean .claude directory", "stale files", "dead weight", or when the workspace
  has accumulated unnecessary state that should be cleaned.
version: 1.0.0
---

# Workspace Hygiene

Systematic cleanup and optimization of the `.claude/` directory and project workspace. Based on analysis of 500+ sessions revealing significant dead weight accumulation.

## Known Dead Weight (from historical analysis)

These are proven cleanup targets with zero risk:

### 1. Empty Session-Env Directories
- **Location**: `~/.claude/session-env/*/`
- **Problem**: 609+ empty directories created per session, never used
- **Action**: Remove all empty directories: `find ~/.claude/session-env -type d -empty -delete`
- **Risk**: Zero — feature creates new dirs on demand

### 2. Failed Telemetry Events
- **Location**: `~/.claude/telemetry/1p_failed_events.*.json`
- **Problem**: Events generated but never sent (telemetry disabled). Files up to 23MB each.
- **Action**: Delete all: `rm ~/.claude/telemetry/1p_failed_events.*.json`
- **Risk**: Zero — these are unsent telemetry payloads

### 3. Empty Todo Files
- **Location**: `~/.claude/todos/*.json`
- **Problem**: 97% of todo files are empty `[]` arrays (1,209 of 1,245)
- **Action**: Remove empty ones: `find ~/.claude/todos -name "*.json" -size 2c -delete`
- **Risk**: Zero — empty arrays contain no data

### 4. Stale Security Warning State
- **Location**: `~/.claude/security_warnings_state_*.json`
- **Problem**: One per session, accumulates indefinitely
- **Action**: Keep last 10, remove older: Sort by date, keep newest 10
- **Risk**: Low — may re-show already-acknowledged warnings (minor UX impact)

### 5. Old Debug Logs
- **Location**: `~/.claude/debug/*.txt`
- **Problem**: 65+ files, some 387KB, rarely needed
- **Action**: Keep last 5, remove older
- **Risk**: Low — historical debug data not needed for future sessions

### 6. Old File History
- **Location**: `~/.claude/file-history/*/`
- **Problem**: Full file snapshots (not diffs). 173 session directories with multiple versions.
- **Action**: Remove sessions older than 30 days (configurable)
- **Risk**: Low — lose undo ability for old sessions only

## Cleanup Process

### Phase 1: Assess (READ ONLY)
Before deleting anything, scan and report:

```bash
# Count dead weight
echo "=== Dead Weight Assessment ==="
echo "Empty session-env dirs: $(find ~/.claude/session-env -type d -empty | wc -l)"
echo "Failed telemetry files: $(ls ~/.claude/telemetry/1p_failed_events.*.json 2>/dev/null | wc -l)"
echo "Empty todo files: $(find ~/.claude/todos -name '*.json' -size 2c 2>/dev/null | wc -l)"
echo "Security warning files: $(ls ~/.claude/security_warnings_state_*.json 2>/dev/null | wc -l)"
echo "Debug log files: $(ls ~/.claude/debug/*.txt 2>/dev/null | wc -l)"
echo "File history dirs: $(ls -d ~/.claude/file-history/*/ 2>/dev/null | wc -l)"

# Calculate total size
echo "=== Total Dead Weight Size ==="
du -sh ~/.claude/telemetry/ 2>/dev/null
du -sh ~/.claude/session-env/ 2>/dev/null
du -sh ~/.claude/todos/ 2>/dev/null
du -sh ~/.claude/debug/ 2>/dev/null
du -sh ~/.claude/file-history/ 2>/dev/null
```

### Phase 2: Confirm with User
ALWAYS show the assessment before cleaning. Ask for explicit confirmation.
Never delete without showing what will be removed and how much space will be freed.

### Phase 3: Execute Cleanup
Run each cleanup category separately with progress reporting.

### Phase 4: Verify
Re-run assessment to confirm cleanup. Report space saved.

## Project Directory Consolidation

### Detecting Fragmented Projects
A project is fragmented when it exists at multiple paths in `~/.claude/projects/`:

```
Example: Internal-Tracker exists at:
  -Volumes-Mac-Internal-Tracker (55 sessions)
  -Volumes-Mac-new-Internal-Tracker (59 sessions)
  -Volumes-Mac-projects-Internal-Tracker (35 sessions)
```

**Detection**: Scan `~/.claude/projects/` directory names, extract project name (last path component), group by name.

**Resolution**: Cannot merge automatically (different paths = different project state). But CAN:
1. Report which projects are fragmented
2. Recommend which path to standardize on (most sessions = most context)
3. Warn when user is about to create a new fragment

## Auto-Optimization

### Cortex Data File Trimming
The Cortex plugin itself generates data files that need periodic trimming:
- `tool-usage.jsonl` — Keep last 2000 entries (auto-trimmed by hook)
- `prompt-log.jsonl` — Keep last 500 entries (auto-trimmed by hook)
- `session-log.jsonl` — Keep last 1000 entries
- `learnings.jsonl` — Keep last 200 entries (older learnings may be stale)
- `anti-patterns.jsonl` — Keep last 100 entries
- `decision-journal.jsonl` — Keep last 500 entries
- `patterns.jsonl` — Keep last 500 entries

### Settings Backup Cleanup
- `~/.claude/settings.json.backup.*` — Keep last 3, remove older
