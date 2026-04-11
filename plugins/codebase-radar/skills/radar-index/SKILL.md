---
name: radar-index
description: "Trigger codebase indexing — builds or refreshes the semantic search index for the current directory."
argument-hint: "[path]"
disable-model-invocation: false
allowed-tools:
  - Bash
---

# codebase-radar Index Builder

Build or refresh the semantic search index for a codebase directory.

## Input

An optional path is provided as `$ARGUMENTS`. If no path is given, use the current working directory.

## Steps

1. Determine the target path:
   - If `$ARGUMENTS` is non-empty, use it as the project root.
   - Otherwise, use the current working directory.

2. Inform the user that indexing is starting:
   ```
   Starting codebase-radar indexing for: <path>
   This may take a few minutes for large codebases...
   ```

3. Delegate to the `radar-indexer` agent to run the indexing job.
   Pass the target path clearly in your message to the agent, for example:
   "Index the codebase at path '<path>' using the index_codebase MCP tool."

4. The radar-indexer agent will:
   - Call `index_codebase` with the path
   - Poll `get_status` for progress
   - Return completion stats

5. When the agent returns, display the final stats:
   ```
   codebase-radar Indexing Complete
   =================================
   Path:          <path>
   Files Indexed: <count>
   Chunks:        <count>
   Duration:      <seconds>s
   Embedding:     <model name>
   =================================
   Use /radar:search <query> to search the indexed codebase.
   ```

6. If the agent reports an error:
   - Show the error message clearly.
   - Suggest: "Check that the MCP server is running. Run `scripts/install.sh` if this is a first-time setup."
