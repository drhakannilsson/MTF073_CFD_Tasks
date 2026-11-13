#!/usr/bin/env python3
"""
t1foam.py - set up, run and post-process the MTF073 Task 1 cases in OpenFOAM.

Each case number (1-40) and mesh gets its own OpenFOAM case directory,
    runs/Case_XX/<mesh>/
copied from baseCase/ and modified for the case. The post-processing
results (figures, summaries, an HTML page per case) are written to
    results/Case_XX/
and results/index.html links to all of them.

Examples:
    ./t1foam.py 5                          # set up, run and post-process case 5
    ./t1foam.py 1-5 12 31-33 -j 8          # several cases, 8 runs in parallel
    ./t1foam.py all -j 12                  # all 40 cases
    ./t1foam.py 7 --setup-only             # only set up (run ./Allrun in each directory)
    ./t1foam.py 7 --no-post                # set up and run, but no post-processing
    ./t1foam.py 7 --post-only              # only post-process existing runs
    ./t1foam.py 7 --meshes nonequi_20x20,equi_20x20 --settings optimal
    ./t1foam.py 7 --mesh ~/myMesh.npz --mesh ~/meshGenCase   # own meshes
    ./t1foam.py --clean 7                  # remove runs/Case_07 and results/Case_07
    ./t1foam.py --clean all                # remove runs/ and results/ completely

Mesh names:
    nonequi_20x20   the non-equidistant validation mesh of the case (meshes.zip)
    nonequi_NxM     the validation mesh refined smoothly to N x M cells
                    (N and M must be multiples of 20)
    equi_NxM        an equidistant mesh with N x M cells
    a path          an .npz file (pointX, pointY), or an OpenFOAM case
                    directory with constant/polyMesh (e.g. from meshGenerator.py)

OpenFOAM must be available, either by sourcing its etc/bashrc before
running this script, or with the --foam option.
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import caseDefinitions as cd  # noqa: E402
import npzToFoam  # noqa: E402

BASECASE = os.path.join(HERE, 'baseCase')
DATA_DIR = HERE   # meshes.zip and Task_1_Reference_results.zip are in this folder
DEFAULT_MESHES = 'nonequi_20x20,equi_20x20,nonequi_40x40,nonequi_80x80'


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------
def parse_case_list(tokens):
    cases = []
    for tok in tokens:
        for part in tok.split(','):
            part = part.strip()
            if not part:
                continue
            if part == 'all':
                cases.extend(range(1, 41))
            elif re.fullmatch(r'\d+-\d+', part):
                a, b = map(int, part.split('-'))
                cases.extend(range(a, b + 1))
            elif part.isdigit():
                cases.append(int(part))
            else:
                raise SystemExit(f"Cannot interpret case number '{part}'")
    out = []
    for c in cases:
        if c not in cd.CASES:
            raise SystemExit(f"Case {c} does not exist (valid: 1-40)")
        if c not in out:
            out.append(c)
    return out


def get_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cases', nargs='*',
                   help="case numbers: e.g. 5, 1-5, 3,7,9, all")
    g = p.add_mutually_exclusive_group()
    g.add_argument('--setup-only', action='store_true', help="only set up the cases")
    g.add_argument('--no-post', action='store_true', help="set up and run, no post-processing")
    g.add_argument('--post-only', action='store_true', help="only post-process existing runs")
    g.add_argument('--clean', action='store_true',
                   help="remove everything generated for the given cases ('all' = everything)")
    p.add_argument('--meshes', default=DEFAULT_MESHES,
                   help=f"comma-separated mesh names (default: {DEFAULT_MESHES})")
    p.add_argument('--mesh', action='append', default=[],
                   help="additional mesh: .npz file or OpenFOAM case directory (repeatable)")
    p.add_argument('--settings', choices=['course', 'optimal'], default='course',
                   help="numerical settings (default: course = Gauss-Seidel as in the Python code)")
    p.add_argument('--resTol', type=float, default=1e-3, help="convergence tolerance (default 1e-3)")
    p.add_argument('--nLinSolIter', type=int, default=10,
                   help="Gauss-Seidel sweeps per iteration, course settings (default 10)")
    p.add_argument('--maxIter', type=int, default=100000, help="max number of iterations")
    p.add_argument('--thickness', type=float, default=npzToFoam.DEFAULT_THICKNESS,
                   help="mesh thickness in z (default 0.1, results are per unit depth anyway)")
    p.add_argument('-j', '--jobs', type=int, default=1, help="number of parallel runs")
    p.add_argument('--foam', default=None,
                   help="OpenFOAM installation to source, e.g. /OpenFOAM/OpenFOAM-v2412")
    p.add_argument('--force', action='store_true',
                   help="overwrite existing run directories without asking")
    p.add_argument('--runs', default=os.path.join(HERE, 'runs'), help="run directory root")
    p.add_argument('--results', default=os.path.join(HERE, 'results'), help="results root")
    p.add_argument('--meshes-zip', default=os.path.join(DATA_DIR, 'meshes.zip'))
    p.add_argument('--reference-zip',
                   default=os.path.join(DATA_DIR, 'Task_1_Reference_results.zip'))
    a = p.parse_args()
    if not a.cases:
        p.error("give at least one case number (or 'all')")
    return a


# ---------------------------------------------------------------------------
# Meshes
# ---------------------------------------------------------------------------
def mesh_list(args):
    names = [m.strip() for m in args.meshes.split(',') if m.strip()]
    return names + [os.path.abspath(os.path.expanduser(m)) for m in args.mesh]


def mesh_dirname(spec):
    if os.path.sep in spec or os.path.exists(spec):
        base = os.path.basename(os.path.normpath(spec))
        return 'custom_' + re.sub(r'\.npz$', '', base)
    return spec


def read_polymesh_points(case_dir):
    """Unique x and y point coordinates of a rectilinear OpenFOAM mesh."""
    with open(os.path.join(case_dir, 'constant', 'polyMesh', 'points')) as f:
        txt = f.read()
    body = txt.split('FoamFile', 1)[1]
    body = body[body.index('}') + 1:]
    num = r'([-+0-9.eE]+)'
    pts = np.array(re.findall(r'\(\s*' + num + r'\s+' + num + r'\s+' + num + r'\s*\)', body),
                   dtype=float)
    x = np.unique(np.round(pts[:, 0], 12))
    y = np.unique(np.round(pts[:, 1], 12))
    return x, y, pts[:, 2].max() - pts[:, 2].min()


def make_mesh(spec, case, run_dir, args):
    """Create constant/polyMesh in run_dir. Returns (x, y) point coordinates."""
    n = case['id']
    m = re.fullmatch(r'(equi|nonequi)_(\d+)x(\d+)', spec)
    if m:
        kind, nx, ny = m.group(1), int(m.group(2)), int(m.group(3))
        if kind == 'equi':
            x, y = npzToFoam.equidistant(case['L'], case['H'], nx, ny)
        else:
            if nx % 20 or ny % 20:
                raise SystemExit(f"{spec}: nonequi meshes must have multiples of 20 cells")
            x, y = npzToFoam.load_npz(f"{args.meshes_zip}:meshes/Case_{n}_nonequi_20x20.npz")
            x, y = npzToFoam.refine_axis(x, nx // 20), npzToFoam.refine_axis(y, ny // 20)
        npzToFoam.write_polymesh(run_dir, x, y, args.thickness)
    elif spec.endswith('.npz'):
        x, y = npzToFoam.load_npz(spec)
        npzToFoam.write_polymesh(run_dir, x, y, args.thickness)
    elif os.path.isfile(os.path.join(spec, 'constant', 'polyMesh', 'points')):
        shutil.copytree(os.path.join(spec, 'constant', 'polyMesh'),
                        os.path.join(run_dir, 'constant', 'polyMesh'))
        x, y, _ = read_polymesh_points(run_dir)
    else:
        raise SystemExit(f"Unknown mesh '{spec}'")
    if not (np.isclose(x[0], 0) and np.isclose(y[0], 0) and np.isclose(x[-1], case['L'])
            and np.isclose(y[-1], case['H'])):
        raise SystemExit(f"Mesh {spec} does not match the domain of case {n} "
                         f"(L = {case['L']}, H = {case['H']})")
    return x, y


def boundary_patches(run_dir):
    """Names of the non-empty patches, from constant/polyMesh/boundary."""
    with open(os.path.join(run_dir, 'constant', 'polyMesh', 'boundary')) as f:
        txt = f.read()
    names = re.findall(r'^\s*(\w+)\s*\n\s*\{[^}]*?type\s+(\w+);', txt, re.M)
    return [nme for nme, typ in names if typ != 'empty']


def boundary_of(patch):
    for name, b in cd.BOUNDARY_OF_PATCH.items():
        if patch.startswith(name):
            return b
    raise SystemExit(f"Patch '{patch}' is not named south*, east*, north* or west*")


# ---------------------------------------------------------------------------
# Case setup
# ---------------------------------------------------------------------------
def fmt(v):
    return repr(float(v))


def expr(formula):
    """Formula string -> OpenFOAM expression syntax (pi -> pi())."""
    return re.sub(r'\bpi\b', 'pi()', formula)


def cpp_constants(case):
    lines = [f"const scalar L = {fmt(case['L'])};", f"const scalar H = {fmt(case['H'])};",
             "const scalar pi = constant::mathematical::pi;"]
    for k, v in case['constants'].items():
        lines.append(f"const scalar {k} = {fmt(v)};")
    btype, bpar = case['b']
    if btype == 'quadratic':
        lines.append(f"const scalar c1 = {fmt(bpar['c1'])};")
        lines.append(f"const scalar c2 = {fmt(bpar['c2'])};")
    lines.append("(void)L; (void)H; (void)pi;")
    return '\n        '.join(lines)


def cpp_source(case):
    btype, bpar = case['b']
    if btype == 'constant':
        return (f"// b = {bpar['b']:g}\n"
                f"            const scalar Su = {fmt(bpar['b'])}*V[celli];\n"
                f"            const scalar Sp = 0;")
    return ("// b = 15(c1 - c2 T^2), split as in the course: Su = 15 c1 dV,\n"
            "            // Sp = -15 c2 T dV (T = latest temperature, kept >= 0)\n"
            "            const scalar Su = 15.0*c1*V[celli];\n"
            "            const scalar Sp = -15.0*c2*max(T, scalar(0))*V[celli];")


def expr_variables(case, patch=False):
    v = [f'"L={fmt(case["L"])}"', f'"H={fmt(case["H"])}"',
         '"x=pos().x()"', '"y=pos().y()"']
    v += [f'"{k}={fmt(val)}"' for k, val in case['constants'].items()]
    return ' '.join(v)


def t_boundary_entries(case, patches):
    out = []
    for p in patches:
        b = boundary_of(p)
        bc = case['bc'][b]
        if bc[0] == 'dirichlet':
            out.append(f"""    {p}
    {{
        // Boundary {b}: T = {bc[1]}
        type            uniformFixedValue;
        uniformValue
        {{
            type        expression;
            variables   ({expr_variables(case)});
            expression  #{{ {expr(bc[1])} #}};
        }}
        value           uniform 0;      // placeholder, e.g. for ParaView
    }}""")
        elif bc[0] == 'neumann':
            out.append(f"""    {p}
    {{
        // Boundary {b}: dT/dn = 0
        type            zeroGradient;
    }}""")
        else:
            h, tinf = bc[1], bc[2]
            out.append(f"""    {p}
    {{
        // Boundary {b}: convective, -k dT/dn = h (T - Tinf), h = {h:g}, Tinf = {tinf}
        // Mixed condition: T_b = f*Tinf + (1 - f)*T_P, where f = h/(h + k_b/delta)
        // and delta = distance from cell centre P to the face. This is the heat
        // flux balance h (Tinf - T_b) = k_b (T_b - T_P)/delta. k_b is taken from
        // the boundary values of DT.
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        Ta              constant {fmt(float(tinf))};
        h               uniform {fmt(h)};
        kappaMethod     lookup;
        kappa           DT;
        value           uniform {fmt(float(tinf))};   // placeholder, e.g. for ParaView
    }}""")
    return '\n'.join(out)


def dt_boundary_entries(case, patches):
    return '\n'.join(f"""    {p}
    {{
        // k at the boundary faces, from the boundary temperature
        type            uniformFixedValue;
        uniformValue
        {{
            type        expression;
            variables   ({expr_variables(case)});
            expression  #{{ {expr(cd.K_MODELS[case['k']]['code'])} #}};
        }}
        value           uniform 1;      // placeholder, e.g. for ParaView
    }}""" for p in patches)


def substitute(path, subs):
    with open(path) as f:
        s = f.read()
    for k, v in subs.items():
        s = s.replace(f'@@{k}@@', str(v))
    left = re.findall(r'@@\w+@@', s)
    if left:
        raise RuntimeError(f"{path}: unreplaced placeholders {left}")
    with open(path, 'w') as f:
        f.write(s)


def setup_run(n, spec, args):
    case = cd.get_case(n)
    mname = mesh_dirname(spec)
    run_dir = os.path.join(args.runs, f"Case_{n:02d}", mname)
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    shutil.copytree(BASECASE, run_dir)
    x, y = make_mesh(spec, case, run_dir, args)
    patches = boundary_patches(run_dir)
    sides = {boundary_of(p) for p in patches}
    if sides != {1, 2, 3, 4}:
        raise SystemExit(f"{spec}: the mesh must have patches on all four sides")

    sysd = os.path.join(run_dir, 'system')
    os.rename(os.path.join(sysd, f'fvSolution.{args.settings}'), os.path.join(sysd, 'fvSolution'))
    for other in ('course', 'optimal'):
        f = os.path.join(sysd, f'fvSolution.{other}')
        if os.path.exists(f):
            os.remove(f)

    _, _, thickness = read_polymesh_points(run_dir)
    zmid = 0.5 * thickness
    desc = '\n'.join(f"//   {k}: {v}" for k, v in cd.describe(case))
    subs = {
        'CASEID': n, 'L': fmt(case['L']), 'H': fmt(case['H']),
        'RESTOL': f"{args.resTol:g}", 'NLINSOLITER': args.nLinSolIter,
        'MAXITER': args.maxIter, 'DESCRIPTION': desc,
        'CONSTANTS': cpp_constants(case),
        'SOURCECODE': cpp_source(case),
        'KEXPR': expr(cd.K_MODELS[case['k']]['code']),
        'EXPRVARIABLES': expr_variables(case),
        'TBOUNDARY': t_boundary_entries(case, patches),
        'DTBOUNDARY': dt_boundary_entries(case, patches),
        'PROBELOCATIONS': '\n'.join(f"        ({fmt(px)} {fmt(py)} {fmt(zmid)})"
                                    for px, py in case['probes']),
        'CASENAME': f"case {n}, mesh {mname}, {args.settings} settings",
    }
    for root, _, files in os.walk(run_dir):
        if 'polyMesh' in root:
            continue
        for f in files:
            substitute(os.path.join(root, f), subs)

    info = {'case': n, 'mesh': mname, 'meshSpec': spec, 'settings': args.settings,
            'resTol': args.resTol, 'nLinSolIter': args.nLinSolIter,
            'maxIter': args.maxIter, 'patches': patches,
            'meshInfo': npzToFoam.mesh_info(x, y),
            'pointX': list(map(float, x)), 'pointY': list(map(float, y))}
    with open(os.path.join(run_dir, 't1foam.json'), 'w') as f:
        json.dump(info, f, indent=1)
    return run_dir


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------
def foam_prefix(args):
    if args.foam:
        bashrc = os.path.join(args.foam, 'etc', 'bashrc')
        if not os.path.isfile(bashrc):
            raise SystemExit(f"Cannot find {bashrc}")
        return f'. "{bashrc}" > /dev/null 2>&1; '
    if not os.environ.get('WM_PROJECT_DIR'):
        raise SystemExit("OpenFOAM is not activated in this terminal. Check with foamVersion "
                         "(see 01_Install_OpenFOAM-v2606_WSL.md), or use "
                         "--foam /path/to/OpenFOAM-vXXXX")
    return ''


def check_foam(args):
    out = subprocess.run(['bash', '-c', foam_prefix(args) +
                          'echo "$WM_PROJECT_VERSION"; command -v laplacianFoam'],
                         capture_output=True, text=True).stdout.split()
    if len(out) < 2:
        raise SystemExit("laplacianFoam not found - is OpenFOAM properly sourced?")
    version = out[0]
    if not version.startswith('v'):
        print(f"WARNING: OpenFOAM-{version} is not an ESI-OpenCFD version (vYYMM). "
              "These cases are made for OpenFOAM-v2606 and may not work.")
    return version


def run_case(run_dir, args):
    t0 = time.time()
    p = subprocess.run(['bash', '-c', foam_prefix(args) + './Allrun'], cwd=run_dir,
                       capture_output=True, text=True)
    status = run_status(run_dir)
    return run_dir, status, time.time() - t0, p.stdout + p.stderr


def run_status(run_dir):
    log = os.path.join(run_dir, 'log.laplacianFoam')
    if not os.path.isfile(log):
        return 'not run'
    with open(log, errors='replace') as f:
        txt = f.read()
    if 'FOAM FATAL' in txt or not re.search(r'^End\s*$', txt, re.M):
        return 'FAILED'
    return 'converged' if 'courseResiduals: converged' in txt else 'NOT converged (maxIter)'


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
def clean(args):
    if args.cases == ['all']:
        for d in (args.runs, args.results):
            if os.path.isdir(d):
                print(f"Removing {d}")
                shutil.rmtree(d)
        return
    for n in parse_case_list(args.cases):
        for d in (os.path.join(args.runs, f"Case_{n:02d}"),
                  os.path.join(args.results, f"Case_{n:02d}")):
            if os.path.isdir(d):
                print(f"Removing {d}")
                shutil.rmtree(d)
    if os.path.isdir(args.results):
        from t1post import htmlReport
        htmlReport.write_index(args.results)


# ---------------------------------------------------------------------------
def main():
    args = get_args()
    if args.clean:
        clean(args)
        return
    cases = parse_case_list(args.cases)
    meshes = mesh_list(args)
    args.runs = os.path.abspath(args.runs)
    args.results = os.path.abspath(args.results)

    run_dirs = [os.path.join(args.runs, f"Case_{n:02d}", mesh_dirname(m))
                for n in cases for m in meshes]

    if not args.post_only:
        # Check OpenFOAM before anything is set up (existing runs are overwritten)
        version = None if args.setup_only else check_foam(args)
        existing = [d for d in run_dirs if os.path.exists(d)]
        if existing and not args.force:
            print(f"{len(existing)} run directories already exist and will be overwritten, e.g.\n"
                  f"  {existing[0]}")
            if not sys.stdin.isatty() or input("Continue? [y/N] ").strip().lower() != 'y':
                raise SystemExit("Aborted (use --force to overwrite without asking)")
        for n in cases:
            for m in meshes:
                d = setup_run(n, m, args)
                print(f"Set up {os.path.relpath(d, HERE)}")
        if args.setup_only:
            print("\nSetup done. Run a case with ./Allrun in its directory "
                  "(with OpenFOAM sourced),\nor rerun this script without --setup-only.")
            return

        print(f"\nRunning {len(run_dirs)} simulation(s) with OpenFOAM-{version}, "
              f"{args.jobs} in parallel.\n"
              "This takes a while, since each simulation first compiles some code.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
            futures = [ex.submit(run_case, d, args) for d in run_dirs]
            for fut in concurrent.futures.as_completed(futures):
                d, status, dt, out = fut.result()
                print(f"  {os.path.relpath(d, args.runs):32s} {status:26s} {dt:6.1f} s")
                if status == 'FAILED' or status == 'not run':
                    print("    -> see the log.* files in that directory")
        if args.no_post:
            return

    from t1post import postProcess
    postProcess.process(cases, args.runs, args.results, args.reference_zip,
                        jobs=args.jobs)
    print(f"\nResults: {os.path.join(args.results, 'index.html')}")


if __name__ == '__main__':
    main()
