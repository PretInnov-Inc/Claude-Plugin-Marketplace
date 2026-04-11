---
name: radar-search
description: "Semantic code search with hybrid BM25 + vector retrieval. Use when user wants to find code by concept, function, or natural language description."
argument-hint: "<search query>"
disable-model-invocation: false
allowed-tools:
  - Bash
---

# codebase-radar Semantic Search

Search the codebase using hybrid BM25 + dense vector retrieval.

## Input

The user's query is provided as `$ARGUMENTS`. If no argument is provided, ask the user what they want to search for.

## Steps

1. Extract the search query from `$ARGUMENTS`.

2. Call the MCP tool `search_code` with:
   - `query`: the user's search query (as natural language or code terms)
   - `project_root`: current working directory
   - `top_k`: 20

3. If the tool returns an error indicating the project is not indexed:
   - Inform the user: "This project hasn't been indexed yet. Running /radar:index first..."
   - Call `index_codebase` with `path` = current directory, then retry the search.

4. Format results as a numbered list. For each result:
   ```
   [N] <relative_file_path>  (lines <start>–<end>)  Score: <score*100 as integer>%  [<language>]
   ─────────────────────────────────────────────────
   <first 3 lines of content preview>
   ...
   ```

5. After listing all results, write a synthesis section:
   ```
   ## What was found

   <2-4 sentence explanation of what the search found, where the relevant code lives,
   and any patterns or themes across results. Mention specific file paths.>
   ```

6. If no results were found:
   - Say: "No results found for '<query>'. The index may need refreshing. Try /radar:index then search again."

7. If fewer than 3 results were returned:
   - Suggest broadening the query: "Try a more general query like '<simplified version>'."
