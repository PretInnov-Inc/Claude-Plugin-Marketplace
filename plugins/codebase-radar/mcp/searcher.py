"""
codebase-radar searcher.py

Hybrid BM25 + dense vector search over LanceDB.
"""

import os
import hashlib
from typing import Optional

import lancedb

from embedder import embed_query


def _get_lancedb_root() -> str:
    root = os.environ.get("RADAR_LANCEDB_ROOT", "")
    if not root:
        root = os.path.expanduser("~/.local/share/claude-plugins/codebase-radar/lancedb")
    return root


def _project_hash(project_root: str) -> str:
    return hashlib.sha256(project_root.encode()).hexdigest()[:12]


def _table_name(project_root: str) -> str:
    return f"radar_{_project_hash(project_root)}"


def search_code(
    project_root: str,
    query: str,
    top_k: int = 10,
    path_filter: Optional[str] = None,
    language: Optional[str] = None
) -> list[dict]:
    """
    Hybrid semantic + BM25 search over the indexed codebase.

    Args:
        project_root: Absolute path to the project root.
        query:        Natural language or code query string.
        top_k:        Number of results to return.
        path_filter:  Optional substring to filter file paths (case-insensitive).
        language:     Optional language name to filter (e.g. "python", "typescript").

    Returns:
        List of result dicts:
          {
            "file_path":      str,
            "relative_path":  str,
            "start_line":     int,
            "end_line":       int,
            "chunk_type":     str,
            "language":       str,
            "content":        str,
            "score":          float  (0.0 – 1.0, higher is better)
          }
    """
    project_root = os.path.abspath(project_root)
    table_name = _table_name(project_root)

    db = lancedb.connect(_get_lancedb_root())
    if table_name not in db.table_names():
        raise ValueError(
            f"No index found for project at '{project_root}'. "
            "Call index_codebase first."
        )

    table = db.open_table(table_name)

    # Embed the query
    query_vector = embed_query(query)

    # Run hybrid search (BM25 + dense vector)
    # Fetch 2x top_k to allow for post-filtering
    fetch_k = top_k * 2

    try:
        results_df = (
            table.search(query_vector, query_type="hybrid")
            .text(query)
            .limit(fetch_k)
            .to_pandas()
        )
    except Exception:
        # Fallback to pure vector search if hybrid not available
        try:
            results_df = (
                table.search(query_vector)
                .limit(fetch_k)
                .to_pandas()
            )
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    # Apply post-filters
    if path_filter:
        pf_lower = path_filter.lower()
        results_df = results_df[
            results_df["file_path"].str.lower().str.contains(pf_lower, na=False)
        ]

    if language:
        lang_lower = language.lower()
        results_df = results_df[
            results_df["language"].str.lower() == lang_lower
        ]

    # Take top_k after filtering
    results_df = results_df.head(top_k)

    # Build result list
    results = []
    for _, row in results_df.iterrows():
        # LanceDB returns _distance (lower = better) or _score (higher = better)
        # Normalize to a 0-1 score where 1.0 is most relevant
        if "_score" in results_df.columns:
            raw_score = float(row.get("_score", 0.0))
            score = min(1.0, max(0.0, raw_score))
        elif "_distance" in results_df.columns:
            dist = float(row.get("_distance", 1.0))
            # Convert L2 distance to similarity score (approximate)
            score = max(0.0, 1.0 - min(dist, 2.0) / 2.0)
        else:
            score = 0.5

        results.append({
            "file_path": str(row.get("file_path", "")),
            "relative_path": str(row.get("relative_path", "")),
            "start_line": int(row.get("start_line", 0)),
            "end_line": int(row.get("end_line", 0)),
            "chunk_type": str(row.get("chunk_type", "other")),
            "language": str(row.get("language", "")),
            "content": str(row.get("content", "")),
            "score": round(score, 4)
        })

    return results
