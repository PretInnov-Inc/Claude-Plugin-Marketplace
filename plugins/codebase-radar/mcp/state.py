"""
codebase-radar state.py

State and configuration management.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional


def _get_config_path() -> str:
    return os.environ.get(
        "RADAR_CONFIG_PATH",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/config.json")
    )


def _get_state_path() -> str:
    return os.environ.get(
        "RADAR_STATE_PATH",
        os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/index-state.json")
    )


def _get_lancedb_root() -> str:
    root = os.environ.get("RADAR_LANCEDB_ROOT", "")
    if not root:
        root = os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/lancedb")
    return root


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep-merge override into base. Override wins for scalar keys."""
    result = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def read_config() -> dict:
    """
    Read config.json and merge it over defaults.

    The persisted file is treated as a sparse override — any keys it omits
    fall back to _default_config(). This prevents partial writes (e.g. the
    session-stop stats update) from masking the full config on reads.
    """
    config_path = _get_config_path()
    defaults = _default_config()
    try:
        with open(config_path, "r") as f:
            persisted = json.load(f)
    except FileNotFoundError:
        return defaults
    except Exception as e:
        raise RuntimeError(f"Failed to read config at '{config_path}': {e}")
    if not isinstance(persisted, dict):
        return defaults
    return _deep_merge(defaults, persisted)


def write_config(config: dict):
    """Write config.json."""
    config_path = _get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def read_state() -> dict:
    """Read index-state.json."""
    state_path = _get_state_path()
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"version": "1.0.0", "projects": {}}
    except Exception as e:
        raise RuntimeError(f"Failed to read state at '{state_path}': {e}")


def write_state(state: dict):
    """Write index-state.json."""
    state_path = _get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _project_hash(project_root: str) -> str:
    return hashlib.sha256(project_root.encode()).hexdigest()[:12]


def _default_config() -> dict:
    return {
        "version": "1.0.0",
        "embedding": {
            "provider": "huggingface",
            "model_id": "all-MiniLM-L6-v2",
            "dimensions": 384
        },
        "chunking": {
            "chunk_size_tokens": 256,
            "chunk_overlap_tokens": 32,
            "ast_enabled": True,
            "fallback": "character"
        },
        "search": {
            "top_k": 10,
            "hybrid_alpha": 0.7,
            "rerank": False
        },
        "exclusions": {
            "patterns": [
                "node_modules/**", ".git/**", "**/*.min.js", "**/*.lock",
                "dist/**", "build/**", "__pycache__/**", "*.pyc",
                "**/*.egg-info/**", ".venv/**", "venv/**"
            ]
        },
        "index_locations": {
            "lancedb_root": ""
        },
        "stats": {
            "total_sessions": 0,
            "total_searches": 0,
            "total_files_indexed": 0
        }
    }


def get_status(project_root: str) -> dict:
    """
    Get the current index status and statistics for a project.

    Returns a dict with project metadata, index stats, and health indicator.
    """
    project_root = os.path.abspath(project_root)
    ph = _project_hash(project_root)
    state = read_state()
    project_entry = state.get("projects", {}).get(ph)

    if not project_entry:
        return {
            "project_root": project_root,
            "project_hash": ph,
            "status": "not_indexed",
            "files_indexed": 0,
            "chunks_total": 0,
            "last_indexed": None,
            "embedding_model": None,
            "embedding_provider": None,
            "health": "ERROR",
            "message": "Project has not been indexed. Call index_codebase to build the index."
        }

    last_indexed = project_entry.get("last_indexed")
    files_indexed = project_entry.get("files_indexed", 0)
    chunks_total = project_entry.get("chunks_total", 0)
    embedding_model = project_entry.get("embedding_model", "unknown")
    embedding_provider = project_entry.get("embedding_provider", "unknown")
    index_status = project_entry.get("status", "complete")
    progress = project_entry.get("progress") or {}
    job = project_entry.get("job") or {}

    # Stale-job detection: if marked "indexing" but the pid is gone,
    # downgrade to "error" so callers don't wait forever.
    if index_status == "indexing" and job.get("pid"):
        try:
            os.kill(int(job["pid"]), 0)
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            index_status = "error"
            project_entry["status"] = "error"
            project_entry["error"] = "Indexing process exited without writing completion state."

    # Determine health
    health = "OK"
    health_notes = []

    if index_status == "indexing":
        health = "WARNING"
        pct = None
        if progress.get("files_total"):
            pct = round(100.0 * progress.get("files_processed", 0) / progress["files_total"], 1)
        health_notes.append(
            f"Indexing in progress: {progress.get('files_processed', 0)}"
            f"/{progress.get('files_total', '?')} files"
            + (f" ({pct}%)" if pct is not None else "")
        )
    elif index_status == "error":
        health = "ERROR"
        err = project_entry.get("error", "Indexing failed.")
        health_notes.append(err)
    elif files_indexed == 0:
        health = "ERROR"
        health_notes.append("No files indexed")
    elif chunks_total == 0:
        health = "WARNING"
        health_notes.append("No chunks in index")
    elif last_indexed:
        try:
            from datetime import datetime, timezone, timedelta
            li = datetime.fromisoformat(last_indexed.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - li).days
            if age_days > 7:
                health = "WARNING"
                health_notes.append(f"Index is {age_days} days old")
        except Exception:
            pass

    # Try to get index size on disk
    lancedb_root = _get_lancedb_root()
    table_name = project_entry.get("table_name", f"radar_{ph}")
    table_dir = os.path.join(lancedb_root, table_name + ".lance")
    index_size_mb = None
    if os.path.isdir(table_dir):
        try:
            total_bytes = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, filenames in os.walk(table_dir)
                for f in filenames
            )
            index_size_mb = round(total_bytes / (1024 * 1024), 2)
        except Exception:
            pass

    return {
        "project_root": project_root,
        "project_hash": ph,
        "status": index_status,
        "files_indexed": files_indexed,
        "chunks_total": chunks_total,
        "last_indexed": last_indexed,
        "embedding_model": embedding_model,
        "embedding_provider": embedding_provider,
        "index_size_mb": index_size_mb,
        "health": health,
        "health_notes": health_notes,
        "table_name": table_name,
        "progress": progress,
        "job": job,
        "error": project_entry.get("error"),
    }


def clear_index(project_root: str, confirm: bool = False) -> dict:
    """
    Clear the semantic index for a project.

    Drops the LanceDB table directory and removes the project from index-state.json.
    Requires confirm=True.
    """
    if not confirm:
        raise ValueError("confirm=True is required to clear the index.")

    project_root = os.path.abspath(project_root)
    ph = _project_hash(project_root)
    state = read_state()
    project_entry = state.get("projects", {}).get(ph)

    if not project_entry:
        return {
            "status": "not_found",
            "message": f"No index found for '{project_root}'."
        }

    table_name = project_entry.get("table_name", f"radar_{ph}")

    # Remove LanceDB table directory
    lancedb_root = _get_lancedb_root()
    table_dir = os.path.join(lancedb_root, table_name + ".lance")
    removed_table = False
    if os.path.isdir(table_dir):
        import shutil
        try:
            shutil.rmtree(table_dir)
            removed_table = True
        except Exception as e:
            return {"status": "error", "message": f"Failed to remove table directory: {e}"}

    # Also try via LanceDB API
    if not removed_table:
        try:
            import lancedb as ldb
            db = ldb.connect(lancedb_root)
            if table_name in db.table_names():
                db.drop_table(table_name)
                removed_table = True
        except Exception:
            pass

    # Remove from state
    state.get("projects", {}).pop(ph, None)
    write_state(state)

    return {
        "status": "cleared",
        "project_root": project_root,
        "table_name": table_name,
        "table_removed": removed_table
    }


def configure(updates: Optional[dict] = None) -> dict:
    """
    Read or update codebase-radar configuration.

    If updates is empty or None, returns current config.
    If updates contains values, deep-merges them into config and saves.

    Returns the resulting configuration.
    """
    config = read_config()

    if not updates:
        return config

    warnings = []

    # Check if embedding model is changing
    old_embedding = config.get("embedding", {}).copy()
    new_embedding = updates.get("embedding", {})
    if new_embedding:
        old_model = old_embedding.get("model_id", "")
        old_provider = old_embedding.get("provider", "")
        new_model = new_embedding.get("model_id", old_model)
        new_provider = new_embedding.get("provider", old_provider)
        if new_model != old_model or new_provider != old_provider:
            warnings.append(
                f"Embedding model changed from '{old_provider}/{old_model}' to "
                f"'{new_provider}/{new_model}'. Existing indexes are invalidated — "
                "run index_codebase with force_full=true to rebuild."
            )

    # Check if chunk size is changing
    old_chunk_size = config.get("chunking", {}).get("chunk_size_tokens", 256)
    new_chunking = updates.get("chunking", {})
    if new_chunking and new_chunking.get("chunk_size_tokens", old_chunk_size) != old_chunk_size:
        warnings.append(
            "Chunk size changed. Existing chunks use the old size. "
            "Run index_codebase to rebuild with the new chunk size."
        )

    config = _deep_merge(config, updates)
    write_config(config)

    return {
        "config": config,
        "warnings": warnings,
        "message": "Configuration updated successfully." if not warnings else
                   "Configuration updated with warnings."
    }
