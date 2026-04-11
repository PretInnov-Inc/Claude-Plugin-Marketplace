# codebase-radar — Hybrid Semantic Search for Claude Code

> **Stop burning tokens on Grep. Search by meaning.**
>
> By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)

---

## What Is codebase-radar?

When you ask Claude Code "where does the auth flow start?" or "find all database error handling", the default approach is to run repeated `Grep` and `Glob` calls — burning context window tokens every time, returning noisy results, and missing code that expresses the concept differently.

**codebase-radar replaces that with a persistent, offline semantic index.**

It chunks your codebase using AST-aware boundaries (tree-sitter for 15 languages), embeds every chunk with local HuggingFace sentence-transformers, stores them in LanceDB, and serves results via **hybrid BM25 + dense vector search** — the same technique used in production retrieval systems. All offline, all free, zero API keys needed.

### Why LanceDB?

Three databases were evaluated — Qdrant, ChromaDB, and LanceDB:

| Database | Hybrid Search | Offline | RAM Usage | Decision |
|----------|--------------|---------|-----------|---------|
| Qdrant | Yes (BM25 via FastEmbed) | ❌ Bug: always tries network | Low | Rejected |
| ChromaDB | No (HNSW only) | ✓ | Grows unbounded | Rejected |
| **LanceDB** | **Yes (native Tantivy/Rust)** | **✓ Fully offline** | **Disk-native** | **Chosen** |

LanceDB stores indexes on disk (not RAM), does hybrid search natively in Rust via Tantivy, and has been proven at 700M vectors. It wins on every dimension for an embedded, offline use case.

### The Token Savings

Semantic search finds the right 10 chunks in one shot. Traditional grep-based exploration often requires 15-40 round trips before Claude has the full picture. Real-world usage shows **40-60% token reduction** on exploration-heavy sessions.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  codebase-radar Architecture                                        │
│                                                                     │
│  Claude Code                    MCP Server (in venv)               │
│  ──────────────                 ─────────────────────────────────  │
│  SessionStart hook ──────────►  Merkle-tree diff detection          │
│    (stdlib Python)              → emits list of changed files       │
│         │                                                           │
│         ▼                                                           │
│  systemMessage: "call          index_codebase MCP tool             │
│  reindex_file for X,Y,Z"  ──►  tree-sitter AST chunking            │
│                                 sentence-transformers embed         │
│                                 LanceDB upsert + FTS index          │
│                                                                     │
│  /radar:search "query"    ──►  search_code MCP tool                │
│                                 embed query → hybrid search         │
│                                 BM25 + dense (RRF merge)            │
│                                 return ranked chunks                │
│                                                                     │
│  PostToolUse hook         ──►  "call reindex_file for edited file" │
│  (Write/Edit/MultiEdit)                                             │
│                                                                     │
│  Stop hook                ──►  log session search stats             │
└─────────────────────────────────────────────────────────────────────┘
```

**Key architectural decision — Hook → MCP Indirection:** Hook handlers use Python stdlib only (zero deps) so they are always fast and never break. The heavy work (lancedb, sentence-transformers, tree-sitter) lives in an isolated venv. Hooks tell Claude what to call via `systemMessage`; Claude calls the MCP tools. This decouples hook reliability from MCP server state.

---

## Installation

### Prerequisites

- Python 3.10+
- Claude Code with MCP support enabled
- ~2GB disk space (for HuggingFace model download on first run)

### Install

```bash
# Clone the marketplace (if you haven't already)
git clone https://github.com/PretInnov-Inc/forge-marketplace.git
cd forge-marketplace

# Run the install script (creates venv, installs deps, validates all 25 files)
bash plugins/codebase-radar/scripts/install.sh
```

### Local Test (without cloning marketplace)

```bash
claude --plugin-dir /path/to/codebase-radar
```

### After Installing

You should see:

```
codebase-radar install complete
================================
  ✓ Python 3.10+ verified
  ✓ venv created at $CLAUDE_PLUGIN_DATA/venv/
  ✓ Dependencies installed (lancedb, sentence-transformers, tree-sitter)
  ✓ 25 plugin files validated
  ✓ MCP server import test passed
  ✓ bin/ tools made executable

Components:
  2 Agents    — radar-explorer, radar-indexer
  4 Skills    — radar, radar-search, radar-index, radar-config
  4 Hooks     — SessionStart, PostToolUse, PreToolUse, Stop
  6 MCP Tools — index_codebase, search_code, reindex_file,
                 get_status, clear_index, configure
  2 CLI Tools — radar-status, radar-reset
================================
```

### First-Time Index

After installing, build the index for your project:

```bash
cd /your/project
/radar:index
```

On first run, codebase-radar downloads `all-MiniLM-L6-v2` (~90MB). Subsequent runs are instant. A 50K-line codebase typically indexes in 30-60 seconds.

---

## Usage — Every Command Explained

### `/radar` — Index Status Dashboard

Shows the current index health for the active project.

```bash
/radar
```

**Example output:**

```
codebase-radar — Index Status
================================
Project:         /home/user/my-app
Project Hash:    a3f7c2b9e014
Status:          Indexed
Files Indexed:   847
Total Chunks:    6,234
Last Indexed:    2026-04-11T09:32:14
Embedding Model: all-MiniLM-L6-v2
Provider:        huggingface (local)
Index Size:      124 MB
Health:          OK
================================
Use /radar:search <query> to search your codebase semantically.
```

**Health logic:**
- `OK` — Index exists, last indexed within 7 days, files > 0
- `WARNING` — Index is older than 7 days, or chunk/file ratio is unexpectedly low
- `ERROR` — Index state is missing or corrupted

---

### `/radar:search <query>` — Semantic Code Search

The main command. Find code by concept, not just keyword.

```bash
# Natural language query
/radar:search "how does user authentication work"

# Find a concept across the codebase
/radar:search "database connection pooling"

# Find error handling patterns
/radar:search "retry logic with exponential backoff"

# Find a specific kind of function
/radar:search "function that validates email address"

# Cross-language concept search
/radar:search "event emitter pattern"
```

**Example output:**

```
[1] src/auth/middleware.py  (lines 45–89)  Score: 94%  [python]
──────────────────────────────────────────
def authenticate_request(request):
    token = request.headers.get("Authorization", "").split(" ")[-1]
    if not token:
        raise AuthError("Missing bearer token")
...

[2] src/auth/jwt.py  (lines 12–67)  Score: 87%  [python]
──────────────────────────────────────────
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
...

## What was found

Authentication flows through two main modules: `src/auth/middleware.py` handles
request-level token extraction and validation (lines 45-89), while `src/auth/jwt.py`
contains the JWT decode logic with expiry checks (lines 12-67). The session store
is in `src/auth/session.py`.
```

**How hybrid search works:**
- Your query is embedded into a 384-dim vector via `all-MiniLM-L6-v2`
- LanceDB runs a dense vector search (semantic similarity) in parallel with BM25 (keyword match)
- Results are merged via Reciprocal Rank Fusion (RRF) at `hybrid_alpha=0.7` (70% vector, 30% BM25)
- This beats pure vector search on exact-match queries, and beats pure BM25 on concept queries

---

### `/radar:index [path]` — Build or Refresh the Index

Triggers a full or incremental index of a codebase.

```bash
# Index the current directory (incremental by default)
/radar:index

# Index a specific path
/radar:index /path/to/other/project

# Force full rebuild (clears and re-embeds everything)
/radar:index --force-full
```

**What happens:**

1. Merkle-tree diff: computes `sha256(first 8KB)` of every non-excluded file — O(n) without reading full content
2. Compares against stored hashes in `data/index-state.json` — finds added/changed/deleted files
3. For each changed file: AST chunking (tree-sitter) → embedding (sentence-transformers) → LanceDB upsert
4. Rebuilds FTS (full-text search) index after bulk upsert
5. Updates state and reports final stats

**Incremental reindexing is the default.** On a 847-file project, only the 3 files you changed since last session get reprocessed — typically completes in under 3 seconds.

---

### `/radar:config` — Configure Settings

View and update codebase-radar settings interactively.

```bash
/radar:config
```

Displays the current config and prompts for which setting to change:

```
codebase-radar Configuration
==============================
Embedding Provider:  huggingface
Embedding Model:     all-MiniLM-L6-v2
Dimensions:          384
Chunk Size (tokens): 256
Chunk Overlap:       32
AST Chunking:        enabled
Fallback Strategy:   character
Search Top-K:        10
Hybrid Alpha:        0.7  (1.0 = vector only, 0.0 = BM25 only)
Reranking:           disabled
Exclusion Patterns:  node_modules/**, .git/**, *.min.js, ...
==============================

Which setting would you like to update?
```

**WARNING:** Changing the embedding model invalidates the existing index. You must clear and rebuild after switching models.

---

## What Happens Automatically (Hooks)

You don't need to run any commands for these — they fire on their own:

| When | Event | Handler | What Happens |
|------|-------|---------|-------------|
| Session start | `SessionStart` | `session-start.py` | Walks filesystem, Merkle-tree diffs changed files, tells Claude which files need reindexing. If >50 files changed, suggests full reindex. |
| After file edit | `PostToolUse` (Write/Edit/MultiEdit) | `post-tool-reindex.py` | Tells Claude to call `reindex_file` for the file that was just edited. Index stays current as you work. |
| Before Grep/Glob | `PreToolUse` (Grep/Glob) | `pre-tool-suggest.py` | Suggests using `/radar:search` as a more powerful alternative. Non-blocking — never prevents the tool call. |
| Session end | `Stop` | `session-stop.py` | Counts search invocations from transcript, extracts query list, appends to `data/search-log.jsonl`. Feeds future analytics. |

### The PostToolUse Loop

This is what makes codebase-radar *live*. Every time you edit a file:

```
You edit src/auth/login.py
      ↓
PostToolUse hook fires
      ↓
Hook emits: "src/auth/login.py was modified. Call reindex_file with path='src/auth/login.py'"
      ↓
Claude calls reindex_file MCP tool
      ↓
login.py is re-chunked, re-embedded, upserted into LanceDB
      ↓
Your next /radar:search sees the updated code
```

The index is never stale by more than one operation.

---

## The 2 Agents

### `radar-explorer` (Sonnet) — Deep Codebase Exploration

The primary exploration agent. Accepts natural language questions, runs semantic search, follows references, reads full files, and returns a structured explanation with file paths and line numbers.

```
User: "How does the payment processing flow work?"

radar-explorer:
  1. Calls search_code("payment processing flow", top_k=15)
  2. Reviews ranked chunks — identifies entry point, business logic, external API calls
  3. Reads full relevant files with Read tool
  4. Uses Grep to trace how functions are called across the codebase
  5. Returns:
     ## Summary
     Payment processing starts at src/payments/handler.py:42...

     ## Key Files
     - src/payments/handler.py (lines 42-98): Entry point, validates cart
     - src/payments/stripe.py (lines 15-67): Stripe API integration
     - src/payments/webhook.py (lines 89-134): Async confirmation handling

     ## How It Works
     ...
```

**Tools:** Read, Grep, Glob, Bash | **Max turns:** 30 | **Read-only** (never writes files)

### `radar-indexer` (Haiku) — Background Indexing Management

Lightweight agent that triggers `index_codebase`, polls `get_status` for progress, and reports completion stats. Runs in the background so large indexing jobs don't block your work.

```
radar-indexer (triggered by /radar:index):
  1. Calls index_codebase(path="/project", incremental=true)
  2. Polls get_status every ~10 seconds
  3. Reports: "Progress: 64% (541 files processed)"
  4. On complete: "Indexing complete. 847 files, 6,234 chunks, 38.4s"
```

**Tools:** Bash (diagnostics only) | **Max turns:** 15 | **Never modifies files**

---

## The 6 MCP Tools

These are called by agents and hooks via the MCP server. You can also call them directly.

| Tool | Purpose |
|------|---------|
| `index_codebase` | Build/refresh index. Params: `path`, `incremental` (default true), `force_full` |
| `search_code` | Hybrid search. Params: `query`, `project_root`, `top_k`, `path_filter`, `language` |
| `reindex_file` | Reindex a single file after edit. Params: `file_path` |
| `get_status` | Health check + stats for a project. Params: `project_root` |
| `clear_index` | Drop index for a project. Params: `project_root`, `confirm` (must be true) |
| `configure` | Read/update config. Params: `updates` (partial dict, deep-merged) |

---

## The 2 CLI Tools

Available in your terminal after `install.sh` runs:

```bash
# Show index status for current directory (or --path)
radar-status
radar-status --path /other/project
radar-status --json   # machine-readable output

# Reset (clear) the index for a project — interactive confirmation
radar-reset
radar-reset --path /other/project
```

---

## Supported Languages (AST Chunking)

tree-sitter is used for semantic chunking (function/class/method boundaries) for these 15 extensions:

| Extension | Language |
|-----------|---------|
| `.py` | Python |
| `.ts`, `.tsx` | TypeScript / TSX |
| `.js`, `.jsx` | JavaScript / JSX |
| `.java` | Java |
| `.cpp`, `.c`, `.h` | C / C++ |
| `.go` | Go |
| `.rs` | Rust |
| `.rb` | Ruby |
| `.swift` | Swift |
| `.kt` | Kotlin |
| `.scala` | Scala |

All other file types fall back to **character-based sliding window** (configurable chunk size + overlap).

---

## Embedding Providers

codebase-radar defaults to local HuggingFace embeddings. Upgrade to a cloud provider for higher-quality embeddings on specialized code:

| Provider | Model | Dims | Cost | Quality |
|---------|-------|------|------|---------|
| **HuggingFace** (default) | `all-MiniLM-L6-v2` | 384 | Free / local | Good |
| OpenAI | `text-embedding-3-small` | 1536 | ~$0.02/1M tokens | Better |
| VoyageAI | `voyage-code-3` | 1024 | ~$0.06/1M tokens | Best for code |

Switch providers via `/radar:config` → "Embedding model". **Switching invalidates the index — you must rebuild after switching.**

To use OpenAI or VoyageAI, set the key in your plugin userConfig or environment:

```json
// plugin userConfig
{
  "openai_api_key": "sk-...",
  "voyageai_api_key": "pa-..."
}
```

---

## Configuration Reference

Default config at `data/config.json`:

```json
{
  "embedding": {
    "provider": "huggingface",
    "model_id": "all-MiniLM-L6-v2",
    "dimensions": 384
  },
  "chunking": {
    "chunk_size_tokens": 256,
    "chunk_overlap_tokens": 32,
    "ast_enabled": true,
    "fallback": "character"
  },
  "search": {
    "top_k": 10,
    "hybrid_alpha": 0.7,
    "rerank": false
  },
  "exclusions": {
    "patterns": [
      "node_modules/**", ".git/**", "**/*.min.js",
      "**/*.lock", "dist/**", "build/**",
      "__pycache__/**", "*.pyc", "**/*.egg-info/**",
      ".venv/**", "venv/**"
    ]
  }
}
```

**`hybrid_alpha`** controls the BM25/vector balance:
- `1.0` — pure dense vector (semantic similarity only)
- `0.7` — 70% vector, 30% BM25 (default — best for mixed workloads)
- `0.0` — pure BM25 (keyword matching only, like grep)

---

## Data Files

| File | Format | What's In It | Auto-Trimmed |
|------|--------|-------------|-------------|
| `data/config.json` | JSON | Embedding, chunking, search, exclusion settings | No |
| `data/index-state.json` | JSON | Per-project file hashes + index stats (keyed by `sha256(root)[:12]`) | No |
| `data/search-log.jsonl` | JSONL | Per-session search queries and counts | Yes (500 max → keep 400) |

The LanceDB index itself lives at `$CLAUDE_PLUGIN_DATA/lancedb/`. Each project gets its own table named `radar_<sha256(root)[:12]>`.

---

## Troubleshooting

**"No results found" or all results have low scores (<0.4)**

- The project may not be indexed. Run `/radar` to check status, then `/radar:index`.
- Try rephrasing the query: concept searches work better as "X implementation" rather than "how does X work"
- Run `/radar:index` to ensure the index is fresh (older than 7 days → stale)

**"MCP server not responding"**

- The venv may not be set up. Run `bash scripts/install.sh` to rebuild it.
- Check that `.mcp.json` is present and the `command` path points to the venv python.
- Start a new Claude Code session to force MCP server reconnection.

**"Indexing fails with lancedb import error"**

```bash
# Manually install deps in the plugin venv
$CLAUDE_PLUGIN_DATA/venv/bin/pip install lancedb>=0.9.0 sentence-transformers>=3.0.0
```

**"First-time indexing is very slow"**

- `all-MiniLM-L6-v2` (~90MB) downloads on first run. This is a one-time cost.
- Large codebases (>10K files) can take 5-10 minutes on the first full index. Subsequent incremental indexes are seconds.

**"Changing embedding model broke the index"**

```bash
# Clear the old index and rebuild
/radar:config     # change provider/model
                  # WARNING is shown — acknowledge it
# Then:
/radar:index      # force_full=true via the config
```

**"Session-start hook is slow"**

- The hook is `async: true` — it runs in the background and doesn't block your session start.
- If it feels slow, increase the exclusion patterns in `/radar:config` to skip large directories (e.g., `vendor/**`, `*.generated.*`).

---

## Compatibility with Other PretInnov Plugins

| Combo | What You Get |
|-------|-------------|
| **codebase-radar alone** | Semantic search + auto-reindex. Works in any project, git or not. |
| **codebase-radar + Clamper** | radar-explorer surfaces relevant code by concept; Clamper maps project DNA via git history and fragile zones. Together: the deepest codebase understanding available. |
| **codebase-radar + Sentinel** | Sentinel's code review agents gain semantic context for finding related code patterns. `radar-explorer` pairs naturally with `sentinel-reviewer` for architectural review. |
| **codebase-radar + Cortex** | Cortex tracks decisions and learnings; codebase-radar makes the code itself searchable. Session intelligence meets semantic search. |

---

## License

MIT — By Siddharth Gupta | [PretInnov Technologies](https://github.com/PretInnov-Inc)
