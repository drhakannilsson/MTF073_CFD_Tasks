"""
htmlReport.py - static HTML pages for browsing the results.

results/index.html          overview table of all post-processed cases
results/Case_XX/index.html  all results of one case, ordered as the sections
                            of the Task 1 report template
"""
import glob
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caseDefinitions as cd  # noqa: E402

CSS = """
:root { --bg:#ffffff; --fg:#1d1d1f; --muted:#6b6b70; --line:#dedee3; --card:#f6f6f8;
        --accent:#2a5db0; --ok:#1d7a3a; --bad:#b3261e; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#17171a; --fg:#e8e8ea; --muted:#9a9aa2; --line:#34343a; --card:#202024;
          --accent:#8ab4f8; --ok:#6fcf8a; --bad:#f28b82; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1250px; margin: 0 auto; padding: 16px 20px 60px; }
nav.top { position: sticky; top: 0; background: var(--bg); border-bottom: 1px solid var(--line);
          padding: 8px 20px; z-index: 2; font-size: 14px; overflow-x: auto; white-space: nowrap; }
nav.top a { margin-right: 14px; }
a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }
h1 { font-size: 26px; margin: 12px 0 4px; } h2 { font-size: 21px; margin-top: 34px;
     border-bottom: 1px solid var(--line); padding-bottom: 4px; }
h3 { font-size: 17px; margin-top: 22px; }
.muted { color: var(--muted); }
table { border-collapse: collapse; margin: 8px 0 14px; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 4px 9px; text-align: left; vertical-align: top; }
th { background: var(--card); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 12px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
figure { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 6px;
         padding: 6px; }
figure img { width: 100%; height: auto; display: block; background: #fff; border-radius: 3px; }
figcaption { font-size: 13px; color: var(--muted); padding: 4px 2px 0; }
details { border: 1px solid var(--line); border-radius: 6px; padding: 6px 12px; margin: 10px 0; }
summary { cursor: pointer; font-weight: 600; }
.ok { color: var(--ok); font-weight: 600; } .bad { color: var(--bad); font-weight: 600; }
.note { background: var(--card); border-left: 3px solid var(--accent); padding: 8px 12px;
        margin: 10px 0; font-size: 14px; }
pre { background: var(--card); padding: 10px; overflow-x: auto; font-size: 13px; }
@media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } main { padding: 12px 16px; } }
"""


def _e(s):
    return html.escape(str(s))


def _fig(src, caption):
    return (f'<figure><a href="{_e(src)}"><img src="{_e(src)}" loading="lazy" alt="{_e(caption)}">'
            f'</a><figcaption>{_e(caption)}</figcaption></figure>')


def _page(title, body, nav=''):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{_e(title)}</title><style>{CSS}</style></head><body>'
            f'{nav}<main>{body}</main></body></html>')


def _status(s):
    if s['converged']:
        return f'<span class="ok">converged</span> ({s["iterations"]} it.)'
    return f'<span class="bad">not converged</span> ({s["iterations"]} it.)'


def write_case_page(outdir, case, run_items, comp, refs, errors, runs_root):
    n = case['id']
    by_mesh = {it['summary']['mesh']: it for it in run_items}
    main = by_mesh.get('nonequi_20x20') or (run_items[0] if run_items else None)

    def figpath(it, key):
        fn = it['figs'].get(key)
        return f"{it['summary']['mesh']}/figures/{fn}" if fn else None

    b = [f'<h1>Case {n} <span class="muted">— OpenFOAM results for MTF073 Task 1</span></h1>']
    b.append('<p><a href="../index.html">&larr; All cases</a></p>')
    if main:
        s = main['summary']
        b.append(f'<p class="muted">OpenFOAM {_e(s["openfoam"])} · {_e(s["settings"])} settings · '
                 f'resTol = {s["resTol"]:g}'
                 + (f' · {s["nLinSolIter"]} Gauss-Seidel sweeps per iteration'
                    if s['settings'] == 'course' else '') + '</p>')
    for m, e in errors:
        b.append(f'<p class="bad">Mesh {_e(m)}: no results ({_e(e)})</p>')

    # 1 Case description
    b.append('<h2 id="s1">1 Case description</h2>')
    b.append('<div class="grid2"><div><table>')
    for k, v in cd.describe(case):
        b.append(f'<tr><th>{_e(k)}</th><td>{_e(v)}</td></tr>')
    b.append('</table><p class="muted">Boundary 1 = south (y = 0), 2 = east (x = L), '
             '3 = north (y = H), 4 = west (x = 0). The OpenFOAM patches have the same names.</p>'
             '</div>')
    b.append(_fig(f"comparison/{comp['schematic']}", 'Domain and boundary conditions') + '</div>')
    b.append('<h3>Runs</h3><table><tr><th>Mesh</th><th>Cells</th><th>Status</th>'
             '<th>Wall time [s]</th><th>&epsilon;</th><th>F [W/m]</th><th>Imbalance</th><th>T min / max [K]</th>'
             '<th>Files</th></tr>')
    for it in run_items:
        s = it['summary']
        mi = s['meshInfo']
        rd = os.path.relpath(it['run'].run_dir, outdir)
        b.append(f'<tr><td>{_e(s["mesh"])}</td><td class="num">{mi["nx"]} x {mi["ny"]}</td>'
                 f'<td>{_status(s)}</td><td class="num">{s["wallTime"]:.3g}</td>'
                 f'<td class="num">{s["epsilon"]:.3g}</td>'
                 f'<td class="num">{s["F"]:.6g}</td><td class="num">{s["globalImbalance"]:.3g}</td>'
                 f'<td class="num">{s["Tmin"]:.4g} / {s["Tmax"]:.4g}</td>'
                 f'<td><a href="{_e(s["mesh"])}/summary.txt">summary</a> · '
                 f'<a href="{_e(rd)}/log.laplacianFoam">log</a> · '
                 f'<a href="{_e(rd)}">case</a></td></tr>')
    b.append('</table><p class="muted">Wall time = wall-clock time of the iterations after the '
             'first one (the first iteration includes compiling the source term code).</p>')

    # 3 Validation
    b.append('<h2 id="s3">3 Validation</h2>')
    v = by_mesh.get('nonequi_20x20')
    if v and refs:
        b.append('<p>OpenFOAM on the prescribed non-equidistant 20 x 20 mesh (left), and the '
                 'reference solution from the course Python code (right). The colour scales are '
                 'set by each solution, so compare the T ranges as well as the patterns.</p>')
        for key, cap in (('temperatureDistribution', 'Temperature'),
                         ('heatFlux', 'Heat flux vectors'),
                         ('wallHeatFlux', 'Wall-normal heat flux'),
                         ('residualConvergence', 'Residual convergence'),
                         ('globalHeatRateImbalanceConvergence', 'Global imbalance'),
                         ('mesh', 'Mesh')):
            if key in refs and figpath(v, key):
                b.append('<div class="grid2">' + _fig(figpath(v, key), f'OpenFOAM: {cap}')
                         + _fig(f'reference/{refs[key]}', f'Reference: {cap}') + '</div>')
    else:
        b.append('<p class="muted">Needs the nonequi_20x20 mesh and the reference results.</p>')

    # 4 and 5, per mesh
    def run_section(it, open_):
        s = it['summary']
        o = ' open' if open_ else ''
        x = [f'<details{o}><summary>{_e(s["mesh"])} — {_status(s)}</summary>']
        x.append('<h3>4.1 Temperature and heat flow</h3><div class="grid">')
        for key, cap in (('temperatureDistribution', 'Temperature'),
                         ('heatFlux', 'Heat flux vectors q = -k grad(T) in the cells'),
                         ('wallHeatFlux', 'Wall-normal heat flux at the boundary faces'),
                         ('conductivity', 'Conductivity k')):
            if figpath(it, key):
                x.append(_fig(figpath(it, key), cap))
        x.append('</div><h3>4.2 Heat rates through the boundaries</h3><table>'
                 '<tr><th></th><th>Heat rate into domain [W/m]</th></tr>')
        for k2, val in s['heatRates'].items():
            x.append(f'<tr><td>{_e(k2)}</td><td class="num">{val:.8g}</td></tr>')
        x.append(f'<tr><th>sum</th><td class="num">{sum(s["heatRates"].values()):.4g}</td></tr>'
                 '</table>')
        x.append('<h3>5 Convergence</h3><div class="grid">')
        for key, cap in (('residualConvergence', '5.1 Normalized residual'),
                         ('residualComparison', '5.1 Course vs OpenFOAM residual'),
                         ('heatRateF', '5.2 Incoming heat rate F'),
                         ('globalHeatRateImbalanceConvergence', '5.3 Global heat rate imbalance'),
                         ('boundaryHeatRates', '5.3 Heat rates per boundary'),
                         ('probeTemperature', '5.4 Monitored temperatures'),
                         ('mesh', 'Mesh')):
            if figpath(it, key):
                x.append(_fig(figpath(it, key), cap))
        x.append('</div>')
        x.append(f'<p>Final values: &epsilon; = {s["epsilon"]:.4g} (resTol = {s["resTol"]:g}), '
                 f'F = {s["F"]:.6g} W/m, global imbalance = {s["globalImbalance"]:.4g}.</p>')
        x.append('<table><tr><th>Monitoring point</th><th>Cell (node i,j)</th>'
                 '<th>Node position</th><th>T in cell [K]</th><th>T interpolated [K]</th></tr>')
        for k, p in enumerate(s['probes']):
            x.append(f'<tr><td>{k+1}: ({p["point"][0]:g}, {p["point"][1]:g})</td>'
                     f'<td>({p["node"][0]}, {p["node"][1]})</td>'
                     f'<td>({p["nodeXY"][0]:.4g}, {p["nodeXY"][1]:.4g})</td>'
                     f'<td class="num">{p["T"]:.6g}</td>'
                     f'<td class="num">{p["T_interpolated"]:.6g}</td></tr>')
        x.append('</table></details>')
        return '\n'.join(x)

    b.append('<h2 id="s4">4 Physical and numerical results · 5 Convergence</h2>')
    b.append('<p>One section per mesh (click to expand).</p>')
    for it in run_items:
        b.append(run_section(it, it is main))

    b.append('<h3 id="s51">5.1 Equidistant vs non-equidistant mesh</h3>')
    if comp.get('equiVsNonequi'):
        b.append('<div class="grid">' + ''.join(
            _fig(f'comparison/{f}', 'Residual convergence, same number of cells')
            for f in comp['equiVsNonequi']) + '</div>')
    else:
        b.append('<p class="muted">Needs an equi and a nonequi mesh with the same number of '
                 'cells.</p>')

    # 6 Mesh study
    b.append('<h2 id="s6">6 Mesh study</h2>')
    rows = comp.get('meshStudyRows', [])
    if rows:
        b.append('<h3>6.1 Meshes</h3><table><tr><th>Mesh</th><th>Cells</th><th>dx min..max</th>'
                 '<th>dy min..max</th><th>Max adjacent size ratio x / y</th></tr>')
        for it in run_items:
            mi = it['summary']['meshInfo']
            b.append(f'<tr><td>{_e(it["summary"]["mesh"])}</td>'
                     f'<td class="num">{mi["nx"]} x {mi["ny"]}</td>'
                     f'<td class="num">{mi["dx_min"]:.4g} .. {mi["dx_max"]:.4g}</td>'
                     f'<td class="num">{mi["dy_min"]:.4g} .. {mi["dy_max"]:.4g}</td>'
                     f'<td class="num">{mi["max_ratio_x"]:.3f} / {mi["max_ratio_y"]:.3f}</td></tr>')
        b.append('</table><div class="grid">' + ''.join(
            _fig(figpath(it, 'mesh'), it['summary']['mesh']) for it in run_items) + '</div>')
        b.append('<h3>6.2 Comparison of results</h3><div class="grid2">')
        if comp.get('profiles'):
            b.append(_fig(f'comparison/{comp["profiles"]}', 'Centreline temperature profiles'))
        if comp.get('allResiduals'):
            b.append(_fig(f'comparison/{comp["allResiduals"]}', 'Residual convergence, all meshes'))
        b.append('</div>')
        if comp.get('meshConvergence'):
            b.append(_fig(f'comparison/{comp["meshConvergence"]}', 'Quantities vs number of cells'))

        # 6.3 table with relative differences to the finest non-equidistant mesh
        ne = [r for r in rows if r['family'] == 'nonequi'] or rows
        ref = max(ne, key=lambda r: r['nCells'])
        nprobe = len(ref['probeT'])
        b.append(f'<h3>6.3 Mesh independence</h3><p>Relative differences (in %) are taken with '
                 f'respect to the finest non-equidistant mesh, <b>{_e(ref["mesh"])}</b>. Heat '
                 f'rate differences are relative to F of that mesh.</p>')
        hdr = (['Mesh', 'Cells', 'Iterations'] + [f'T point {k+1} [K]' for k in range(nprobe)]
               + ['T max [K]'] + [f'Q{bb} [W/m]' for bb in (1, 2, 3, 4)] + ['F [W/m]'])
        b.append('<div style="overflow-x:auto"><table><tr>' + ''.join(f'<th>{_e(h)}</th>' for h in hdr)
                 + '</tr>')

        def rel(a, r0, scale=None):
            sc = abs(scale if scale is not None else r0)
            return '' if sc == 0 else f'<br><span class="muted">{100*(a-r0)/sc:+.3f}%</span>'

        for r in rows:
            cells = [_e(r['mesh']), f'{r["nCells"]}', f'{r["iterations"]}']
            cells += [f'{t:.5g}{rel(t, ref["probeT"][k])}' for k, t in enumerate(r['probeT'])]
            cells += [f'{r["Tmax"]:.5g}{rel(r["Tmax"], ref["Tmax"])}']
            cells += [f'{q:.6g}{rel(q, ref["Q"][k], ref["F"])}' for k, q in enumerate(r['Q'])]
            cells += [f'{r["F"]:.6g}{rel(r["F"], ref["F"])}']
            b.append('<tr>' + ''.join(f'<td class="num">{c}</td>' for c in cells) + '</tr>')
        b.append('</table></div>')
        b.append('<div class="note">The values at the monitoring points are interpolated '
                 'bilinearly between the nodes, so that the same physical point is compared on '
                 'all meshes. Note that the solutions are only converged to resTol, which also '
                 'affects the differences between the meshes.</div>')

    nav = ('<nav class="top"><a href="../index.html">All cases</a>'
           '<a href="#s1">1 Case</a><a href="#s3">3 Validation</a>'
           '<a href="#s4">4–5 Results &amp; convergence</a><a href="#s51">5.1 Equi vs nonequi</a>'
           '<a href="#s6">6 Mesh study</a></nav>')
    with open(os.path.join(outdir, 'index.html'), 'w') as f:
        f.write(_page(f'Case {n} – OpenFOAM', '\n'.join(b), nav))


def write_index(results_root):
    b = ['<h1>MTF073 Task 1 — OpenFOAM results</h1>',
         '<p class="muted">One page per case, with the results ordered as the sections of the '
         'report template. The numbers below are for the validation mesh nonequi_20x20 (or the '
         'first mesh, if that one is not available).</p>',
         '<table><tr><th>Case</th><th>Meshes</th><th>Status</th><th>F [W/m]</th>'
         '<th>Imbalance</th><th>T min / max [K]</th><th>Settings</th><th>OpenFOAM</th></tr>']
    ncases = 0
    for cdir in sorted(glob.glob(os.path.join(results_root, 'Case_*'))):
        sums = []
        for jf in glob.glob(os.path.join(cdir, '*', 'summary.json')):
            with open(jf) as f:
                sums.append(json.load(f))
        if not sums or not os.path.isfile(os.path.join(cdir, 'index.html')):
            continue
        ncases += 1
        sums.sort(key=lambda s: (s['mesh'] != 'nonequi_20x20', s['mesh']))
        s = sums[0]
        allconv = all(x['converged'] for x in sums)
        name = os.path.basename(cdir)
        b.append(f'<tr><td><a href="{name}/index.html">Case {s["case"]}</a></td>'
                 f'<td>{len(sums)}</td>'
                 f'<td>{"<span class=ok>all converged</span>" if allconv else "<span class=bad>check</span>"}'
                 f'</td><td class="num">{s["F"]:.6g}</td>'
                 f'<td class="num">{s["globalImbalance"]:.3g}</td>'
                 f'<td class="num">{s["Tmin"]:.4g} / {s["Tmax"]:.4g}</td>'
                 f'<td>{_e(s["settings"])}</td><td class="muted">{_e(s["openfoam"])}</td></tr>')
    b.append('</table>')
    if not ncases:
        b.append('<p class="muted">No post-processed cases.</p>')
    with open(os.path.join(results_root, 'index.html'), 'w') as f:
        f.write(_page('Task 1 OpenFOAM results', '\n'.join(b)))
