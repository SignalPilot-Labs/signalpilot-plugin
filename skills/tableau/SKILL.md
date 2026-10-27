---
name: tableau
description: "Load when the user asks about Tableau: find, build, copy, edit, redesign, or check a Tableau workbook, dashboard, view, or data source. Covers the tableau_* tools, the .twb builder with its design layer, data sources on SignalPilot connections, the design standard, and the render review."
type: skill
---

# Tableau

The org connected a Tableau site to SignalPilot. The `tableau_*` tools act on
that site. The gateway holds the Tableau token and the warehouse passwords.
You never see them and you must not ask the user for them.

A Tableau workbook is one XML file (`.twb`). A dashboard is part of a
workbook. To change a dashboard, you download the workbook, change the XML,
and publish the workbook again. Workbooks can be large (1 to 15 MB). Do not
read a whole workbook file into your context. Use the scripts in this skill
directory and targeted `grep` or Python edits.

Scripts (Python standard library only). Run them with
`python3 "${CLAUDE_SKILL_DIR}/<script>"`:

| Script | Use it to |
|---|---|
| `twb_inspect.py` | Summarize a workbook: data sources, dashboards, sheets, warnings. Show one sheet or one dashboard in detail. |
| `twb_retarget.py` | Point a workbook at other data: remove extracts, change database servers, change the Tableau site, rename published data source references, replace file sources. |
| `twb_build.py` | Build a workbook from a JSON spec. The contract is `twb_spec.schema.json`. With `"theme": {"name": "sp"}` it uses the design layer (`twb_design.py`, `twb_layout.py`): cards, combo charts, ranked and status bars, styled tables, and a card-grid page. Examples: `examples/team_scorecard.spec.json`, `examples/ae_scorecard.spec.json`. |

Read these files in this skill directory:

| File | When |
|---|---|
| `DESIGN.md` | Before you build or change any dashboard. It is the design standard and the render review checklist. |
| `QUIRKS.md` | When a publish or a render fails, or before you edit workbook XML by hand. |

## Tools

| Tool | What it does |
|---|---|
| `tableau_search` | Find workbooks, views, data sources, and projects by name. |
| `tableau_get_workbook` | Get one workbook: project, URL, views, and connections. |
| `tableau_download_workbook` | Save the workbook `.twb` in `tableau/` and return a short summary. |
| `tableau_publish_workbook` | Publish a `.twb` from your workspace. The gateway adds warehouse credentials to database connections on the SignalPilot connection host. |
| `tableau_publish_datasource` | Publish a live data source on a SignalPilot connection (a table or a SQL query). |
| `tableau_datasource_fields` | List the fields and types of a published data source. |
| `tableau_datasource_connections` | Get a published data source: owner, certification, extract flag, and its database connections (type, server, port, user). |
| `tableau_lineage` | Get lineage from the Metadata API. A data source gives its databases, tables, custom SQL, and the workbooks that use it. A workbook gives its data sources and their tables. A table gives the data sources and workbooks that read it. `fields: true` adds formulas and source columns. |
| `tableau_query_datasource` | Run an aggregate query through Tableau on a published data source. |
| `tableau_view_image` | Render a view or dashboard to PNG. It saves `artifacts/tableau-<name>.png` and returns the path, not the image. Open the file with the Read tool to look at it. |
| `tableau_view_data` | Get the data behind a view as CSV. |
| `tableau_connection_info` | Get the server, port, database, and user name Tableau must use for a SignalPilot connection. No password. |

## Rules

1. Find before you build. Search the site first. If the user names a
   workbook or dashboard, use that one.
2. Render before you change. Before you edit a dashboard, render it with
   `tableau_view_image`. Keep that image to compare.
3. Render after you publish. Render every dashboard you changed or built.
   Open the saved PNG with the Read tool and look at it. Fix empty sheets, errors, and wrong labels before you
   report.
4. Check the numbers. For each headline number, compare
   `tableau_query_datasource` (or `tableau_view_data`) with a SignalPilot SQL
   query on the same model. Report the two values.
5. Data comes from SignalPilot connections. Use the chat's selected
   connection unless the user names another one. Build data sources on dbt
   models (marts) when one fits the question.
6. Edit in place only when the user asks to edit. To edit, publish with the
   same workbook name, the same project, and `overwrite` true. If the user
   asks for a new or copied dashboard, use a new workbook name.
7. Do not delete Tableau content. There is no delete tool.
   The sender's role sets which Tableau projects you can use, for reads and
   for publishing. Content in other projects is hidden. If a call fails
   because of the role, use a project that the error lists, or tell the user
   their role does not include that content. Do not try to work around it.
   The org can also set one project for data sources. Then leave `project`
   empty when you publish a data source, and publish workbooks elsewhere.
8. Never write a password, token, or secret into a file.
9. If a step fails, read the error, fix the cause, and try again. Do not
   report success until the render shows the data.
10. Design is part of the task. Every dashboard you build or change must meet
    `DESIGN.md`. Use the design layer for new pages. Review each render with
    the checklist in `DESIGN.md` and fix what fails before you report.
11. Do not publish a duplicate data source. Before you publish one, list the
    data sources with `tableau_search` (`kind: "datasource"`, empty query).
    For each one with a similar name or on the same tables, get its source
    with `tableau_lineage` (`datasource`).
    - If one reads the same table, or SQL that gives the same rows, on the
      same connection, use it. Do not publish another one.
    - If the name is taken by a data source with a different source, choose a
      new name. Overwrite a data source only when the user asks you to change
      that data source.
    - Tell the user which data source you used, or why you added a new one.
12. Estimate every new data source before you publish it. A live data
    source runs its query on the warehouse each time a dashboard loads. Call
    `estimate_query_cost` with the connection and the data source SQL. For a
    `table` data source, estimate the heaviest query the dashboard needs (the
    aggregate over the table). Do not run the query to test its speed.
    - If the p90 is 2 minutes or less, publish.
    - If the p90 is more than 2 minutes, make the SQL faster and estimate
      again. For example: filter to the dates the page shows, select only the
      columns the page uses, aggregate before you join, and remove joins that
      do not change the numbers. The numbers must stay the same.
    - If the p90 is still more than 2 minutes, do not publish. Tell the user
      that the query is heavy, give the p90, and recommend a dbt mart that
      stores the rollup. Wait for the answer. If the user agrees, build the
      mart and publish the data source on it with `table`. If the user wants
      the direct query, publish it.

## Flow A: edit an existing dashboard

For a small change (a title, a filter, a formula), edit the XML (steps below).
For a redesign, or when the page does not meet `DESIGN.md`, rebuild the page
with the design layer (Flow B) and replace the old dashboard in the same
workbook. Keep every number the old page showed.

1. `tableau_search` with the dashboard or workbook name. Get the workbook.
2. `tableau_view_image` on the dashboard. Keep the image.
3. `tableau_download_workbook`. Then run
   `twb_inspect.py tableau/<file>.twb` for the summary.
4. Run `twb_inspect.py FILE --dashboard "<name>"` to see its sheets. Run
   `twb_inspect.py FILE --worksheet "<sheet>"` to see shelves, filters, and
   formulas of a sheet.
5. Change the XML with a small Python script (read, replace, write). Keep the
   internal data source names and field names. Tableau uses them in every
   shelf. Common edits:
   - Change a title: the `<title>` run text inside `<layout-options>` of the
     worksheet, or a text zone on the dashboard.
   - Change a formula: the `formula` attribute of the `<calculation>` inside
     the `<column caption='...'>` of the data source.
   - Change a filter value: the `member` attributes inside `<filter>`.
   - Change the mark type: `<mark class='Bar' />` in the pane.
   - Add a sheet: build it with `twb_build.py` against the same published data
     source, then copy the `<worksheet>` and `<window>` elements into the
     workbook and add a `<zone name='...'>` to the dashboard.
6. Check that the XML parses:
   `python3 -c "import xml.etree.ElementTree as E; E.parse('FILE')"`.
7. `tableau_publish_workbook` with the same name and project, `overwrite` true.
8. `tableau_view_image` on the dashboard. Compare with the first image.

## Flow B: build a new dashboard on SignalPilot data

1. Find the data in SignalPilot first (dbt models, SQL). List every number the
   page must show. Aggregate in SQL to know the values you expect.
2. Plan the page before you write the spec (see `DESIGN.md`): the header, the
   4 to 6 headline cards, the main comparison charts, a table if the user
   needs detail, and the footer definitions.
3. Publish the data:
   - When cards and charts must agree, publish ONE rollup data source for the
     page: `tableau_publish_datasource` with `sql` that returns one row per
     group and month with every measure. No `WITH` (CTE).
   - Otherwise publish one data source per dbt model with `table`.
4. `tableau_datasource_fields` on each data source. Use the field names and
   types in your spec. Type mapping: STRING string, INTEGER integer, REAL
   real, DATE date, DATETIME datetime, BOOLEAN boolean.
5. Write the spec. Start from `examples/team_scorecard.spec.json`. Keep
   `"theme": {"name": "sp"}`. Use the kinds `card`, `combo`, `ranked_bars`,
   `status_bars`, and `table`, and a dashboard with `header`, `rows`, and
   `footer`. Put period windows in small calculations (month, month last
   year, YTD, last YTD) driven by a Report Month parameter, then sums like
   `SUM(IF [Is YTD] THEN [gm] END)`. More options:
   - Parameters: `parameters`, use them as `[Parameters].[Name]`, filter a sheet
     on a boolean calculation with `values: [true]`, show them in
     `header.controls`.
   - Months: `mname(date_field)`.
   - Integer ids and codes: give the field `"role": "dimension"`.
6. `python3 "${CLAUDE_SKILL_DIR}/twb_build.py" spec.json tableau/<name>.twb`.
7. `tableau_publish_workbook` with a new name. Put it in the project the user
   names, else the default project.
8. Render with `tableau_view_image`. Review it with the checklist in
   `DESIGN.md`. Fix the spec, build, publish, and render again until every
   item passes. Then check the numbers (rule 4).

## Flow C: copy a workbook onto SignalPilot data

Use this when a workbook reads data that SignalPilot does not own (another
server, extracts, spreadsheets).

1. Download and inspect. List each data source by kind.
2. `published` sources: publish a data source on the SignalPilot connection
   for the same table or view (`tableau_publish_datasource`). If the new
   content URL differs, rewrite references with
   `twb_retarget.py IN OUT --published OLD=NEW`. The content URL comes from the
   data source name without spaces and punctuation, for example
   `qryHappyPath (DW)` becomes `qryHappyPathDW`.
3. `database` sources: get the values with `tableau_connection_info`, then
   `twb_retarget.py IN OUT --db-server HOST --db-port PORT --db-username USER
   [--from-server OLD] [--dbname OLD=NEW]`.
4. Sources with extracts: add `--strip-extracts`. A published data source
   with an extract fails to publish until you remove it.
5. `file` sources (Excel, CSV, Google Drive): Tableau Cloud cannot reach the
   user's files. Tell the user. If a SignalPilot model has the same data,
   point the source at it. `--files-to-db SCHEMA.DB` rewrites the source to a
   table and prints the CREATE TABLE statement that table needs.
6. If the workbook moves to another site, add `--site POD SITE`.
7. Publish, render every dashboard, and report which sheets still show no
   data and why.

## Flow D: map Tableau content to SignalPilot data

Use this to find which tables a dashboard reads, which dashboards a table or
dbt model feeds, or to plan a move onto dbt models.

1. To list the published data sources, use `tableau_search` with
   `kind: "datasource"` and an empty query.
2. For one data source, use `tableau_lineage` with `datasource`. For one
   workbook, use `workbook`. The result gives the tables and custom SQL each
   data source reads.
3. To find the content that reads one table, use `tableau_lineage` with
   `table` (`schema.table` or `database.schema.table`). Use the table name
   that the warehouse uses. The match is exact.
4. Use `fields: true` only when you need the formulas or the source columns.
   The answer is much larger.
5. Match each table to a SignalPilot model (dbt `ref` or source) with the
   SignalPilot schema tools. Report the tables that have no model.

New content can take a few minutes to show lineage. If the Metadata API is
off for the site, use `tableau_datasource_connections` and
`twb_inspect.py` instead.

## Errors you can see

See `QUIRKS.md`. If the integration is not enabled, tell the user to turn it
on in Integrations and stop.

## Report

Give the workbook name, the project, and the dashboard URL. Show the rendered
dashboard with `![name](artifacts/tableau-<name>.png)`. List what you changed,
the number checks from rule 4, and the design review items you checked.
