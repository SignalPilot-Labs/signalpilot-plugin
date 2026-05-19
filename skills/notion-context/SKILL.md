---
name: notion-context
description: "Gather business context from Notion before dbt builds. Searches pages, extracts definitions/decisions/constraints, writes structured context for the build agent and notion-verify subagent."
---

# Notion Context Skill

Gather business context from Notion using SignalPilot's governed Notion tools.

## 1. Find the Integration

Call `list_notion_integrations` to see all configured Notion integrations. Pick
the integration to use:

- If the user named one in the task instruction, use that.
- If only one Notion integration exists, use it.
- If multiple exist and none was specified, list them and ask the user.
- If none exist, skip — Notion context is optional. Do not block the workflow.

Save the working `integration_name` for all subsequent calls.

## 2. Search

Extract keywords from the task instruction — table names, metric names, business
terms not defined in YML.

```
notion_search
  integration_name: "<name>"
  query: "<keywords>"
```

**No results?** Try in order:
1. Broader keywords ("daily shop orders" -> "orders")
2. Synonyms ("revenue" -> "sales")
3. Individual terms

If still nothing -> write the context file with `No relevant Notion context
found.` (include the `# Integration:` header) and return.

## 3. Fetch and Navigate

For each matching page (up to 5):

```
notion_fetch_page
  integration_name: "<name>"
  page_id: "<id>"
```

**If the page lists child pages but has no content** — it's a container page.
Fetch the child pages that look relevant to the task (by title). Meeting notes
and transcripts are typically one level down from the container.

**If the page has content** — extract from it directly.

## 4. Extract and Tag Context

Scan page content for three categories:

| Category | Signal phrases | Example |
|---|---|---|
| **DEFINITION** | "X means Y", "X is defined as", "X = Y" | "active customer = 1+ orders in 90 days" |
| **DECISION** | "we decided", "agreed to", "going with" | "grain is (shop_id, date)" |
| **CONSTRAINT** | "exclude", "only include", "must filter" | "exclude test orders where source = 'internal'" |

For each item, tag its **relevance** to the current task:

| Tag | Criteria |
|---|---|
| DIRECT | Names a table, column, metric, or filter in the current task |
| RELATED | Same domain but doesn't name specific objects in the task |

Discard items with no connection to the task.

For each kept item record:
- Verbatim excerpt (under 200 chars) or paraphrase
- Source page title and ID
- Category (DEFINITION / DECISION / CONSTRAINT)
- Relevance (DIRECT / RELATED)

Check for **contradictions** between items. If two sources disagree, flag both
with `CONFLICT:`. Do NOT silently pick one.

## 5. Write Context File

Write `notion_context.md` in the working directory:

```
# NOTION CONTEXT
# Integration: <integration_name>
# Task: <task summary>
# Sources: <N> pages searched, <M> items extracted

## DEFINITIONS
- [DEF-1] [DIRECT] "<term>" = <definition>
  Source: <page_title> — https://notion.so/<page_id>

## DECISIONS
- [DEC-1] [DIRECT] <decision statement>
  Source: <page_title> — https://notion.so/<page_id>
- [DEC-2] [RELATED] <decision statement>
  Source: <page_title> — https://notion.so/<page_id>

## CONSTRAINTS
- [CON-1] [DIRECT] <constraint>
  Source: <page_title> — https://notion.so/<page_id>

## CONFLICTS
- <item A> (from <page_A>) vs <item B> (from <page_B>)

## SOURCES CONSULTED
- <page_title> — https://notion.so/<page_id> — <N> items extracted
```

Each item gets a stable ID (DEF-1, DEC-1, CON-1) and a relevance tag (DIRECT /
RELATED). The verify agent uses these to check coverage — DIRECT items that are
missing from SQL are flagged as verification failures.

## 6. Return to Agent

Return DEFINITIONS, DECISIONS, and CONSTRAINTS to the calling agent. The agent
MUST:
- Apply DIRECT items when making grain, join, filter, and column decisions
- Note RELATED items as supporting context
- Write `-- NOTION: [DEF-1] <brief reason>` comments in SQL for every decision
  influenced by Notion context. Use the item ID from the context file.
- Flag CONFLICT items and explain which side was chosen

## Rules

- NEVER fabricate context. No Notion source = no context item.
- NEVER block the workflow on missing context. It's supplementary.
- NEVER silently resolve conflicts. Flag them.
