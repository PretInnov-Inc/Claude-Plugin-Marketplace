---
name: doctor
description: >-
  Alias for sentinel-doctor. Use when: user types /doctor, wants a quick health check,
  "is sentinel working?", "check hooks", "why isn't sentinel running?", "diagnose sentinel",
  "sentinel health", "plugin doctor". Runs the unified Sentinel diagnostic.
  DO NOT trigger for: reviewing application code (→ sentinel), auditing skill quality (→ sentinel-audit).
argument-hint: "[--full|--hooks|--config|--data|--lineage|--quick]"
allowed-tools: Read, Glob, Grep, Bash, TodoWrite
execution_mode: direct
---

Run the `sentinel-doctor` skill with the provided `$ARGUMENTS`.

Invoke it now — do not restate this instruction to the user.
