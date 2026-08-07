# Chunk-agent prompt template

Reuse this verbatim per chunk (swap the bracketed values), and send all chunk
agents in a single message with `run_in_background: false` so they execute in
parallel and you get every result back in this turn.

```
You are auditing custom field usage on the Salesforce [OBJECT] object
([ORG LABEL, e.g. "production org"], via the "[MCP CONNECTION NAME]" MCP
connection — tools named mcp__[...]__*, e.g. soqlQuery).

Read the field metadata list at: [CHUNK FILE PATH]
It's a JSON array of objects: {name, label, type, description, inlineHelpText,
picklistCount}. These are the fields you must audit — no others.

Scope: only count records where [SCOPE FILTER, e.g. Account_Status__c NOT IN
('Rejected','Churned')]. Two known totals for that scope (already computed,
do not re-derive):
- TOTAL_ALL = [N] (all in-scope records)
- TOTAL_RECENT = [N] (in-scope records with CreatedDate in the last 365 days,
  i.e. add "AND CreatedDate = LAST_N_DAYS:365" to the same filter)

For every field in your chunk, get:
1. count_all = COUNT(field) over the ALL scope
2. count_recent = COUNT(field) over the RECENT scope

Use SOQL aggregate queries to do this efficiently in batches, NOT one query
per field. Example batch query pattern (use short aliases a0, a1, a2... in
the SAME ORDER as the fields you list, so you can map results back
positionally):
SELECT COUNT(Field_One__c) a0, COUNT(Field_Two__c) a1, COUNT(Field_Three__c) a2
FROM [OBJECT] WHERE [SCOPE FILTER]

Batch ~15 fields per query. Run one batch query for the ALL scope and one for
the RECENT scope (add the CreatedDate condition) per group of ~15 fields.

IMPORTANT — some field types (long text area / rich text = "textarea",
multi-select picklist = "multipicklist", and sometimes encrypted string) are
NOT filterable/aggregatable in SOQL and will make the WHOLE batch query fail
with a MALFORMED_QUERY error. If a batch fails:
- Retry the batch after removing the field(s) most likely responsible (start
  with any textarea/multipicklist/encryptedstring typed fields in that batch,
  remove one at a time if needed).
- For any field you cannot get a count for this way, mark it with note
  "not_aggregatable_via_soql" and still report its type — don't spend
  excessive retries, just isolate and move on after 2-3 attempts.

For every field compute pct_all = round(100*count_all/[TOTAL_ALL], 2) and
pct_recent = round(100*count_recent/[TOTAL_RECENT], 2). If a field is
not_aggregatable, leave counts/pcts null and just note the type.

Return ONLY a compact pipe-delimited text block, one line per field, no
prose, no markdown table, in this exact format (one header line then data
lines):
name|label|type|count_all|pct_all|count_recent|pct_recent|note

Use empty string for missing note. This must cover ALL fields in the chunk
file — do not skip any. Keep your final answer to just this data block,
nothing else.
```

## Recovering "not_aggregatable" boolean fields

After all chunks return, pull out every row where `note ==
not_aggregatable_via_soql` and `type == boolean`. For each, run directly
(not delegated — this is cheap and worth doing yourself):

```sql
SELECT COUNT(Id) FROM [OBJECT] WHERE [SCOPE FILTER] AND [Field__c] = true
```

That gives `count_all` (no recent split — not worth the extra query volume
for a handful of formula/managed-package checkboxes). Note these rows as
`boolean_true_count_only` so the report doesn't imply a recent-trend was
checked.

Spot-check 2-3 of the *non-boolean* `not_aggregatable` fields yourself with a
raw `COUNT()` query before trusting the label — agents occasionally blame the
wrong field in a batch and give up on something that was actually fine.
