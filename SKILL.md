---
name: salesforce-field-audit
description: >
  Audit field usage/population on any Salesforce object — which custom fields
  are populated, at what rate, and which are dead/legacy deprecation
  candidates. Use when asked to "audit fields", "field usage audit", "which
  fields can we deprecate", or similar for a Salesforce object (Account,
  Contact, Opportunity, Lead, custom objects, etc).
---

# salesforce-field-audit

Measures population rate for every custom field on a Salesforce object, splits
it into an all-time rate and a last-12-months rate (to separate fields still
being written to from ones that quietly died), and produces a deprecation
shortlist. Built from a full pass on Account; generalizes to any object.

## Use When

- "Audit the X object" / "field usage audit for X" / "what fields can we
  deprecate on X"
- Cleaning up an object before a data model change, package uninstall, or
  before adding new fields (avoid duplicating something dead)
- Investigating whether a specific integration's fields are still in use

## Requires

A Salesforce MCP connection with `getObjectSchema` and `soqlQuery` tools
(read-only is sufficient — this workflow never writes). If multiple
connections are available (e.g. prod vs sandbox), ask which one.

## First Move — scope questions

Before running anything, confirm with the user (use AskUserQuestion, this
mirrors the choices made for the Account audit):

1. **Which org/connection** to query, if more than one is available.
2. **Field scope** — custom fields only (`__c`, usually the deprecation
   candidates and the fast path) vs. all fields including standard ones.
3. **Record scope** — audit all records as-is, or exclude a known
   inactive/closed/converted state. Inspect the object's schema for an
   obvious status/active/stage field before asking; propose it as the
   recommended option rather than asking blind.

## Workflow

### 1. Pull schema, extract field list

Call `getObjectSchema` for the target object. It comes back large — it will
likely be spilled to a file rather than inlined. Use `jq` to pull just the
field list into a compact JSON file (name, label, type, description,
inlineHelpText, picklistCount), filtered to the field scope from step 0 (e.g.
`select(.name | endswith("__c"))` for custom-only).

Grep field labels/names for status/active/churn/closed-type keywords to find
the record-scope filter field, then confirm its picklist values with a
`GROUP BY` count query before committing to a filter — don't guess which
values mean "inactive."

### 2. Establish scope totals

Two numbers everything else is a percentage of:
- `TOTAL_ALL` — `SELECT COUNT(Id) FROM <Object> WHERE <scope filter>`
- `TOTAL_RECENT` — same filter plus `AND CreatedDate = LAST_N_DAYS:365`

### 3. Chunk fields, fan out agents

Split the field list into chunks of ~50 and write each to its own JSON file.
Spawn one Agent per chunk (foreground, all in one message so they run in
parallel — see `references/agent-prompt-template.md` for the exact prompt to
reuse). Each agent:

- Runs batched `SELECT COUNT(f1) a0, COUNT(f2) a1, ... FROM <Object> WHERE
  <scope>` queries (~15 fields per query) against `TOTAL_ALL`, and again with
  `AND CreatedDate = LAST_N_DAYS:365` against `TOTAL_RECENT`.
- On a batch error, isolates and drops the offending field(s), and tags them
  `not_aggregatable_via_soql` rather than burning retries.
- Returns one pipe-delimited line per field:
  `name|label|type|count_all|pct_all|count_recent|pct_recent|note`

This is the expensive part of the audit — for ~300 fields expect ~6 agents ×
~15 tool calls each. Don't run it serially in the main loop; that's what the
fan-out is for.

### 4. Recover what you can from "not_aggregatable"

SOQL refuses `COUNT()` on long text areas, multi-select picklists, and some
formula/encrypted fields — but **boolean fields in that list are usually
recoverable**: run `SELECT COUNT(Id) FROM <Object> WHERE <scope> AND
<field> = true` for each (aggregate is blocked, but the equality filter
usually isn't). This alone can save 15-20 fields from "unqueryable." True long
text areas, multi-select picklists, and encrypted strings stay flagged —
they need a data export to assess properly.

Verify one or two of these on the live org before trusting the whole batch —
agents sometimes mislabel a field as unaggregatable when the real problem was
a neighbor in the same batch.

### 5. Reassemble and verify coverage

Concatenate all chunk outputs into one file. Before trusting it: diff the set
of field names returned against the original extracted field list. Missing or
duplicated fields mean an agent silently dropped/repeated something — fix
before categorizing, not after.

### 6. Categorize and find package culprits

Run `scripts/categorize.py` on the assembled rows — it applies the category
thresholds (dead / near-dead / legacy-declining / needs-review / low-adoption
/ moderate / core) and groups fields by managed-package namespace (detected
generically from the `Namespace__Field__c` naming pattern, no hardcoded
package list) to surface which integrations are leaving dead fields behind.
See `references/categories.md` for exact thresholds and rationale.

### 7. Report

Run `scripts/render_markdown_report.py` for a findings file the user can keep
in the repo/notes, and (unless the user only asked for the file) build an
Artifact using `scripts/render_html_report.py`'s output as the page — it's a
searchable/sortable/filterable field ledger, not just a static table. Load
`artifact-design` before touching the HTML if you're customizing it further.

## Output Shape

- Lead with the deprecation-candidate count and rate (e.g. "112 of 295 fields,
  38%, are dead/near-dead/legacy").
- Package/namespace culprits ranked by how much of their footprint is dead —
  this is usually the most actionable finding ("uninstall X, it left 42 dead
  fields").
- Full per-field table as a secondary artifact (markdown table if compact
  enough to be useful; HTML ledger if the field count makes a static table
  unwieldy — past ~40-50 rows, prefer the interactive version).
- Flag the unqueryable-type fields as a distinct "needs manual review" bucket,
  not silently dropped and not lumped in with confirmed-dead.

## Anti-Patterns

- Don't compute population % against the whole object with no record-scope
  filter if the object has an obvious active/inactive split — a dead field on
  churned/closed records reads very differently than a dead field org-wide.
- Don't skip the recent-window comparison — an all-time-only pass can't tell
  "used for 5 years, phased out last year" from "actually still core."
- Don't silently drop fields that error out of aggregate queries — recover
  what you can (booleans) and explicitly flag the rest.
- Don't run 300 individual per-field queries in the main conversation loop —
  batch and fan out (steps 3-4); it's both slower and burns context for no
  reason.
