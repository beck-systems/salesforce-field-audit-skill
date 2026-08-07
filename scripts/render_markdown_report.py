#!/usr/bin/env python3
"""
Render a findings.md from a categorize.py output file.

Usage:
  python3 render_markdown_report.py categorized.json out.md \
      --object Account --org "Production" --date 2026-08-06 \
      --scope-filter "Account_Status__c NOT IN ('Rejected','Churned')" \
      --total-all 50000 --total-recent 8000 --total-org 52000 \
      [--top 60]

--top caps how many individual field rows go into the markdown table (the
full set still lives in categorized.json / the HTML artifact) — markdown
tables get unreadable past ~50-60 rows. Rows are already sorted worst-first
by categorize.py, so the cap keeps the highest-signal ones.
"""
import argparse
import json


def pct(v):
    return "—" if v is None else f"{v:.2f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("categorized_json")
    ap.add_argument("out_md")
    ap.add_argument("--object", required=True)
    ap.add_argument("--org", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--scope-filter", default="")
    ap.add_argument("--total-all", type=int, required=True)
    ap.add_argument("--total-recent", type=int, required=True)
    ap.add_argument("--total-org", type=int, default=None)
    ap.add_argument("--top", type=int, default=80)
    args = ap.parse_args()

    data = json.load(open(args.categorized_json))
    rows = data["rows"]
    pkgs = data["package_summary"]

    lines = []
    lines.append(f"# {args.object} Object Field Audit")
    lines.append("")
    meta_bits = []
    if args.org:
        meta_bits.append(f"**Org:** {args.org}")
    if args.date:
        meta_bits.append(f"**Date:** {args.date}")
    meta_bits.append(f"**Custom fields audited:** {data['total_fields']}")
    if meta_bits:
        lines.append("  \n".join(meta_bits))
        lines.append("")

    lines.append("## Scope")
    lines.append("")
    if args.scope_filter:
        lines.append(f"- Record filter: `{args.scope_filter}`")
    lines.append(f"- In-scope records (all-time): **{args.total_all:,}**"
                  + (f" of {args.total_org:,} total" if args.total_org else ""))
    lines.append(f"- In-scope records created in the last 365 days: **{args.total_recent:,}**")
    lines.append("- Population % is computed against these two denominators; "
                  "the recent figure isolates whether a field is still being "
                  "written to on new records.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"**{data['deprecation_candidates']} of {data['total_fields']} fields "
                  f"({data['deprecation_candidate_pct']}%) are deprecation candidates** "
                  "(dead, near-dead, or legacy/declining).")
    lines.append("")
    lines.append("| Category | Fields |")
    lines.append("|---|---:|")
    for c, n in data["category_counts"].items():
        lines.append(f"| {c} | {n} |")
    lines.append("")

    if pkgs:
        lines.append("## Managed-package culprits")
        lines.append("")
        lines.append("Fields grouped by namespace (`Namespace__Field__c`), ranked by "
                      "share flagged dead/near-dead/legacy/unqueryable. A namespace "
                      "where most of its footprint is flagged usually means a "
                      "decommissioned integration still leaving fields behind.")
        lines.append("")
        lines.append("| Namespace | Fields on object | Flagged | % flagged |")
        lines.append("|---|---:|---:|---:|")
        for p in pkgs:
            lines.append(f"| `{p['namespace']}` | {p['total_fields']} | {p['flagged']} | {p['flagged_pct']}% |")
        lines.append("")

    shown = rows[: args.top]
    lines.append(f"## Field ledger{' (top ' + str(len(shown)) + ' by severity, see full data file for the rest)' if len(rows) > len(shown) else ''}")
    lines.append("")
    lines.append("| Field | API Name | Type | % Populated (all) | % Populated (recent) | Status |")
    lines.append("|---|---|---|---:|---:|---|")
    for r in shown:
        label = r["label"].replace("|", "\\|")
        desc = (r.get("description") or r.get("inlineHelpText") or "").strip().replace("|", "\\|").replace("\n", " ")
        cell = f"{label}<br><sub>{desc[:120]}</sub>" if desc else label
        lines.append(
            f"| {cell} | `{r['name']}` | {r['type']} | {pct(r.get('pct_all'))} | "
            f"{pct(r.get('pct_recent'))} | {r['category']} |"
        )
    lines.append("")

    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md} ({len(shown)}/{len(rows)} field rows included)")


if __name__ == "__main__":
    main()
