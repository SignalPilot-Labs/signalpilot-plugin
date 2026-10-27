---
name: recommendations
description: "Chat only. Load in the same message as the verifier subagents, after you send the answer. Covers how to decide if this run found a context gap or a dbt gap, and how to file it with the make_recommendations tool."
type: skill
---

# Recommendations: tell the data team what would make you faster

You just answered a question. Now look back at the run. Decide if a missing
or wrong file in the project's context folder, a missing dbt model, or a
wrong one slowed you down or made you guess.
For each gap you find, file one suggestion with `make_recommendations`. An
admin reviews each suggestion and accepts or rejects it as a whole. Accepted
changes reach the repository through a pull request. Nothing changes until a
person accepts it.

Most runs have no gap. Filing nothing is the normal result. When you find a
gap to file, tell the user in one line before you start on it.

The context folder holds the team's knowledge as files: metric definitions,
rules, skills, dashboard specs, and evals. Its path is in the system prompt.
Its `README.md` says which kind of file goes where and in which format.

## When to recommend

The bar is high for new files: when the context folder and the dbt project
are accurate, almost every run files nothing new. File a new file or model
only when it would make the next similar question much faster or prevent a
wrong answer. Saving one or two queries is not enough.

**Wrong or out-of-date documentation is the exception. Always file it, even
when it is small.** If a context file says something that you proved false
with a query or the SQL, file an `update` (or a `delete`) for it. File it
even when it did not slow you down, and even when another file had the right
fact. A wrong file misleads the next person or agent who reads it. These
fixes are small and quick for an admin to review, so they are the best
suggestions. Examples: a file says a column is always NULL but the data has
values; a file names a table or source that the SQL no longer reads; a count,
date range, or default filter in a file is wrong.

File when one of these is true:

1. A context file misled you. It pointed at the wrong table, column, filter,
   or project, and you had to find the truth yourself.
2. A large part of the run went to finding one fact that a short context file
   could state. For example, most of your queries, or most of the time.
   Examples: which column holds a metric, which filter is the default, what a
   code or a status value means.
3. You made an assumption that no context file, YAML description, or query
   result supported, and a different assumption would change the number.
4. The user corrected you, and the correction is a rule that applies to
   future questions, not only to this one.
5. You rebuilt the same multi-step logic from raw or staging tables that a
   mart would serve directly, and other questions will need the same logic.
6. A model is missing a grain, a key, or a join that the question needed, and
   no existing model can answer it.
7. A context file is wrong or out of date (see above). Always file it.
8. A dbt model is wrong or out of date: you found a bug in its SQL (a
   fan-out, a lost filter, a wrong join or grain), its logic is outdated (it
   still reads a retired source or applies an old business rule) or
   disagrees with the context folder or with what the data shows, or a test
   or YAML description is wrong or out of date. Fix it on a branch and file
   it (see "For a change to the dbt project" below). Always file a proven bug
   fix, even a small one.

Items 1 to 4 and 7 are **context** gaps. Items 5, 6 and 8 are **dbt** gaps.

## When not to recommend

Do not file a suggestion when any of these is true:

- The context folder already covers it. Search the folder first (for example
  with Grep on the metric or column name). If a file exists but is wrong or
  incomplete, recommend an `update` to it, not a new file.
- The gap comes from how the user worded the question.
- The problem is in SignalPilot itself, for example a tool error or a timeout.
- The fact matters only for this one question.
- A new file would save only a little time. (This does not apply to wrong or
  out-of-date files: always fix those.)
- You are not sure the fact is true. Verify it with a query first, or do not
  file it.
- The verifiers found an error in your own work. That is your mistake to
  correct, not a gap.

Recommend a new dbt model rarely. Do it when the time saved is large or the
gap blocks a class of questions. Do not recommend a new model to save one or
two queries. Fixes to existing models (item 8) are different: file every bug
or wrong description you prove.

## How to group changes

One call files one suggestion. One suggestion fixes one gap. An admin accepts
or rejects a whole suggestion, so each suggestion must be one decision.

For each pair of changes, ask this question:

> If the admin accepts one change and rejects the other, is the context
> folder or the project wrong or incomplete?

- If yes, the changes belong in the same suggestion.
- If no, file them as separate suggestions, even if they are about the same
  table or came from the same run.

Changes that belong together:

- A new rule, and an update or a delete for each existing file that the new
  rule makes wrong. This is one suggestion, even with many changes.
- Two files that together explain one metric. Example: the org-wide
  definition and the project file that says which column holds it.
- A new dbt model and the context file that tells agents to use it.

Changes that are separate suggestions:

- Two facts that each stand alone. Example: which column holds net revenue,
  and what the container size codes mean. They share a table, but an admin
  can accept one without the other.
- A context file and a dbt model that fix different problems.
- A fix for an old file that your new rule does not contradict. If you
  noticed that an unrelated file is wrong, file it on its own.

Keep each suggestion as small as the test allows. Do not add a change "while
you are there". A large suggestion is correct only when every change in it
depends on the others.

Most runs have no gap. When a run has more than one gap, file one suggestion
for each gap, at most three in one run. File the most useful one first.

## How to write the call

- `suggestion_title`: a short name for the gap. Example: "Net revenue column
  is not documented".
- `suggestion_description`: two to four plain sentences for a manager who does
  not read SQL. Say what was missing, what it cost this run, and what the
  change makes possible. Do not use table or column names here.
- `evidence`: one factual sentence about this run. Example: "I ran 9 queries
  before I found that net revenue is `net_revenue` on the weekly mart."
- `category`: `context` or `dbt`.

For each context file:

- Use `{"type": "context_file", "action": "create" | "update" | "delete",
  "path": "...", "content": "...", "why": "..."}`.
- `path` is relative to the context folder, for example
  `metrics/sales/net-revenue.yml` or `skills/tableau-weeks/SKILL.md`. Load the
  `signalpilot-dbt:context` skill for where each kind of file goes and its
  exact format, and follow the folder's `README.md`. A file in the wrong
  format fails the save check.
- `content` is the whole new file. For an `update`, read the current file and
  send it in full with your edit, not only the changed lines. Leave it empty
  for `delete`.
- Write the text as instructions to a data agent: what to use, what not to
  use, and the default filters. Keep a new file short.
- To remove a file that describes something that no longer exists, use
  `action: delete` with a `why`.

For a change to the dbt project (a new or changed model, or a fix to a YAML
description, a test, or a doc):

- Make it in `/workspace` and commit it to a `signalpilot/<short-name>`
  branch, then push. Load the `github` skill for the git steps.
- Build changed models with `dbt_execute` first. A description-only change
  needs no build.
- File the branch as one change:
  `{"type": "dbt_branch", "branch": "signalpilot/<short-name>", "reason": "...", "files": [{"path": "...", "why": "..."}]}`.
  The tool reads the diff from the branch; do not paste SQL.
- Write `reason` as one sentence about the problem the change fixes.
- Give one `files` item for each changed file. Each `why` is one sentence:
  what changes in that file and why. Do not repeat the diff.
- After you push more commits to a filed branch, call the tool again with the
  same branch. The suggestion then shows the new diff.
- Keep one gap on one branch. Put a context file that points at the new model
  in the same call.
- Do not open a pull request. The admin creates it from the suggestion.

Wrong or out-of-date YAML descriptions are always worth filing, like wrong
context files: fix the text on a branch and file it, even for a one-line fix.

## After the call

The result names the suggestion number, or an open suggestion that already
covers the same gap. The chat shows the user a card for it, with a Support
button. When you send the one-line follow-up about the verifiers, add one
short sentence that names each suggestion. Example: "I also filed
suggestions #12 and #13 to document the net revenue column and the container
size codes." Do not describe them further in the chat.

If you file nothing, say nothing about it. Do not tell the user that you did
not file a suggestion.

The tool runs the same check that an admin sees on the Suggestions page. A
suggestion that fails it is not filed. Plan for it before the first call:

- Search the context folder for the metric, table, and project your change is
  about. List every file that your change makes wrong, and put the fix for
  each one in the same call. These fixes pass the grouping test: without
  them, the context folder is in conflict.

If the tool returns a list of problems, do not give up and do not reword your
change to get past the check. Resolve every problem:

1. Read each listed file in the context folder.
2. For each file, decide which statement is true for this data. Run a query
   if you are not sure.
3. Add a `context_file` change for each file to the same call. Delete a file
   that describes a table, model, or project that no longer exists.
   Otherwise update it with the full corrected file. If your own change is
   the wrong one, fix or drop it. Fix only what the tool listed. Do not add
   other changes to this suggestion.
4. Call `make_recommendations` again with all the changes.

You may call the tool three times in total for one gap. If it still fails,
stop. If the tool says the check is not available, stop. For any other
error, fix the input once and call again. If it fails again, stop. Do not
tell the user about a failed call.
