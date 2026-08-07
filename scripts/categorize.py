#!/usr/bin/env python3
"""
Categorize a Salesforce field-population audit and group by managed-package
namespace. See ../references/categories.md for the thresholds this encodes.

Input: a JSON file containing a list of row objects with at least:
  name, label, type, count_all, pct_all, count_recent, pct_recent, note
(note is "" | "not_aggregatable_via_soql" | "boolean_true_count_only")
Optionally also: description, inlineHelpText (carried through untouched).

Usage:
  python3 categorize.py rows.json categorized.json
"""
import json
import sys
from collections import Counter, defaultdict


def categorize(r):
    if r.get("note") == "not_aggregatable_via_soql":
        return "Needs manual review (unqueryable type)"
    pa = r.get("pct_all")
    pr = r.get("pct_recent")
    if pa is None:
        return "Needs manual review (unqueryable type)"
    if pa == 0:
        return "Dead — 0% populated"
    if pa < 0.1:
        return "Near-dead — <0.1% populated"
    if pr is None:
        return "In use (no recent trend available)" if pa >= 5 else "Low adoption"
    if pa >= 5 and pr < max(1.0, pa * 0.3):
        return "Legacy — declining, rarely set on new records"
    if pa >= 40 or pr >= 40:
        return "Core / actively used"
    if pa < 5 and pr < 5:
        return "Low adoption"
    return "Moderate use"


def namespace_of(name):
    parts = name.split("__")
    if len(parts) >= 3 and parts[-1] == "c":
        return parts[0]
    return None


DEPRECATION_CANDIDATE = {
    "Dead — 0% populated",
    "Near-dead — <0.1% populated",
    "Legacy — declining, rarely set on new records",
}


def main():
    if len(sys.argv) != 3:
        print("usage: categorize.py <rows.json> <categorized_out.json>", file=sys.stderr)
        sys.exit(1)

    rows = json.load(open(sys.argv[1]))
    for r in rows:
        r["category"] = categorize(r)

    cat_counts = Counter(r["category"] for r in rows)
    dep_count = sum(1 for r in rows if r["category"] in DEPRECATION_CANDIDATE)

    packages = defaultdict(list)
    for r in rows:
        ns = namespace_of(r["name"])
        if ns:
            packages[ns].append(r)

    pkg_summary = []
    for ns, items in packages.items():
        flagged = sum(
            1
            for r in items
            if r["category"] in DEPRECATION_CANDIDATE
            or r["category"] == "Needs manual review (unqueryable type)"
        )
        pkg_summary.append(
            {
                "namespace": ns,
                "total_fields": len(items),
                "flagged": flagged,
                "flagged_pct": round(100 * flagged / len(items), 1),
            }
        )
    # Rank by absolute flagged count first — a namespace with 42 dead fields
    # is a bigger finding than a single-field namespace that happens to be
    # 100% dead. Percentage is the tiebreaker, not the primary sort.
    pkg_summary.sort(key=lambda p: (-p["flagged"], -p["flagged_pct"]))

    order = {
        "Dead — 0% populated": 0,
        "Near-dead — <0.1% populated": 1,
        "Legacy — declining, rarely set on new records": 2,
        "Needs manual review (unqueryable type)": 3,
        "Low adoption": 4,
        "Moderate use": 5,
        "In use (no recent trend available)": 6,
        "Core / actively used": 7,
    }
    rows.sort(key=lambda r: (order[r["category"]], -(r.get("pct_all") or -1)))

    out = {
        "total_fields": len(rows),
        "deprecation_candidates": dep_count,
        "deprecation_candidate_pct": round(100 * dep_count / len(rows), 1),
        "category_counts": dict(sorted(cat_counts.items(), key=lambda x: -x[1])),
        "package_summary": pkg_summary,
        "rows": rows,
    }
    json.dump(out, open(sys.argv[2], "w"), indent=1)

    print(f"{len(rows)} fields categorized -> {sys.argv[2]}")
    print(f"deprecation candidates: {dep_count} ({out['deprecation_candidate_pct']}%)")
    for c, n in out["category_counts"].items():
        print(f"  {n:4d}  {c}")
    if pkg_summary:
        print("\npackage namespaces (by % flagged):")
        for p in pkg_summary:
            print(f"  {p['namespace']:20s} {p['flagged']}/{p['total_fields']} flagged ({p['flagged_pct']}%)")


if __name__ == "__main__":
    main()
