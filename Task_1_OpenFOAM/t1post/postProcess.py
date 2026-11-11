"""
postProcess.py - post-process all runs of the given cases:

    results/Case_XX/<mesh>/figures/*.png    figures for each run
    results/Case_XX/<mesh>/summary.json     key numbers for each run
    results/Case_XX/<mesh>/summary.txt      the same, human readable
    results/Case_XX/comparison/*.png        validation, convergence and mesh study
    results/Case_XX/reference/*.png         reference results (course Python code)
    results/Case_XX/index.html              everything for the case, by report section
    results/index.html                      overview of all cases
"""
import concurrent.futures
import glob
import json
import os
import re
import sys
import traceback
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import caseDefinitions as cd  # noqa: E402
from t1post import htmlReport, plots  # noqa: E402
from t1post.foamReader import RunData  # noqa: E402


def mesh_family(name):
    return name.split('_')[0] if name.split('_')[0] in ('equi', 'nonequi') else 'custom'


def summary_text(s):
    lines = [f"Case {s['case']}, mesh {s['mesh']}, {s['settings']} settings",
             f"OpenFOAM: {s['openfoam']}",
             f"Converged: {s['converged']} after {s['iterations']} iterations "
             f"(epsilon = {s['epsilon']:.4g}, resTol = {s['resTol']:g})",
             f"Incoming heat rate F = {s['F']:.8g} W/m",
             f"Global heat rate imbalance = {s['globalImbalance']:.4g}",
             "Heat rates into the domain [W/m]:"]
    for k, v in s['heatRates'].items():
        lines.append(f"    {k:10s} {v: .8g}")
    lines.append(f"    {'sum':10s} {sum(s['heatRates'].values()): .8g}")
    lines.append(f"T min / max = {s['Tmin']:.6g} / {s['Tmax']:.6g} K")
    for k, p in enumerate(s['probes']):
        lines.append(f"Monitoring point {k+1} ({p['point'][0]:g}, {p['point'][1]:g}): "
                     f"T(node {p['node'][0]},{p['node'][1]}) = {p['T']:.6g} K, "
                     f"interpolated T = {p['T_interpolated']:.6g} K")
    mi = s['meshInfo']
    lines.append(f"Mesh: {mi['nx']} x {mi['ny']} cells, dx = {mi['dx_min']:.4g}..{mi['dx_max']:.4g}, "
                 f"dy = {mi['dy_min']:.4g}..{mi['dy_max']:.4g}, max adjacent size ratio "
                 f"{mi['max_ratio_x']:.3f} (x), {mi['max_ratio_y']:.3f} (y)")
    return '\n'.join(lines) + '\n'


def extract_reference(n, reference_zip, outdir):
    files = {}
    if not reference_zip or not os.path.isfile(reference_zip):
        return files
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(reference_zip) as z:
        for member in z.namelist():
            m = re.search(rf'(?:^|/)Case_{n}_(\w+)\.png$', member)
            if m:
                fn = os.path.basename(member)
                with open(os.path.join(outdir, fn), 'wb') as f:
                    f.write(z.read(member))
                files[m.group(1)] = fn
    return files


def process_case(n, runs_root, results_root, reference_zip):
    case = cd.get_case(n)
    case_runs = os.path.join(runs_root, f"Case_{n:02d}")
    outdir = os.path.join(results_root, f"Case_{n:02d}")
    os.makedirs(outdir, exist_ok=True)
    runs, errors = [], []
    for jf in sorted(glob.glob(os.path.join(case_runs, '*', 't1foam.json'))):
        rd = os.path.dirname(jf)
        try:
            runs.append(RunData(rd))
        except Exception as e:  # noqa: BLE001
            errors.append((os.path.basename(rd), str(e)))

    # Sort: nonequi (by size), equi (by size), custom
    order = {'nonequi': 0, 'equi': 1, 'custom': 2}
    runs.sort(key=lambda r: (order[mesh_family(r.mesh)], r.nI * r.nJ, r.mesh))

    run_items = []
    for r in runs:
        rdir = os.path.join(outdir, r.mesh)
        figs = plots.run_plots(r, os.path.join(rdir, 'figures'))
        s = r.summary()
        with open(os.path.join(rdir, 'summary.json'), 'w') as f:
            json.dump(s, f, indent=1)
        with open(os.path.join(rdir, 'summary.txt'), 'w') as f:
            f.write(summary_text(s))
        run_items.append({'run': r, 'summary': s, 'figs': figs})

    # Case-level figures
    cdir = os.path.join(outdir, 'comparison')
    os.makedirs(cdir, exist_ok=True)
    comp = {'schematic': plots.case_schematic(case, os.path.join(cdir, f'Case_{n}_schematic.png'))}
    if runs:
        # Equidistant vs non-equidistant meshes with the same number of cells
        pairs = []
        for r in runs:
            if mesh_family(r.mesh) == 'equi':
                twin = [q for q in runs if mesh_family(q.mesh) == 'nonequi'
                        and q.nI == r.nI and q.nJ == r.nJ]
                if twin:
                    pairs.append((twin[0], r))
        comp['equiVsNonequi'] = []
        for a, b in pairs:
            comp['equiVsNonequi'].append(plots.residual_comparison(
                [a, b], os.path.join(cdir, f'Case_{n}_residuals_{a.mesh}_vs_{b.mesh}.png'),
                f'Residual convergence, {a.nI-2} x {a.nJ-2} cells'))
        if len(runs) > 1:
            comp['allResiduals'] = plots.residual_comparison(
                runs, os.path.join(cdir, f'Case_{n}_residuals_allMeshes.png'),
                'Residual convergence, all meshes')
            comp['profiles'] = plots.profile_comparison(
                runs, os.path.join(cdir, f'Case_{n}_profiles.png'))
        rows = []
        for it in run_items:
            s = it['summary']
            rows.append({'mesh': s['mesh'], 'family': mesh_family(s['mesh']),
                         'nCells': s['meshInfo']['nx'] * s['meshInfo']['ny'],
                         'iterations': s['iterations'], 'Tmin': s['Tmin'], 'Tmax': s['Tmax'],
                         'probeT': [p['T_interpolated'] for p in s['probes']],
                         'Q': [s['heatRates'][f'boundary{b}'] for b in (1, 2, 3, 4)],
                         'F': s['F']})
        comp['meshStudyRows'] = rows
        if len(rows) > 1:
            comp['meshConvergence'] = plots.mesh_convergence(
                rows, os.path.join(cdir, f'Case_{n}_meshConvergence.png'))

    refs = extract_reference(n, reference_zip, os.path.join(outdir, 'reference'))
    htmlReport.write_case_page(outdir, case, run_items, comp, refs, errors, runs_root)
    return n, len(runs), errors


def process(cases, runs_root, results_root, reference_zip, jobs=1):
    os.makedirs(results_root, exist_ok=True)
    print(f"\nPost-processing {len(cases)} case(s)")
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, jobs)) as ex:
        futs = {ex.submit(process_case, n, runs_root, results_root, reference_zip): n
                for n in cases}
        for fut in concurrent.futures.as_completed(futs):
            n = futs[fut]
            try:
                _, nruns, errors = fut.result()
                print(f"  Case {n:2d}: {nruns} run(s) post-processed"
                      + (f", {len(errors)} without results" if errors else ''))
                for m, e in errors:
                    print(f"     {m}: {e}")
            except Exception:  # noqa: BLE001
                print(f"  Case {n:2d}: post-processing FAILED")
                traceback.print_exc()
    htmlReport.write_index(results_root)
