#!/usr/bin/env python3
"""
Render a self-contained, searchable/sortable/filterable HTML field-ledger
report from a categorize.py output file. Publish the result with the
Artifact tool (load the artifact-design skill first if you plan to restyle
rather than just re-run this as-is).

Usage:
  python3 render_html_report.py categorized.json out.html \
      --object Account --org "Production" \
      --scope-filter "Account_Status__c NOT IN ('Rejected','Churned')" \
      --total-all 50000 --total-recent 8000 --total-org 52000 \
      [--max-packages 10]
"""
import argparse
import html
import json

CSS = r"""
:root{
  --bg:#EEF1EE; --bg-raised:#FFFFFF; --bg-sunken:#E4E8E3;
  --text:#12151A; --text-dim:#54595E; --text-faint:#7A7F84;
  --border:#D5DAD4; --border-strong:#BFC5BE;
  --accent:#3B5BA5; --accent-soft:#E4E9F3; --accent-text:#2A4680;
  --critical:#A8402F; --critical-soft:#F5E1DD;
  --warning:#9C6B10; --warning-soft:#F6EAD2;
  --good:#2F6B4C; --good-soft:#DFEEE5;
  --neutral:#5D6167; --neutral-soft:#E6E7E8;
  --shadow: 0 1px 2px rgba(20,20,15,0.06), 0 6px 20px -8px rgba(20,20,15,0.12);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#131619; --bg-raised:#1A1E22; --bg-sunken:#0F1214;
    --text:#E7E9E4; --text-dim:#A6ABA6; --text-faint:#7C8280;
    --border:#2B3034; --border-strong:#3A4045;
    --accent:#8CA3DE; --accent-soft:#232C3E; --accent-text:#AFC0EA;
    --critical:#DE8B7B; --critical-soft:#332320;
    --warning:#D8B36C; --warning-soft:#332A19;
    --good:#8FC3A6; --good-soft:#1C2B23;
    --neutral:#A2A7AB; --neutral-soft:#25282B;
    --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 24px -8px rgba(0,0,0,0.5);
  }
}
:root[data-theme="dark"]{
  --bg:#131619; --bg-raised:#1A1E22; --bg-sunken:#0F1214;
  --text:#E7E9E4; --text-dim:#A6ABA6; --text-faint:#7C8280;
  --border:#2B3034; --border-strong:#3A4045;
  --accent:#8CA3DE; --accent-soft:#232C3E; --accent-text:#AFC0EA;
  --critical:#DE8B7B; --critical-soft:#332320;
  --warning:#D8B36C; --warning-soft:#332A19;
  --good:#8FC3A6; --good-soft:#1C2B23;
  --neutral:#A2A7AB; --neutral-soft:#25282B;
  --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 24px -8px rgba(0,0,0,0.5);
}
:root[data-theme="light"]{
  --bg:#EEF1EE; --bg-raised:#FFFFFF; --bg-sunken:#E4E8E3;
  --text:#12151A; --text-dim:#54595E; --text-faint:#7A7F84;
  --border:#D5DAD4; --border-strong:#BFC5BE;
  --accent:#3B5BA5; --accent-soft:#E4E9F3; --accent-text:#2A4680;
  --critical:#A8402F; --critical-soft:#F5E1DD;
  --warning:#9C6B10; --warning-soft:#F6EAD2;
  --good:#2F6B4C; --good-soft:#DFEEE5;
  --neutral:#5D6167; --neutral-soft:#E6E7E8;
  --shadow: 0 1px 2px rgba(20,20,15,0.06), 0 6px 20px -8px rgba(20,20,15,0.12);
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{
  background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5; -webkit-font-smoothing:antialiased; overflow-x:hidden;
}
.wrap{max-width:1160px; margin:0 auto; padding:0 24px 96px;}
header.masthead{padding:56px 0 32px; border-bottom:1px solid var(--border); margin-bottom:40px;}
.eyebrow{font-size:12.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--accent-text); font-weight:600; margin:0 0 14px; display:flex; align-items:center; gap:10px;}
.eyebrow::before{content:""; width:7px; height:7px; border-radius:50%; background:var(--accent); display:inline-block;}
h1{font-family:Georgia,'Iowan Old Style','Palatino Linotype','Book Antiqua',serif; font-size:clamp(30px,4vw,44px); line-height:1.08; margin:0 0 14px; font-weight:600; text-wrap:balance; letter-spacing:-0.01em;}
.dek{font-size:16.5px; color:var(--text-dim); max-width:640px; margin:0 0 20px;}
.meta-row{display:flex; flex-wrap:wrap; gap:22px; font-size:13px; color:var(--text-faint); font-variant-numeric:tabular-nums;}
.meta-row span b{color:var(--text-dim); font-weight:600;}
.stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px; background:var(--border); border:1px solid var(--border); border-radius:10px; overflow:hidden; margin-bottom:44px;}
.stat{background:var(--bg-raised); padding:20px 18px;}
.stat .n{font-family:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace; font-size:28px; font-weight:600; letter-spacing:-0.02em; font-variant-numeric:tabular-nums; display:block; margin-bottom:4px;}
.stat .l{font-size:12.5px; color:var(--text-faint); line-height:1.3;}
.stat.crit .n{color:var(--critical);} .stat.warn .n{color:var(--warning);} .stat.good .n{color:var(--good);} .stat.neu .n{color:var(--neutral);}
section{margin-bottom:52px;}
.section-head{display:flex; align-items:baseline; justify-content:space-between; gap:16px; margin-bottom:6px; flex-wrap:wrap;}
h2{font-family:Georgia,'Iowan Old Style','Palatino Linotype','Book Antiqua',serif; font-size:22px; font-weight:600; margin:0; letter-spacing:-0.005em;}
.section-note{font-size:13.5px; color:var(--text-faint); margin:0 0 22px; max-width:680px;}
.pkg-list{display:flex; flex-direction:column; gap:10px;}
.pkg-row{display:grid; grid-template-columns:150px 1fr 96px; align-items:center; gap:16px; background:var(--bg-raised); border:1px solid var(--border); border-radius:8px; padding:12px 16px;}
.pkg-name{font-family:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace; font-size:13.5px; font-weight:600; color:var(--text);}
.pkg-bar-track{height:8px; border-radius:5px; background:var(--neutral-soft); overflow:hidden; display:flex;}
.pkg-bar-fill{height:100%; background:var(--critical);}
.pkg-stat{font-size:12.5px; color:var(--text-dim); text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap;}
.pkg-stat b{color:var(--text); font-weight:600;}
.toolbar{display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:16px; position:sticky; top:0; z-index:5; background:var(--bg); padding:12px 0; border-bottom:1px solid var(--border);}
#search{flex:1 1 220px; min-width:180px; max-width:320px; padding:9px 12px; border-radius:7px; border:1px solid var(--border-strong); background:var(--bg-raised); color:var(--text); font-size:13.5px;}
#search:focus{outline:2px solid var(--accent); outline-offset:1px;}
.pill{border:1px solid var(--border-strong); background:var(--bg-raised); color:var(--text-dim); font-size:12.5px; padding:6px 12px; border-radius:999px; cursor:pointer; white-space:nowrap; font-weight:500; transition:background .12s,color .12s,border-color .12s;}
.pill:hover{border-color:var(--accent);}
.pill:focus-visible{outline:2px solid var(--accent); outline-offset:1px;}
.pill.active{background:var(--accent); border-color:var(--accent); color:#fff;}
.count-line{font-size:12.5px; color:var(--text-faint); margin-left:auto; white-space:nowrap; font-variant-numeric:tabular-nums;}
.table-scroll{overflow-x:auto; border:1px solid var(--border); border-radius:10px; background:var(--bg-raised); box-shadow:var(--shadow);}
table{width:100%; border-collapse:collapse; min-width:880px;}
thead th{position:sticky; top:49px; background:var(--bg-sunken); z-index:3; text-align:left; font-size:11.5px; text-transform:uppercase; letter-spacing:.05em; color:var(--text-faint); font-weight:600; padding:10px 14px; border-bottom:1px solid var(--border); cursor:pointer; user-select:none; white-space:nowrap;}
thead th:hover{color:var(--text);}
thead th.num{text-align:right;}
thead th .arrow{font-size:10px; margin-left:4px; opacity:.5;}
tbody td{padding:10px 14px; border-bottom:1px solid var(--border); font-size:13.5px; vertical-align:top;}
tbody tr:hover{background:var(--bg-sunken);}
tbody tr:last-child td{border-bottom:none;}
td.num{text-align:right; font-family:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace; font-variant-numeric:tabular-nums; white-space:nowrap;}
.fname{font-weight:600; font-size:13.5px;}
.fapi{display:block; font-family:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace; font-size:11.5px; color:var(--text-faint); margin-top:2px;}
.fdesc{color:var(--text-dim); font-size:12.5px; max-width:320px; display:block; margin-top:3px; line-height:1.35;}
.ftype{color:var(--text-faint); font-size:12px; font-family:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace;}
.chip{display:inline-block; font-size:11px; font-weight:600; padding:3px 9px; border-radius:999px; white-space:nowrap; letter-spacing:.01em;}
.chip.crit{background:var(--critical-soft); color:var(--critical);}
.chip.warn{background:var(--warning-soft); color:var(--warning);}
.chip.good{background:var(--good-soft); color:var(--good);}
.chip.neu{background:var(--neutral-soft); color:var(--neutral);}
.chip.acc{background:var(--accent-soft); color:var(--accent-text);}
.dash{color:var(--text-faint);}
.empty-msg{padding:40px; text-align:center; color:var(--text-faint); font-size:13.5px;}
footer.methodology{border-top:1px solid var(--border); padding-top:24px; margin-top:8px; font-size:12.5px; color:var(--text-faint); line-height:1.6; max-width:760px;}
footer.methodology h3{font-size:13px; text-transform:uppercase; letter-spacing:.05em; color:var(--text-dim); margin:0 0 8px; font-weight:600;}
footer.methodology p{margin:0 0 10px;}
footer.methodology ul{margin:0 0 10px; padding-left:18px;}
@media (max-width:640px){ .pkg-row{grid-template-columns:110px 1fr 76px; gap:10px; padding:10px 12px;} .stats{grid-template-columns:repeat(2,1fr);} }
"""

CHIP_CLASS = {
    "Dead — 0% populated": "crit",
    "Near-dead — <0.1% populated": "crit",
    "Legacy — declining, rarely set on new records": "warn",
    "Needs manual review (unqueryable type)": "neu",
    "Low adoption": "neu",
    "Moderate use": "acc",
    "Core / actively used": "good",
    "In use (no recent trend available)": "acc",
}
CHIP_LABEL = {
    "Dead — 0% populated": "Dead",
    "Near-dead — <0.1% populated": "Near-dead",
    "Legacy — declining, rarely set on new records": "Legacy",
    "Needs manual review (unqueryable type)": "Needs review",
    "Low adoption": "Low adoption",
    "Moderate use": "Moderate",
    "Core / actively used": "Core",
    "In use (no recent trend available)": "In use",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("categorized_json")
    ap.add_argument("out_html")
    ap.add_argument("--object", required=True)
    ap.add_argument("--org", default="")
    ap.add_argument("--scope-filter", default="")
    ap.add_argument("--total-all", type=int, required=True)
    ap.add_argument("--total-recent", type=int, required=True)
    ap.add_argument("--total-org", type=int, default=None)
    ap.add_argument("--max-packages", type=int, default=10)
    args = ap.parse_args()

    data = json.load(open(args.categorized_json))
    rows = data["rows"]
    pkgs = data["package_summary"][: args.max_packages]

    cc = data["category_counts"]
    dead_n = cc.get("Dead — 0% populated", 0)
    review_n = cc.get("Needs manual review (unqueryable type)", 0)
    core_n = cc.get("Core / actively used", 0)

    compact_rows = [
        [
            r["name"], r["label"], r["type"],
            r.get("count_all"), r.get("pct_all"), r.get("count_recent"), r.get("pct_recent"),
            r["category"],
            (r.get("description") or r.get("inlineHelpText") or "").strip()[:180],
        ]
        for r in rows
    ]
    pkg_data = [
        {"name": p["namespace"], "total": p["total_fields"], "flagged": p["flagged"], "pct": p["flagged_pct"]}
        for p in pkgs
    ]

    obj = html.escape(args.object)
    org_bit = f" — {html.escape(args.org)}" if args.org else ""
    scope_bit = f"<code>{html.escape(args.scope_filter)}</code>" if args.scope_filter else "no filter"
    total_org_bit = f" of {args.total_org:,} total" if args.total_org else ""

    body = f"""<title>{obj} Object Field Audit{org_bit}</title>
<style>{CSS}</style>
<div class="wrap">

<header class="masthead">
  <p class="eyebrow">Salesforce Data Audit</p>
  <h1>{obj} Object Field Audit</h1>
  <p class="dek">Population rates for {data['total_fields']} custom fields on {obj}, measured against the in-scope record set, with a 12-month recency check to separate fields still in use from ones that quietly stopped being written to.</p>
  <div class="meta-row">
    <span><b>{args.total_all:,}</b> in-scope records{total_org_bit}</span>
    <span><b>{args.total_recent:,}</b> created in the last 12 months</span>
    <span>Scope: {scope_bit}</span>
  </div>
</header>

<div class="stats">
  <div class="stat"><span class="n">{data['total_fields']}</span><span class="l">custom fields audited</span></div>
  <div class="stat crit"><span class="n">{dead_n}</span><span class="l">fields at 0% populated</span></div>
  <div class="stat warn"><span class="n">{data['deprecation_candidates']}</span><span class="l">deprecation candidates ({data['deprecation_candidate_pct']}%)</span></div>
  <div class="stat neu"><span class="n">{review_n}</span><span class="l">unqueryable types — need manual review</span></div>
  <div class="stat good"><span class="n">{core_n}</span><span class="l">core / actively used fields</span></div>
</div>
"""

    if pkg_data:
        body += """
<section id="culprits">
  <div class="section-head"><h2>Where the dead weight comes from</h2></div>
  <p class="section-note">Fields grouped by managed-package namespace, ranked by the share flagged dead, near-dead, legacy, or unqueryable. A namespace where most of its footprint is flagged usually means a decommissioned integration still leaving fields behind.</p>
  <div class="pkg-list" id="pkgList"></div>
</section>
"""

    body += """
<section id="ledger">
  <div class="section-head"><h2>Full field ledger</h2></div>
  <p class="section-note">Sort by clicking a column header. % Populated (recent) covers recently created records — a field that's high overall but near-zero recently is being phased out even though historical records still carry it.</p>
  <div class="toolbar">
    <input id="search" type="text" placeholder="Search field name, label, or description…" aria-label="Search fields">
    <button class="pill active" data-cat="all">All</button>
  </div>
  <div class="table-scroll">
    <table>
      <thead>
        <tr>
          <th data-key="label">Field</th>
          <th data-key="type">Type</th>
          <th data-key="pct_all" class="num">% Populated (all)</th>
          <th data-key="pct_recent" class="num">% Populated (recent)</th>
          <th data-key="category">Status</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</section>

<footer class="methodology">
  <h3>Methodology</h3>
"""
    body += f"  <p>Scope: {scope_bit} — {args.total_all:,} in-scope records{total_org_bit}. \"Recent\" = CreatedDate in the trailing 365 days ({args.total_recent:,} records), used to check whether a field is still being written to on new records versus only present on old ones.</p>\n"
    body += """  <p>Population was measured with SOQL <code>COUNT(field)</code> aggregates, batched across fields. Boolean fields SOQL won't aggregate directly were measured instead via <code>WHERE field = true</code> — those show an all-time rate only, no recent split.</p>
  <ul>
    <li>Fields flagged "needs manual review" are long text areas, multi-select picklists, or encrypted strings — SOQL can't filter or aggregate them at all. A data export is required to check them properly.</li>
    <li>"Legacy" fields are populated all-time but have fallen off sharply on recently created records — still present, no longer being set.</li>
  </ul>
</footer>

</div>
"""

    script = f"""
<script id="field-data" type="application/json">{json.dumps(compact_rows)}</script>
<script id="pkg-data" type="application/json">{json.dumps(pkg_data)}</script>
<script>
(function(){{
  var raw = JSON.parse(document.getElementById('field-data').textContent);
  var rows = raw.map(function(r){{
    return {{ name:r[0], label:r[1], type:r[2], count_all:r[3], pct_all:r[4], count_recent:r[5], pct_recent:r[6], category:r[7], desc:r[8] }};
  }});
  var CHIP_CLASS = {json.dumps(CHIP_CLASS)};
  var CHIP_LABEL = {json.dumps(CHIP_LABEL)};

  var catCounts = {{}};
  rows.forEach(function(r){{ catCounts[r.category] = (catCounts[r.category]||0) + 1; }});
  var toolbar = document.querySelector('.toolbar');
  var countLine = document.createElement('span');
  countLine.className = 'count-line';
  Object.keys(catCounts).sort(function(a,b){{ return catCounts[b]-catCounts[a]; }}).forEach(function(cat){{
    var btn = document.createElement('button');
    btn.className = 'pill'; btn.setAttribute('data-cat', cat);
    btn.textContent = (CHIP_LABEL[cat]||cat) + ' (' + catCounts[cat] + ')';
    toolbar.insertBefore(btn, countLine);
  }});
  toolbar.appendChild(countLine);

  function fmtPct(v){{ if(v===null||v===undefined) return '<span class="dash">—</span>'; return v.toFixed(2) + '%'; }}

  var tbody = document.getElementById('tbody');
  var state = {{ cat:'all', q:'', sortKey:null, sortDir:1 }};

  function matches(r){{
    if(state.cat !== 'all' && r.category !== state.cat) return false;
    if(state.q){{ var hay=(r.name+' '+r.label+' '+r.desc).toLowerCase(); if(hay.indexOf(state.q)===-1) return false; }}
    return true;
  }}

  function render(){{
    var filtered = rows.filter(matches);
    if(state.sortKey){{
      var k=state.sortKey, dir=state.sortDir;
      filtered = filtered.slice().sort(function(a,b){{
        var av=a[k], bv=b[k];
        if(av===null||av===undefined) av=(typeof bv==='number')?-1:'';
        if(bv===null||bv===undefined) bv=(typeof av==='number')?-1:'';
        if(typeof av==='string'){{ av=av.toLowerCase(); bv=bv.toLowerCase(); }}
        if(av<bv) return -1*dir; if(av>bv) return 1*dir; return 0;
      }});
    }}
    tbody.innerHTML = '';
    if(!filtered.length){{
      var tr=document.createElement('tr'); var td=document.createElement('td');
      td.colSpan=5; td.className='empty-msg'; td.textContent='No fields match.';
      tr.appendChild(td); tbody.appendChild(tr);
    }} else {{
      filtered.forEach(function(r){{
        var tr=document.createElement('tr');
        var tdField=document.createElement('td');
        var nameEl=document.createElement('span'); nameEl.className='fname'; nameEl.textContent=r.label;
        var apiEl=document.createElement('span'); apiEl.className='fapi'; apiEl.textContent=r.name;
        tdField.appendChild(nameEl); tdField.appendChild(apiEl);
        if(r.desc){{ var d=document.createElement('span'); d.className='fdesc'; d.textContent=r.desc; tdField.appendChild(d); }}
        var tdType=document.createElement('td'); tdType.className='ftype'; tdType.textContent=r.type;
        var tdAll=document.createElement('td'); tdAll.className='num'; tdAll.innerHTML=fmtPct(r.pct_all);
        var tdRecent=document.createElement('td'); tdRecent.className='num'; tdRecent.innerHTML=fmtPct(r.pct_recent);
        var tdCat=document.createElement('td');
        var chip=document.createElement('span'); chip.className='chip '+(CHIP_CLASS[r.category]||'neu'); chip.textContent=CHIP_LABEL[r.category]||r.category;
        tdCat.appendChild(chip);
        tr.appendChild(tdField); tr.appendChild(tdType); tr.appendChild(tdAll); tr.appendChild(tdRecent); tr.appendChild(tdCat);
        tbody.appendChild(tr);
      }});
    }}
    countLine.textContent = filtered.length + ' of ' + rows.length + ' fields';
  }}

  document.querySelectorAll('.pill').forEach(function(btn){{
    btn.addEventListener('click', function(){{
      document.querySelectorAll('.pill').forEach(function(b){{ b.classList.remove('active'); }});
      btn.classList.add('active'); state.cat = btn.getAttribute('data-cat'); render();
    }});
  }});
  document.getElementById('search').addEventListener('input', function(e){{ state.q = e.target.value.trim().toLowerCase(); render(); }});
  document.querySelectorAll('thead th').forEach(function(th){{
    th.addEventListener('click', function(){{
      var key = th.getAttribute('data-key');
      if(state.sortKey===key){{ state.sortDir*=-1; }} else {{ state.sortKey=key; state.sortDir=1; }}
      document.querySelectorAll('thead th .arrow').forEach(function(a){{ a.remove(); }});
      var arrow=document.createElement('span'); arrow.className='arrow'; arrow.textContent = state.sortDir===1?'▲':'▼';
      th.appendChild(arrow); render();
    }});
  }});

  var pkgEl = document.getElementById('pkgList');
  if(pkgEl){{
    var pkgData = JSON.parse(document.getElementById('pkg-data').textContent);
    pkgData.forEach(function(p){{
      var row=document.createElement('div'); row.className='pkg-row';
      var nameEl=document.createElement('div'); nameEl.className='pkg-name'; nameEl.textContent=p.name;
      var track=document.createElement('div'); track.className='pkg-bar-track';
      var fill=document.createElement('div'); fill.className='pkg-bar-fill'; fill.style.width=p.pct+'%';
      fill.style.background = p.pct<40 ? 'var(--good)' : (p.pct<70 ? 'var(--warning)' : 'var(--critical)');
      track.appendChild(fill);
      var statEl=document.createElement('div'); statEl.className='pkg-stat'; statEl.innerHTML='<b>'+p.pct+'%</b> flagged';
      row.appendChild(nameEl); row.appendChild(track); row.appendChild(statEl);
      row.title = p.flagged + ' of ' + p.total + ' fields flagged';
      pkgEl.appendChild(row);
    }});
  }}

  render();
}})();
</script>
"""

    with open(args.out_html, "w") as f:
        f.write(body + script)
    print(f"wrote {args.out_html}")


if __name__ == "__main__":
    main()
