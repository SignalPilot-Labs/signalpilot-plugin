---
name: context
description: "Load before you read, write, or suggest a change to the team's context folder. Covers the folder layout, every file type and its exact format, the save checks, and how to use context in an answer."
---

# Team context

The team keeps what it knows about the data as files in the project's context
folder. The folder is `{context_dir}/` at the repository root (`context/` by
default). In the chat sandbox it is `/workspace/<folder>`. The default branch is
the source of truth. A chat reads the commit it pinned at the start.

## How to use context in an answer

1. Read `README.md` and `AGENT.md` first.
2. Read only the files that apply to the question. Do not read the whole folder.
   Find them by title, `description`, the `People also say:` synonyms, and each
   skill's `when_to_load`. `AGENT.md` often names the file for each question.
3. A context file is documentation, not proof. Read the SQL behind a number and
   check the file against the data before you quote it.
4. When sources disagree:
   - Data and model SQL win over a context file. Say so, and suggest a fix.
   - A specific metric, definition, or skill wins over `AGENT.md`.
   - Do not answer from a metric with `status: retired`.
   - A wrong dbt column description is fixed in the dbt project, not here.
5. A number that rests only on a context file's recipe is never fully
   reconciled. Grade it 🟡 at best.

## File types

The path decides the type. Paths are case-insensitive. A file in the wrong place
is read as another type or as a plain document.

| Path | Type |
|---|---|
| `AGENT.md` | The brief for every chat |
| `README.md` | The folder's own rules for editors |
| `metrics/<topic>/<metric>.yml` | One governed number |
| `metrics/<topic>/_topic.yml` | The shared meaning and traps of one topic |
| `metrics/_definitions/<slug>.yml` | A word or concept that is not one number |
| `skills/<name>/SKILL.md` | A procedure for one kind of question |
| `dashboards/<slug>.dashboard.json` | A reviewed dashboard |
| `evals/<suite>.json`, `evals/prompts/<id>.txt` | Questions the agent must get right |
| Any other `.md` | A note for people. Read it only when `AGENT.md` points to it. |

Use lowercase words joined by hyphens for file and folder names.

### AGENT.md and README.md

- Markdown. No frontmatter and no required headings.
- `AGENT.md`: the business, where the data is (main marts and their grain), the
  rules for most questions, and which file to open for which question. Keep it
  under about 1,500 words (a longer file is a warning). Do not copy the catalog,
  numbers that age, or dbt descriptions. Name the model instead.
- `README.md`: the map of the folder, the format of each type, and the writing
  rules. Follow it before you change any file.

### Metric, topic, and definition files (YAML)

One YAML mapping. The keys must be exactly these, in this order:

| File | Keys, in order |
|---|---|
| Metric | `title`, `owner`, `description`, `ai_context`, `sql_hint` |
| Topic (`_topic.yml`) | `title`, `owner`, `description`, `ai_context` |
| Definition | `title`, `owner`, `description`, `ai_context` |

`status` and `evals` are optional, after the other keys.

- `title`: the name people use, for example `Net revenue`.
- `owner`: a non-empty list. It must include `analytics-eng`. Other known owners
  are `sales-ops`, `finance`, `marketing`, `customer-success`, `revenue-ops`;
  any other value is a warning.
- `description`: one sentence for a person. End it with a full stop.
- `ai_context`: 3 to 6 lines for the agent: meaning, basis, traps. The last line
  starts with `People also say:` and lists 4 to 8 synonyms, separated by commas.
- `sql_hint` (metric only): the SQL that produces the number on this warehouse.
  Use `{{ name }}` placeholders for the period and other inputs. Do not put a
  literal date range in it.
- `status`: `approved` or `retired`. A retired file stays as history.
- `evals` (metric only): a list of questions. Each has `question` (required) and
  optional `params` (values for the placeholders), `gold_value`, `gold_from`,
  `tolerance` (relative, for example `0.005`), `behavior` (for example
  `ask_clarification`), `mentions` (words a behavior answer must contain).

Example metric:

```yaml
title: Net revenue
owner: [analytics-eng, finance]
description: Revenue after discounts and refunds, on the order date.
ai_context: |
  Booked on order_date, not ship date.
  Refunds are subtracted in the month of the original order.
  Excludes marketplace fees.
  People also say: sales, revenue, net sales, turnover, top line
sql_hint: |
  select sum(net_revenue) from analytics.marts.fct_orders
  where order_date between {{ start_date }} and {{ end_date }}
status: approved
```

The metric key is `<topic>/<file name without .yml>`, for example
`sales/net-revenue`.

### Skill files

`skills/<name>/SKILL.md` starts with YAML frontmatter between `---` lines:

- `name`: lowercase letters, digits, and hyphens. Same as the folder name.
- `description`: what the skill teaches, in one line.
- `when_to_load`: the questions that need it.

Other frontmatter keys are allowed and ignored. The body is the procedure.

### Dashboard specs

`dashboards/<slug>.dashboard.json` is SignalPilot dashboard JSON: `version`,
`title`, `datasets` (each `{connection, sql}` or inline `rows`), optional
`filters`, and `charts` (each with `id`, `type`, `title`, `dataset`, and the
fields its type needs). The save check needs only `title`, `datasets`, and
`charts`; the full schema is checked when a chat builds the dashboard. Load the
`signalpilot-dbt:dashboard` skill before you write one.

### Eval questions

`evals/<suite>.json` is one JSON object with a `questions` list (it can be
empty). Optional `name`, `description`, and `defaults.tolerance`. Each question
can have `id` (lowercase with underscores, recommended), `kind` (`query` or
`behavior`), `title`, `question`, `from_metric` (a metric key), `gold_value`,
`gold_from`, `tolerance`, `expect` (`behavior`, `mentions`, `value`), and
`source`. A plain-text file `evals/prompts/<id>.txt` is the question text and
wins over `question`.

## Save checks

SignalPilot checks every changed context file before it saves. Errors block the
save. Warnings do not.

- YAML: does not parse, is not one mapping, keys out of order, `owner` empty or
  without `analytics-eng`, `ai_context` not 3 to 6 lines, last line not
  `People also say:`, `status` not `approved` or `retired`: error.
- YAML: unknown owner, `description` without a full stop, fewer than 4 or more
  than 8 synonyms: warning.
- Skill: no frontmatter, frontmatter does not parse, or `name`,
  `description`, or `when_to_load` missing: error.
- Dashboard: not JSON, or `title`, `datasets`, or `charts` missing: error.
- Evals: not JSON, or `questions` is not a list: error.
- `AGENT.md` over about 1,500 words: warning.

## How context changes

In a data chat, never write to the context folder: the project checkout is
read-only, and a changed file rejects the run. In a Context Studio session,
write the files directly, in the formats above. Context changes through review:

1. You find a missing or wrong context file that slowed you down or made you
   guess. File a `context_file` change in your recommendations (see the
   `recommendations` skill). Give the exact path and the full new file content
   in the right format.
2. An admin opens it in Context Studio. Studio commits to its own branch,
   runs the save checks and the automatic reviewer, and opens a pull request.
3. When the pull request merges to the default branch, new chats read it.

Do not put calculated results or dates that age into a context file.
