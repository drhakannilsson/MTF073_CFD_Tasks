#!/usr/bin/env python3
"""
npzToFoam.py - convert a structured 2D mesh in NumPy .npz format to an
OpenFOAM polyMesh (constant/polyMesh).

The .npz file is the format written by meshGenerator.py (and used in the
MTF073 Python code): it contains the arrays pointX and pointY, both of
shape (nI-1, nJ-1) = (nx+1, ny+1), with pointX[i,j], pointY[i,j] the
coordinates of mesh point (i,j).

The OpenFOAM mesh gets one cell in the z direction (thickness given by
--thickness) and the same patch layout as the OpenFOAM export of
meshGenerator.py:
    south (y = 0)   = boundary 1 in the task description
    east  (x = L)   = boundary 2
    north (y = H)   = boundary 3
    west  (x = 0)   = boundary 4
    frontAndBack    = empty (makes the case 2D)
Cells are numbered i + nx*j (i along x, j along y).

Usage:
    python3 npzToFoam.py mesh.npz caseDir [--thickness 0.1]
    python3 npzToFoam.py meshes.zip:meshes/Case_1_nonequi_20x20.npz caseDir

The module is also imported by t1foam.py.
"""
import argparse
import io
import os
import zipfile

import numpy as np

DEFAULT_THICKNESS = 0.1


# ---------------------------------------------------------------------------
# Reading / creating mesh coordinates
# ---------------------------------------------------------------------------
def load_npz(path):
    """Return the 1D arrays (x_faces, y_faces) from an npz file.

    path may be 'file.npz' or 'archive.zip:member.npz'."""
    if ':' in path and path.split(':', 1)[0].endswith('.zip'):
        zpath, member = path.split(':', 1)
        with zipfile.ZipFile(zpath) as z:
            data = np.load(io.BytesIO(z.read(member)))
    else:
        data = np.load(path)
    pointX, pointY = data['pointX'], data['pointY']
    x = np.asarray(pointX[:, 0], dtype=float)
    y = np.asarray(pointY[0, :], dtype=float)
    # The mesh must be rectilinear (pointX independent of j, pointY of i)
    if not (np.allclose(pointX, x[:, None]) and np.allclose(pointY, y[None, :])):
        raise ValueError(f"{path}: the mesh is not rectilinear")
    return x, y


def equidistant(L, H, nx, ny):
    """Mesh point coordinates for an equidistant mesh."""
    return np.linspace(0.0, L, nx + 1), np.linspace(0.0, H, ny + 1)


def _pchip_slopes(s, x):
    """Fritsch-Carlson slopes for monotone cubic Hermite interpolation."""
    h = np.diff(s)
    delta = np.diff(x) / h
    m = np.zeros_like(x)
    m[0], m[-1] = delta[0], delta[-1]
    for k in range(1, len(x) - 1):
        if delta[k - 1] * delta[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    return m


def refine_axis(x, r):
    """Refine a 1D point distribution by a factor r (integer).

    The point coordinate is regarded as a smooth function x(s) of the point
    index s and evaluated at s = 0, 1/r, 2/r, ... using monotone cubic
    interpolation. This keeps the original stretching smoothly (no jumps in
    cell size), and keeps all original points."""
    r = int(r)
    if r == 1:
        return x.copy()
    s = np.arange(len(x), dtype=float)
    m = _pchip_slopes(s, x)
    sf = np.linspace(0.0, s[-1], r * (len(x) - 1) + 1)
    k = np.minimum(np.floor(sf).astype(int), len(x) - 2)
    t = sf - k
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    xf = h00 * x[k] + h10 * m[k] + h01 * x[k + 1] + h11 * m[k + 1]
    xf[0], xf[-1] = x[0], x[-1]
    return xf


def mesh_info(x, y):
    """Some cell-size information about the mesh, as a dict."""
    info = {}
    for name, c in (('x', x), ('y', y)):
        d = np.diff(c)
        ratio = np.maximum(d[1:] / d[:-1], d[:-1] / d[1:]) if len(d) > 1 else np.array([1.0])
        info['n' + name] = len(d)
        info['d' + name + '_min'] = float(d.min())
        info['d' + name + '_max'] = float(d.max())
        info['max_ratio_' + name] = float(ratio.max())
    return info


# ---------------------------------------------------------------------------
# Writing the OpenFOAM polyMesh
# ---------------------------------------------------------------------------
def _header(foam_class, obj, note=None):
    s = ("/*--------------------------------*- C++ -*----------------------------------*\\\n"
         "  Written by npzToFoam.py (MTF073 Task 1 OpenFOAM cases)\n"
         "\\*---------------------------------------------------------------------------*/\n"
         "FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
         f"    class       {foam_class};\n")
    if note:
        s += f'    note        "{note}";\n'
    s += f'    location    "constant/polyMesh";\n    object      {obj};\n}}\n\n'
    return s


def write_polymesh(case_dir, x, y, thickness=DEFAULT_THICKNESS):
    """Write constant/polyMesh for the rectilinear mesh with point
    coordinates x (nx+1) and y (ny+1). Returns the polyMesh directory."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    nx, ny = len(x) - 1, len(y) - 1

    def pt(i, j, k):
        return i + (nx + 1) * (j + (ny + 1) * k)

    def cell(i, j):
        return i + nx * j

    faces, owner, neighbour = [], [], []
    # Internal faces, upper-triangular order (sorted by owner, then neighbour).
    # Point order gives (right-hand rule) a normal from owner to neighbour.
    for j in range(ny):
        for i in range(nx):
            if i < nx - 1:  # east face of cell (i,j), normal +x
                faces.append((pt(i+1, j, 0), pt(i+1, j+1, 0), pt(i+1, j+1, 1), pt(i+1, j, 1)))
                owner.append(cell(i, j))
                neighbour.append(cell(i+1, j))
            if j < ny - 1:  # north face of cell (i,j), normal +y
                faces.append((pt(i, j+1, 0), pt(i, j+1, 1), pt(i+1, j+1, 1), pt(i+1, j+1, 0)))
                owner.append(cell(i, j))
                neighbour.append(cell(i, j+1))
    n_internal = len(faces)

    patches = []  # (name, type, nFaces, startFace)

    def add_patch(name, kind, plist):
        patches.append((name, kind, len(plist), len(faces)))
        for f, o in plist:
            faces.append(f)
            owner.append(o)

    # Boundary faces, normals pointing out of the domain
    add_patch('west', 'patch', [((pt(0, j, 0), pt(0, j, 1), pt(0, j+1, 1), pt(0, j+1, 0)), cell(0, j))
                                for j in range(ny)])
    add_patch('east', 'patch', [((pt(nx, j, 0), pt(nx, j+1, 0), pt(nx, j+1, 1), pt(nx, j, 1)), cell(nx-1, j))
                                for j in range(ny)])
    add_patch('south', 'patch', [((pt(i, 0, 0), pt(i+1, 0, 0), pt(i+1, 0, 1), pt(i, 0, 1)), cell(i, 0))
                                 for i in range(nx)])
    add_patch('north', 'patch', [((pt(i, ny, 0), pt(i, ny, 1), pt(i+1, ny, 1), pt(i+1, ny, 0)), cell(i, ny-1))
                                 for i in range(nx)])
    back = [((pt(i, j, 0), pt(i, j+1, 0), pt(i+1, j+1, 0), pt(i+1, j, 0)), cell(i, j))
            for j in range(ny) for i in range(nx)]
    front = [((pt(i, j, 1), pt(i+1, j, 1), pt(i+1, j+1, 1), pt(i, j+1, 1)), cell(i, j))
             for j in range(ny) for i in range(nx)]
    add_patch('frontAndBack', 'empty', back + front)

    points = [(xx, yy, zz) for zz in (0.0, thickness) for yy in y for xx in x]

    mesh_dir = os.path.join(case_dir, 'constant', 'polyMesh')
    os.makedirs(mesh_dir, exist_ok=True)
    note = (f"nPoints:{len(points)}  nCells:{nx*ny}  "
            f"nFaces:{len(faces)}  nInternalFaces:{n_internal}")

    def write(name, foam_class, items, with_note=False):
        with open(os.path.join(mesh_dir, name), 'w') as f:
            f.write(_header(foam_class, name, note if with_note else None))
            f.write(f"{len(items)}\n(\n")
            f.write("\n".join(items))
            f.write("\n)\n")

    write('points', 'vectorField', [f"({xx!r} {yy!r} {zz!r})" for xx, yy, zz in points])
    write('faces', 'faceList', ["4({} {} {} {})".format(*f) for f in faces])
    write('owner', 'labelList', [str(c) for c in owner], with_note=True)
    write('neighbour', 'labelList', [str(c) for c in neighbour], with_note=True)
    write('boundary', 'polyBoundaryMesh',
          [f"    {name}\n    {{\n        type            {kind};\n"
           + ("        inGroups        1(empty);\n" if kind == 'empty' else "")
           + f"        nFaces          {n};\n        startFace       {start};\n    }}"
           for name, kind, n, start in patches])
    return mesh_dir


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('npz', help="mesh file (file.npz or archive.zip:member.npz)")
    p.add_argument('caseDir', help="OpenFOAM case directory (constant/polyMesh is written)")
    p.add_argument('--thickness', type=float, default=DEFAULT_THICKNESS,
                   help=f"mesh thickness in z (default {DEFAULT_THICKNESS})")
    p.add_argument('--refine', type=int, default=1,
                   help="refine the mesh by this integer factor in both directions")
    a = p.parse_args()
    x, y = load_npz(a.npz)
    x, y = refine_axis(x, a.refine), refine_axis(y, a.refine)
    d = write_polymesh(a.caseDir, x, y, a.thickness)
    print(f"Wrote {d}: {len(x)-1} x {len(y)-1} cells")


if __name__ == '__main__':
    main()
