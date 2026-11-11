"""
foamReader.py - read OpenFOAM ascii results of a Task 1 run and arrange them
as structured node arrays with the same layout as in the course Python code:

    nI = nx + 2, nJ = ny + 2 nodes: index 0 and nI-1 (nJ-1) are the boundary
    nodes (face centres), the others are the cell centres. Corner nodes are
    only for plotting (average of the two neighbouring boundary nodes).
"""
import glob
import json
import os
import re

import numpy as np

_NUM = r'[-+0-9.eE]+'


def _parse_values(txt, pos):
    """Parse 'uniform X' or 'nonuniform List<T> N ( ... )' starting at pos.
    Returns (values, is_uniform)."""
    m = re.compile(r'\s*uniform\s+(\([^)]*\)|' + _NUM + ')').match(txt, pos)
    if m:
        v = m.group(1)
        if v.startswith('('):
            return np.array(v[1:-1].split(), dtype=float), True
        return float(v), True
    m = re.compile(r'\s*nonuniform\s+List<(\w+)>\s*(\d+)\s*\(').match(txt, pos)
    if not m:
        # e.g. "nonuniform List<scalar> 0()" for empty patches
        m0 = re.compile(r'\s*nonuniform\s+List<(\w+)>\s*0\s*\(\s*\)').match(txt, pos)
        if m0:
            return np.array([]), False
        raise ValueError(f"cannot parse field values at: {txt[pos:pos+80]!r}")
    kind, n = m.group(1), int(m.group(2))
    start = m.end()
    if kind == 'scalar':
        end = txt.index(')', start)
        vals = np.array(txt[start:end].split(), dtype=float)
    else:
        # list of vectors: find the matching closing parenthesis
        depth, i = 1, start
        while depth:
            c = txt[i]
            depth += (c == '(') - (c == ')')
            i += 1
        body = txt[start:i - 1]
        vals = np.array(re.findall(_NUM, body), dtype=float).reshape(n, -1)
    if len(vals) != n:
        raise ValueError(f"expected {n} values, got {len(vals)}")
    return vals, False


def read_field(path, patches):
    """Read an ascii volField. Returns (internal, {patch: values or None})."""
    with open(path) as f:
        txt = f.read()
    m = re.search(r'\binternalField\b', txt)
    internal, _ = _parse_values(txt, m.end())
    bstart = txt.index('boundaryField', m.end())
    boundary = {}
    for p in patches:
        mp = re.compile(r'\n\s*' + re.escape(p) + r'\s*\n\s*\{').search(txt, bstart)
        if not mp:
            boundary[p] = None
            continue
        # end of this patch entry: next patch name at the same indentation
        nxt = re.compile(r'\n    \w+\s*\n    \{').search(txt, mp.end())
        end = nxt.start() if nxt else len(txt)
        mv = re.compile(r'\n\s*value\s+').search(txt, mp.end(), end)
        boundary[p] = _parse_values(txt, mv.end() - 1)[0] if mv else None
    return internal, boundary


def latest_time(run_dir):
    times = []
    for d in os.listdir(run_dir):
        try:
            t = float(d)
        except ValueError:
            continue
        if t > 0 and os.path.isfile(os.path.join(run_dir, d, 'T')):
            times.append((t, d))
    return max(times)[1] if times else None


class RunData:
    """All data of one run, as node arrays and convergence histories."""

    def __init__(self, run_dir):
        self.run_dir = run_dir
        with open(os.path.join(run_dir, 't1foam.json')) as f:
            self.info = json.load(f)
        self.case = self.info['case']
        self.mesh = self.info['mesh']
        self.patches = self.info['patches']
        self.pointX1 = np.array(self.info['pointX'])
        self.pointY1 = np.array(self.info['pointY'])
        self.time = latest_time(run_dir)
        if self.time is None:
            raise RuntimeError(f"{run_dir}: no results found")
        self._read_fields()
        self._read_histories()

    # ---------------------------------------------------------------- fields
    def _read_fields(self):
        x, y = self.pointX1, self.pointY1
        nx, ny = len(x) - 1, len(y) - 1
        self.nI, self.nJ = nI, nJ = nx + 2, ny + 2
        self.L, self.H = x[-1], y[-1]
        tdir = os.path.join(self.run_dir, self.time)

        # Node coordinates (same as calcNodePositions in the course code)
        xn = np.concatenate(([x[0]], 0.5 * (x[1:] + x[:-1]), [x[-1]]))
        yn = np.concatenate(([y[0]], 0.5 * (y[1:] + y[:-1]), [y[-1]]))
        self.nodeX, self.nodeY = np.meshgrid(xn, yn, indexing='ij')
        self.pointX, self.pointY = np.meshgrid(x, y, indexing='ij')

        C, Cb = read_field(os.path.join(tdir, 'C'), self.patches)
        C = np.atleast_2d(C)
        ci = np.searchsorted(x, C[:, 0]) - 1 + 1   # node index i (1..nx)
        cj = np.searchsorted(y, C[:, 1]) - 1 + 1
        self._cell_ij = (ci, cj)

        # boundary face -> node index
        self._face_ij = {}
        for p in self.patches:
            fc = np.atleast_2d(Cb[p])
            side = p.split('_')[0]
            if side in ('west', 'east'):
                j = np.searchsorted(y, fc[:, 1])
                i = np.zeros_like(j) if side == 'west' else np.full_like(j, nI - 1)
            else:
                i = np.searchsorted(x, fc[:, 0])
                j = np.zeros_like(i) if side == 'south' else np.full_like(i, nJ - 1)
            self._face_ij[p] = (i, j)

        self.T = self._scalar_nodes(os.path.join(tdir, 'T'))
        self.k = self._scalar_nodes(os.path.join(tdir, 'DT'))

        # Heat flux vectors in the cells (NaN at the boundaries, as in the course code)
        qi, _ = read_field(os.path.join(tdir, 'q'), self.patches)
        self.qX = np.full((nI, nJ), np.nan)
        self.qY = np.full((nI, nJ), np.nan)
        self.qX[ci, cj] = qi[:, 0]
        self.qY[ci, cj] = qi[:, 1]

        # Wall-normal heat flux out of the domain at the boundary faces,
        # as vectors (normal component of the heat flux vector)
        _, qwb = read_field(os.path.join(tdir, 'qWall'), self.patches)
        self.qWallX = np.full((nI, nJ), np.nan)
        self.qWallY = np.full((nI, nJ), np.nan)
        self.qWallOut = np.full((nI, nJ), np.nan)
        normals = {'west': (-1, 0), 'east': (1, 0), 'south': (0, -1), 'north': (0, 1)}
        for p in self.patches:
            i, j = self._face_ij[p]
            v = np.broadcast_to(np.asarray(qwb[p], dtype=float), i.shape)
            nxv, nyv = normals[p.split('_')[0]]
            self.qWallOut[i, j] = v
            self.qWallX[i, j] = v * nxv
            self.qWallY[i, j] = v * nyv

    def _scalar_nodes(self, path):
        nI, nJ = self.nI, self.nJ
        internal, boundary = read_field(path, self.patches)
        a = np.full((nI, nJ), np.nan)
        ci, cj = self._cell_ij
        a[ci, cj] = internal
        for p in self.patches:
            i, j = self._face_ij[p]
            if boundary[p] is None:
                # zeroGradient: boundary value = value in the adjacent cell
                ii = np.clip(i, 1, nI - 2)
                jj = np.clip(j, 1, nJ - 2)
                a[i, j] = a[ii, jj]
            else:
                a[i, j] = boundary[p]
        # corners (only for contour plots)
        for i, j, i1, j1 in ((0, 0, 1, 0), (nI-1, 0, nI-2, 0), (0, nJ-1, 1, nJ-1),
                             (nI-1, nJ-1, nI-2, nJ-1)):
            jn = 1 if j == 0 else nJ - 2
            a[i, j] = 0.5 * (a[i1, j1] + a[i, jn])
        return a

    def cell_index(self, px, py):
        """Node indices (i, j) of the cell containing the point."""
        i = int(np.searchsorted(self.pointX1, px))
        j = int(np.searchsorted(self.pointY1, py))
        return min(max(i, 1), self.nI - 2), min(max(j, 1), self.nJ - 2)

    # ------------------------------------------------------------- histories
    def _read_histories(self):
        pp = os.path.join(self.run_dir, 'postProcessing')
        d = np.loadtxt(os.path.join(pp, 'courseResiduals.dat'), ndmin=2)
        names = ['iteration', 'epsilon', 'F', 'Din', 'Dout', 'Sin', 'Sout',
                 'globalImbalance', 'Q1', 'Q2', 'Q3', 'Q4', 'Qsource']
        self.hist = {n: d[:, k] for k, n in enumerate(names)}

        # Probes
        pf = sorted(glob.glob(os.path.join(pp, 'probes', '*', 'T')))
        self.probe_points = []
        self.probe_hist = None
        if pf:
            with open(pf[0]) as f:
                for line in f:
                    m = re.match(r'#\s*Probe\s+\d+\s+\((' + _NUM + r')\s+(' + _NUM + r')\s+', line)
                    if m:
                        self.probe_points.append((float(m.group(1)), float(m.group(2))))
            self.probe_hist = np.loadtxt(pf[0], comments='#', ndmin=2)

        # OpenFOAM's own initial residual
        sf = sorted(glob.glob(os.path.join(pp, 'solverInfo', '*', 'solverInfo.dat')))
        self.foam_residual = None
        if sf:
            rows = []
            with open(sf[0]) as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    s = line.split()
                    if len(s) >= 3:
                        rows.append((float(s[0]), float(s[2])))
            if rows:
                self.foam_residual = np.array(rows)

        # Log file information
        self.foam_version = ''
        self.converged = False
        log = os.path.join(self.run_dir, 'log.laplacianFoam')
        if os.path.isfile(log):
            with open(log, errors='replace') as f:
                txt = f.read()
            m = re.search(r'^Build\s*:\s*(.*)$', txt, re.M)
            if m:
                self.foam_version = m.group(1).strip()
            m = re.search(r'openfoam-(\d+)', txt)
            if m:
                self.foam_version = f"v{m.group(1)} ({self.foam_version})"
            self.converged = 'courseResiduals: converged' in txt
            m = re.findall(r'ExecutionTime = ([0-9.eE+-]+) s', txt)
            self.execution_time = float(m[-1]) if m else float('nan')

    # --------------------------------------------------------------- summary
    def summary(self):
        h = self.hist
        last = {k: float(v[-1]) for k, v in h.items()}
        s = {
            'case': self.case, 'mesh': self.mesh, 'settings': self.info['settings'],
            'resTol': self.info['resTol'], 'nLinSolIter': self.info['nLinSolIter'],
            'openfoam': self.foam_version, 'converged': self.converged,
            'iterations': int(last['iteration']), 'epsilon': last['epsilon'],
            'F': last['F'], 'globalImbalance': last['globalImbalance'],
            'heatRates': {'boundary1': last['Q1'], 'boundary2': last['Q2'],
                          'boundary3': last['Q3'], 'boundary4': last['Q4'],
                          'source': last['Qsource']},
            'Tmin': float(np.nanmin(self.T)), 'Tmax': float(np.nanmax(self.T)),
            'meshInfo': self.info['meshInfo'],
            'probes': [],
        }
        for k, (px, py) in enumerate(self.probe_points):
            i, j = self.cell_index(px, py)
            s['probes'].append({'point': [px, py], 'node': [i, j],
                                'nodeXY': [float(self.nodeX[i, j]), float(self.nodeY[i, j])],
                                'T': float(self.probe_hist[-1, k + 1]),
                                'T_interpolated': self.interpolate(px, py)})
        return s

    def interpolate(self, px, py):
        """Bilinear interpolation of T between the nodes."""
        xs, ys = self.nodeX[:, 0], self.nodeY[0, :]
        i = int(np.clip(np.searchsorted(xs, px), 1, len(xs) - 1))
        j = int(np.clip(np.searchsorted(ys, py), 1, len(ys) - 1))
        wx = (px - xs[i - 1]) / (xs[i] - xs[i - 1])
        wy = (py - ys[j - 1]) / (ys[j] - ys[j - 1])
        T = self.T
        return float((1 - wx) * (1 - wy) * T[i - 1, j - 1] + wx * (1 - wy) * T[i, j - 1]
                     + (1 - wx) * wy * T[i - 1, j] + wx * wy * T[i, j])

    def profiles(self):
        """T along the horizontal (y = H/2) and vertical (x = L/2) centrelines,
        linearly interpolated between the nodes."""
        xs, ys = self.nodeX[:, 0], self.nodeY[0, :]

        def interp_y(yv):
            j = np.clip(np.searchsorted(ys, yv), 1, len(ys) - 1)
            w = (yv - ys[j - 1]) / (ys[j] - ys[j - 1])
            return (1 - w) * self.T[:, j - 1] + w * self.T[:, j]

        def interp_x(xv):
            i = np.clip(np.searchsorted(xs, xv), 1, len(xs) - 1)
            w = (xv - xs[i - 1]) / (xs[i] - xs[i - 1])
            return (1 - w) * self.T[i - 1, :] + w * self.T[i, :]

        return {'x': xs, 'T_yMid': interp_y(0.5 * self.H),
                'y': ys, 'T_xMid': interp_x(0.5 * self.L)}
