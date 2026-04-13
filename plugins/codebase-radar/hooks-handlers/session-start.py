#!/usr/bin/env python3
"""
SessionStart hook handler for codebase-radar.
STDLIB ONLY — no external dependencies.

Reads index-state.json, computes diff vs current filesystem,
and emits instructions for Claude to call MCP index/reindex tools.
"""

import json
import os
import sys
import hashlib
import fnmatch
from pathlib import Path
from datetime import datetime, timezone


def compute_file_hash(file_path: str) -> str:
    """Compute sha256 of first 8KB of a file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            h.update(f.read(8192))
        return h.hexdigest()
    except (OSError, IOError):
        return ""


# ─── gitignore-style exclusion matcher (mirrors mcp/indexer.py) ───
#
# MUST stay behavior-compatible with indexer._matches_exclusion or the
# hook's filesystem diff will count different files than the indexer does.
def compile_exclusions(patterns):
    """Classify patterns into (dir_names, file_globs, path_globs)."""
    dir_names = set()
    file_globs = []
    path_globs = []
    for raw in patterns or []:
        pat = (raw or "").strip()
        if not pat:
            continue
        stripped = pat
        for suffix in ("/**/*", "/**", "/"):
            if stripped.endswith(suffix):
                stripped = stripped[: -len(suffix)]
                break
        if stripped and "/" not in stripped and "*" not in stripped and "?" not in stripped:
            dir_names.add(stripped)
            continue
        if pat.startswith("**/"):
            rest = pat[3:]
            if "/" not in rest:
                file_globs.append(rest)
                continue
        if "/" not in pat:
            file_globs.append(pat)
            continue
        path_globs.append(pat)
    return dir_names, file_globs, path_globs


def matches_exclusion(rel_path, compiled):
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


# Allow-list defaults — MUST stay in sync with mcp/indexer.py
# DEFAULT_INCLUDE_EXTENSIONS / DEFAULT_INCLUDE_FILENAMES.
DEFAULT_INCLUDE_EXTENSIONS = {
    ".py", ".pyi", ".pyx", ".pxd",
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts",
    ".vue", ".svelte", ".astro",
    ".html", ".htm", ".xhtml",
    ".css", ".scss", ".sass", ".less", ".styl",
    ".java", ".kt", ".kts", ".scala", ".sc", ".groovy", ".gradle",
    ".clj", ".cljs", ".cljc", ".edn",
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hxx", ".hh",
    ".m", ".mm",
    ".go", ".rs", ".zig", ".d", ".nim", ".v", ".cr", ".odin",
    ".sh", ".bash", ".zsh", ".fish", ".ksh",
    ".ps1", ".psm1", ".psd1", ".bat", ".cmd",
    ".rb", ".php", ".pl", ".pm", ".tcl", ".lua", ".r", ".jl",
    ".ex", ".exs", ".erl", ".hrl",
    ".fs", ".fsi", ".fsx",
    ".ml", ".mli", ".hs", ".lhs", ".elm", ".purs",
    ".swift", ".dart", ".cs", ".vb",
    ".sql", ".graphql", ".gql", ".proto", ".thrift", ".avsc",
    ".yaml", ".yml", ".toml",
    ".json", ".json5", ".jsonc",
    ".xml", ".xsd", ".wsdl", ".plist",
    ".ini", ".cfg", ".conf", ".config", ".properties",
    ".tf", ".tfvars", ".hcl", ".nomad", ".nix",
    ".dockerfile", ".containerfile",
    ".mk", ".cmake", ".bazel", ".bzl", ".buck",
    ".mod", ".sum",
    ".md", ".mdx", ".markdown", ".rst", ".adoc", ".asciidoc", ".org",
    ".txt", ".text",
    ".ipynb", ".mdc",
}

DEFAULT_INCLUDE_FILENAMES = {
    "Dockerfile", "Containerfile",
    "Makefile", "GNUmakefile", "makefile",
    "Gemfile", "Rakefile", "Podfile", "Fastfile", "Appfile", "Matchfile",
    "Vagrantfile", "Berksfile", "Thorfile",
    "Jenkinsfile", "Brewfile",
    "BUILD", "WORKSPACE", "MODULE.bazel", "BUILD.bazel",
    "CMakeLists.txt",
    "LICENSE", "LICENCE", "COPYING", "COPYRIGHT", "NOTICE",
    "AUTHORS", "CONTRIBUTORS", "MAINTAINERS",
    "OWNERS", "CODEOWNERS",
    "README", "CHANGELOG", "CHANGES", "HISTORY", "TODO", "ROADMAP",
    "VERSION",
    ".gitignore", ".gitattributes", ".gitmodules", ".mailmap",
    ".dockerignore", ".npmignore", ".eslintignore", ".prettierignore",
    ".editorconfig",
    ".prettierrc", ".eslintrc", ".babelrc", ".stylelintrc",
    ".env.example", ".env.template", ".env.sample", ".env.dist",
}


def is_included(rel_path, extensions, filenames):
    """Return True if rel_path is on the allow-list."""
    basename = os.path.basename(rel_path)
    if basename in filenames:
        return True
    ext = os.path.splitext(basename)[1].lower()
    if ext and ext in extensions:
        return True
    return False


def git_tracked_files(project_root):
    """
    Return relative paths of every file git considers part of project_root,
    recursing into nested git repositories. Mirrors mcp/indexer.py
    _git_tracked_files. None if project_root isn't in a git repo.
    """
    import subprocess
    project_root_abs = os.path.abspath(project_root)
    results = set()
    visited = set()

    def scan(scan_root):
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
                capture_output=True, timeout=60,
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
            if abs_p != project_root_abs and not abs_p.startswith(project_root_abs + os.sep):
                continue
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


def bootstrap_venv_if_missing(plugin_data: str, plugin_root: str) -> dict | None:
    """
    If the MCP venv is missing, kick off install.sh in the background.
    Returns a hook output dict if bootstrap was triggered, else None.
    The MCP server cannot start without the venv, so this is the difference
    between a working plugin and a broken one for first-time users.
    """
    import subprocess
    venv_python = os.path.join(plugin_data, "venv", "bin", "python3")
    if os.path.exists(venv_python):
        return None

    install_script = os.path.join(plugin_root, "scripts", "install.sh")
    if not os.path.exists(install_script):
        return None

    log_path = os.path.join(plugin_data, "install.log")
    os.makedirs(plugin_data, exist_ok=True)
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = plugin_root
    env["CLAUDE_PLUGIN_DATA"] = plugin_data
    try:
        with open(log_path, "ab") as logf:
            subprocess.Popen(
                ["bash", install_script],
                stdout=logf, stderr=logf,
                env=env, start_new_session=True,
            )
    except Exception:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "[codebase-radar] First-run: MCP server venv is missing. "
                "Auto-installing dependencies in the background (lancedb, sentence-transformers, "
                "tree-sitter — takes 2-5 minutes). The MCP search tools will be unavailable "
                "this session but will work in the next session. "
                f"Install log: {log_path}"
            )
        }
    }


def main():
    plugin_data = os.environ.get(
        "CLAUDE_PLUGIN_DATA",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar")
    )
    plugin_root = os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        str(Path(__file__).parent.parent)
    )

    # First-run bootstrap: install MCP venv if missing, then exit early
    bootstrap = bootstrap_venv_if_missing(plugin_data, plugin_root)
    if bootstrap is not None:
        print(json.dumps(bootstrap))
        return

    # Read stdin for session info
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
    cwd = os.getcwd()

    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            session_id = data.get("session_id", session_id)
            cwd = data.get("cwd", cwd)
    except Exception:
        pass

    # Compute project hash from cwd
    project_hash = hashlib.sha256(cwd.encode()).hexdigest()[:12]

    # Read index-state.json
    state_path = os.path.join(plugin_data, "index-state.json")
    state = {"version": "1.0.0", "projects": {}}
    try:
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                state = json.load(f)
    except Exception:
        pass

    projects = state.get("projects", {})
    project_entry = projects.get(project_hash)

    # Read config for exclusion patterns. Fall back to a comprehensive
    # default list (kept in sync with mcp/indexer.py DEFAULT_EXCLUSION_PATTERNS)
    # so hook-side filesystem counts match the indexer's effective scope.
    config_path = os.path.join(plugin_data, "config.json")
    exclusion_patterns = [
        # Dependency / vcs / caches / build outputs (bare names → any depth)
        "node_modules", "bower_components", "vendor", "Pods",
        ".git", ".svn", ".hg",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
        ".venv", "venv", "env", ".eggs",
        "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".astro",
        ".cache", ".parcel-cache", ".turbo", ".vite", ".yarn",
        "target", "bin", "obj", ".gradle",
        ".idea", ".vscode", ".vs",
        ".claude", ".cursor", ".aider", ".continue", ".zed", ".copilot",
        ".sourcegraph", ".codeium", ".tabnine",
        "site-packages", ".ipynb_checkpoints",
        "coverage", ".nyc_output", "htmlcov",
        "lancedb", ".lancedb",
        # File globs
        "*.min.js", "*.min.css", "*.map", "*.bundle.js", "*.chunk.js",
        "*.lock", "*-lock.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "*.pyc", "*.pyo", "*.class", "*.jar", "*.so", "*.dylib", "*.dll",
        "*.exe", "*.o", "*.a", "*.wasm",
        "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.ico", "*.svg", "*.avif",
        "*.mp4", "*.webm", "*.mov", "*.mp3", "*.wav", "*.ogg",
        "*.pdf", "*.zip", "*.tar", "*.gz", "*.7z",
        "*.whl", "*.nupkg", "*.deb", "*.rpm", "*.dmg", "*.pkg", "*.msi", "*.apk",
        "*.woff", "*.woff2", "*.ttf", "*.otf", "*.eot", "*.bcmap", "*.pfb", "*.pfm",
        "*.parquet", "*.pkl", "*.h5", "*.npy", "*.db", "*.sqlite", "*.lance",
        "*.log", "*.swp", "*.bak", "*.tmp", ".DS_Store",
    ]
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            exclusion_patterns = (
                config.get("exclusions", {}).get("patterns")
                or exclusion_patterns
            )
    except Exception:
        pass

    compiled_exclusions = compile_exclusions(exclusion_patterns)

    # --- Case 1: Project not indexed at all ---
    if not project_entry:
        output = {
            "hookSpecificOutput": {
                "additionalContext": (
                    f"[codebase-radar] Project at '{cwd}' has NOT been indexed yet. "
                    f"Project hash: {project_hash}. "
                    "The semantic search index is empty for this project."
                ),
                "systemMessage": (
                    f"The codebase-radar plugin has detected that the project at '{cwd}' "
                    "has no semantic search index. Call the MCP tool `index_codebase` with "
                    f"path='{cwd}' to build the index. This enables fast semantic code search "
                    "with `/radar:search` for the rest of this session."
                )
            }
        }
        print(json.dumps(output))
        return

    # --- Case 2: Project is indexed — compute filesystem diff ---
    stored_hashes = project_entry.get("file_hashes", {})
    files_indexed = project_entry.get("files_indexed", 0)
    chunks_total = project_entry.get("chunks_total", 0)
    last_indexed = project_entry.get("last_indexed", "unknown")
    embedding_model = project_entry.get("embedding_model", "all-MiniLM-L6-v2")

    changed_files = []
    new_files = []
    current_files = set()

    # Prefer git ls-files — cheaper than walking a 30k+ file tree, and
    # authoritative about which files "count" as project content.
    git_files = git_tracked_files(cwd)

    def _record_candidate(abs_path, rel_path):
        if matches_exclusion(rel_path, compiled_exclusions):
            return
        if not is_included(rel_path, DEFAULT_INCLUDE_EXTENSIONS, DEFAULT_INCLUDE_FILENAMES):
            return
        current_files.add(rel_path)
        current_hash = compute_file_hash(abs_path)
        if not current_hash:
            return
        if rel_path not in stored_hashes:
            new_files.append(abs_path)
        elif stored_hashes[rel_path] != current_hash:
            changed_files.append(abs_path)

    try:
        if git_files is not None:
            for rel_path in git_files:
                abs_path = os.path.join(cwd, rel_path)
                if os.path.isfile(abs_path):
                    _record_candidate(abs_path, rel_path)
        else:
            for root, dirs, files in os.walk(cwd):
                pruned = []
                for d in dirs:
                    if d in compiled_exclusions[0]:
                        continue
                    d_rel = os.path.relpath(os.path.join(root, d), cwd)
                    if matches_exclusion(d_rel, compiled_exclusions):
                        continue
                    pruned.append(d)
                dirs[:] = pruned

                for fname in files:
                    abs_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(abs_path, cwd)
                    _record_candidate(abs_path, rel_path)
    except Exception:
        pass

    all_modified = changed_files + new_files
    total_changed = len(all_modified)

    # Build stats context
    stats_context = (
        f"[codebase-radar] Index stats for '{cwd}': "
        f"files_indexed={files_indexed}, chunks={chunks_total}, "
        f"last_indexed={last_indexed}, embedding_model={embedding_model}, "
        f"changed_since_last_index={total_changed}"
    )

    # --- Case 2a: Many changes — suggest full reindex ---
    if total_changed > 50:
        output = {
            "hookSpecificOutput": {
                "additionalContext": stats_context,
                "systemMessage": (
                    f"codebase-radar detected {total_changed} changed/new files in '{cwd}' "
                    f"since the last index ({last_indexed}). "
                    "Rather than reindexing each file individually, call the MCP tool "
                    f"`index_codebase` with path='{cwd}' and incremental=true to do a fast "
                    "incremental refresh of the semantic search index."
                )
            }
        }
        print(json.dumps(output))
        return

    # --- Case 2b: Small number of changes — list individual files ---
    if total_changed > 0:
        file_list = "\n".join(f"  - {f}" for f in all_modified[:50])
        system_msg = (
            f"codebase-radar detected {total_changed} modified/new file(s) in '{cwd}' "
            f"since the last index ({last_indexed}). "
            "Call the MCP tool `reindex_file` for each of the following files to keep "
            "the semantic search index current:\n" + file_list
        )
    else:
        system_msg = (
            f"codebase-radar: The semantic index for '{cwd}' is up to date "
            f"({files_indexed} files, {chunks_total} chunks, last indexed {last_indexed}). "
            "Use `/radar:search <query>` for semantic code search."
        )

    output = {
        "hookSpecificOutput": {
            "additionalContext": stats_context,
            "systemMessage": system_msg
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block the session
        sys.exit(0)
