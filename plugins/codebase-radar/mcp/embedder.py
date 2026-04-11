"""
codebase-radar embedder.py

Embedding abstraction supporting:
- HuggingFace sentence-transformers (local, default)
- OpenAI text-embedding-3-small (cloud)
- VoyageAI voyage-code-3 (cloud)

Auto-detects provider from config.json. Caches model in memory.
"""

import os
import json
from pathlib import Path
from typing import Optional

# Module-level cache
_cached_provider: Optional[str] = None
_cached_model_id: Optional[str] = None
_cached_model = None  # SentenceTransformer or client object
_cached_embed_fn = None


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


def _get_embedder():
    """Load and cache the embedding model based on config."""
    global _cached_provider, _cached_model_id, _cached_model, _cached_embed_fn

    config = _load_config()
    embedding_cfg = config.get("embedding", {})
    provider = embedding_cfg.get("provider", "huggingface")
    model_id = embedding_cfg.get("model_id", "all-MiniLM-L6-v2")

    # Return cached if same config
    if (provider == _cached_provider and model_id == _cached_model_id
            and _cached_embed_fn is not None):
        return _cached_embed_fn

    if provider == "huggingface":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_id)

        def embed_fn(texts: list[str]) -> list[list[float]]:
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [e.tolist() for e in embeddings]

        _cached_model = model

    elif provider == "openai":
        import openai
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Configure it in plugin userConfig or set the env var."
            )
        client = openai.OpenAI(api_key=api_key)
        effective_model = model_id if model_id != "all-MiniLM-L6-v2" else "text-embedding-3-small"

        def embed_fn(texts: list[str]) -> list[list[float]]:
            response = client.embeddings.create(model=effective_model, input=texts)
            return [item.embedding for item in response.data]

        _cached_model = client

    elif provider == "voyageai":
        import voyageai
        api_key = os.environ.get("VOYAGEAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "VOYAGEAI_API_KEY environment variable not set. "
                "Configure it in plugin userConfig or set the env var."
            )
        client = voyageai.Client(api_key=api_key)
        effective_model = model_id if model_id != "all-MiniLM-L6-v2" else "voyage-code-3"

        def embed_fn(texts: list[str]) -> list[list[float]]:
            result = client.embed(texts, model=effective_model, input_type="document")
            return result.embeddings

        _cached_model = client

    else:
        raise ValueError(f"Unknown embedding provider: '{provider}'. "
                         "Valid options: 'huggingface', 'openai', 'voyageai'")

    _cached_provider = provider
    _cached_model_id = model_id
    _cached_embed_fn = embed_fn
    return embed_fn


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings.

    Returns a list of float vectors, one per input text.
    """
    if not texts:
        return []
    embed_fn = _get_embedder()
    return embed_fn(texts)


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.

    Returns a float vector.
    """
    results = embed_texts([query])
    return results[0] if results else []


def get_dimensions() -> int:
    """Return the embedding dimensions for the current model."""
    config = _load_config()
    return config.get("embedding", {}).get("dimensions", 384)


def get_provider_info() -> dict:
    """Return current embedding provider configuration."""
    config = _load_config()
    embedding_cfg = config.get("embedding", {})
    return {
        "provider": embedding_cfg.get("provider", "huggingface"),
        "model_id": embedding_cfg.get("model_id", "all-MiniLM-L6-v2"),
        "dimensions": embedding_cfg.get("dimensions", 384)
    }
