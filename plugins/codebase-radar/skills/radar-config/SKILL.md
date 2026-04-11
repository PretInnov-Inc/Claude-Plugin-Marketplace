---
name: radar-config
description: "Configure codebase-radar settings — embedding model, chunk size, exclusion patterns, search parameters."
argument-hint: ""
disable-model-invocation: false
allowed-tools:
  - Bash
---

# codebase-radar Configuration

View and update codebase-radar configuration settings.

## Steps

1. Call the MCP tool `configure` with no arguments (or an empty updates dict) to retrieve the current configuration state.

2. Display the current settings in a readable table:
   ```
   codebase-radar Configuration
   ==============================
   Embedding Provider:  <provider>
   Embedding Model:     <model_id>
   Dimensions:          <dimensions>
   Chunk Size (tokens): <chunk_size_tokens>
   Chunk Overlap:       <chunk_overlap_tokens>
   AST Chunking:        <enabled/disabled>
   Fallback Strategy:   <character>
   Search Top-K:        <top_k>
   Hybrid Alpha:        <hybrid_alpha>  (1.0 = vector only, 0.0 = BM25 only)
   Reranking:           <enabled/disabled>
   Exclusion Patterns:  <patterns as comma list>
   LanceDB Root:        <path>
   ==============================
   ```

3. Ask the user which setting they want to change:
   "Which setting would you like to update? Options:
   1. Embedding model (provider + model ID)
   2. Chunk size
   3. Chunk overlap
   4. Search top-k
   5. Hybrid alpha
   6. Exclusion patterns
   7. AST chunking on/off
   Enter a number or type the setting name:"

4. Once the user specifies a change, call the MCP tool `configure` with an `updates` dict containing only the changed fields.

   Field mapping:
   - "Embedding model" → updates: `{"embedding": {"provider": "...", "model_id": "..."}}`
   - "Chunk size" → updates: `{"chunking": {"chunk_size_tokens": N}}`
   - "Chunk overlap" → updates: `{"chunking": {"chunk_overlap_tokens": N}}`
   - "Search top-k" → updates: `{"search": {"top_k": N}}`
   - "Hybrid alpha" → updates: `{"search": {"hybrid_alpha": F}}`
   - "Exclusion patterns" → updates: `{"exclusions": {"patterns": [...]}}`
   - "AST chunking" → updates: `{"chunking": {"ast_enabled": true/false}}`

5. Important warnings to display:

   If the user changes the embedding model:
   ```
   WARNING: Changing the embedding model will invalidate the existing index.
   The current index uses <old_model> which produces <old_dimensions>-dimensional vectors.
   The new model <new_model> produces different dimensions.

   You must clear and rebuild the index:
     1. Run /radar:index with force_full=true
     OR
     2. Run the MCP tool clear_index (with confirm=true) then /radar:index

   Changes have been saved. The new model will be used on next index build.
   ```

   If the user changes chunk size:
   ```
   NOTE: Chunk size change affects new indexing runs only.
   Existing chunks in the index were created with the old chunk size.
   Run /radar:index to rebuild with the new chunk size.
   ```

6. After applying changes, display the updated configuration table.
