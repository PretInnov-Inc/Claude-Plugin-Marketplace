---
name: radar
description: "Show codebase-radar dashboard — index status, file count, chunks, last indexed time, embedding model, index health. Use when user runs /radar or asks about index status."
argument-hint: ""
disable-model-invocation: false
allowed-tools:
  - Bash
---

# codebase-radar Dashboard

Show the current index status for the active project directory.

## Steps

1. Determine the current project directory using the shell environment (treat it as the project root).

2. Call the MCP tool `get_status` with `project_root` set to the current directory path.

3. If the MCP tool returns an error or no data, display a helpful message:
   ```
   No index found for this directory.
   Run /radar:index to build the semantic search index.
   ```

4. If status data is returned, format it as a clean status table:

   ```
   codebase-radar — Index Status
   ================================
   Project:         <project path>
   Project Hash:    <first 12 chars of sha256(path)>
   Status:          <Indexed / Not Indexed / Stale>
   Files Indexed:   <count>
   Total Chunks:    <count>
   Last Indexed:    <ISO timestamp or "never">
   Embedding Model: <model name>
   Provider:        <huggingface / openai / voyageai>
   Index Size:      <size on disk in MB if available>
   Health:          <OK / WARNING / ERROR>
   ================================
   ```

5. Health status logic:
   - OK: index exists, last_indexed within 7 days, files_indexed > 0
   - WARNING: last_indexed older than 7 days, or chunk count seems low relative to file count
   - ERROR: index state is missing or corrupted

6. After the table, print a one-line tip:
   - If not indexed: "Run /radar:index to build the semantic search index."
   - If stale (WARNING): "Run /radar:index to refresh the index."
   - If OK: "Use /radar:search <query> to search your codebase semantically."
