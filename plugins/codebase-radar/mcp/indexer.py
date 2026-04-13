"""
codebase-radar indexer.py

Core indexing logic for building and maintaining the LanceDB semantic index.

LanceDB table schema:
  chunk_id:      str  (sha256(file_path + start_line))
  file_path:     str  (absolute)
  relative_path: str  (relative to project root)
  start_line:    int
  end_line:      int
  chunk_type:    str  (function|class|method|other)
  language:      str
  content:       str
  vector:        list[float]

Table name: sha256(project_root)[:12]
"""

import os
import sys
import json
import hashlib
import fnmatch
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa

from chunker import chunk_file
from embedder import embed_texts, get_dimensions, get_provider_info


def _load_config() -> dict:
    config_path = os.environ.get(
        "RADAR_CONFIG_PATH",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/config.json")
    )
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_state_path() -> str:
    return os.environ.get(
        "RADAR_STATE_PATH",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/index-state.json")
    )


def _get_lancedb_root() -> str:
    root = os.environ.get("RADAR_LANCEDB_ROOT", "")
    if not root:
        root = os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/lancedb")
    os.makedirs(root, exist_ok=True)
    return root


def _read_state() -> dict:
    state_path = _get_state_path()
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"version": "1.0.0", "projects": {}}


def _write_state(state: dict):
    state_path = _get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _project_hash(project_root: str) -> str:
    return hashlib.sha256(project_root.encode()).hexdigest()[:12]


def _table_name(project_root: str) -> str:
    return f"radar_{_project_hash(project_root)}"


def _file_hash(file_path: str) -> str:
    """SHA256 of first 8KB of file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            h.update(f.read(BINARY_SNIFF_BYTES))
        return h.hexdigest()
    except Exception:
        return ""


def _read_head_and_hash(abs_path: str):
    """
    One-pass read of the first 8 KB for both the hash and binary sniff.
    Returns (hash_hex, head_bytes, size) or (None, None, None) on error.
    """
    try:
        size = os.path.getsize(abs_path)
    except OSError:
        return None, None, None
    try:
        with open(abs_path, "rb") as f:
            head = f.read(BINARY_SNIFF_BYTES)
    except Exception:
        return None, None, None
    h = hashlib.sha256()
    h.update(head)
    return h.hexdigest(), head, size


def _chunk_id(file_path: str, start_line: int) -> str:
    return hashlib.sha256(f"{file_path}:{start_line}".encode()).hexdigest()[:16]


#
# Exclusion / file-filter machinery.
#
# Previous implementation used fnmatch with patterns like "node_modules/**".
# fnmatch does NOT support globstar — `**` is treated identically to `*` and
# matches anything except `/`. So "node_modules/**" only caught top-level
# node_modules/; nested occurrences (any/depth/node_modules/foo) were walked,
# explaining why a 2.4 GB tree of plugin sources produced 34k+ files to index.
#
# New algorithm is gitignore-style path-component matching:
#   * A bare name with no slash and no glob chars (e.g. "node_modules", ".git")
#     is a DIRECTORY NAME and matches any path component of that name anywhere.
#   * A pattern with a glob but no slash (e.g. "*.min.js", "*.png") is a
#     FILE-BASENAME GLOB and matches the leaf filename only.
#   * A pattern ending in "/**" or "/" is also treated as a directory name
#     (stripped of the suffix) for backward compat with the old config shape.
#   * Anything else is a FULL PATH GLOB against the relative path.

DEFAULT_EXCLUSION_PATTERNS = [
    # Dependency & package directories
    "node_modules", "bower_components", "jspm_packages", "vendor", "Pods",
    # VCS
    ".git", ".svn", ".hg", ".bzr",
    # Python caches & envs
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
    ".venv", "venv", "env", "virtualenv", ".eggs",
    # JS/TS build outputs & caches
    "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".astro",
    ".docusaurus", ".cache", ".parcel-cache", ".turbo", ".vite", ".yarn",
    # JVM / .NET / Rust / Go build outputs
    "target", "bin", "obj", ".gradle", ".m2",
    # Editor / IDE / AI tooling data dirs (NOT project source — huge caches)
    ".idea", ".vscode", ".vs", ".history",
    ".claude", ".cursor", ".aider", ".continue", ".zed", ".copilot",
    ".sourcegraph", ".codeium", ".tabnine",
    # Coverage / test output
    "coverage", ".nyc_output", "htmlcov", ".coverage",
    # Infra / IaC
    ".terraform", ".serverless",
    # Python site-packages anywhere in the tree (installed deps, type stubs)
    "site-packages", ".ipynb_checkpoints",
    # Vector DB / radar's own artifacts — never recursively index your index
    "lancedb", ".lancedb",
    # OS / misc
    ".DS_Store",

    # File basename patterns: minified, source maps, bundles
    "*.min.js", "*.min.css", "*.min.map",
    "*.map", "*.bundle.js", "*.chunk.js", "*.hot-update.js", "*.d.ts.map",
    # Lock files
    "*.lock", "*-lock.json", "*.lockb",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Cargo.lock", "Gemfile.lock", "composer.lock", "Pipfile.lock",
    # Compiled / binary artifacts
    "*.pyc", "*.pyo", "*.pyd",
    "*.class", "*.jar", "*.war", "*.ear",
    "*.so", "*.dylib", "*.dll", "*.exe",
    "*.o", "*.a", "*.obj", "*.lib",
    "*.wasm",
    # Images
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.tiff", "*.tif",
    "*.webp", "*.ico", "*.svg", "*.avif", "*.heic",
    # Video
    "*.mp4", "*.webm", "*.mov", "*.avi", "*.mkv", "*.flv", "*.m4v",
    # Audio
    "*.mp3", "*.wav", "*.ogg", "*.flac", "*.m4a", "*.aac",
    # Docs / archives
    "*.pdf", "*.doc", "*.docx", "*.ppt", "*.pptx", "*.xls", "*.xlsx",
    "*.zip", "*.tar", "*.tar.gz", "*.tgz", "*.gz", "*.bz2", "*.xz", "*.7z", "*.rar",
    # Packages / installers
    "*.whl", "*.nupkg", "*.deb", "*.rpm", "*.dmg", "*.pkg", "*.msi", "*.apk",
    # Fonts (incl. PDF.js binary font maps)
    "*.woff", "*.woff2", "*.ttf", "*.otf", "*.eot", "*.bcmap", "*.pfb", "*.pfm",
    # Serialized data / ML artifacts (not source)
    "*.parquet", "*.arrow", "*.feather", "*.avro", "*.orc",
    "*.pkl", "*.h5", "*.hdf5", "*.npy", "*.npz",
    "*.db", "*.sqlite", "*.sqlite3",
    "*.lance",
    # Logs / temp / editor backups
    "*.log", "*.pid", "*.swp", "*.swo", "*.bak", "*.tmp", "*~",
]

# File-level guards. Any of these will skip the file without reading its
# full contents — critical for avoiding OOM on huge generated blobs that
# slip past extension-based exclusions.
DEFAULT_MAX_FILE_SIZE_BYTES = 1_000_000
DEFAULT_MAX_LINE_COUNT = 10_000
BINARY_SNIFF_BYTES = 8192


# ────────── Inclusion allow-list (opt-out default behavior) ──────────
#
# Blacklists are a losing battle: new tools create new data directories and
# new binary formats faster than you can update exclusions. For code search,
# the only robust approach is an allow-list of source-code extensions — the
# same strategy used by ripgrep's --type, GitHub code search, Sourcegraph.
#
# A file is INCLUDED for indexing if ANY of:
#   * its extension is in DEFAULT_INCLUDE_EXTENSIONS, OR
#   * its basename is in DEFAULT_INCLUDE_FILENAMES (for extensionless build
#     files like Dockerfile, LICENSE, Makefile).
#
# Users can override via config.inclusions.{extensions, filenames}, or
# disable allow-list mode entirely via config.inclusions.enabled=false
# (falls back to pure exclusion-based filtering).

DEFAULT_INCLUDE_EXTENSIONS = {
    # Python
    ".py", ".pyi", ".pyx", ".pxd",
    # JavaScript / TypeScript
    ".js", ".jsx", ".mjs", ".cjs",
    ".ts", ".tsx", ".mts", ".cts",
    # Web frameworks
    ".vue", ".svelte", ".astro",
    # Web markup / styles
    ".html", ".htm", ".xhtml",
    ".css", ".scss", ".sass", ".less", ".styl",
    # JVM
    ".java", ".kt", ".kts", ".scala", ".sc", ".groovy", ".gradle",
    ".clj", ".cljs", ".cljc", ".edn",
    # Systems
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hxx", ".hh",
    ".m", ".mm",
    ".go", ".rs", ".zig", ".d", ".nim", ".v", ".cr", ".odin",
    # Shell
    ".sh", ".bash", ".zsh", ".fish", ".ksh",
    ".ps1", ".psm1", ".psd1",
    ".bat", ".cmd",
    # Scripting / interpreted
    ".rb", ".php", ".pl", ".pm", ".tcl", ".lua",
    ".r", ".jl",
    # Functional
    ".ex", ".exs", ".erl", ".hrl",
    ".fs", ".fsi", ".fsx",
    ".ml", ".mli", ".hs", ".lhs",
    ".elm", ".purs",
    # Mobile / Apple
    ".swift", ".dart",
    # .NET
    ".cs", ".vb",
    # Data / queries / schemas
    ".sql", ".graphql", ".gql",
    ".proto", ".thrift", ".avsc",
    # Config / data formats — commonly source
    ".yaml", ".yml", ".toml",
    ".json", ".json5", ".jsonc",
    ".xml", ".xsd", ".wsdl", ".plist",
    ".ini", ".cfg", ".conf", ".config", ".properties",
    # Infrastructure as code
    ".tf", ".tfvars", ".hcl", ".nomad", ".nix",
    ".dockerfile", ".containerfile",
    # Build files
    ".mk", ".cmake", ".bazel", ".bzl", ".buck",
    # Go modules
    ".mod", ".sum",
    # Docs
    ".md", ".mdx", ".markdown", ".rst",
    ".adoc", ".asciidoc", ".org",
    ".txt", ".text",
    # Notebooks (JSON-backed, still text-searchable)
    ".ipynb",
    # Plugin/Claude-specific authoring formats
    ".mdc",
}

DEFAULT_INCLUDE_FILENAMES = {
    # Build files with no extension
    "Dockerfile", "Containerfile",
    "Makefile", "GNUmakefile", "makefile",
    "Gemfile", "Rakefile", "Podfile", "Fastfile", "Appfile", "Matchfile",
    "Vagrantfile", "Berksfile", "Thorfile",
    "Jenkinsfile", "Brewfile",
    "BUILD", "WORKSPACE", "MODULE.bazel", "BUILD.bazel",
    "CMakeLists.txt",
    # Licenses & docs (commonly no extension)
    "LICENSE", "LICENCE", "COPYING", "COPYRIGHT", "NOTICE",
    "AUTHORS", "CONTRIBUTORS", "MAINTAINERS",
    "OWNERS", "CODEOWNERS",
    "README", "CHANGELOG", "CHANGES", "HISTORY", "TODO", "ROADMAP",
    "VERSION",
    # Dotfiles that are source config
    ".gitignore", ".gitattributes", ".gitmodules", ".mailmap",
    ".dockerignore", ".npmignore", ".eslintignore", ".prettierignore",
    ".editorconfig",
    ".prettierrc", ".eslintrc", ".babelrc", ".stylelintrc",
    ".env.example", ".env.template", ".env.sample", ".env.dist",
}


def _is_included(rel_path: str, extensions: set, filenames: set) -> bool:
    """
    Allow-list check. Returns True if rel_path should be indexed.
    Only called when inclusions.enabled is True (default).
    """
    basename = os.path.basename(rel_path)
    if basename in filenames:
        return True
    ext = os.path.splitext(basename)[1].lower()
    if ext and ext in extensions:
        return True
    return False


def _git_tracked_files(project_root: str):
    """
    Return relative paths of every file that git considers part of the
    project tree starting at project_root, recursing into nested git
    repositories. Returns None if project_root is not in a git repo or
    git is unavailable.

    Why recurse? `git ls-files` treats nested repositories (directories
    containing their own .git/) as opaque — it lists them as "dirname/"
    with a trailing slash and does NOT descend. That's correct for the
    outer repo's perspective, but useless for a code-search indexer: the
    user wants the ACTUAL files, not a placeholder. So for every such
    nested-repo marker we encountered, we run `git ls-files` at that
    location with the same --exclude-standard flag and merge results.
    This preserves gitignore semantics independently in each repo,
    matching what a developer expects.

    Delegating to git means every .gitignore (nested, global, info/exclude),
    along with negation rules and anchoring, is honored correctly without
    us reimplementing the 20+ years of gitignore edge cases.
    """
    import subprocess
    project_root_abs = os.path.abspath(project_root)
    results: set = set()
    visited: set = set()

    def scan(scan_root: str) -> bool:
        if scan_root in visited:
            return True
        visited.add(scan_root)
        try:
            probe = subprocess.run(
                ["git", "-C", scan_root, "rev-parse", "--show-toplevel"],
                capture_output=True, timeout=5,
            )
            if probe.returncode != 0:
                return False
            res = subprocess.run(
                ["git", "-C", scan_root, "ls-files",
                 "--cached", "--others", "--exclude-standard", "-z"],
                capture_output=True, timeout=120,
            )
            if res.returncode != 0:
                return False
        except Exception:
            return False

        for raw in res.stdout.split(b"\x00"):
            if not raw:
                continue
            try:
                entry = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            abs_p = os.path.normpath(os.path.join(scan_root, entry))
            # Keep only entries under project_root.
            if abs_p != project_root_abs and not abs_p.startswith(project_root_abs + os.sep):
                continue
            # Nested-repo marker (trailing slash) or any directory-like
            # entry that's actually a directory → recurse.
            if entry.endswith("/") or os.path.isdir(abs_p):
                if os.path.isdir(abs_p):
                    scan(abs_p)
                continue
            if os.path.isfile(abs_p):
                rel = os.path.relpath(abs_p, project_root_abs)
                results.add(rel)
        return True

    if not scan(project_root_abs):
        return None
    return results or None


def _compile_exclusions(patterns: list):
    """Classify patterns into (dir_names, file_globs, path_globs)."""
    dir_names: set = set()
    file_globs: list = []
    path_globs: list = []
    for raw in patterns or []:
        pat = (raw or "").strip()
        if not pat:
            continue
        # Back-compat: "foo/**", "foo/", "foo/**/*" → directory name "foo"
        stripped = pat
        for suffix in ("/**/*", "/**", "/"):
            if stripped.endswith(suffix):
                stripped = stripped[: -len(suffix)]
                break
        # Bare name with no glob chars → dir-name match anywhere
        if stripped and "/" not in stripped and "*" not in stripped and "?" not in stripped:
            dir_names.add(stripped)
            continue
        # "**/*.ext" → treat tail as basename glob
        if pat.startswith("**/"):
            rest = pat[3:]
            if "/" not in rest:
                file_globs.append(rest)
                continue
        # No slash + has glob → basename glob
        if "/" not in pat:
            file_globs.append(pat)
            continue
        path_globs.append(pat)
    return dir_names, file_globs, path_globs


def _matches_exclusion(rel_path: str, compiled) -> bool:
    """Return True if rel_path is excluded by the compiled triple."""
    dir_names, file_globs, path_globs = compiled
    rp = rel_path.replace("\\", "/")
    parts = rp.split("/")
    for part in parts:
        if part in dir_names:
            return True
    basename = parts[-1] if parts else rp
    for pat in file_globs:
        if fnmatch.fnmatch(basename, pat):
            return True
    for pat in path_globs:
        if fnmatch.fnmatch(rp, pat):
            return True
    return False


def _file_filter_reason(abs_path: str, size: int, head_bytes: bytes,
                        max_size: int, max_lines: int):
    """
    Returns a short reason string if this file should be skipped at the
    file level (not path-pattern level), or None to proceed.

    Callers pass `size` and `head_bytes` already-read (during file hashing)
    to avoid reopening the file twice.
    """
    if size > max_size:
        return f"size>{max_size}B"
    if b"\x00" in head_bytes:
        return "binary"
    if size > 200_000:
        try:
            with open(abs_path, "rb") as f:
                n = 0
                for _ in f:
                    n += 1
                    if n > max_lines:
                        return f"lines>{max_lines}"
        except Exception:
            return "unreadable"
    return None


def _open_or_create_table(db: lancedb.LanceDBConnection, table_name: str) -> lancedb.table.Table:
    """Open existing table or create with correct schema."""
    dims = get_dimensions()
    schema = pa.schema([
        pa.field("chunk_id", pa.string()),
        pa.field("file_path", pa.string()),
        pa.field("relative_path", pa.string()),
        pa.field("start_line", pa.int32()),
        pa.field("end_line", pa.int32()),
        pa.field("chunk_type", pa.string()),
        pa.field("language", pa.string()),
        pa.field("content", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), dims)),
    ])

    existing = db.table_names()
    if table_name in existing:
        return db.open_table(table_name)
    else:
        return db.create_table(table_name, schema=schema)


def _upsert_chunks(table: lancedb.table.Table, chunks_data: list[dict]):
    """Upsert a list of chunk records into the LanceDB table."""
    if not chunks_data:
        return

    # Delete existing chunks for each file_path being upserted
    file_paths = list(set(c["file_path"] for c in chunks_data))
    for fp in file_paths:
        try:
            # Escape single quotes in path
            safe_fp = fp.replace("'", "\\'")
            table.delete(f"file_path = '{safe_fp}'")
        except Exception:
            pass

    # Add new chunks
    table.add(chunks_data)


def _build_fts_index(table: lancedb.table.Table):
    """Create or replace full-text search index on content field."""
    try:
        table.create_fts_index("content", replace=True)
    except Exception:
        pass  # FTS index is optional — hybrid search degrades to vector-only


def _merge_project_state(ph: str, project_root: str, updates: dict):
    """
    Read-modify-write a single project's entry in index-state.json.

    Other fields (file_hashes, last_indexed, etc.) on the project entry are
    preserved. Used for progress updates so that concurrent `get_status` reads
    see intermediate state.
    """
    state = _read_state()
    entry = state.setdefault("projects", {}).setdefault(ph, {})
    entry["project_root"] = project_root
    for k, v in updates.items():
        entry[k] = v
    _write_state(state)


def index_codebase(path: str, incremental: bool = True, force_full: bool = False,
                   job_id: Optional[str] = None) -> dict:
    """
    Build or refresh the semantic search index for a project directory.

    Args:
        path: Absolute path to project root.
        incremental: If True, only process changed/new files.
        force_full: If True, clear all existing data and reindex from scratch.
        job_id: Optional job id recorded in state so callers can correlate.

    Writes progress to index-state.json as it runs so `get_status` can report
    files_processed / files_total while indexing is in flight.

    Returns:
        Stats dict with files_indexed, chunks_total, duration_seconds, etc.
    """
    start_time = time.time()
    project_root = os.path.abspath(path)
    ph = _project_hash(project_root)

    # Mark job as started immediately so get_status reflects reality even if
    # the caller (or a crash) never sees the return value.
    _merge_project_state(ph, project_root, {
        "status": "indexing",
        "progress": {"files_processed": 0, "files_total": 0, "chunks_processed": 0, "current_file": None},
        "job": {
            "job_id": job_id,
            "pid": os.getpid(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "incremental": incremental,
            "force_full": force_full,
        },
        "error": None,
    })

    try:
        return _index_codebase_impl(
            project_root, ph, incremental, force_full, start_time
        )
    except Exception as e:
        import traceback as _tb
        _merge_project_state(ph, project_root, {
            "status": "error",
            "error": f"{type(e).__name__}: {e}",
            "error_traceback": _tb.format_exc(),
        })
        raise


def _index_codebase_impl(project_root: str, ph: str, incremental: bool,
                         force_full: bool, start_time: float) -> dict:
    config = _load_config()
    exclusion_patterns = (
        config.get("exclusions", {}).get("patterns")
        or DEFAULT_EXCLUSION_PATTERNS
    )
    compiled_exclusions = _compile_exclusions(exclusion_patterns)

    # File-level guards (configurable, with safe defaults)
    file_limits = config.get("file_limits", {}) or {}
    max_size = int(file_limits.get("max_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES))
    max_lines = int(file_limits.get("max_line_count", DEFAULT_MAX_LINE_COUNT))

    # Allow-list (inclusion) rules. Enabled by default — see commentary on
    # DEFAULT_INCLUDE_EXTENSIONS for rationale. Users can pass extra
    # extensions/filenames (merged with defaults) or disable via enabled=false.
    inclusions_cfg = config.get("inclusions", {}) or {}
    inclusion_enabled = inclusions_cfg.get("enabled", True)
    user_exts = inclusions_cfg.get("extensions") or []
    user_names = inclusions_cfg.get("filenames") or []
    include_extensions = DEFAULT_INCLUDE_EXTENSIONS | {
        (e if e.startswith(".") else "." + e).lower() for e in user_exts
    }
    include_filenames = DEFAULT_INCLUDE_FILENAMES | set(user_names)

    state = _read_state()
    project_entry = state.get("projects", {}).get(ph, {})
    stored_hashes = project_entry.get("file_hashes", {})

    # Connect to LanceDB
    db = lancedb.connect(_get_lancedb_root())
    table_name = _table_name(project_root)

    if force_full:
        # Drop and recreate table
        try:
            db.drop_table(table_name)
        except Exception:
            pass
        stored_hashes = {}

    table = _open_or_create_table(db, table_name)

    # Build initial file candidate list.
    #
    # PRIMARY: `git ls-files` if project_root is inside a git repo — this
    # delegates ALL gitignore interpretation (nested .gitignore, global
    # gitignore, .git/info/exclude, negation rules) to git itself, which is
    # the only correct implementation of gitignore semantics that exists.
    #
    # FALLBACK: os.walk with our bare-name dir pruning, for non-git trees.
    files_to_process = []       # (abs_path, rel_path, current_hash)
    all_rel_paths = set()
    skipped_stats = {"excluded_dir": 0, "excluded_file": 0, "not_included": 0,
                     "too_large": 0, "binary": 0, "too_many_lines": 0,
                     "unreadable": 0}

    use_git = bool(config.get("use_git", True))
    git_files = _git_tracked_files(project_root) if use_git else None
    index_source = "git_ls_files" if git_files is not None else "filesystem_walk"

    def _process_candidate(abs_path, rel_path):
        """Apply per-file filters and decide whether to queue for indexing."""
        if _matches_exclusion(rel_path, compiled_exclusions):
            skipped_stats["excluded_file"] += 1
            return
        if inclusion_enabled and not _is_included(
            rel_path, include_extensions, include_filenames
        ):
            skipped_stats["not_included"] += 1
            return
        current_hash, head, size = _read_head_and_hash(abs_path)
        if current_hash is None:
            skipped_stats["unreadable"] += 1
            return
        reason = _file_filter_reason(abs_path, size, head, max_size, max_lines)
        if reason:
            if reason.startswith("size>"):
                skipped_stats["too_large"] += 1
            elif reason == "binary":
                skipped_stats["binary"] += 1
            elif reason.startswith("lines>"):
                skipped_stats["too_many_lines"] += 1
            else:
                skipped_stats["unreadable"] += 1
            return
        all_rel_paths.add(rel_path)
        if not incremental or force_full:
            files_to_process.append((abs_path, rel_path, current_hash))
        elif rel_path not in stored_hashes or stored_hashes[rel_path] != current_hash:
            files_to_process.append((abs_path, rel_path, current_hash))

    if git_files is not None:
        # Sorted for deterministic indexing order (nicer progress output).
        for rel_path in sorted(git_files):
            abs_path = os.path.join(project_root, rel_path)
            if not os.path.isfile(abs_path):
                continue
            _process_candidate(abs_path, rel_path)
    else:
        for root, dirs, files in os.walk(project_root):
            # Prune excluded dirs in-place; `d in dir_names` is O(1) set lookup.
            pruned = []
            for d in dirs:
                if d in compiled_exclusions[0]:
                    skipped_stats["excluded_dir"] += 1
                    continue
                d_rel = os.path.relpath(os.path.join(root, d), project_root)
                if _matches_exclusion(d_rel, compiled_exclusions):
                    skipped_stats["excluded_dir"] += 1
                    continue
                pruned.append(d)
            dirs[:] = pruned

            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, project_root)
                _process_candidate(abs_path, rel_path)

    # Process files: chunk, embed, upsert — STREAMING per-file.
    #
    # The previous implementation accumulated every chunk for every file into a
    # single `pending_chunks` list before embedding. On a 12k-file / 100k-chunk
    # tree that materialized hundreds of MB of text on top of the ~600 MB torch
    # + MiniLM resident set and macOS Jetsam SIGKILL'd the process (exit 137).
    #
    # New shape: for each file, embed and upsert its chunks immediately in
    # sub-batches of `batch_size`. Memory is bounded to one file's chunks plus
    # the model. Hashes and per-file progress are persisted along the way so a
    # killed run can resume on the next incremental call.
    new_hashes = dict(stored_hashes)
    files_indexed = 0
    chunks_total = 0
    batch_size = 32

    # I/O throttling: many small disk writes hurt on long runs. Persist
    # progress every PROGRESS_EVERY files; persist file_hashes (the resume
    # checkpoint, which can be MB-sized) less often.
    PROGRESS_EVERY = 10
    HASH_PERSIST_EVERY = 100

    # Report total up-front so `get_status` can show denominator while we work.
    _merge_project_state(ph, project_root, {
        "progress": {
            "files_processed": 0,
            "files_total": len(files_to_process),
            "chunks_processed": 0,
            "current_file": None,
        }
    })

    for file_idx, (abs_path, rel_path, file_hash) in enumerate(files_to_process, start=1):
        chunks = chunk_file(abs_path)
        if not chunks:
            new_hashes[rel_path] = file_hash
            files_indexed += 1
            continue

        # Embed this file's chunks in sub-batches of batch_size so giant
        # generated files (e.g. minified bundles that slipped past exclusions)
        # still don't blow memory.
        file_records = []
        for i in range(0, len(chunks), batch_size):
            sub = chunks[i:i + batch_size]
            try:
                vectors = embed_texts([c["text"] for c in sub])
            except Exception as e:
                # Skip individual file on embedding failure — don't kill the
                # whole indexing run for one bad file.
                _merge_project_state(ph, project_root, {
                    "progress": {
                        "files_processed": files_indexed,
                        "files_total": len(files_to_process),
                        "chunks_processed": chunks_total,
                        "current_file": rel_path,
                        "last_error": f"Skipped {rel_path}: {type(e).__name__}: {e}",
                    }
                })
                file_records = []
                break

            for chunk, vec in zip(sub, vectors):
                file_records.append({
                    "chunk_id": _chunk_id(abs_path, chunk["start_line"]),
                    "file_path": abs_path,
                    "relative_path": rel_path,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "chunk_type": chunk["chunk_type"],
                    "language": chunk["language"],
                    "content": chunk["text"],
                    "vector": [float(v) for v in vec],
                })

        if file_records:
            _upsert_chunks(table, file_records)
            chunks_total += len(file_records)

        new_hashes[rel_path] = file_hash
        files_indexed += 1

        # Throttled progress write — every PROGRESS_EVERY files.
        if files_indexed % PROGRESS_EVERY == 0 or file_idx == len(files_to_process):
            update = {
                "progress": {
                    "files_processed": files_indexed,
                    "files_total": len(files_to_process),
                    "chunks_processed": chunks_total,
                    "current_file": rel_path,
                }
            }
            # Less-frequent: also persist file_hashes so a SIGKILL can resume.
            if files_indexed % HASH_PERSIST_EVERY == 0:
                update["file_hashes"] = new_hashes
                update["files_indexed"] = files_indexed
                update["chunks_total"] = chunks_total
            _merge_project_state(ph, project_root, update)

    # Build FTS index after bulk upsert
    if files_to_process:
        _build_fts_index(table)

    # Count total chunks in table
    try:
        total_chunks_in_table = table.count_rows()
    except Exception:
        total_chunks_in_table = chunks_total

    duration = time.time() - start_time
    now = datetime.now(timezone.utc).isoformat()
    provider_info = get_provider_info()

    # Update state (preserve project_root, clear transient job info)
    state = _read_state()  # re-read in case progress writes raced with us
    state.setdefault("projects", {})[ph] = {
        "project_root": project_root,
        "last_indexed": now,
        "files_indexed": len(new_hashes),
        "chunks_total": total_chunks_in_table,
        "file_hashes": new_hashes,
        "embedding_model": provider_info["model_id"],
        "embedding_provider": provider_info["provider"],
        "dimensions": provider_info["dimensions"],
        "table_name": table_name,
        "status": "complete",
        "progress": {
            "files_processed": len(new_hashes),
            "files_total": len(new_hashes),
            "chunks_processed": total_chunks_in_table,
            "current_file": None,
        },
        "job": None,
        "error": None,
        "skipped": skipped_stats,
        "index_source": index_source,
    }
    _write_state(state)

    return {
        "status": "complete",
        "project_root": project_root,
        "files_processed": files_indexed,
        "files_total": len(new_hashes),
        "chunks_added": chunks_total,
        "chunks_total": total_chunks_in_table,
        "duration_seconds": round(duration, 2),
        "embedding_model": provider_info["model_id"],
        "last_indexed": now,
        "skipped": skipped_stats,
        "index_source": index_source,
    }


def reindex_file(file_path: str) -> dict:
    """
    Update the semantic index for a single modified file.

    Removes old chunks, re-chunks, re-embeds, and re-inserts.
    """
    abs_path = os.path.abspath(file_path)

    # Find which project this file belongs to
    state = _read_state()
    project_root = None
    project_hash = None

    for ph, entry in state.get("projects", {}).items():
        pr = entry.get("project_root", "")
        if abs_path.startswith(pr + os.sep) or abs_path.startswith(pr + "/"):
            project_root = pr
            project_hash = ph
            break

    if not project_root:
        # Try using cwd as project root
        project_root = os.getcwd()
        project_hash = _project_hash(project_root)

    # File-level guards: a post-edit monster file shouldn't be re-embedded.
    # Also enforce inclusion allow-list — a rename to an excluded extension
    # should drop the file from the index rather than re-embed it.
    config = _load_config()
    file_limits = config.get("file_limits", {}) or {}
    max_size = int(file_limits.get("max_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES))
    max_lines = int(file_limits.get("max_line_count", DEFAULT_MAX_LINE_COUNT))
    inclusions_cfg = config.get("inclusions", {}) or {}
    inclusion_enabled = inclusions_cfg.get("enabled", True)
    if inclusion_enabled:
        user_exts = inclusions_cfg.get("extensions") or []
        user_names = inclusions_cfg.get("filenames") or []
        include_extensions = DEFAULT_INCLUDE_EXTENSIONS | {
            (e if e.startswith(".") else "." + e).lower() for e in user_exts
        }
        include_filenames = DEFAULT_INCLUDE_FILENAMES | set(user_names)
        rel_check = os.path.relpath(abs_path, project_root)
        if not _is_included(rel_check, include_extensions, include_filenames):
            db = lancedb.connect(_get_lancedb_root())
            table = _open_or_create_table(db, _table_name(project_root))
            try:
                safe_fp = abs_path.replace("'", "\\'")
                table.delete(f"file_path = '{safe_fp}'")
            except Exception:
                pass
            _update_file_state(state, project_hash, project_root, rel_check, "")
            _write_state(state)
            return {"status": "skipped", "file": abs_path, "reason": "not_in_allow_list"}
    _, head, size = _read_head_and_hash(abs_path)
    if head is not None:
        skip_reason = _file_filter_reason(abs_path, size, head, max_size, max_lines)
        if skip_reason:
            # Treat as "file deleted from index scope": drop its chunks, clear
            # its state entry, and return the reason so callers know why.
            db = lancedb.connect(_get_lancedb_root())
            table = _open_or_create_table(db, _table_name(project_root))
            try:
                safe_fp = abs_path.replace("'", "\\'")
                table.delete(f"file_path = '{safe_fp}'")
            except Exception:
                pass
            _update_file_state(state, project_hash, project_root,
                               os.path.relpath(abs_path, project_root), "")
            _write_state(state)
            return {"status": "skipped", "file": abs_path, "reason": skip_reason}

    db = lancedb.connect(_get_lancedb_root())
    table_name = _table_name(project_root)

    # Open table or create if missing
    table = _open_or_create_table(db, table_name)

    # Delete old chunks for this file
    try:
        safe_fp = abs_path.replace("'", "\\'")
        table.delete(f"file_path = '{safe_fp}'")
    except Exception:
        pass

    # Re-chunk
    chunks = chunk_file(abs_path)
    if not chunks:
        # File may have been deleted or is empty — just clean up state
        _update_file_state(state, project_hash, project_root,
                           os.path.relpath(abs_path, project_root), "")
        _write_state(state)
        return {"status": "complete", "file": abs_path, "chunks_added": 0}

    # Embed in sub-batches (same streaming shape as the main indexer) to
    # cap memory in case of a huge edited file.
    rel_path = os.path.relpath(abs_path, project_root)
    batch_size = 32
    records = []
    for i in range(0, len(chunks), batch_size):
        sub = chunks[i:i + batch_size]
        vectors = embed_texts([c["text"] for c in sub])
        for chunk, vec in zip(sub, vectors):
            cid = _chunk_id(abs_path, chunk["start_line"])
            records.append({
            "chunk_id": cid,
            "file_path": abs_path,
            "relative_path": rel_path,
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "chunk_type": chunk["chunk_type"],
            "language": chunk["language"],
            "content": chunk["text"],
            "vector": [float(v) for v in vec]
        })

    table.add(records)
    _build_fts_index(table)

    # Update state hash
    new_hash = _file_hash(abs_path)
    _update_file_state(state, project_hash, project_root, rel_path, new_hash)

    try:
        total = table.count_rows()
    except Exception:
        total = len(records)

    state["projects"][project_hash]["chunks_total"] = total
    _write_state(state)

    return {
        "status": "complete",
        "file": abs_path,
        "chunks_added": len(records),
        "chunks_total": total
    }


def _update_file_state(state: dict, project_hash: str, project_root: str,
                       rel_path: str, file_hash: str):
    """Update a single file's hash in project state."""
    if project_hash not in state.get("projects", {}):
        state.setdefault("projects", {})[project_hash] = {
            "project_root": project_root,
            "file_hashes": {}
        }
    if file_hash:
        state["projects"][project_hash].setdefault("file_hashes", {})[rel_path] = file_hash
    else:
        state["projects"][project_hash].get("file_hashes", {}).pop(rel_path, None)

    state["projects"][project_hash]["last_indexed"] = datetime.now(timezone.utc).isoformat()
