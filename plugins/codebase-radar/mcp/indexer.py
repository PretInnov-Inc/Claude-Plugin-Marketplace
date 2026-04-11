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
            h.update(f.read(8192))
        return h.hexdigest()
    except Exception:
        return ""


def _chunk_id(file_path: str, start_line: int) -> str:
    return hashlib.sha256(f"{file_path}:{start_line}".encode()).hexdigest()[:16]


def _matches_exclusion(rel_path: str, patterns: list) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(rel_path.replace("\\", "/"), pattern):
            return True
    return False


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


def index_codebase(path: str, incremental: bool = True, force_full: bool = False) -> dict:
    """
    Build or refresh the semantic search index for a project directory.

    Args:
        path: Absolute path to project root.
        incremental: If True, only process changed/new files.
        force_full: If True, clear all existing data and reindex from scratch.

    Returns:
        Stats dict with files_indexed, chunks_total, duration_seconds, etc.
    """
    start_time = time.time()
    project_root = os.path.abspath(path)
    config = _load_config()
    exclusion_patterns = config.get("exclusions", {}).get("patterns", [
        "node_modules/**", ".git/**", "**/*.min.js", "**/*.lock",
        "dist/**", "build/**", "__pycache__/**", "*.pyc",
        "**/*.egg-info/**", ".venv/**", "venv/**"
    ])

    state = _read_state()
    ph = _project_hash(project_root)
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

    # Walk filesystem
    files_to_process = []
    all_rel_paths = set()

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [
            d for d in dirs
            if not _matches_exclusion(
                os.path.relpath(os.path.join(root, d), project_root),
                exclusion_patterns
            )
        ]
        for fname in files:
            abs_path = os.path.join(root, fname)
            rel_path = os.path.relpath(abs_path, project_root)

            if _matches_exclusion(rel_path, exclusion_patterns):
                continue

            all_rel_paths.add(rel_path)
            current_hash = _file_hash(abs_path)
            if not current_hash:
                continue

            if not incremental or force_full:
                files_to_process.append((abs_path, rel_path, current_hash))
            elif rel_path not in stored_hashes or stored_hashes[rel_path] != current_hash:
                files_to_process.append((abs_path, rel_path, current_hash))

    # Process files: chunk, embed, upsert
    new_hashes = dict(stored_hashes)
    files_indexed = 0
    chunks_total = 0
    batch_size = 32

    # Collect all chunks before batching embeddings
    pending_chunks = []

    for abs_path, rel_path, file_hash in files_to_process:
        chunks = chunk_file(abs_path)
        if not chunks:
            new_hashes[rel_path] = file_hash
            continue

        for chunk in chunks:
            pending_chunks.append({
                "_file_path": abs_path,
                "_rel_path": rel_path,
                "_file_hash": file_hash,
                "_chunk": chunk
            })

    # Embed in batches
    if pending_chunks:
        texts = [pc["_chunk"]["text"] for pc in pending_chunks]

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_pending = pending_chunks[i:i + batch_size]

            vectors = embed_texts(batch_texts)

            records = []
            for j, (vec, pc) in enumerate(zip(vectors, batch_pending)):
                chunk = pc["_chunk"]
                cid = _chunk_id(pc["_file_path"], chunk["start_line"])
                records.append({
                    "chunk_id": cid,
                    "file_path": pc["_file_path"],
                    "relative_path": pc["_rel_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "chunk_type": chunk["chunk_type"],
                    "language": chunk["language"],
                    "content": chunk["text"],
                    "vector": [float(v) for v in vec]
                })

            _upsert_chunks(table, records)
            chunks_total += len(records)

            # Mark files as processed
            seen_files = set()
            for pc in batch_pending:
                if pc["_rel_path"] not in seen_files:
                    new_hashes[pc["_rel_path"]] = pc["_file_hash"]
                    files_indexed += 1
                    seen_files.add(pc["_rel_path"])

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

    # Update state
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
        "status": "complete"
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
        "last_indexed": now
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

    # Embed
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)
    rel_path = os.path.relpath(abs_path, project_root)

    records = []
    for chunk, vec in zip(chunks, vectors):
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
