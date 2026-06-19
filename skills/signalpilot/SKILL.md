---
name: signalpilot
description: "BLOCKING REQUIREMENT: If the user's message mentions dbt, SQL, database, or data pipeline — invoke this skill as your FIRST tool call, BEFORE Read, Glob, Grep, Bash, or Agent. Covers: SignalPilot MCP tools, available skills, and the governed workflow for dbt projects, SQL queries, schema discovery, and database access."
---

# SignalPilot — Governed AI Database Access

## User-visible Progress Contract
SignalPilot work is often tool-heavy. Keep the user oriented while you use MCP
tools:

- Before the first MCP call, write one short sentence explaining what you are
  checking and why.
- Before each major phase, write one short progress sentence for schema
  scouting, query validation, model/notebook edits, execution, error repair, and
  final verification.
- After a tool result changes the plan, finds a data-quality issue, or fails,
  summarize what changed and what you will do next.
- Do not expose private reasoning, chain-of-thought, raw JSON, or every tool
  parameter. Explain intent and findings in human terms.
- Do not leave the user watching only MCP calls. A good run has concise
  assistant text between groups of tool calls.
- Final answers should mention the evidence actually checked and any residual
  uncertainty.

## MCP Tools
The SignalPilot MCP provides governed database access:
- `query_database` — governed read-only SQL execution
- `validate_sql` / `explain_query` / `estimate_query_cost` — pre-execution checks
- `schema_overview` / `schema_ddl` / `schema_link` — schema discovery
- `describe_table` / `explore_table` / `explore_columns` / `explore_column` — deep dives
- `list_tables` / `get_relationships` / `find_join_path` — structure and joins
- `compare_join_types` — JOIN impact analysis
- `get_date_boundaries` — date ranges across all tables
- `check_model_schema` / `validate_model_output` / `audit_model_sources` — dbt validation
- `analyze_grain` — cardinality and grain analysis
- `debug_cte_query` — step-through CTE debugging
- `dbt_error_parser` — parse dbt error output into structured info
- `list_projects` / `get_project` — dbt project management
- `check_budget` / `connection_health` / `query_history` — operational
- `list_notion_integrations` / `notion_search` / `notion_fetch_page` / `notion_create_page` — Notion integration

## Local Scripts (via plugin)
For local dbt project work, use these standalone scripts:
- `scan_project.py` — scan a dbt project: models, stubs, deps, hazards, work order
- `validate_project.py` — run `dbt parse` and report structural errors

Use `ToolSearch` to discover additional tools as needed.

## Available Skills
Load these skills as needed for specialized work:

### dbt Projects
- `/signalpilot-dbt:dbt-workflow` — Load FIRST for any dbt project. Full 8-step
  workflow: scan, load skills, validate, discover macros, research, spec, write, verify.
- `/signalpilot-dbt:dbt-write` — Load at the writing step for SQL model rules
- `/signalpilot-dbt:dbt-debugging` — Load when dbt run/parse fails
- `/signalpilot-dbt:dbt-date-spines` — Load to fix current_date/now() hazards
- `/signalpilot-dbt:dbt-testing` — Load for unit tests / data tests
- `/signalpilot-dbt:dbt-snapshots` — Load for snapshots / SCD2
- `/signalpilot-dbt:dbt-versioning` — Load for model versioning
- `/signalpilot-dbt:dbt-knowledgebase` — Load to use the knowledge base in dbt work

### SQL (load the one matching your database)
- `/signalpilot-dbt:duckdb-sql` — DuckDB-specific syntax and gotchas
- `/signalpilot-dbt:snowflake-sql` — Snowflake-specific patterns
- `/signalpilot-dbt:bigquery-sql` — BigQuery-specific patterns
- `/signalpilot-dbt:sqlite-sql` — SQLite-specific patterns

### Domain knowledge (load the one matching the data)
- `/signalpilot-dbt:domain-ecommerce`, `domain-financial`, `domain-healthcare`,
  `domain-hr`, `domain-marketing`, `domain-media`, `domain-product`

### Database branching
- `/signalpilot-dbt:xata` — Xata Postgres branches: connect, diff two branches, and
  check whether an upstream branch's schema change breaks dbt before it merges

### Notion Context
- `/signalpilot-dbt:notion-context` — Gather business context from Notion. Load this skill when the user asks for it; it is separate from the dbt workflow.

### General
- `/signalpilot-dbt:sql-workflow` — Structured query building and verification
- `/signalpilot-dbt:knowledge-base` — Propose and search reusable knowledge entries
- `/signalpilot-dbt:write-report` — Write a structured analysis report

## Quick Start

**For dbt projects:** Load `/signalpilot-dbt:dbt-workflow` — it orchestrates the
full lifecycle including scanning, mapping, writing, and verification.

**For SQL queries:** Load `/signalpilot-dbt:sql-workflow` + the SQL skill for your
database engine.

**For schema exploration:** Use the MCP tools directly — `schema_overview` for a
broad view, `describe_table` for column details, `explore_table` for sample data.
