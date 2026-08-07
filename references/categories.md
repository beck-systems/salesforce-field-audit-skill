# Category thresholds

Applied in this order (first match wins) by `scripts/categorize.py`. `pa` =
pct_all, `pr` = pct_recent (may be `None` for boolean-fallback rows).

| Category | Condition | Meaning |
|---|---|---|
| Needs manual review (unqueryable type) | `note == not_aggregatable_via_soql` after the boolean-recovery pass | textarea / multipicklist / encryptedstring SOQL can't touch — needs a data export to assess |
| Dead — 0% populated | `pa == 0` | never set, in scope, ever |
| Near-dead — <0.1% populated | `0 < pa < 0.1` | a handful of records, statistically dead |
| In use (no recent trend available) | `pr is None and pa >= 5` | boolean-fallback rows only — can't check recency, but clearly not dead |
| Legacy — declining, rarely set on new records | `pa >= 5 and pr < max(1.0, pa * 0.3)` | populated historically, all but stopped being set on new records — the "quietly deprecated" case a single all-time number can't catch |
| Core / actively used | `pa >= 40 or pr >= 40` | |
| Low adoption | `pa < 5 and pr < 5` (or boolean-fallback with `pa < 5`) | niche/optional field, still trickles in — not a deprecation candidate on its own, but worth a product owner sanity check |
| Moderate use | everything else | |

## Why the recent-window comparison matters

A field at 45% all-time population looks healthy in isolation. If the same
field is at 2% among records created in the last 12 months, it's actually
"Legacy" — something (a form, an integration, a process) that used to set it
stopped, and the all-time number is propped up by old records that will
eventually roll off. This is usually the more actionable finding than raw
"Dead" fields, because it points at a *recent* process change worth asking
about, not just historical debt.

## Package/namespace grouping

A managed-package field's API name is `Namespace__FieldName__c` — splitting
on `__` gives 3 segments (`[Namespace, FieldName, c]`) vs. 2 for a native
custom field (`[FieldName, c]`). `scripts/categorize.py` uses this split
directly rather than a hardcoded namespace list, so it works unmodified on
orgs with different installed packages. Group by namespace, then rank by
`% of that namespace's fields on this object that are Dead/Near-dead/Legacy/
Needs-review` — a namespace where the majority of its footprint is dead is
usually a decommissioned integration, and is a stronger, more actionable
finding than any single dead field.
