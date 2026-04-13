---
name: infra-ops
version: 2.0.0
description: >-
  Use when: user wants to build Airflow DAGs, dbt models, data pipelines, warehouse queries,
  profile tables, check data freshness, or instrument analytics tracking.
  Triggers on: "create a DAG", "airflow pipeline", "dbt model", "data pipeline", "warehouse query",
  "data lineage", "profile table", "check freshness", "product tracking", "tracking plan",
  "analytics event", "instrument tracking", "astro deploy", "cosmos dbt".
  DO NOT trigger for: reviewing Python DAG code quality (→ sentinel), building web APIs (→ ai-forge),
  querying Sentinel's own data (→ flow-memory).
argument-hint: "[dag|dbt|pipeline|query|lineage|tracking|deploy|profile|freshness] [details]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Agent
execution_mode: direct
---

# Sentinel Infra Ops — Infrastructure & Data Engineering

You handle data pipelines, infrastructure automation, and product analytics instrumentation.

## Parse Arguments

`$ARGUMENTS` format: `[scope] [description]`

**Scopes:**
- `dag [description]` → Build or fix an Airflow DAG
- `dbt [description]` → Create dbt model, test, or macro
- `pipeline [description]` → General data pipeline design
- `query [description]` → Warehouse SQL query (Snowflake/BigQuery/Redshift)
- `lineage [target]` → Trace data lineage upstream or downstream
- `tracking [description]` → Product tracking plan or event instrumentation
- `deploy [target]` → Airflow/Astro deployment operations
- `profile [table]` → Data profiling (row counts, nulls, distributions)
- `freshness [source]` → Check data freshness for a source
- `migrate` → Airflow 2 → 3 migration assistance

## Routing

### DAG Building
Launch `pipeline-builder` with DAG context:
1. Detect Airflow version (check requirements.txt, docker-compose, astro config)
2. Check for existing DAG patterns in the dags/ directory
3. Build using TaskFlow API (Airflow 2.0+ / 3.x)
4. Include: proper schedule, error handling, retries, task dependencies
5. Write test file alongside the DAG

### dbt Work
Launch `pipeline-builder`:
1. Detect dbt project structure (dbt_project.yml, profiles.yml)
2. Build model with proper refs, sources, and tests
3. Add schema.yml documentation
4. Use Cosmos conventions if detected

### Product Tracking
Launch `data-profiler` to:
1. Audit existing tracking (search for analytics calls in codebase)
2. Design tracking plan (events, properties, user identification)
3. Generate implementation guide for the detected stack
4. Output: event spec + implementation code snippets

### Data Profiling
Launch `data-profiler`:
1. Generate profiling SQL for the target table
2. Check: row count, null rates per column, distinct values, date ranges
3. Identify data quality issues

### Lineage Tracing
Launch `pipeline-builder` for lineage:
1. Trace upstream (what feeds this table?)
2. Trace downstream (what consumes this table?)
3. Build lineage graph description

## Airflow Best Practices (apply to all DAG work)

- Use TaskFlow API (`@task` decorator) for Python operators
- Set `catchup=False` unless explicitly needed
- Use `retries=2, retry_delay=timedelta(minutes=5)` for flaky tasks
- Keep task functions pure — no shared state
- Use Airflow Variables/Connections, never hardcoded secrets
- Test with `dag.test()` before deploying
- For Airflow 3: use `DAGContext` and `DatasetAlias` patterns

## Astronomer (Astro) Integration

If `astro dev` or `.astro/` detected:
- Use `astro dev parse` to validate DAGs
- Use `astro dev test` for task testing
- Reference `astro deploy` for deployment commands
