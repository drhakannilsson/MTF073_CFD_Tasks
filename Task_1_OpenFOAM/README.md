# MTF073 Task 1 in OpenFOAM

This folder sets up, runs and post-processes the 40 cases of Task 1 (2D steady heat
conduction) in OpenFOAM, so that the results can be compared with your own Python code.

All cases are created from a **single base case** (`baseCase/`), which the script
`t1foam.py` copies and modifies for each case number and mesh. The post-processing
produces the figures and numbers asked for in the Task 1 report template, in the same
style as the course Python code. You can browse them in a web browser.

## Requirements

- OpenFOAM-v2606 from openfoam.com (ESI-OpenCFD), installed as in
  [01_Install_OpenFOAM-v2606_WSL.md](../01_Install_OpenFOAM-v2606_WSL.md). The versions
  from openfoam.org (OpenFOAM-12, 13, …) are **not** supported.
- A C++ compiler, which OpenFOAM uses to compile the case-specific code at run time
  (this is normally available wherever OpenFOAM is installed).
- Python 3 with NumPy and Matplotlib.
- The files `meshes.zip` and `Task_1_Reference_results.zip`, which are included in this
  folder (or give other locations with `--meshes-zip` and `--reference-zip`).

## Quick start

See [Task_1_02_all_cases.md](../Task_1_02_all_cases.md) for a step-by-step description.

```bash
./t1foam.py 5                                  # set up, run and post-process case 5
```
OpenFOAM must be activated in the terminal (automatic with the installation in
[01_Install_OpenFOAM-v2606_WSL.md](../01_Install_OpenFOAM-v2606_WSL.md)), or given with
`--foam /path/to/OpenFOAM-vXXXX`.
Then open `results/index.html` (or `results/Case_05/index.html`) in a web browser.

## Usage

```bash
./t1foam.py 5                        # one case
./t1foam.py 1-5 12 31-33 -j 8        # lists and ranges, 8 runs in parallel
./t1foam.py all -j 12                # all 40 cases (about 12 minutes on 12 cores)
./t1foam.py 7 --setup-only           # only set up the OpenFOAM cases
./t1foam.py 7 --no-post              # set up and run, but no post-processing
./t1foam.py 7 --post-only            # post-process existing runs again
./t1foam.py 7 --settings optimal     # efficient OpenFOAM settings instead of the course settings
./t1foam.py 7 --meshes nonequi_20x20,equi_20x20,equi_40x40
./t1foam.py 7 --mesh myMesh.npz --mesh myMeshGeneratorCase   # your own meshes
./t1foam.py 7 --resTol 1e-5 --nLinSolIter 5
./t1foam.py --clean 7                # remove runs/Case_07 and results/Case_07
./t1foam.py --clean all              # remove everything generated (same as ./Allclean)
./t1foam.py -h                       # all options
```

Existing run directories are overwritten after you confirm, or without asking if you
give `--force`.

### Meshes

| Name | Mesh |
|---|---|
| `nonequi_20x20` | the prescribed non-equidistant validation mesh of the case (from `meshes.zip`) |
| `nonequi_NxM` | the validation mesh, smoothly refined to N x M cells (N and M multiples of 20) |
| `equi_NxM` | equidistant mesh with N x M cells |
| a path | a `.npz` file from `meshGenerator.py`, or an OpenFOAM case directory with `constant/polyMesh` (e.g. saved with the OpenFOAM option of `meshGenerator.py`) |

The default is `nonequi_20x20,equi_20x20,nonequi_40x40,nonequi_80x80`. This covers the
validation, the comparison between equidistant and non-equidistant meshes with the same
number of cells, and a mesh study.

`npzToFoam.py` converts an `.npz` mesh to an OpenFOAM mesh on its own:
```bash
./npzToFoam.py myMesh.npz myCase                 # writes myCase/constant/polyMesh
./npzToFoam.py myMesh.npz myCase --refine 2      # refined twice in each direction
```
The patches are called `south` (boundary 1, y = 0), `east` (boundary 2, x = L),
`north` (boundary 3, y = H) and `west` (boundary 4, x = 0), plus `frontAndBack`
(`empty`, which makes the case 2D). This matches the OpenFOAM export of
`meshGenerator.py`. A side split into several patches (`south_0`, `south_1`, …) is
also handled.

## Generated files

```
runs/Case_05/nonequi_20x20/     complete OpenFOAM case (logs, results, Allrun, Allclean)
runs/Case_05/equi_20x20/        ...
results/index.html              overview of all post-processed cases
results/Case_05/index.html      all results of case 5, ordered as the report sections
results/Case_05/<mesh>/figures/ figures of each run
results/Case_05/<mesh>/summary.txt, summary.json   key numbers of each run
results/Case_05/comparison/     validation, convergence comparison and mesh study figures
results/Case_05/reference/      reference figures from the course Python code
```

Everything is generated inside `runs/` and `results/`. `./Allclean` removes both.

### What is shown, by report section

| Report section | Results |
|---|---|
| 1 Case description | table and sketch of domain, boundary conditions, k and b |
| 3 Validation | OpenFOAM next to the reference solution on the 20 x 20 validation mesh: temperature, heat-flux vectors, wall-normal heat flux, residuals, imbalance, mesh |
| 4.1, 4.2 Results | temperature, heat-flux vectors, wall-normal heat flux, conductivity, heat rates through each boundary |
| 5.1 Residuals | normalized residual (course definition) vs iteration, equidistant vs non-equidistant mesh, and OpenFOAM's own residual for comparison |
| 5.2 Heat rate F | F vs iteration |
| 5.3 Energy balance | global heat-rate imbalance vs iteration, and heat rates per boundary vs iteration |
| 5.4 Monitored temperature | T vs iteration in the cells at two monitoring points |
| 6 Mesh study | mesh table (cell counts, sizes, max size ratio), mesh plots, centreline profiles, values at the monitoring points, extrema, boundary heat rates and their relative differences to the finest mesh |

## How the cases are set up in OpenFOAM

Look at the files of a run directory, e.g. `runs/Case_05/nonequi_20x20/`, together with
this description. A case can be rerun by hand with `./Allclean; ./Allrun` in that
directory.

**Solver.** All cases use the standard solver `laplacianFoam`, which solves
`ddt(T) - laplacian(DT, T) = fvOptions(T)`. The time derivative is switched off
(`steadyState` in `system/fvSchemes`), the field `DT` holds the conductivity k, and
the source term b is added through `fvOptions`. This gives the steady heat
conduction equation of the task. Each "time step" is one iteration. Formally,
OpenFOAM gives DT the unit m²/s and the source the unit K/s; here they are simply used
as numbers.

**Parameters.** `system/caseParameters` contains L, H, resTol, nLinSolIter and maxIter,
and a description of the case.

The cases are set up in the same way as in
[Task_1_01_OpenFOAM_tutorial.md](../Task_1_01_OpenFOAM_tutorial.md):

**Boundary conditions** (`0.orig/T`; `0/T` is created from it by `./Allrun`):
- Dirichlet: `uniformFixedValue` with an expression for T.
- Homogeneous Neumann: `zeroGradient`.
- Convective: `externalWallHeatFluxTemperature` with `mode coefficient`. The boundary
  value is a weighted mean of T∞ and the temperature in the adjacent cell,
  T_b = f T∞ + (1 − f) T_P, with f = h/(h + k_b/δ), where δ is the distance from the
  cell centre to the face. This is the heat-flux balance h(T∞ − T_b) = k_b(T_b − T_P)/δ.

**Conductivity** (the field `DT`):
- At the boundary faces: `uniformFixedValue` with an expression for k, evaluated with
  the boundary temperature (`0.orig/DT`).
- In the cells: set by `setExprFields` before the simulation starts, from the initial
  guess T = 0 (`system/setExprFieldsDict`), and updated after each iteration by the
  function object `conductivity` (`system/controlDict`), with the same expression.
- The face conductivity is linearly interpolated between the cell centres
  (`laplacianSchemes`, `Gauss linear orthogonal`).

**Source term** (`system/fvOptions`, a `scalarCodedSource` compiled at run time): as in
the course, b·ΔV = Su + Sp·T_P with Su and Sp including the cell volume. For
b = 15(c1 − c2T²), Su = 15c1ΔV and Sp = −15c2T\*ΔV, where T\* is the latest
temperature. Su goes to the right-hand side and −Sp to a_P.

**Numerical settings.**
- `--settings course` (default) mimics the course code. Each iteration does
  `nLinSolIter` Gauss-Seidel sweeps (`smoothSolver` with the `GaussSeidel` smoother in
  `system/fvSolution`). The iterations stop when the normalized residual is below
  `resTol` (default 0.001).
- `--settings optimal` solves the linear system to machine accuracy in each iteration
  with the conjugate gradient method (`PCG`, the matrix is symmetric). Linear cases then converge
  in one iteration, and nonlinear cases in a few iterations.

**Convergence monitoring** (`system/courseResiduals`, a coded function object that is
the same in all cases). After each iteration it computes the following, all per unit
depth:
- the normalized residual ε = Σ|aP TP − (Σ anb Tnb + Su)| / F, where the sum is taken
  over the OpenFOAM matrix of the latest iteration,
- F = Din + Sin, the total heat rate into the domain,
- the heat rates through each boundary and from the source term,
- the global imbalance |Din − Dout + Sin − Sout| / F,
- the wall-clock time of the iterations after the first one (the first iteration
  includes compiling the source term code), shown in the Runs table of the case page,
  to compare the run times of different settings.

It writes these (except the wall-clock time) to the log file, and all of them to `postProcessing/courseResiduals.dat`, and stops
the run when ε < resTol. It also creates the heat-flux fields `q = −k grad(T)` (in the
cells) and `qWall = −k dT/dn` (at the boundary faces, out of the domain, from the
temperature gradient just inside the boundary), which are written with T.

The standard function objects `probes` (monitored temperatures) and `solverInfo`
(OpenFOAM's own residuals) are also used. They are written to `postProcessing/`.

**Differences from the course Python code** (small, but good to know):
- OpenFOAM uses cell-centred control volumes. They are the same as in the course code:
  the nodes are the cell centres, and the boundary nodes are the boundary face centres.
- The Gauss-Seidel sweeps run through the cells in a different order.
- ε is evaluated with the conductivity and source term updated with the latest
  temperature, i.e. just before the next iteration.
- OpenFOAM's own residual (`Initial residual` in the log) is normalized in another way
  than the course residual. Both are plotted for comparison.

## Files

| File | Purpose |
|---|---|
| [`01_Install_OpenFOAM-v2606_WSL.md`](../01_Install_OpenFOAM-v2606_WSL.md) | how to install OpenFOAM-v2606 in Ubuntu (WSL) on Windows, and how to remove it again |
| [`02_Install_ParaView_Windows.md`](../02_Install_ParaView_Windows.md) | how to install ParaView in Windows and view the results, and how to remove it again |
| [`04_The_OpenFOAM_flange_tutorial.md`](../04_The_OpenFOAM_flange_tutorial.md) | introduction to OpenFOAM for beginners: the flange tutorial and ParaView |
| [`Task_1_01_OpenFOAM_tutorial.md`](../Task_1_01_OpenFOAM_tutorial.md) | how to set up such cases by hand in OpenFOAM, without the scripts |
| [`Task_1_02_all_cases.md`](../Task_1_02_all_cases.md) | step-by-step description of how to run all cases with the scripts in this folder |
| `t1foam.py` | main script: setup, run, post-process, clean |
| `caseDefinitions.py` | the 40 cases (domain, boundary conditions, k, b, monitoring points) |
| `npzToFoam.py` | conversion of `.npz` meshes to OpenFOAM, refinement of meshes |
| `baseCase/` | the base case. `@@NAME@@` placeholders are replaced by `t1foam.py` |
| `Task1/` | the finished case of `Task_1_01_OpenFOAM_tutorial.md` |
| `t1post/foamReader.py` | reads the OpenFOAM results into node arrays as in the course code |
| `t1post/plots.py` | figures |
| `t1post/postProcess.py` | post-processing of all runs of a case |
| `t1post/htmlReport.py` | HTML pages |
| `meshes.zip` | the prescribed non-equidistant validation meshes of the 40 cases |
| `Task_1_Reference_results.zip` | the reference results of the course Python code |
| `Allclean` | removes everything generated |

---

© 2026 Håkan Nilsson. Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
