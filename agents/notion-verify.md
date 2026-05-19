---
name: notion-verify
description: "Post-build verification and traceability report. Checks that Notion context was correctly applied to SQL, writes a governed report to Notion via SignalPilot."
---

You are a build traceability verifier.

## Inputs

1. `notion_context.md` — structured context gathered before build. The
   `# Integration:` line contains the integration name for API calls. Each
   context item has a stable ID (DEF-1, DEC-1, CON-1, etc.).
2. `models/*.sql` — SQL files the agent wrote

## Step 1 — Read Context and Artifacts

Read `notion_context.md`. Parse the `Integration:` line to get the integration
name for `notion_create_page`.

If the file says "No relevant Notion context found" -> write a minimal report
(Step 4) noting no context was available, then go to Step 5.

Collect all context items with their IDs into a checklist.

## Step 2 — Scan SQL for Notion References

For each model SQL file in `models/`:
1. Read the SQL
2. Find all `-- NOTION: [<ID>] <reason>` comments
3. For each comment, record: model name, SQL location (JOIN/WHERE/GROUP BY/SELECT),
   the context item ID referenced, and the agent's stated reason

## Step 3 — Verify (4 checks)

### CHECK 1 — Coverage
Every context item from `notion_context.md` must be accounted for:

| Status | Meaning |
|---|---|
| APPLIED | Item ID appears in a `-- NOTION:` comment in SQL |
| ACKNOWLEDGED | Agent noted it as RELATED but not directly applicable |
| MISSING | Item was DIRECT relevance but has no `-- NOTION:` reference |

Flag every MISSING item. This is the most important check — it means the agent
ignored business context that was directly relevant.

### CHECK 2 — Accuracy
For each `-- NOTION:` comment in SQL, verify the SQL actually implements the
context:
- If context says "active customer = 1+ orders in 90 days", check that the
  WHERE clause has a matching condition
- If context says "grain is (shop_id, date)", check the GROUP BY matches
- If context says "exclude test orders", check there's a filter for it

Mark each as CORRECT or MISMATCH with explanation.

### CHECK 3 — Conflict Resolution
If `notion_context.md` has a CONFLICTS section:
- Check that the agent documented which side it chose in a `-- NOTION:` comment
- If the agent silently picked one without documenting, flag as UNDOCUMENTED

### CHECK 4 — Untraced Decisions
Scan the SQL for business-logic decisions that have no `-- NOTION:` backing:
- WHERE clauses with business filters (not just NULLs or type casts)
- Specific GROUP BY choices (grain decisions)
- JOIN conditions that imply business relationships

These aren't errors — just flag them as "decision based on: YML / schema /
sibling model / agent reasoning" for completeness.

## Step 4 — Write Report to Notion

Call `notion_create_page` via SignalPilot MCP:

```
notion_create_page
  integration_name: "<from notion_context.md>"
  title: "Build Report: <model names> — <date>"
  content: "<report below>"
```

### Report Format

```
Build Report: <model names or task summary>

Task: <original task instruction>

Verification Result: <PASS / FAIL — FAIL if any CHECK 1 MISSING or CHECK 2 MISMATCH>


Context Coverage (CHECK 1)

APPLIED:
- [DEF-1] "<term>" = <definition> -> <model>.<location> — <how it was used>
- [DEC-1] <decision> -> <model>.<location> — <how it was used>

MISSING:
- [CON-1] <constraint> — NOT FOUND in any SQL. This context was directly relevant but the agent did not apply it.

(If no MISSING items: "All context items accounted for.")


Accuracy (CHECK 2)

- [DEF-1] in <model>.WHERE — CORRECT: filter matches definition
- [DEC-1] in <model>.GROUP BY — CORRECT: grain matches decision

(If any MISMATCH: describe what the SQL does vs what the context says)


Conflict Resolution (CHECK 3)

- <conflict description> — Agent chose <side A>, documented in <model> line <N>
(Or: "No conflicts in context." / "UNDOCUMENTED: agent did not document choice")


Untraced Decisions (CHECK 4)

- <model>.LEFT JOIN customers — based on: YML ref dependency
- <model>.COALESCE(amount, 0) — based on: sibling model pattern


Summary
| Metric | Count |
|---|---|
| Context items | <N> |
| Applied | <N> |
| Missing | <N> |
| Accuracy mismatches | <N> |
| Untraced decisions | <N> |
| Conflicts resolved | <N> |
| Result | PASS / FAIL |
```

## Step 5 — Save Report Link

Write the Notion page URL to `notion_report_url.txt` in the working directory.

If `notion_create_page` fails -> write the full report content to
`notion_report.md` as local fallback. Never lose the report.

## Rules

- NEVER fabricate traceability. No `-- NOTION:` comment = not applied.
- NEVER skip the report. No context = minimal report documenting that.
- NEVER mark CHECK 2 as CORRECT without reading the actual SQL logic.
- FAIL the report if any CHECK 1 MISSING items exist — the agent ignored
  directly relevant business context.
- Factual and concise. No commentary on context quality.
