# Introduction to OpenFOAM: the flange tutorial

This introduction is for students who have never used OpenFOAM. It shows how to:

- start OpenFOAM in a terminal window,
- copy and run the `flange` tutorial of the solver `laplacianFoam` (heat conduction),
- understand every file and setting of the case,
- read the log file,
- look at the results with ParaView.

The commands are for OpenFOAM from openfoam.com (version `v2606`; other `vYYMM` versions
work in the same way) on Linux (Ubuntu in WSL on Windows).

Contents:
1. [What OpenFOAM is](#1-what-openfoam-is)
2. [The terminal commands you need](#2-the-terminal-commands-you-need)
3. [Starting OpenFOAM](#3-starting-openfoam)
4. [Copying the flange tutorial](#4-copying-the-flange-tutorial)
5. [The structure of a case](#5-the-structure-of-a-case)
6. [Running the case](#6-running-the-case)
7. [How OpenFOAM files are written](#7-how-openfoam-files-are-written)
8. [The settings, file by file](#8-the-settings-file-by-file)
9. [Reading the log file](#9-reading-the-log-file)
10. [Viewing the results with ParaView](#10-viewing-the-results-with-paraview)
11. [Useful commands for finding information](#11-useful-commands-for-finding-information)
12. [Exercises](#12-exercises)
13. [Common problems](#13-common-problems)


## 1. What OpenFOAM is

OpenFOAM is a collection of programs for finite-volume CFD. It is not one program with
a graphical interface. Instead you have:

- **Solvers.** Each solves a certain set of equations. `laplacianFoam` solves the
  heat-conduction (diffusion) equation, and `simpleFoam` solves steady incompressible
  flow.
- **Utilities.** These prepare or process data: `blockMesh` creates meshes,
  `checkMesh` checks them, and `postProcess` evaluates results.
- **Text files.** A **case** is a directory with text files that describe the mesh,
  the boundary conditions, the material properties and the numerical settings. You edit
  them with any text editor.
- **ParaView**, a separate program for viewing the results.

A typical workflow: copy an existing case that is close to what you want, edit its text
files, run the utilities and the solver in a terminal, and look at the results in
ParaView.


## 2. The terminal commands you need

| Command | Meaning |
|---|---|
| `pwd` | show the current directory |
| `ls`, `ls -l` | list files (with details) |
| `cd dir`, `cd ..`, `cd` | go to `dir`, one level up, your home directory |
| `mkdir -p dir` | create a directory (and its parents) |
| `cp -r a b` | copy file or directory `a` to `b` |
| `rm -r dir` | delete a directory. **There is no undo.** |
| `cat file`, `less file` | show a file (`q` quits `less`) |
| `tail -n 20 file`, `tail -f file` | last 20 lines of a file, or follow a growing file (Ctrl-C stops) |
| `grep word file` | lines of `file` that contain `word` |
| `nano file` | edit a file in the terminal (Ctrl+O and Enter saves, Ctrl+X exits) |
| Tab key | completes file and command names. Use it all the time. |
| Ctrl-C | stops the running command |

`$NAME` is the value of the environment variable `NAME`, e.g. `echo $HOME`.


## 3. Starting OpenFOAM

Install OpenFOAM-v2606 in Ubuntu (WSL) as described in
[01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md). OpenFOAM is
then activated automatically in every new Ubuntu terminal window. If you have several OpenFOAM versions installed, use one alias per version instead, as described in that guide.

Check that it worked:
```sh
foamVersion                  # should print OpenFOAM-v2606
echo $WM_PROJECT_VERSION     # the same, as a variable: v2606
which laplacianFoam          # should print the path of the solver
```

Activating OpenFOAM also sets some useful environment variables. Below are some that contain paths, which you can show with e.g. `echo $FOAM_TUTORIALS`.

| Environment variable | Contents |
|---|---|
| `$FOAM_TUTORIALS` | the tutorial cases that come with OpenFOAM (read-only, don't run them there) |
| `$FOAM_RUN` | your own directory for running cases, e.g. `~/OpenFOAM/<username>-v2606/run` |
| `$FOAM_SRC` | the source code, which also contains the documentation of all models |
| `$WM_PROJECT_DIR` | the OpenFOAM installation directory |

There are also aliases for going to these directories:

| Alias | Goes to |
|---|---|
| `tut` | `$FOAM_TUTORIALS` |
| `run` | `$FOAM_RUN` |
| `src` | `$FOAM_SRC` |
| `foam` | `$WM_PROJECT_DIR` |

You typically run your cases in the `$FOAM_RUN` directory, although it is not a requirement.

## 4. Copying the flange tutorial

Never run a tutorial in the installation directory. Copy it to your own run directory:
```sh
mkdir -p $FOAM_RUN
cp -r $FOAM_TUTORIALS/basic/laplacianFoam/flange $FOAM_RUN/
cd $FOAM_RUN/flange
ls
```
You should see:
```
0.orig  Allclean  Allrun  Allrun-parallel  constant  system
```

**Case description:** The flange is a 3D metal part (a pipe flange, about 5 cm across). It
is at 273 K at the start. At time 0 one surface is suddenly heated to 573 K and another
is kept at 273 K. The other surfaces are insulated. The solver computes how the
temperature develops in time, until t = 3 s.


## 5. The structure of a case

Every OpenFOAM case has the same structure:

| Directory or file | Contents |
|---|---|
| `0/` | initial and boundary conditions of the fields (here: `T`) at time 0 |
| `0.orig/` | a backup of `0/`. The tutorial scripts copy it to `0/`, so that you can always start again from clean files. |
| `constant/` | things that don't change during the run: the mesh (`constant/polyMesh/`) and physical properties (`transportProperties`) |
| `system/` | how to run: time control (`controlDict`), discretization schemes (`fvSchemes`), linear solvers (`fvSolution`), settings for utilities (`...Dict`) |
| `Allrun`, `Allclean` | scripts that run and clean the case |
| `0.1/`, `0.2/`, …, `3/` | results at these times, written by the solver (time directories) |
| `log.*` | output of the commands run by `Allrun` |


## 6. Running the case

### With the `Allrun`script

Type:

```sh
./Allrun
```
This takes a few seconds and prints:
```
Restore 0/ from 0.orig/
Running ansysToFoam on .../flange
Running laplacianFoam on .../flange
Running foamToEnsight on .../flange
Running foamToVTK on .../flange
```
The `Allrun` script contains:
```sh
#!/bin/sh
cd "${0%/*}" || exit                                # Run from this directory
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions

restore0Dir

runApplication ansysToFoam \
    ${FOAM_TUTORIALS:?}/resources/geometry/flange.ans -scale 0.001

runApplication $(getApplication)

if true
then
    runApplication foamToEnsight -noZero
    runApplication foamToVTK
fi
```
- `RunFunctions` defines helper functions for the tutorial scripts.
- `restore0Dir` copies `0.orig/` to `0/`.
- `runApplication X` runs the command `X` and writes its output to `log.X`. It refuses
  to run if `log.X` already exists, so that results are not overwritten by mistake.
  Run `./Allclean` first if you want to run again.
- `ansysToFoam` converts a mesh made in the program ANSYS (`flange.ans`) to OpenFOAM
  format. `-scale 0.001` converts the coordinates from mm to m. Most cases create the
  mesh with `blockMesh` instead.
- `$(getApplication)` reads the solver name from `system/controlDict`
  (`laplacianFoam`) and runs it.
- `foamToEnsight` and `foamToVTK` convert the results to other file formats
  (directories `EnSight/` and `VTK/`). You don't need them for ParaView.

`./Allclean` removes everything that was generated (time directories, `0/`, mesh,
logs) and leaves the original case. `Allrun-parallel` runs the same case on several
processors (see `system/decomposeParDict`). It is not needed here.

### Step by step

To learn what happens, it is better to run the steps yourself after `./Allclean`:
```sh
./Allclean
cp -r 0.orig 0
ansysToFoam $FOAM_TUTORIALS/resources/geometry/flange.ans -scale 0.001
checkMesh
laplacianFoam | tee log.laplacianFoam
```
`| tee log.laplacianFoam` shows the output and also saves it in a file. Alternatives:
`laplacianFoam > log.laplacianFoam` saves without showing. Follow it from another
terminal window with `tail -f log.laplacianFoam`. Cancel the `tail` command with Ctrl-C. Optionally, put the process in background and forward both error messages and output to the log fil with `laplacianFoam >& log.laplacianFoam&`. Then you can use follow the log file from the sma terminal window with `tail -f log.laplacianFoam`. Cancel the `tail` command with Ctrl-C.

### The mesh check

`checkMesh` reports, among other things:
```
Mesh stats
    points:           7189
    cells:            5712
    boundary patches: 4
Overall number of cells of each type:
    hexahedra:     5340
    prisms:        372
...
    Mesh non-orthogonality Max: 43.7851 average: 12.4899
    Non-orthogonality check OK.
...
Mesh OK.
```
- **Non-orthogonality** is the angle between the line connecting two cell centres and
  the normal of the face between them. It is 0 for a mesh of rectangles like those in
  the course code. Here it is up to 44°, which needs the corrections described in
  Section 8.
- Always run `checkMesh` on a new mesh and look for `Mesh OK`.

### The results

After the run, there is a directory for every 0.1 s:
```
0  0.1  0.2  ...  2.9  3
```
Each contains the fields at that time:

| File | Contents |
|---|---|
| `T` | temperature |
| `DT` | the diffusivity (constant here) |
| `gradTx`, `gradTy`, `gradTz` | components of ∇T |
| `flux` | the vector DT·∇T |
| `uniform/` | the time information (used for restarting) |

All are text files. Look at `3/T`: it has the same structure as `0/T` (Section 8), but
the `internalField` is now a `nonuniform List` with one value per cell (5712 values).


## 7. How OpenFOAM files are written

All input files use the same syntax ("dictionaries"). Example, `constant/transportProperties`:
```cpp
/*--------------------------------*- C++ -*----------------------------------*\
  (banner, only a comment)
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

DT              4e-05;

// ************************************************************************* //
```
The rules:
- **Header.** Every file starts with a `FoamFile` header. It tells OpenFOAM what kind of
  data follows (`class`) and the name of the object. Copy it from an existing file and
  change `object`.
- **Entries.** An entry is `keyword value;`. **Don't forget the semicolon.** The amount
  of white space doesn't matter.
- **Sub-dictionaries.** `name { ... }` groups entries.
- **Lists.** `( ... )`, e.g. `(0 0 1)` for a vector, or a list of names.
- **Comments.** `//` to the end of the line, or `/* ... */`, as in C++.
- **Patterns.** A keyword in quotes is a regular expression (pattern) and matches
  several names, e.g. `"(patch1|patch3)"` matches `patch1` and `patch3`.
- **Variables and includes.** `$name` is the value of an entry defined earlier in the
  file, and `#include "file"` inserts another file. These are used in the course
  tutorial.
- **Dimensions.** `dimensions [0 0 0 1 0 0 0];` gives the unit as powers of the SI
  base units, in the order [kg m s K mol A cd]. `[0 0 0 1 0 0 0]` is K, and
  `[0 2 -1 0 0 0 0]` is m²/s. OpenFOAM checks that the terms of an equation have the
  same units.


## 8. The settings, file by file

### The equation

`laplacianFoam` solves the transient heat-conduction (diffusion) equation

    ∂T/∂t = ∇·(DT ∇T)

where DT is the thermal diffusivity α = k/(ρ c_p) in m²/s. Written as in the course,

    ∂T/∂t − ∂/∂x(DT ∂T/∂x) − ∂/∂y(DT ∂T/∂y) − ∂/∂z(DT ∂T/∂z) = 0.

In the `laplacianFoam`solver's source code this is the line
`fvm::ddt(T) - fvm::laplacian(DT, T) == fvOptions(T)`. `fvOptions(T)` is an optional
source term, which is not used in the flange case.

### The mesh: `constant/polyMesh/`

The mesh is stored as lists:
- `points`: coordinates,
- `faces`: each face as a list of point numbers,
- `owner` and `neighbour`: the two cells on each side of every face,
- `boundary`: the groups of boundary faces.

The boundary faces are grouped into **patches**. `constant/polyMesh/boundary` lists them:
```cpp
4
(
    patch1
    {
        type            patch;
        nFaces          2440;
        startFace       15316;
    }
    patch2 { type patch; nFaces 348; startFace 17756; }
    patch3 { type patch; nFaces  96; startFace 18104; }
    patch4 { type patch; nFaces 384; startFace 18200; }
)
```
The patch names are used in the field files to give each patch a boundary condition.
You normally never edit these files by hand; utilities such as `blockMesh` write them.

### Initial and boundary conditions: `0/T`

```cpp
dimensions      [0 0 0 1 0 0 0];        // K

internalField   uniform 273;            // initial temperature in all cells

boundaryField
{
    "(patch1|patch3)"
    {
        type            zeroGradient;   // dT/dn = 0: insulated
    }
    patch2
    {
        type            fixedValue;     // prescribed temperature (Dirichlet)
        value           uniform 273;
    }
    patch4
    {
        type            fixedValue;
        value           uniform 573;
    }
}
```
- `internalField` holds the values in the cells. `uniform 273` means the same value
  everywhere. A `nonuniform List<scalar>` has one value per cell (as in the results).
- `boundaryField` must contain every patch of the mesh, by name or pattern.
- `fixedValue` sets the temperature at the boundary faces (Dirichlet condition). Its
  `value` can also be `nonuniform`.
- `zeroGradient` sets the normal gradient to zero (homogeneous Neumann condition). The
  boundary value is then equal to the value in the adjacent cell.
- There are many more boundary conditions. `laplacianFoam -listScalarBCs` lists all
  available types for scalar fields.

### Physical properties: `constant/transportProperties`

```cpp
DT              4e-05;      // thermal diffusivity [m^2/s]
```
This is constant in space and time. (In the course tutorial, DT is instead given as a
field in `0/DT`, which can vary.)

### Time control: `system/controlDict`

```cpp
application     laplacianFoam;  // the solver (used by Allrun)

startFrom       latestTime;     // start from the latest time directory (restart)
startTime       0;              // used if startFrom is startTime
stopAt          endTime;
endTime         3;              // end time [s]
deltaT          0.005;          // time step [s]: 600 time steps

writeControl    runTime;        // write at intervals of simulated time ...
writeInterval   0.1;            // ... every 0.1 s
purgeWrite      0;              // keep all written times (N > 0: keep only the last N)

writeFormat     ascii;          // text files (binary is smaller and faster)
writePrecision  6;              // significant digits in the written values
writeCompression off;
timeFormat      general;        // how time directory names are written
timePrecision   6;

runTimeModifiable true;         // re-read the dictionaries if you edit them during the run
```
- **Restarting.** `startFrom latestTime` makes a stopped run continue where it
  stopped. It also means that running `laplacianFoam` again in a finished case starts
  at t = 3 and stops immediately. Use `./Allclean`, or delete the time directories, to
  start again.
- **Other write controls.** `writeControl timeStep` writes every `writeInterval`
  time steps instead.
- The `controlDict` is also where **function objects** are added, under `functions`.
  These are tools that compute and write extra results during the run, e.g. probes and
  heat rates. They are used in the course tutorial.

### Discretization schemes: `system/fvSchemes`

```cpp
ddtSchemes
{
    default         Euler;                  // first-order implicit time discretization
}

gradSchemes
{
    default         none;
    grad(T)         Gauss linear;           // grad T from face values (Gauss theorem),
}                                           // linear interpolation to the faces

divSchemes
{
    default         none;                   // no convection terms in this equation
}

laplacianSchemes
{
    default         none;
    laplacian(DT,T) Gauss linear corrected; // diffusion term
}

interpolationSchemes
{
    default         linear;                 // cell-to-face interpolation
}

snGradSchemes
{
    default         corrected;              // face-normal gradient
}
```
Each section is for one type of term in the equations. `default` applies to all terms
of that type. `default none` means that every term must be listed explicitly. If one is
missing, the solver stops with an error that names it.

The diffusion term `laplacian(DT,T)` is discretized as in the course: the integral over
a cell is the sum over its faces of DT_f · (∂T/∂n)_f · A_f.
- **`Gauss`**: the integral is converted to a sum over the faces (Gauss divergence
  theorem).
- **`linear`**: DT is linearly interpolated from the cell centres to the faces.
- **`corrected`**: the face-normal gradient is (T_N − T_P)/|d| (central differencing,
  as in the course), plus a correction for non-orthogonal faces. On an orthogonal mesh
  the correction is zero.

`Euler` is the implicit Euler method: ∂T/∂t ≈ (T − T_old)/Δt, with the other terms at
the new time level. `steadyState` removes the time derivative; this is used in the
course cases.

### Linear solvers: `system/fvSolution`

```cpp
solvers
{
    T
    {
        solver          PCG;        // preconditioned conjugate gradient
        preconditioner  DIC;        // diagonal incomplete Cholesky
        tolerance       1e-06;      // stop when the residual is below 1e-6 ...
        relTol          0;          // ... or below relTol times the initial residual
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 2;
}
```
- **The linear system.** In each time step, the discretized equation is a linear system
  A·T = b with one equation per cell. `solvers` says how to solve it for `T`. PCG is
  efficient for the symmetric matrices of diffusion problems. Other options are
  `smoothSolver` with `smoother GaussSeidel` (as in the course code) and `GAMG`
  (multigrid).
- **Stopping the linear solver.** It iterates until the residual is below `tolerance`,
  or below `relTol` × the initial residual. `maxIter` and `minIter` limit the number of
  iterations.
- **Non-orthogonal correctors.** The non-orthogonal correction in `corrected` is
  computed from the latest T, i.e. explicitly. `nNonOrthogonalCorrectors 2` solves the
  equation 1 + 2 = 3 times per time step, each time with an updated correction. On an
  orthogonal mesh, 0 is enough.


## 9. Reading the log file

The start of `log.laplacianFoam`:
```
Create time
Create mesh for time = 0

SIMPLE: no convergence criteria found. Calculations will run for 3 steps.

Reading field T
Reading diffusivity DT
No finite volume options present

Calculating temperature distribution

Time = 0.005

DICPCG:  Solving for T, Initial residual = 1, Final residual = 1.65094e-07, No Iterations 5
DICPCG:  Solving for T, Initial residual = 0.00446913, Final residual = 2.58563e-07, No Iterations 3
DICPCG:  Solving for T, Initial residual = 0.000148071, Final residual = 1.6611e-07, No Iterations 2
ExecutionTime = 0.03 s  ClockTime = 0 s
```
- **Start-up.** The solver reads the mesh and the fields. "Calculations will run for 3
  steps" really means *until time 3*. There are no convergence criteria because the
  `SIMPLE` dictionary has no `residualControl`.
- **Per time step.** Each time step starts with `Time = ...`.
- **The solver lines.** There are 3 `Solving for T` lines per time step, because of
  the 2 non-orthogonal correctors.
  - `DICPCG` is the linear solver (PCG with the DIC preconditioner).
  - `Initial residual` is the normalized residual of A·T = b before solving, with the
    T of the previous solution.
  - `Final residual` is the residual after solving.
  - `No Iterations` is the number of PCG iterations needed.
- **Timing.** `ExecutionTime` is CPU time, and `ClockTime` is wall-clock time.
- **The end.** The log ends with `End`. If something goes wrong, there is a
  `FOAM FATAL ERROR` message instead. It usually names the file and the entry that
  caused the problem.

Towards the end of the run the temperature hardly changes any more, and the initial
residuals are small:
```
Time = 3

DICPCG:  Solving for T, Initial residual = 0.000111319, Final residual = 2.01013e-07, No Iterations 2
DICPCG:  Solving for T, Initial residual = 3.29413e-07, Final residual = 3.29413e-07, No Iterations 0
...
End
```
To see the last residuals quickly:
```sh
grep "Solving for T" log.laplacianFoam | tail
```

### Extracting data from the log with foamLog

`foamLog` extracts the residuals and other values from a log file into separate text
files, which are easier to plot:
```sh
foamLog log.laplacianFoam
ls logs
```
It writes the files to the directory `logs/`:
```
clockTime_0  executionTime_0  T_0  T_1  T_2  TFinalRes_0  TFinalRes_1  TFinalRes_2
TIters_0  TIters_1  TIters_2  Time_0  ...
```

| File | Contents |
|---|---|
| `T_0` | initial residual of T |
| `TFinalRes_0` | final residual of T |
| `TIters_0` | number of linear-solver iterations |
| `executionTime_0`, `clockTime_0` | CPU and wall-clock time |

The number at the end of a file name says which solution within the time step the
values are from. Here there are three solutions per time step (the 2 non-orthogonal
correctors), so `T_0`, `T_1` and `T_2` hold the first, second and third.

Each file has two columns separated by a tab: the time and the value, e.g. `logs/T_0`:
```
0.005	1
0.01	0.203755
0.015	0.109922
...
```
`foamLog -list log.laplacianFoam` lists all variables that can be extracted.

These are plain text files, so you can import them into any program for plotting,
e.g. Python (NumPy and Matplotlib), Matlab, gnuplot or a spreadsheet. In Python:
```python
import numpy as np
import matplotlib.pyplot as plt

for i in range(3):
    data = np.loadtxt(f'logs/T_{i}')      # columns: time, initial residual
    plt.semilogy(data[:, 0], data[:, 1], label=f'solution {i+1} in each time step')
plt.xlabel('Time [s]')
plt.ylabel('Initial residual of T')
plt.legend()
plt.show()
```
Run `foamLog` again after a new run. It overwrites the files in `logs/`.


## 10. Viewing the results with ParaView

### Opening the case

Use ParaView installed in Windows, as described in
[02_Install_ParaView_Windows.md](02_Install_ParaView_Windows.md). In the case directory,
in the Ubuntu terminal, create an empty file whose name ends with `.foam`. It tells
ParaView that this is an OpenFOAM case:
```sh
touch flange.foam
```
In ParaView, select *File → Open*, click the run directory under *Favorites*, open the
`flange` directory, select `flange.foam`, and click *OK*.

The windows and menu names below are those of ParaView 6.2 and may differ slightly
between versions.

### First view

1. **Apply.** The case appears in the *Pipeline Browser* (top left). Below it, the
   *Properties* panel shows the reader settings. Click the green **Apply** button.
   Nothing is shown until you click Apply, and you must click it again after changing
   settings.
2. **Choose what to read.** In *Properties*:
   - *Mesh Regions* selects what is read: `internalMesh` (the cells) and, if you tick
     them, the patches (`patch/patch1`, … or `patch1`, …, depending on the reader).
   - *Cell Arrays* selects the fields (`T`, `gradTx`, `flux`, …).
   - *Create cell-to-point filtered data* creates point data (see below). Tick it. It
     is not ticked by default in ParaView 6.2.
3. **Colour by T.** In the toolbar, change the colouring from *Solid Color* to **T**.
4. **Change the time.** Use the time controls in the toolbar: first, previous, play,
   next, last, and the time field. Go to the last time (3).
5. **Rescale the colours.** The colour range is set at the first time shown. Click
   *Rescale to Data Range*, or *Rescale to Custom Range* to set your own limits. The
   *Toggle Color Legend Visibility* button shows the colour bar.
6. **Rotate and zoom.** Rotate with the left mouse button, move with the middle
   button (or Shift + left), and zoom with the wheel or the right button. The toolbar
   buttons *Set view direction to +X, +Y, +Z* give standard views. Use +Z or −Z for
   the 2D course cases.
7. **Show the mesh.** Change the representation from *Surface* to *Surface With Edges*.

### Cell values and point values

OpenFOAM stores one value per cell (cell centre), like the nodes of the course code.
ParaView can show this in two ways:
- **Cell data** (the cube symbol next to `T` in the colour menu): each cell gets one
  colour.
- **Point data** (the dot symbol): values interpolated to the mesh points, which gives
  smooth colours. The OpenFOAM reader creates the point data if *Create
  cell-to-point filtered data* is ticked in *Properties* (not ticked by default in
  ParaView 6.2). You can also use the filter *Cell Data to Point Data*.

### Common filters

Select the case in the *Pipeline Browser* and choose a filter from the *Filters* menu
(or the toolbar, or Ctrl+Space and type the name). Then click **Apply**. Each filter
appears as a new item in the pipeline, and the eye symbol shows or hides it.

| Filter | Use |
|---|---|
| **Slice** | values on a plane through the 3D body. Set the origin and normal in *Properties*. |
| **Clip** | cuts away half of the body, to see the inside |
| **Contour** | iso-surfaces in 3D, or iso-lines in 2D, of a field. Add the values in *Properties*, e.g. with *Add a range of values*. |
| **Plot Over Line** | a graph of the fields along a line between two points. Opens a line-chart view. *File → Save Data* writes the values to a CSV file. |
| **Glyph** | arrows for a vector field, e.g. `flux` (= DT ∇T, so the heat flux points the other way) |
| **Calculator** | computes a new field from a formula, e.g. `-flux` or `mag(flux)` |
| **Extract Block** | selects some patches or the internal mesh |

### Saving

- *File → Save Screenshot* saves an image of the view.
- *File → Save Animation* saves an image for each time (a movie).
- *File → Save State* saves the whole pipeline. Load it again with *File → Load
  State*, possibly for another case with the same structure.


## 11. Useful commands for finding information

| Command | What it does |
|---|---|
| `laplacianFoam -help` | the options of a solver or utility (works for all commands) |
| `laplacianFoam -listScalarBCs` | all boundary conditions for scalar fields |
| `laplacianFoam -listFunctionObjects` | all function objects |
| `laplacianFoam -listFvOptions` | all fvOptions (source terms) |
| `foamListTimes` | the time directories of the case |
| `foamDictionary -entry deltaT -value system/controlDict` | print an entry of a dictionary |
| `foamDictionary -entry boundaryField/patch4 0/T` | print a sub-dictionary |
| `foamDictionary -entry deltaT -set 0.01 system/controlDict` | change an entry from the command line |
| `ls $FOAM_TUTORIALS/basic` | more tutorials. Searching the tutorials (`grep -r keyword $FOAM_TUTORIALS`) is the fastest way to find examples of a setting. |
| `find $FOAM_SRC -name "*fixedValue*"` | find the source code of a model. The header files (`.H`) start with a description and a usage example. |

The OpenFOAM user guide and the source code documentation are at
<https://www.openfoam.com/documentation>.


## 12. Exercises

Do these in your copy of the case. Run `./Allclean` and `./Allrun` after each change,
and look at the results in ParaView. In ParaView, *File → Reload Files* reads new
results without restarting.

1. **Diffusivity.** Increase `DT` by a factor of 10 in `constant/transportProperties`.
   How does the temperature at t = 0.5 s change? Why?
2. **Boundary conditions.** Make patch2 insulated (`zeroGradient`) as well. What is the
   temperature everywhere for long times? Then use 373 K on patch4 instead.
3. **Output.** Write the results every 0.5 s instead of every 0.1 s. Keep only the
   last 3 written times.
4. **Linear solver.** Use `smoothSolver` with `smoother GaussSeidel;` instead of PCG.
   (Remove the `preconditioner` line.) Compare the number of iterations in the log.
5. **Steady state.** Compute the final (steady) temperature directly:
   - In `fvSchemes`, set `ddtSchemes { default steadyState; }`.
   - In `controlDict`, set `deltaT 1; endTime 20; writeInterval 20;`.

   Each "time step" is now one iteration (one solution of the linear system). Watch
   the initial residual decrease in the log. Compare the result with the transient
   solution at t = 3 s; the temperature range should be almost the same (about
   274–573 K). This is how the course cases are run.
6. **Restart.** Set `endTime 4` in the finished transient case and run `laplacianFoam`
   again (without `Allclean`). What happens, and why?


## 13. Common problems

| Problem | Cause and fix |
|---|---|
| `laplacianFoam: command not found` | OpenFOAM is not activated in this terminal (Section 3). |
| `runApplication` says *already run on ... remove log file* | The log file of an earlier run exists. Run `./Allclean` first. |
| The solver starts and ends immediately | `startFrom latestTime` and the case has already reached `endTime`. Run `./Allclean`. |
| `FOAM FATAL IO ERROR ... keyword ... is undefined` | A required entry is missing or misspelled. The message names the file and the entry. |
| `FOAM FATAL IO ERROR ... Unexpected token` or wrong line numbers | A missing `;`, `}` or `)` near the reported line. |
| `Cannot find patchField entry for patch5` | A patch of the mesh has no boundary condition in `0/T`. Every patch must be listed (or matched by a pattern). |
| `Entry 'laplacian(DT,T)' not found` (or similar) | A scheme is missing in `fvSchemes`, with `default none`. |
| ParaView shows nothing | Click **Apply**, check the eye symbol in the pipeline, and check that `internalMesh` is selected. |
| ParaView shows only the start time | Use the time controls to go to a later time. *File → Reload Files* if the run was still going on. |
| Only cell data, no smooth colours | Tick *Create cell-to-point filtered data* in *Properties* and click **Apply**. |
| Colours look uniform | The colour range is from another time. Click *Rescale to Data Range*. |

## Next

Now you can continue with [Task_1_01_OpenFOAM_tutorial.md](Task_1_01_OpenFOAM_tutorial.md).