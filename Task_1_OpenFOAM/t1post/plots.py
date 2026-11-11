"""
plots.py - figures in the style of T1_codeFunctions_template.py.

All data come from OpenFOAM (fields and function-object output), read by
foamReader.RunData. Nothing is computed here except interpolation for
profiles.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

plt.rcParams.update({'font.size': 12})


def _save(fig, path, tight=False):
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches='tight' if tight else None)
    plt.close(fig)
    return os.path.basename(path)


def _contour(ax, r, field, label, cmap='coolwarm'):
    m = ax.contourf(r.nodeX.T, r.nodeY.T, field.T, cmap=cmap, levels=30)
    cbar = plt.colorbar(m, ax=ax)
    cbar.set_label(label)
    return m


def _frame(ax, r):
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-0.2 * r.L, 1.2 * r.L)
    ax.set_ylim(-0.2 * r.H, 1.2 * r.H)


def run_plots(r, figdir):
    """All figures for one run. Returns {key: filename}."""
    os.makedirs(figdir, exist_ok=True)
    pre = os.path.join(figdir, f"Case_{r.case}_")
    out = {}
    h = r.hist
    it = h['iteration']

    # Mesh
    fig, ax = plt.subplots()
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_title('Computational mesh \n (Corner nodes only needed for visualization)')
    ax.axis('equal')
    ax.vlines(r.pointX[:, 0], 0, r.H, colors='k', linestyles='dashed')
    ax.hlines(r.pointY[0, :], 0, r.L, colors='k', linestyles='dashed')
    ms = 4 if r.nI <= 42 else (2 if r.nI <= 82 else 1)
    ax.plot(r.nodeX, r.nodeY, 'ro', ms=ms)
    out['mesh'] = _save(fig, pre + 'mesh.png')

    # Temperature
    fig, ax = plt.subplots()
    ax.set_title('Temperature distribution')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.axis('equal')
    _contour(ax, r, r.T, 'Temperature [K]')
    out['temperatureDistribution'] = _save(fig, pre + 'temperatureDistribution.png')

    # Conductivity
    fig, ax = plt.subplots()
    ax.set_title('Conductivity (final)')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.axis('equal')
    _contour(ax, r, r.k, 'k [W/(m K)]', cmap='viridis')
    out['conductivity'] = _save(fig, pre + 'conductivity.png')

    # Residual convergence (course definition)
    fig, ax = plt.subplots()
    ax.set_title('Residual convergence')
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Residual [-]')
    ax.plot(it, h['epsilon'])
    ax.axhline(r.info['resTol'], color='k', ls=':', lw=1, label=f"resTol = {r.info['resTol']:g}")
    ax.legend()
    ax.grid()
    ax.set_yscale('log')
    out['residualConvergence'] = _save(fig, pre + 'residualConvergence.png')

    # Course residual vs OpenFOAM's own residual
    if r.foam_residual is not None:
        fig, ax = plt.subplots()
        ax.set_title('Course residual vs OpenFOAM residual')
        ax.set_xlabel('Iterations')
        ax.set_ylabel('Residual [-]')
        ax.plot(it, h['epsilon'], label='course: $\\epsilon$ (normalized by F)')
        ax.plot(r.foam_residual[:, 0], r.foam_residual[:, 1],
                label='OpenFOAM: initial residual of T')
        ax.grid()
        ax.set_yscale('log')
        ax.legend(fontsize=10)
        out['residualComparison'] = _save(fig, pre + 'residualComparison.png')

    # Heat flux vectors in the cells
    fig, ax = plt.subplots()
    ax.set_title('Heat flux')
    _contour(ax, r, r.T, 'Temperature [K]')
    ax.quiver(r.nodeX, r.nodeY, r.qX, r.qY, color='black')
    _frame(ax, r)
    out['heatFlux'] = _save(fig, pre + 'heatFlux.png')

    # Wall-normal heat flux at the boundary faces
    fig, ax = plt.subplots()
    ax.set_title('Wall-normal heat flux \n (from internal temperature gradient)')
    _contour(ax, r, r.T, 'Temperature [K]')
    ax.quiver(r.nodeX, r.nodeY, r.qWallX, r.qWallY, color='black')
    _frame(ax, r)
    out['wallHeatFlux'] = _save(fig, pre + 'wallHeatFlux.png')

    # Global heat rate imbalance
    fig, ax = plt.subplots()
    ax.set_title('Global heat rate imbalance convergence')
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Global heat rate imbalance [-]')
    ax.plot(it, h['globalImbalance'])
    ax.grid()
    ax.set_yscale('log')
    out['globalHeatRateImbalanceConvergence'] = _save(
        fig, pre + 'globalHeatRateImbalanceConvergence.png')

    # Incoming heat rate F
    fig, ax = plt.subplots()
    ax.set_title(f"Incoming heat rate, final F = {h['F'][-1]:.6g} W/m")
    ax.set_xlabel('Iterations')
    ax.set_ylabel('F [W/m]')
    ax.plot(it, h['F'], label='F = Din + Sin')
    ax.plot(it, h['Din'], '--', label='Din (boundaries)')
    if np.any(h['Sin'] > 0):
        ax.plot(it, h['Sin'], ':', label='Sin (source)')
    ax.grid()
    ax.legend()
    out['heatRateF'] = _save(fig, pre + 'heatRateF.png')

    # Heat rates through each boundary
    fig, ax = plt.subplots()
    ax.set_title('Heat rates into the domain')
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Heat rate [W/m]')
    for b in (1, 2, 3, 4):
        ax.plot(it, h[f'Q{b}'], label=f'boundary {b}')
    ax.plot(it, h['Qsource'], 'k--', label='source term')
    total = h['Q1'] + h['Q2'] + h['Q3'] + h['Q4'] + h['Qsource']
    ax.plot(it, total, 'k:', label='sum')
    ax.grid()
    ax.legend(fontsize=9)
    out['boundaryHeatRates'] = _save(fig, pre + 'boundaryHeatRates.png')

    # Monitored temperatures
    if r.probe_hist is not None:
        fig, ax = plt.subplots()
        ax.set_title('Monitored temperature')
        ax.set_xlabel('Iterations')
        ax.set_ylabel('Temperature [K]')
        for k, (px, py) in enumerate(r.probe_points):
            i, j = r.cell_index(px, py)
            ax.plot(r.probe_hist[:, 0], r.probe_hist[:, k + 1],
                    label=f"node ({i},{j}) at ({r.nodeX[i, j]:.3g}, {r.nodeY[i, j]:.3g})")
        ax.grid()
        ax.legend(fontsize=10)
        out['probeTemperature'] = _save(fig, pre + 'probeTemperature.png')
    return out


# ---------------------------------------------------------------------------
# Case-level comparison figures
# ---------------------------------------------------------------------------
def case_schematic(case, path):
    """Sketch of the domain with the boundary conditions of the case."""
    import caseDefinitions as cd
    L, H = case['L'], case['H']
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.add_patch(plt.Rectangle((0, 0), L, H, fc='#f3f3f3', ec='k', lw=1.5))
    txt = {}
    for b in (1, 2, 3, 4):
        bc = case['bc'][b]
        if bc[0] == 'dirichlet':
            txt[b] = f"T = {bc[1]}"
        elif bc[0] == 'neumann':
            txt[b] = "dT/dn = 0"
        else:
            txt[b] = f"h = {bc[1]:g}, T$_\\infty$ = {bc[2]}"
    d = 0.06 * max(L, H)
    ax.text(L / 2, -d, f"boundary 1: {txt[1]}", ha='center', va='top')
    ax.text(L + d, H / 2, f"boundary 2:\n{txt[2]}", ha='left', va='center')
    ax.text(L / 2, H + d, f"boundary 3: {txt[3]}", ha='center', va='bottom')
    ax.text(-d, H / 2, f"boundary 4:\n{txt[4]}", ha='right', va='center')
    ax.text(L / 2, H / 2, cd.K_MODELS[case['k']]['text'] + '\n'
            + cd.B_MODELS[case['b'][0]]['text'].format(**case['b'][1]),
            ha='center', va='center', fontsize=10)
    if case['k'] == 'region':
        ax.add_patch(plt.Rectangle((0.7, 0.3), 0.4, 0.1, fc='#c9d9f0', ec='b', ls='--'))
    ax.set_xlim(-0.75 * L, 1.75 * L)
    ax.set_ylim(-0.35 * H - 0.1, 1.35 * H + 0.1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Case {case['id']}: L = {L:g}, H = {H:g}")
    return _save(fig, path, tight=True)


def residual_comparison(runs, path, title):
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Residual [-]')
    for r in runs:
        ax.plot(r.hist['iteration'], r.hist['epsilon'], label=r.mesh)
    ax.axhline(runs[0].info['resTol'], color='k', ls=':', lw=1)
    ax.grid()
    ax.set_yscale('log')
    ax.legend()
    return _save(fig, path)


def profile_comparison(runs, path):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    for r in runs:
        p = r.profiles()
        axs[0].plot(p['x'], p['T_yMid'], '.-', ms=3, label=r.mesh)
        axs[1].plot(p['T_xMid'], p['y'], '.-', ms=3, label=r.mesh)
    axs[0].set_title('T along y = H/2')
    axs[0].set_xlabel('x [m]')
    axs[0].set_ylabel('Temperature [K]')
    axs[1].set_title('T along x = L/2')
    axs[1].set_xlabel('Temperature [K]')
    axs[1].set_ylabel('y [m]')
    for ax in axs:
        ax.grid()
        ax.legend(fontsize=9)
    return _save(fig, path)


def mesh_convergence(rows, path):
    """Relative differences to the finest non-equidistant mesh vs number of cells."""
    ne = [r for r in rows if r['family'] == 'nonequi'] or rows
    ref = max(ne, key=lambda r: r['nCells'])
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    for name, mk in (('nonequi', 'o-'), ('equi', 's--'), ('custom', '^:')):
        rs = sorted([r for r in rows if r['family'] == name and r is not ref],
                    key=lambda r: r['nCells'])
        if not rs:
            continue
        n = [r['nCells'] for r in rs]
        for k in range(len(ref['probeT'])):
            axs[0].plot(n, [100 * abs(r['probeT'][k] - ref['probeT'][k]) / abs(ref['probeT'][k])
                            for r in rs], mk, label=f"{name}: point {k+1}")
        for b in (1, 2, 3, 4):
            if abs(ref['Q'][b - 1]) > 1e-12 * ref['F']:
                axs[1].plot(n, [100 * abs(r['Q'][b - 1] - ref['Q'][b - 1]) / ref['F'] for r in rs],
                            mk, label=f"{name}: boundary {b}")
        dT = [100 * abs(r['Tmax'] - ref['Tmax']) / abs(ref['Tmax']) for r in rs]
        dT = [d if d > 1e-10 else np.nan for d in dT]
        axs[2].plot(n, dT, mk, label=f"{name}: Tmax")
    axs[0].set_title('T at monitoring points (interpolated)')
    axs[1].set_title('Heat rates through boundaries\n(difference relative to F)')
    axs[2].set_title('Maximum temperature')
    for ax in axs:
        ax.set_xscale('log')
        ydata = np.concatenate([ln.get_ydata() for ln in ax.get_lines()] or [np.array([])])
        if np.any(ydata > 0):
            ax.set_yscale('log')
        else:
            ax.text(0.5, 0.5, 'no difference\n(e.g. set by a boundary condition)',
                    ha='center', va='center', transform=ax.transAxes, color='0.4')
        ax.set_xlabel('Number of cells')
        ax.set_ylabel(f"|difference to {ref['mesh']}| [%]")
        ax.grid(True, which='both', alpha=0.4)
        if ax.get_lines():
            ax.legend(fontsize=8)
    fig.suptitle(f"Mesh study: differences relative to the finest non-equidistant mesh "
                 f"({ref['mesh']})", fontsize=12)
    return _save(fig, path)
