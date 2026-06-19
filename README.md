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
| Notion | `notion_search`, `notion_fetch_page`, `notion_create_page` |

### Skills (from Step 2)

| Skill | Description |
|-------|-------------|
| `/signalpilot-dbt:signalpilot` | Main entry point — schema discovery, governed queries, skill router |
| `/signalpilot-dbt:sql-workflow` | Structured SQL query building with verification |
| `/signalpilot-dbt:dbt-workflow` | Full 8-step dbt project workflow (scan, load skills, validate, macros, research, spec, write, verify) |
| `/signalpilot-dbt:dbt-write` | dbt model writing with column naming and type rules |
| `/signalpilot-dbt:dbt-debugging` | Fix dbt run/parse failures |
| `/signalpilot-dbt:dbt-date-spines` | Fix current_date hazards in date spine models |
| `/signalpilot-dbt:dbt-testing` | Unit tests and data tests |
| `/signalpilot-dbt:dbt-snapshots` | Snapshots / SCD2 |
| `/signalpilot-dbt:dbt-versioning` | Model versioning |
| `/signalpilot-dbt:dbt-knowledgebase` | Use the knowledge base within dbt work |
| `/signalpilot-dbt:knowledge-base` | Propose and search reusable knowledge entries |
| `/signalpilot-dbt:write-report` | Write a structured analysis report |
| `/signalpilot-dbt:xata` | Xata Postgres branches — connect, diff two branches, and flag schema changes that break dbt before merge |
| Domain skills | `domain-ecommerce`, `domain-financial`, `domain-healthcare`, `domain-hr`, `domain-marketing`, `domain-media`, `domain-product` |
| DB-specific | `bigquery-sql`, `snowflake-sql`, `duckdb-sql`, `sqlite-sql` |
| `/signalpilot-dbt:notion-context` | Gather business context from Notion (separate skill, load on request) |

### Agents (from Step 2)

| Agent | Description |
|-------|-------------|
| `verifier` | Post-build verification of dbt models (7-check protocol) |
| `value-verifier` | Aggregate value cross-validation of built models |
| `notion-verify` | Post-build traceability report — writes to Notion documenting how context influenced the build |

## How It Works

1. You ask Claude to build a dbt project or write SQL
2. Claude loads the `signalpilot` skill (tools overview + skill router)
3. For dbt projects, `dbt-workflow` orchestrates the workflow using SignalPilot MCP tools
4. If a Notion integration is configured in SignalPilot, business context is gathered before building (Step 0)
5. At Step 5, the `verifier` agent checks all models for correctness
6. If Notion context was used, a traceability report is written to Notion (Step 6)
7. You get a verified, working dbt project with full audit trail

## Notion Integration (Optional)

Connect your Notion workspace to give the agent access to meeting notes, product
specs, and data dictionaries for business context during dbt builds.

### Setup

1. Open the SignalPilot web UI at `http://localhost:3200/integrations`
2. Click **Add** under the Notion section
3. Paste your Notion internal integration access token
4. Add page URLs for search scope (pages the agent can search)
5. Add a report destination URL (where verification reports are created)

Create a Notion integration at [notion.so/profile/integrations](https://www.notion.so/profile/integrations)
to get an access token. Share pages with the integration in Notion for the agent to see them.

### What it does

- **Before build:** Searches Notion pages for definitions, decisions,
  and constraints relevant to the task.
- **During build:** Agent references Notion context when making grain, join, filter,
  and column decisions. Leaves `-- NOTION: <source>` comments in SQL.
- **After build:** Writes a traceability report to Notion mapping every context
  item to the SQL decision it influenced.

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- A SignalPilot account ([signalpilot.ai](https://signalpilot.ai)) or self-hosted instance

## License

Apache-2.0
