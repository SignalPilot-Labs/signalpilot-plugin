# SignalPilot Plugin for Claude Code

Governed AI database access — sandboxed queries, schema discovery, and intelligent model building powered by [SignalPilot](https://signalpilot.ai).

## Quick Install

```bash
# 1. Add the SignalPilot marketplace
claude plugin marketplace add SignalPilot-Labs/signalpilot-plugin

# 2. Install the plugin
claude plugin install signalpilot-dbt@signalpilot
```

During install you'll be prompted for:
- **SignalPilot URL**: `https://gateway.signalpilot.ai` (cloud) or `http://localhost:3300` (local)
- **API Token**: Your `sp_` API key from the SignalPilot dashboard

### MCP Server only (one-liner, no plugin)

If you just want the MCP tools without skills/agents:

```bash
# Cloud
claude mcp add --transport http signalpilot https://gateway.signalpilot.ai/mcp \
  --header "Authorization: Bearer sp_YOUR_API_KEY"

# Local / self-hosted
claude mcp add --transport http signalpilot http://localhost:3300/mcp
```

## What's Included

### MCP Tools (30+)

| Category | Tools |
|----------|-------|
| Schema Discovery | `schema_overview`, `list_tables`, `describe_table`, `explore_table`, `explore_column`, `explore_columns`, `get_relationships`, `schema_ddl`, `schema_link` |
| Querying | `query_database`, `validate_sql`, `explain_query`, `estimate_query_cost` |
| Analysis | `analyze_grain`, `schema_statistics`, `find_join_path`, `compare_join_types`, `get_date_boundaries`, `schema_diff` |
| Governance | `check_budget`, `query_history`, `audit_model_sources`, `validate_model_output` |
| Infrastructure | `list_database_connections`, `connection_health`, `connector_capabilities` |

### Skills

| Skill | Description |
|-------|-------------|
| `/signalpilot-dbt:signalpilot` | Main entry point — schema discovery, governed queries |
| `/signalpilot-dbt:sql-workflow` | Structured SQL query building with verification |
| `/signalpilot-dbt:dbt-workflow` | Full dbt project workflow (scan, map, validate, write, verify) |
| `/signalpilot-dbt:dbt-write` | dbt model writing with column naming and type rules |
| `/signalpilot-dbt:dbt-debugging` | Fix dbt run/parse failures |
| `/signalpilot-dbt:dbt-date-spines` | Fix current_date hazards in date spine models |
| DB-specific | `bigquery-sql`, `snowflake-sql`, `duckdb-sql`, `sqlite-sql` |

### Agents

| Agent | Description |
|-------|-------------|
| `verifier` | Post-build verification of dbt models (7-check protocol) |

## How It Works

1. You ask Claude to build a dbt project or write SQL
2. Claude loads the `signalpilot` skill (tools overview + skill router)
3. For dbt projects, `dbt-workflow` orchestrates a 5-step workflow using SignalPilot MCP tools
4. At Step 5, the `verifier` agent checks all models for correctness
5. You get a verified, working dbt project

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- A SignalPilot account ([signalpilot.ai](https://signalpilot.ai)) or self-hosted instance

## License

Apache-2.0
