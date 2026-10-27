---
name: dbt-workflow
description: "Load FIRST before any dbt project work. Covers the full 8-step dbt workflow: project scanning, skill loading, validation, macro discovery, research, technical spec, SQL writing, and verification. Also covers output shape inference, incremental model handling, and what to trust in YML."
disable-model-invocation: false
allowed-tools: Bash(dbt *) Bash(python3 *)
---

# dbt Workflow Skill - Full Project Lifecycle

## Overview

This skill orchestrates the complete dbt project workflow. Load it FIRST whenever
working on a dbt project - it contains rules that affect how you interpret everything.

In a chat, read `dbt run`, `dbt build`, and `dbt test` here as `dbt_execute` with the same `select`, and `validate_project.py` as `inspect_dbt` `parse`. Before each run or build, call `estimate_query_cost` on each model's compiled SQL.

## Tools

### scan_project.py - Project scanner (Step 1)
```bash
python3 "${CLAUDE_SKILL_DIR}/scan_project.py" "<project_directory>"
```
Returns: models to build, stubs to rewrite, dependencies, required columns,
sources, macros (with full definitions), and current_date hazards.

### validate_project.py - dbt parse validator (Step 3)
```bash
python3 "${CLAUDE_SKILL_DIR}/validate_project.py" "<project_directory>"
```
Runs `dbt parse` and returns structured errors, warnings, and orphan patches.

### map_columns - Upstream observations

`map_columns` accepts `upstream_tables="<physical_relation1>,<physical_relation2>"` for pre-write inspection when SQL has no lineage. Its statuses describe available columns rather than output requirements.

### find_column_producers - Existing producers (MCP tool, Step 5)

Call `find_column_producers(connection_name, column_names="<col1>,<col2>", project_dir)` before writing SQL. It reports every existing model that already projects each named output column, the relations it reads, and the expression - the project's producer for a value is the model that already computes it.

### verify_model_values - Aggregate cross-validator (MCP tool, Step 8)
Call `verify_model_values(connection_name, model_name)` on a DuckDB connection only. On other connections, compare the model against its sources with `query_database`.
Queries the model output, finds the upstream fact table, picks the largest
slice, and compares the model's metric values against both COUNT(*) and
COUNT(DISTINCT <key>) from the raw source. Reports MATCH, MISMATCH, or
WARNING (model uses DISTINCT when COUNT(*) is larger). Used by the
value-verifier subagent in Step 8.

## Context Check (before Step 1)

Before starting the workflow, read the project's context folder (its path
is in the system prompt): its README.md and AGENT.md first, then only the
files that apply to the task. They hold this project's conventions,
metric definitions, and prior research.

Context files INFORM your work but do NOT skip any steps. Always run the
full 8-step workflow. The context makes you faster because you already know
what to look for - but you still verify everything via `query_database`
and the verification subagents.

## The 8-Step Workflow

ALWAYS run Steps 1, 2, 3, and 8. Steps 4-7 are ONLY for projects
with stubs to rewrite or models to build (from the Step 1 scan).
If the scan shows 0 stubs and 0 missing models AND the task does NOT
ask to edit, fix, remove, or modify existing files, skip Steps 4-7
entirely - go from Step 3 straight to Step 8.

If the task edits existing models (edit, fix, remove a variable, refactor),
do NOT skip Steps 4-7 even if the scan shows nothing to build. Edit the
files in Step 7, then run `dbt run --select <edited_model1> <edited_model2>`
to rebuild them - edited SQL only takes effect after materialization.

Even if the task says "create model X" - if X.sql already exists in
the scan's "EXISTING COMPLETE" list, it is already created. Verify it
in Step 8, do not recreate it.

Track each workflow step that you will run as a step in the plan file.

### Step 1 - Map the project
Run the filesystem scan:
`python3 "${CLAUDE_SKILL_DIR}/scan_project.py" "<project_directory>"`. For joins between
tables, use `find_join_path` or `get_relationships` when a model needs them.

Read the ENTIRE output. Record:
- STUBS TO REWRITE
- MODELS TO BUILD
- DEPENDENCIES
- REQUIRED COLUMNS
- AVAILABLE MACROS (with definitions)

`prebuild_state.md` is verifier evidence: the baseline of each supplied model before you change it. The plan file tracks progress. If it already exists, read it and do not overwrite it.

Before the first dbt command, call `list_tables(connection_name)` when no baseline exists because a build can overwrite supplied relations.

When no baseline exists, create `<project_dir>/prebuild_state.md`. For each supplied model, record `CREATE`, `REWRITE STUB`, `MODIFY`, or `VERIFY` plus the verbatim task-authorized change because the verifier must tell requested changes from scope expansion. Read its SQL/YML config and `dbt_project.yml`; record its SQL path, materialization, database, schema, and alias because verification needs the original node identity.

Match each configured relation against `list_tables`. Record `ABSENT` when no relation exists. When a relation exists, call `explore_columns(connection_name, table="<qualified_relation>", include_samples=true, include_stats=true)` because types and values establish its current contract. For each column, add `COUNT(*) - COUNT(<quoted column>) AS <quoted column_name_nulls>` to one `query_database` query because NULL coverage and zero rows must be explicit.

Record every static `ref()`, `source()`, and direct physical relation in `FROM` or `JOIN` within supplied models and their dependency closure because bindings are not always variable-driven. Record each original relation expression and its resolved physical relation. Record each source's database, schema, identifier, enabled value, and resolved relation. Search the same files for `var(` and `env_var(`; record each expression, its project value or declared default, every binding field that consumes it, and its resolved relation because indirect bindings can change population.

Record every binding, or mark it `ABSENT`, before the first `dbt_execute` `run` or `build`.

If the task describes a runtime bug (type mismatch, wrong values, broken output), run `dbt run --select <pre_existing_model> 2>&1 | tail -50` on the affected pre-existing model - `dbt parse` passing does NOT mean the model produces correct output.

### Step 2 - Load supporting skills
Load ALL THREE skills now - they contain rules needed for writing AND
verifying models. Classify the domain from the task instruction and
source table names in the Step 1 scan output.

1. `/signalpilot-dbt:dbt-write`
2. The SQL skill for your database (e.g. `/signalpilot-dbt:duckdb-sql`)
3. The domain skill matching the task:
 - Revenue/invoices/ledgers/fiscal → `/signalpilot-dbt:domain-financial`
 - Campaigns/clicks/email/SMS/messaging/attribution → `/signalpilot-dbt:domain-marketing`
 - Events/sessions/features/guides/analytics → `/signalpilot-dbt:domain-product`
 - Employees/hiring/issues/SCD/tickets → `/signalpilot-dbt:domain-hr`
 - Orders/products/discounts/returns/charges/spend → `/signalpilot-dbt:domain-ecommerce`
 - Movies/sports/credits/content → `/signalpilot-dbt:domain-media`
 - Clinical/patients/encounters/diagnoses/costs → `/signalpilot-dbt:domain-healthcare`

Also load these conditional skills when the task or project requires them:
4. If the task mentions "test", "unit test", "add tests", "verify logic", "verify the logic",
   "check logic", "check correctness", OR the Step 1 scan found `unit_tests:` blocks in YML:
   → `/signalpilot-dbt:dbt-testing`
   Load this skill BEFORE writing any test YAML - unit tests use a different YAML structure than schema tests.
5. If the task mentions "snapshot", "SCD", "slowly changing", "track changes", "history",
   OR the Step 1 scan found a `snapshots/` directory:
   → `/signalpilot-dbt:dbt-snapshots`
6. If the task mentions "version", "v2", "backward compatible",
   OR the Step 1 scan found `versions:` blocks in YML:
   → `/signalpilot-dbt:dbt-versioning`

Do NOT skip this step. These skills contain rules that apply to
verification (Step 8), not just writing.

### Step 3 - Validate and fix stale upstreams
Run `python3 "${CLAUDE_SKILL_DIR}/validate_project.py" "<project_directory>"`.
If errors, fix them before proceeding.

MANDATORY: if the Step 1 scan flagged `current_date` or `now()` hazards in
PRE-EXISTING models, rebuild those models NOW:
`dbt run --select <flagged_model1> <flagged_model2>`
These models contain stale data from a prior run. Without rebuilding, all
downstream models inherit wrong row counts. Do NOT skip this even if the
context folder covers the model - it cannot fix stale materialized data.

Do NOT use `+`. If no hazards flagged, skip the rebuild.

### Step 4 - Discover project macros
Read the AVAILABLE MACROS section from Step 1 output. For each macro NOT
referenced by any existing complete model:
1. Read its definition - it is printed in the scan output.
2. Identify what column it produces. `extract_hour(created_at)` produces
   `hour_created_at`. `normalize_timestamp(created_at)` produces
   `normalized_created_at`.
Record a macro output only when its definition returns an output expression and every required input exists in this model's established upstreams because helper macros do not define columns by themselves.

### Step 5 - Research (data exploration)
Apply source-selection defaults to `CREATE` and `REWRITE STUB` work. For `MODIFY` and `VERIFY` work, preserve every binding recorded in `prebuild_state.md` unless the verbatim task authorizes its change because research defaults do not redefine an existing model.

Call `describe_table` before you filter, group, or join on a column you have
not seen in a result. On SQL Server, INFORMATION_SCHEMA column names are
upper case.

For EACH model that needs SQL, gather the facts to write it correctly:

1. **Driving table** - the Step 1 scan's AGGREGATION DRIVING TABLE hint flags a
   parent whose rows have no matching children. Classify by the model's METRICS, then
   FOLLOW the result - this is binding; do NOT override based on the task phrase
   "aggregate X by Y" (that names what to summarize, not the FROM clause):
 - If every child metric is a COUNT or SUM (e.g. `total_parts`, `total_orders`) -
     meaningful as 0 for a childless parent - KEEP childless rows: drive FROM the
     parent, LEFT JOIN children.
 - If any metric is a RATIO, AVERAGE, or SCORE that divides by the child count
     (e.g. NPS = (positive − negative) / total, avg_rating) - undefined (division by
     zero) for a childless parent - DROP childless rows: drive FROM the child
     aggregation, INNER JOIN the entity.
   LEFT JOIN all other upstreams.
2. **Cardinalities** - run `query_database` with `SELECT COUNT(*)` and
   `SELECT COUNT(DISTINCT <key>)` on each upstream to confirm grain.
3. **Contract** - read the model's YML entry for column names, tests, and
   descriptions.
Call `map_columns` with `upstream_tables="<physical_relation1>,<physical_relation2>"` before writing SQL because source projections must be visible before materialization. Qualify an `AMBIGUOUS` relation or correct a `NOT FOUND` name and rerun the call because unresolved upstreams cannot support construction. When `map_columns` reports `POSITIONAL ALIGNMENT` or `POSITIONAL DECORATION CANDIDATES`, those are hints about which source column each YML name maps to. Confirm each pair against YML descriptions, sibling SQL, and sample values, and record the confirmed mapping in your Step 5 notes for the Step 6 spec. If one source table covers every YML column, the scan flags no LOOKUP JOINS, and no AGGREGATION DRIVING TABLE hint applies, build from that single table with no join - a second table would only add or drop rows.
4. **Sibling patterns** - read sibling SQL and the YML in `dbt_packages/`
   for JOIN types, CASE WHEN predicates, and categorical vocabulary. The test
   data is often too sparse to reveal every value; the package YML descriptions
   are not.
5. **Categorical values** - run `query_database` with `SELECT DISTINCT <col>`
   on status/flag/type columns before writing CASE WHEN. The values determine
   which rows are purchases vs returns vs cancelled.

**CTE extraction override:** If you are extracting CTEs from a parent model,
read the parent model's outermost final SELECT - the table in its FROM clause
is the true spine. Run `SELECT COUNT(DISTINCT <key>)` on both the spine and the
aggregation source. If counts differ, use the spine.

### Step 6 - Write technical spec
Write `<project_dir>/technical_spec.md`: the decisions from your Step 5
research. It is not SQL, not raw query output, and not domain rules.

If the file already exists (a retry), read it. Keep `prebuild_state.md`.
Check each decision that the failure touches against the task, the YML, the
source relations, and the verifier findings. Fix unsupported decisions before
you change SQL. A relation that this attempt created is not original evidence.

Put these sections in the spec:

1. **Build order** at the top: each model in dependency order, with its layer
   (staging, intermediate, mart) and what it depends on.
2. **One plan per model**, with all seven fields:
   - **Source**: `ref('model')` or the raw table. When an upstream model already
     computes a value, use `ref()` of that model. Do not recompute it.
   - **Driving table**: the table in FROM, with its row count from Step 1 or a
     `query_database` COUNT.
   - **Joins**: each join type and its exact keys.
   - **Key expressions**: each computed column. When a sibling or upstream
     model defines it, copy it exactly and name that model and column. The
     Source field must list `ref()` of that model.
   - **Filters**: each WHERE/HAVING, with its reason (a skill rule, the YML, or a
     query result), or "none".
   - **Expected grain**: what one row means.
   - **Expected rows**: from query cardinalities. Do not guess.
3. **Decisions**: one line each: what you chose, why, and the evidence.

Example model plan:

```
## Model: fct_revenue
- Source: ref('int_order_items') - already computes item_total
- Driving table: int_order_items (600K rows)
- Joins: dim_customers ON customer_id = customer_id (LEFT JOIN)
- Key expressions: total_revenue = SUM(item_total) [int_order_items.item_total]
- Filters: status != 'returned' (domain-ecommerce: returns are not revenue)
- Expected grain: one row per customer
- Expected rows: ~75K (query: 75K distinct customers excluding returns)
```

When a verifier reports FAIL, update the spec first: edit the field that
caused the failure, add a decision line, then rewrite the SQL from the spec.

STOP this step when the spec file is written and every model has all seven
fields.

### Step 7 - Write and Build ALL Models
Read `<project_dir>/technical_spec.md` from Step 6. Write SQL for each
model following the spec's build order, sources, joins, and expressions.

For each model in dependency order:
1. Match YML column names EXACTLY where they exist.
2. Copy JOIN types and aggregation patterns from sibling analysis. Before
   finalizing this model, re-check the Step 1 scan's LOOKUP JOINS section and the
   sibling's date/timestamp handling for this model's columns - these two are the
   easiest to skip.
3. Read the YML description for date boundaries. If it says "to the
   current date" or "to today", add `WHERE date_col <= current_date`.
4. Read the YML description for transformation rules. If it states
   explicit logic ("categorized as X if Y"), implement that logic.
5. Write the SQL file.

Do NOT rewrite pre-existing SQL files from scratch. For bug-fix tasks, EDIT the existing SQL minimally - change only the broken expression (e.g., add a CAST, fix an aggregation function). Keep all existing JOINs, CTEs, column aliases, and WHERE clauses intact. Rewriting from scratch drops logic the original author put there (lookup JOINs, filters, aliases) that you may not notice is missing.

After ALL SQL files are written, run `python3 "${CLAUDE_SKILL_DIR}/inspect_model_state.py" "<project_directory>" <model1> <model2>` because inline overrides and incremental guards can change first-build output.
Resolve each `FAIL` before building because it marks an unusable model state.
Review each `REVIEW` or `WARN` against the task, YML, and `dbt_project.yml` because those files establish materialization intent.

Preserve every `ref()`, `source()`, direct-relation expression, source identifier, schema, database, alias, enabled flag, and resolved relation recorded in `prebuild_state.md` unless the verbatim task requests that binding change because a successful empty input is valid project state. Do not redirect a configured source merely to produce rows.

**Estimate every model.** For each model you wrote or changed, built or not, before any query runs its SQL: compile it (`dbt_execute` `compile`) and call `estimate_query_cost` on the compiled SELECT. If it does not fit the 150-second limit, optimize it and estimate again; if you cannot, call `request_query_time_limit`. Record `<model> | <p90> | <fits, optimized, or time requested>` under `## Estimates` in the spec (`technical_spec.md`; in a chat, `analytics-steps.md`).

Build ONLY the models you wrote:
`dbt run --select <model1> <model2> <model3>` (NO `+` prefix).

The `+` prefix rebuilds upstream models you did NOT write, destroying
surrogate key assignments and FK relationships in pre-existing models.
Try without `+` first. If a model fails because an upstream dependency
is not yet materialized, THEN add `+` for that specific model only.

If `dbt run` fails on ANY model - including package models in
`dbt_packages/` - load the dbt-debugging skill and fix the error.
A failed upstream build blocks downstream materialization; a successful zero-row relation does not.

Do NOT run a bare `dbt run` - it rebuilds ALL models including pre-existing ones.

### Step 8 - Verify and Fix
Start only when each model you wrote or changed has a line under `## Estimates`. In a chat, verify before you commit, push, file a suggestion, or open a PR. For a data question, answer first, then verify.

Run `query_database` with `SELECT 1` because verification requires a live connection. Retry the call after a connection error.

Dispatch `verifier` and `value-verifier` in parallel because structure and values require independent evidence. Pass the verbatim task, project directory, connection name, supplied model names, `prebuild_state.md`, and `technical_spec.md`. Do not add expected values, column definitions, SQL interpretations, or preferred fixes beyond the verbatim task and project artifacts because the verifiers must derive their own evidence.

Reject a report whose summary disagrees with its check statuses because contradictory reports cannot authorize changes. Reject a report missing a required per-model status, FAIL recommendation, or NEEDS request because incomplete reports cannot authorize changes. Redispatch a verifier whose report contains `NEEDS` with the requested project or database evidence because incomplete diagnosis cannot authorize changes. Do not edit files while any `NEEDS` remains.

Reproduce each FAIL's cited evidence before changing code because verifier inferences are not implementation authority. Redispatch the responsible verifier with the contrary evidence when the cited result does not reproduce. Re-enter Step 6 when the failure reproduces because `technical_spec.md` must record the supported correction before implementation. Acquire evidence named by a FAIL recommendation in Step 6 before recording the correction because Step 7 cannot choose an unsupported value.

Apply the smallest evidence-backed change in Step 7 because unrelated edits broaden regression risk. Rebuild each changed model with Step 7's existing command. Redispatch both verifiers for every changed model because SQL changes invalidate both reports.

STOP when every applicable check is PASS and each inapplicable check is N/A. Do not modify project files after this condition because verification is complete.

---

## Output Shape - Read YML Description BEFORE Writing SQL

Extract from `description:` field:
- **ENTITY**: "for each customer/driver/order" → one row per qualifying entity
- **QUALIFIER**: "due to returned items" / "with at least one order" → filter or INNER JOIN
- **TEMPORAL SCOPE**: "rolling window", "MoM", "WoW", or "month-over-month" in the
  description → ONE output date (latest), not all historical dates. Filter with
  `WHERE date_col = (SELECT MAX(date_col) FROM source)`.
- **DATE BOUNDARY**: "from X to the current date" or "to today" in the description
  → cap the output with `WHERE date_col <= current_date`. When crossing a calendar
  spine with entities (e.g. one row per guide per day), add the cap to the cross
  join: `ON spine.date_day >= entity.created_on AND spine.date_day <= current_date`.
- **PERIOD-OVER-PERIOD**: If the description mentions MoM, WoW, YoY comparisons
  AND you are writing this model from scratch (stub/missing), the comparison column
  must be `CAST(NULL AS DOUBLE)` - see rule below.

**How to read YML descriptions:** Descriptions tell you what the data MEANS, not
what code to write. Use them to:
- Identify which source columns to use
- Understand the business meaning of each column
- Pick the right aggregation logic

But do NOT treat descriptions as literal computation instructions. After reading
the description, always verify your logic against the actual source data.

Write at top of SQL: `-- EXPECTED SHAPE: <row count or formula> - REASON: <quote>`

## Incremental Models and Period-Over-Period Columns

When a dbt project uses `materialized="incremental"` models, the project is
designed to accumulate state over multiple runs. On a **first run** (full refresh,
no prior state), incremental models build from scratch.

**If you are writing a new model that includes period-over-period metrics
(MoM, WoW, YoY) and the project has not been run incrementally before**:
1. Output rows for the **latest date only**: `WHERE date_col = (SELECT MAX(date_col) FROM source)`
2. Period-over-period columns must be `CAST(NULL AS DOUBLE)` - there is no prior
   aggregated state to compare against.

**This rule overrides sibling patterns.** Even if a sibling model computes
period-over-period values with LAG/LEAD, your new model MUST use
CAST(NULL AS DOUBLE). The sibling is incremental and accumulates history
over multiple runs - your table-materialized model has no prior state.

**Debugging incremental models with missing rows**: inspect the boundary predicate first. If the model uses `WHERE date_col > (SELECT MAX(date_col) FROM {{ this }})`, rows sharing the MAX date are silently dropped - change `>` to `>=` and add a `unique_key` to handle deduplication. Do NOT use `--full-refresh` as a fix - it bypasses the incremental path that must remain correct.

## What to Trust in YML

**Trust YML for**: column names (exact match required), column descriptions (what
each column represents), ref dependencies (what tables to join).

## Google Sheets and CSV Sources

Google Sheets and CSV connectors produce trailing empty rows - entire rows where every column is NULL. When UNION ALL combines multiple sheets, identical empty rows multiply across sources.

Do NOT filter these with `WHERE col IS NOT NULL` - that removes valid rows with partial NULLs. Use `SELECT DISTINCT` after the UNION ALL to collapse identical empty rows to one.

**Do NOT trust YML for**: grain/row count. YML `unique` and `not_null` tests are
assertions that may be aspirational or wrong.

Derive the grain from these signals (in priority order):
1. **Unique key structure**: If the YML defines a unique/surrogate key, examine its composition
2. **Column list**: The columns themselves reveal the grain
3. **Upstream model grain**: Check existing upstream models
4. **Source cardinality**: Query source tables to check expected row count
5. **Sibling model row counts**: Check complete models at the same level

Do NOT pre-deduplicate lookup tables before joining - fan-out from duplicate
keys may be valid data. See dbt-write Section 3 for when fan-out is correct
vs when to deduplicate.

## Validate Project (Standalone)

Run: `python3 "${CLAUDE_SKILL_DIR}/validate_project.py" "<project_dir>"`

This runs `dbt parse` and produces a structured report of errors, warnings,
and orphan patches (yml-defined models with no .sql file). Use this as the
Step 3 validation when the MCP server is not available. Accepts an optional
second argument for timeout in seconds (default 60).

## Rules

- For code-review or multiple-choice analysis tasks: trace every output column back through all CTEs to its source. A computed-but-unused column (calculated but never SELECTed) is a defect. Do not assert a data quality problem without querying the source to confirm it exists.
- NEVER run `dbt` commands with `run_in_background` or `&` - dbt holds a database
  write lock while running
- Do not modify existing `.yml` files unless the task asks or you fix a missing `schema:` in a source definition. Create YAML with a description, column docs, and tests for each new model.
- Do NOT guess column names - use the YML contract as source of truth. Exception: if a pre-existing table or sibling model shows the column contains a display value (name, label) rather than a raw FK, follow that pattern (see dbt-write §3).
- Do NOT install external packages - all dbt packages are pre-bundled in dbt_packages/
