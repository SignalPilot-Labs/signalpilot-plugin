---
name: notebook
description: "Load before you write or run an analysis notebook in chat. Covers the notebook file format, run_notebook, the sp SDK, governed queries, files, and charts."
type: skill
---

# Notebook

A notebook is a Python file in `artifacts/`. You write it with `Write`, change
it with `Edit`, and run it with `run_notebook`. The chat shows the notebook to
the user with the output of each cell. Evidence for an answer comes from your
notebook.

## The file format

A notebook is a marimo file. Each cell is a function with the `@app.cell`
decorator. This is a complete notebook:

```python
import signalpilot as sp

app = sp.App()


@app.cell
def _():
    from sp_env import sp, db, pd, np
    return


@app.cell
def _():
    sp.md("# Gross margin rate, 2024 and 2025")
    return


@app.cell
def _():
    sp.md("Load the monthly margin result from the earlier query")
    return


@app.cell
def _():
    margins = db.result_df("<result_id>")
    print("result monthly margin by year: <result_id>")
    margins
    return


if __name__ == "__main__":
    app.run()
```

Rules for the file:

1. Start the file with `import signalpilot as sp` and `app = sp.App()`. End it
   with the `if __name__ == "__main__":` block.
2. Make the first cell `from sp_env import sp, db, pd, np`. `sp_env` already
   ran `sp.init()` and connected `db` to the chat's connection. Do not call
   `sp.init()` or `sp.connect()` again. Do not import `signalpilot` in a cell.
3. Name each cell function `_`. Leave the parameters empty and write `return`
   with no value. The notebook finds which names each cell reads and defines.
4. Make the second cell a title: `sp.md("# <title of the analysis>")`. Write a
   short title from the user's request.
5. Indent the cell body by four spaces.
6. End each data cell with the DataFrame the user should see (a bare name on
   the last line, like `margins` above). The notebook shows it as a table, and
   the report gives you its rows. Do not print the same table too. End each
   chart cell with the figure. A cell that only prints shows the user plain
   text.

## Cell rules (marimo, not Jupyter)

- Each top-level name is defined in one cell only. A second definition is an
  error. This includes imports: import a module in one cell only.
- A name that starts with `_` is private to its cell. Use it for values that
  only this cell needs: `_fig`, `_ax`, and loop variables. Give a public name
  to a value that a later cell reads.
- A cell runs after every cell that defines a name it reads. Keep the file in
  the same order, so the notebook reads from top to bottom.
- Put one text cell before each code cell. The text cell holds one
  `sp.md("...")` call with a one-line summary of the code cell. Write
  `sp.md("Join invoice lines to accounts for one row per account per month")`.
  Do not write `sp.md("Run a query")`. Do not use a heading mark in a summary.
- Put one query in each cell, with a few derived columns at most. Aggregate in
  SQL. Use Python for ratios and formatting only. Keep a cell under 20 lines.
- `pd` and `np` come from `sp_env`. `plt` does not. Put
  `import matplotlib.pyplot as plt` in one cell before the first chart cell.

## Before you write the first cell

Write every cell of the analysis before you run it. Fixing cells until they
stop failing produces code that runs and answers the wrong question.

Settle these four facts first, from the dbt project and the governed tools:

1. The SQL dialect of the connection. SQL Server takes `YEAR(x)`,
   `select top 10`, and three-part `Database.schema.table` names.
2. The definition of every column you name, from its model SQL. A column that
   sums cleanly can still mean something other than its name.
3. The grain of each mart, so you know when a `GROUP BY` fans out.
4. Which results you already have. Every `query_database` result has an id.
   Load it with `db.result_df("<result_id>")`. Do not run the same SQL again.

## Run the notebook

Call `run_notebook` with the path, for example `artifacts/gross_margin.py`.

1. Every cell runs on each call, in a new Python process. Nothing stays in
   memory between calls. A re-run is fast when cells load saved results with
   `db.result_df(id)`. A cell that runs `db.query_df(sql)` queries again.
2. The report starts with one line: the cell count and how many cells are ok,
   failed, or skipped. Then each cell has a status line:
   `[3] failed: <first line of the cell>`.
3. Under a cell, the report shows its `error`, its `printed` text, and its
   `displayed` value (the last expression of the cell).
4. A `skipped` cell did not run because a cell before it failed. Fix the
   failed cell. The skipped cell then runs.
5. To fix a cell, change it with `Edit` and call `run_notebook` again. Fix
   every failed cell before you run again.
6. Pass `cells` (cell numbers or names) to see only those cells in full.
   Failed cells are always in full.
7. Pass `timeout_seconds` for a slow notebook. The default is 300 seconds.

## What you see of a cell output

The report never hides a cut. Know the three places where the report shows
less than the full output.

### 1. A displayed table holds up to 50 rows

When a cell ends with a DataFrame, the notebook shows an interactive table to
the user and saves up to 50 rows. A table of 50 rows or fewer is complete:

```
table: 12 rows x 5 columns. Complete: every row is below, and the user sees the same table.
```

Read it from the report. Do not print it again. A bigger table is a preview:

```
table: 240 rows x 5 columns. The preview below shows 50 of 240 rows. It is NOT the full table: print the values you need.
```

The other rows are not in the report. Do not read a claim about the whole
table from a preview. Aggregate it, or print the rows you need.

### 2. Long text is cut with a marker

Printed text and displayed text keep their first 6,000 characters in each
cell. A cut ends with:

```
[cut: showing the first 6,000 of 18,230 characters. Read <file> for the rest.]
```

The whole report keeps its first 40,000 characters. The full report, with no
cuts, is always in the file on the second line of the report. Read that file
with `Read` when you need the rest.

### 3. A query result can be cut by its row limit

`db.query_df(sql)` returns at most `row_limit` rows (default 1,000). The
DataFrame is then incomplete. Use `db.query_result(sql)` to see
`completeness`, or aggregate in SQL.

### What is safe to read

- A number that you print: `print(len(df))`, a sum, a count, a min, or a max.
- A displayed table that the report marks as complete.
- A slice of a big table that you print: `print(df.head(80).to_string(index=False))`.
  Print only the columns you need.
- An `assert` in a check cell. If the claim is false, the cell fails and you
  see the error.

## Check a claim before you write it

1. Before you write a claim with "only", "all", "none", "every", "highest",
   "lowest", "first", or "last", add a check cell. The check cell filters the
   full DataFrame to the rows that the claim is about. Then it prints the
   count and those rows:

   ```python
   _declined = monthly_yoy[monthly_yoy["yoy_pct"] < 0]
   print(len(_declined), "months declined")
   print(_declined[["month_name", "yoy_pct"]].to_string(index=False))
   ```

2. Compare the printed count and rows with the claim. "Only March declined"
   needs a count of 1 and the row for March. If they do not agree, change the
   claim, not the check.
3. Every number and every named row in the answer must come from text that
   you printed and read in full.

## The sp SDK

| Call | Result |
|---|---|
| `db.result_df(result_id)` | **Use first.** A saved `query_database` result as a typed DataFrame. No query runs. |
| `db.result(result_id)` | The same saved result as a list of row dicts. |
| `db.query_df(sql, row_limit=1000)` | Runs a new query. A typed DataFrame. Its id is `df.attrs["result_id"]`. |
| `db.query(sql, row_limit=1000)` | Rows as a list of dicts. Call `.df()` to get a DataFrame. |
| `db.query_result(sql, row_limit=100_000)` | Dict with `rows`, `columns`, and `completeness`. |
| `sp.connections()` | Names of the connections you may query. |
| `sp.artifact_path("name.png")` | The path for one artifact file. |
| `sp.dashboard_dataset(name, connection=..., sql=...)` | Runs the SQL and writes a dashboard snapshot. See the `signalpilot-dbt:dashboard` skill. |

Rules:

- For every query that a cell runs or loads, print one line:
  `result <what it shows>: <result_id>`. Cite that id in the answer as
  `![what it shows](queries/<result_id>)`.
- Do not write your own query helper. Do not convert column types by hand.
  `db.query_df` and `db.result_df` already return typed columns.
- Every query goes through `db`. Never open a warehouse connection from
  `Bash`, a driver, or a script. The data plane is read-only.
- Write SQL in the dialect of the connection.
- Do not copy MCP row previews into a DataFrame. Load the result by its id.
- `Gateway error (HTTP 400): Query blocked` means governance refused the SQL.
  Read the reason. Fix the SQL. Do not work around it.

## Files

- `sp.artifact_path("name.png")` returns the path for a deliverable and makes
  its directory. Pass it to `savefig`, `to_csv`, or `open`.
- Saving a file makes it exist. Only a reference shows it. Reference it once,
  on its own line, under the finding it supports: an image as
  `![alt](artifacts/name.png)`, any other file as
  `[Download name.ext](artifacts/name.ext)`.
- Working notes (`analytics-steps.md`, `prebuild-state.md`) go to
  `$SP_CHAT_SCRATCH_DIRECTORY`, not to `artifacts/`.
- Use short lowercase file names with underscores.
- Notebooks from earlier turns in the conversation are still in `artifacts/`.
  Edit a notebook to change its analysis. Do not start a second notebook for
  the same analysis.

## Charts

1. Make charts with matplotlib in the notebook. The house theme is already
   applied. Do not set colors, fonts, or a style.
2. Put one chart in each cell, one finding in each chart, and one axis in each
   figure. Add a title, axis labels with units, and a legend for more than one
   series.
3. Save with `_fig.savefig(sp.artifact_path("revenue_by_month.png"))`. Do not
   pass `dpi`, `facecolor`, or `bbox_inches`. Then end the cell with `_fig`, so
   the notebook shows the chart as well as saving it.
4. You cannot see the image. Check the data first: x values sorted, 8 series or
   fewer, 24 categories or fewer, no null values.
5. Never draw charts with block characters, ASCII, or emoji.

## Tables and reports

- A table the user will reuse:
  `df.to_csv(sp.artifact_path("name.csv"), index=False)`.
- A long analysis can also save `artifacts/report.md`. The chat answer is
  still the full answer.

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `The variable 'x' was defined by another cell` | Two cells define one name. | Rename one of them, or prefix it with `_` when only that cell uses it. |
| `The file is not a valid notebook` | The file is not in the marimo format. | Start the file with `import signalpilot as sp` and `app = sp.App()`, and decorate each cell with `@app.cell`. |
| `NameError` for `db`, `sp`, `pd`, or `np` | The first cell does not import `sp_env`. | Make the first cell `from sp_env import sp, db, pd, np`. |
| `NameError: name 'plt' is not defined` | `plt` is not imported. | Add one cell with `import matplotlib.pyplot as plt`. |
| `Query blocked: SQL parse error` | The SQL is not valid in the connection dialect. | Fix the SQL for that dialect. |
| `completeness: "truncated"` | The row limit cut the result. | Aggregate in SQL or raise `row_limit`. |
| `did not finish in 300 s` | A slow cell. | Load saved results by id, aggregate in SQL, or pass `timeout_seconds`. |
