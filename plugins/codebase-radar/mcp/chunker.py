"""
codebase-radar chunker.py

Code chunking with two strategies:
1. AST-based via tree-sitter (functions, classes, methods as chunks)
2. Fallback: character-based sliding window

Returns list of chunk dicts:
  {
    "text": str,
    "start_line": int,
    "end_line": int,
    "chunk_type": "function" | "class" | "method" | "other",
    "language": str
  }
"""

import os
import json
from pathlib import Path
from typing import Optional


# Map file extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

# Node types that represent top-level code units per language
CHUNK_NODE_TYPES = {
    "python": ["function_definition", "class_definition", "decorated_definition"],
    "typescript": ["function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "export_statement"],
    "tsx": ["function_declaration", "class_declaration", "method_definition",
            "arrow_function", "export_statement"],
    "javascript": ["function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "export_statement"],
    "java": ["method_declaration", "class_declaration", "constructor_declaration"],
    "cpp": ["function_definition", "class_specifier"],
    "c": ["function_definition"],
    "go": ["function_declaration", "method_declaration", "type_declaration"],
    "rust": ["function_item", "impl_item", "struct_item", "enum_item", "trait_item"],
    "ruby": ["method", "class", "module", "singleton_method"],
    "swift": ["function_declaration", "class_declaration", "struct_declaration",
              "protocol_declaration"],
    "kotlin": ["function_declaration", "class_declaration", "object_declaration"],
    "scala": ["function_definition", "class_definition", "object_definition", "trait_definition"],
}


def _node_type_to_chunk_type(node_type: str) -> str:
    if "class" in node_type or "struct" in node_type or "enum" in node_type:
        return "class"
    if "method" in node_type:
        return "method"
    if "function" in node_type or "func" in node_type or "arrow" in node_type:
        return "function"
    return "other"


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


def _get_chunk_config() -> tuple[int, int, bool]:
    """Returns (chunk_size_chars, chunk_overlap_chars, ast_enabled)."""
    config = _load_config()
    chunking = config.get("chunking", {})
    chunk_size_tokens = chunking.get("chunk_size_tokens", 256)
    chunk_overlap_tokens = chunking.get("chunk_overlap_tokens", 32)
    ast_enabled = chunking.get("ast_enabled", True)
    # Approximate: 1 token ~= 4 chars
    return chunk_size_tokens * 4, chunk_overlap_tokens * 4, ast_enabled


def _ast_chunk(content: str, language: str) -> Optional[list[dict]]:
    """
    Use tree-sitter to extract function/class nodes as chunks.
    Returns None if tree-sitter is unavailable or parsing fails.
    """
    try:
        from tree_sitter_language_pack import get_parser
        parser = get_parser(language)
    except Exception:
        return None

    try:
        tree = parser.parse(content.encode("utf-8", errors="replace"))
    except Exception:
        return None

    target_types = set(CHUNK_NODE_TYPES.get(language, []))
    if not target_types:
        return None

    chunks = []
    lines = content.splitlines()

    def walk(node):
        if node.type in target_types:
            start_line = node.start_point[0]  # 0-indexed
            end_line = node.end_point[0]      # 0-indexed
            chunk_lines = lines[start_line:end_line + 1]
            text = "\n".join(chunk_lines)
            if text.strip():
                chunks.append({
                    "text": text,
                    "start_line": start_line + 1,  # 1-indexed
                    "end_line": end_line + 1,       # 1-indexed
                    "chunk_type": _node_type_to_chunk_type(node.type),
                    "language": language
                })
            # Don't recurse into found nodes to avoid double-counting nested classes
            return
        for child in node.children:
            walk(child)

    walk(tree.root_node)

    # If no top-level nodes found, return None so fallback runs
    if not chunks:
        return None

    return chunks


def _character_chunk(content: str, language: str,
                     chunk_size: int, overlap: int) -> list[dict]:
    """
    Fallback: sliding window character-based chunking.
    Tries to split on newlines to avoid cutting mid-line.
    """
    if not content.strip():
        return []

    chunks = []
    lines = content.splitlines()
    current_lines = []
    current_size = 0
    line_idx = 0
    chunk_start_line = 1

    while line_idx < len(lines):
        line = lines[line_idx]
        line_len = len(line) + 1  # +1 for newline

        if current_size + line_len > chunk_size and current_lines:
            # Emit the current chunk
            text = "\n".join(current_lines)
            end_line = chunk_start_line + len(current_lines) - 1
            chunks.append({
                "text": text,
                "start_line": chunk_start_line,
                "end_line": end_line,
                "chunk_type": "other",
                "language": language
            })

            # Overlap: keep last N characters worth of lines
            overlap_text = text[-overlap:] if len(text) > overlap else text
            overlap_lines = overlap_text.splitlines()
            current_lines = overlap_lines
            current_size = sum(len(l) + 1 for l in overlap_lines)
            chunk_start_line = end_line - len(overlap_lines) + 1
        else:
            current_lines.append(line)
            current_size += line_len
            line_idx += 1

    # Emit remaining
    if current_lines:
        text = "\n".join(current_lines)
        end_line = chunk_start_line + len(current_lines) - 1
        chunks.append({
            "text": text,
            "start_line": chunk_start_line,
            "end_line": end_line,
            "chunk_type": "other",
            "language": language
        })

    return chunks


def chunk_file(file_path: str) -> list[dict]:
    """
    Chunk a source code file into semantically meaningful segments.

    Tries AST-based chunking first (if enabled and language supported).
    Falls back to character-based sliding window.

    Returns list of chunk dicts with text, start_line, end_line, chunk_type, language.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    language = EXTENSION_TO_LANGUAGE.get(ext, "text")

    chunk_size, chunk_overlap, ast_enabled = _get_chunk_config()

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return []

    if not content.strip():
        return []

    # Try AST chunking if enabled and language is supported
    if ast_enabled and language != "text":
        ast_chunks = _ast_chunk(content, language)
        if ast_chunks:
            return ast_chunks

    # Fallback to character chunking
    return _character_chunk(content, language, chunk_size, chunk_overlap)


def chunk_text(text: str, language: str = "text") -> list[dict]:
    """
    Chunk raw text (not a file) using character-based sliding window.
    """
    chunk_size, chunk_overlap, _ = _get_chunk_config()
    return _character_chunk(text, language, chunk_size, chunk_overlap)
