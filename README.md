# SignalPilot Plugin for Claude Code

Governed AI database access — sandboxed queries, schema discovery, and intelligent model building powered by [SignalPilot](https://signalpilot.ai).

## Install

### Step 1: Connect the MCP server

```bash
# Cloud
claude mcp add --transport http signalpilot https://gateway.signalpilot.ai/mcp \
  --header "Authorization: Bearer sp_YOUR_API_KEY"

# Local / self-hosted
claude mcp add --transport http signalpilot http://localhost:3300/mcp
```

### Step 2: Install the plugin (optional — adds skills + agents)

```bash
claude plugin marketplace add SignalPilot-Labs/signalpilot-plugin
claude plugin install signalpilot-dbt@signalpilot
```

Step 1 gives you all 30+ MCP tools. Step 2 adds skills and agents on top.

## What's Included

### MCP Tools (from Step 1)

| Category | Tools |
|----------|-------|
| Schema Discovery | `schema_overview`, `list_tables`, `describe_table`, `explore_table`, `explore_column`, `explore_columns`, `get_relationships`, `schema_ddl`, `schema_link` |
| Querying | `query_database`, `validate_sql`, `explain_query`, `estimate_query_cost` |
| Analysis | `analyze_grain`, `schema_statistics`, `find_join_path`, `compare_join_types`, `get_date_boundaries`, `schema_diff` |
| Governance | `check_budget`, `query_history`, `audit_model_sources`, `validate_model_output` |
| Infrastructure | `list_database_connections`, `connection_health`, `connector_capabilities` |

### Skills (from Step 2)

| Skill | Description |
|-------|-------------|
| `/signalpilot-dbt:signalpilot` | Main entry point — schema discovery, governed queries |
| `/signalpilot-dbt:sql-workflow` | Structured SQL query building with verification |
| `/signalpilot-dbt:dbt-workflow` | Full dbt project workflow (scan, map, validate, write, verify) |
| `/signalpilot-dbt:dbt-write` | dbt model writing with column naming and type rules |
| `/signalpilot-dbt:dbt-debugging` | Fix dbt run/parse failures |
| `/signalpilot-dbt:dbt-date-spines` | Fix current_date hazards in date spine models |
| DB-specific | `bigquery-sql`, `snowflake-sql`, `duckdb-sql`, `sqlite-sql` |
| `/signalpilot-dbt:notion-setup` | One-time Notion MCP setup + search scope config |
| `/signalpilot-dbt:notion-context` | Gather business context from Notion meeting notes |

### Agents (from Step 2)

| Agent | Description |
|-------|-------------|
| `verifier` | Post-build verification of dbt models (7-check protocol) |
| `notion-verify` | Post-build traceability report — writes to Notion documenting how context influenced the build |

## How It Works

1. You ask Claude to build a dbt project or write SQL
2. Claude loads the `signalpilot` skill (tools overview + skill router)
3. For dbt projects, `dbt-workflow` orchestrates the workflow using SignalPilot MCP tools
4. If Notion is configured, business context is gathered before building (Step 0)
5. At Step 5, the `verifier` agent checks all models for correctness
6. If Notion context was used, a traceability report is written to Notion (Step 6)
7. You get a verified, working dbt project with full audit trail

## Notion Integration (Optional)

Connect your Notion workspace to give the agent access to meeting notes, product
specs, and data dictionaries for business context during dbt builds.

### Setup

```bash
# 1. Connect Notion MCP (browser OAuth on first use)
claude mcp add --transport http --scope project notion https://mcp.notion.com/mcp

# 2. Configure search scope + report page
/signalpilot-dbt:notion-setup
```

### What it does

- **Before build:** Searches configured Notion pages for definitions, decisions,
  and constraints relevant to the task. Tags each item by relevance (DIRECT/RELATED).
- **During build:** Agent references Notion context when making grain, join, filter,
  and column decisions. Leaves `-- NOTION: <source>` comments in SQL.
- **After build:** Writes a traceability report to Notion mapping every context
  item to the SQL decision it influenced.

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- A SignalPilot account ([signalpilot.ai](https://signalpilot.ai)) or self-hosted instance

## License

Apache-2.0
