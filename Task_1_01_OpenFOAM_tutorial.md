# Setting up the Task 1 heat-conduction cases in OpenFOAM

This tutorial shows how to set up the Task 1 cases (2D steady heat conduction with varying conductivity and source terms) in OpenFOAM. It also shows how to get the results asked for in the report. It is written from a pure OpenFOAM point of view: everything is done with OpenFOAM dictionaries, utilities and function objects.

You are assumed to know how to run the `flange` tutorial of `laplacianFoam`
(`$FOAM_TUTORIALS/basic/laplacianFoam/flange`). You should also know how to set
constant `fixedValue` and `zeroGradient` boundary conditions. If you are new to
OpenFOAM, start with [04_The_OpenFOAM_flange_tutorial.md](04_The_OpenFOAM_flange_tutorial.md). The tutorial goes
through what you need beyond that, in the order you need it:

1. [Steady heat conduction with laplacianFoam](#1-steady-heat-conduction-with-laplacianfoam)
2. [A 2D mesh with non-equidistant cells](#2-a-2d-mesh-with-non-equidistant-cells)
3. [Spatially varying temperature (Dirichlet) boundary conditions](#3-spatially-varying-temperature-dirichlet-boundary-conditions)
4. [Heat-flux (Neumann) boundary conditions](#4-heat-flux-neumann-boundary-conditions)
5. [Spatially varying conductivity](#5-spatially-varying-conductivity)
6. [Temperature-dependent conductivity](#6-temperature-dependent-conductivity)
7. [Source terms, linearized and implicit](#7-source-terms-linearized-and-implicit)
8. [Convective boundary conditions](#8-convective-boundary-conditions)
9. [Linear solver and discretization settings](#9-linear-solver-and-discretization-settings)
10. [Convergence: residuals and stopping the iterations](#10-convergence-residuals-and-stopping-the-iterations)
11. [Post-processing](#11-post-processing)
12. [Putting it together: Allrun](#12-putting-it-together-allrun)
13. [Common errors](#13-common-errors)

Appendix A. [Other options, also for older OpenFOAM versions](#appendix-a-other-options-also-for-older-openfoam-versions)

The examples use case 1 and case 11 from the course:

| | Case 1 | Case 11 |
|---|---|---|
| Domain | L = 1, H = 0.5 | L = H = 1 |
| Boundary 1 (south, y = 0) | convective, h = 1000, T∞ = 35 | T = 10 |
| Boundary 2 (east, x = L) | T = 10 + 20 sin(πy/H) | T = 20 |
| Boundary 3 (north, y = H) | T = 10 | T = 20x/L |
| Boundary 4 (west, x = 0) | dT/dn = 0 | dT/dn = 0 |
| Conductivity | k = 5(1 + 100x/L) | k = 2(1 + 20T/T1), T1 = 10 |
| Source term | b = −1.5 | b = 15(c1 − c2T²), c1 = 20, c2 = 0.2 |

The other cases use the same building blocks. To run all 40 cases with ready-made
scripts, continue with [Task_1_02_all_cases.md](Task_1_02_all_cases.md).

**OpenFOAM version:** This tutorial is for OpenFOAM-v2606 from openfoam.com, installed
as in [01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md). Other options, also working in
older versions, are given in [Appendix A](#appendix-a-other-options-also-for-older-openfoam-versions).


## 1. Steady heat conduction with laplacianFoam

`laplacianFoam` solves

    ddt(T) − laplacian(DT, T) = fvOptions(T)

and the course equation is

    ∂/∂x(k ∂T/∂x) + ∂/∂y(k ∂T/∂y) + b = 0.

Three changes to the flange setup make these the same.

**Steady state.** Switch off the time derivative in `system/fvSchemes`:
```cpp
ddtSchemes
{
    default         steadyState;
}
```
Each "time step" is now one iteration (one update of the coefficients and one call
to the linear solver). Use `deltaT 1` and let `endTime` be the maximum number of
iterations (`system/controlDict`):
```cpp
startTime       0;
endTime         10000;     // maximum number of iterations
deltaT          1;
writeControl    timeStep;
writeInterval   10000;     // write only at the end (see Section 10)
```

**Conductivity.** In the flange tutorial, DT is a constant in
`constant/transportProperties`. If a field file `0/DT` exists, `laplacianFoam` reads
that field instead and ignores `transportProperties`, so DT can vary in space and be
changed during the run. Use `DT` for k:
```cpp
FoamFile { version 2.0; format ascii; class volScalarField; object DT; }

dimensions      [0 2 -1 0 0 0 0];   // what laplacianFoam expects
internalField   uniform 1;          // set properly in Sections 5 and 6

boundaryField
{
    "(south|east|north|west)"
    {
        type            calculated;
        value           uniform 1;
    }
    frontAndBack
    {
        type            empty;
    }
}
```
OpenFOAM expects DT in m²/s (a diffusivity). Here DT simply holds the numbers of k
in W/(m K). With T in K, the source term b in `fvOptions` then has the unit W/m³.
The dimension checks don't mind, because all terms are scaled consistently.

**Source term.** b is added through `system/fvOptions` (Section 7).

**Initial condition.** The course code starts from T = 0, so use
`internalField uniform 0;` in `0/T`.

Keep the original files in `0.orig/` and start `Allrun` with `restore0Dir`, as in the
flange tutorial. The utilities in the next sections modify the files in `0/`.


## 2. A 2D mesh with non-equidistant cells

OpenFOAM meshes are always 3D. A 2D case is a mesh that is **one cell thick** in z,
with the front and back faces in a patch of type `empty`. Name the four sides after
their boundary numbers in the task, so that the dictionaries are easy to read:

| Task boundary | Location | Patch name |
|---|---|---|
| 1 | y = 0 | `south` |
| 2 | x = L | `east` |
| 3 | y = H | `north` |
| 4 | x = 0 | `west` |
| – | z = 0 and z = thickness | `frontAndBack` (type `empty`) |

A `system/blockMeshDict` for case 11 (L = H = 1, 20 × 20 cells), with cells that are
smaller near the boundaries:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }

L   1;
H   1;

vertices
(
    (0  0  0) ($L 0  0) ($L $H 0) (0 $H 0)
    (0  0  1) ($L 0  1) ($L $H 1) (0 $H 1)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (20 20 1)
    simpleGrading
    (
        // (fraction of length, fraction of cells, last/first cell size)
        ((0.5 0.5 3) (0.5 0.5 0.333))   // x: fine at both ends
        ((0.5 0.5 3) (0.5 0.5 0.333))   // y: fine at both ends
        1
    )
);

boundary
(
    south        { type patch; faces ((0 1 5 4)); }
    east         { type patch; faces ((1 2 6 5)); }
    north        { type patch; faces ((3 7 6 2)); }
    west         { type patch; faces ((0 4 7 3)); }
    frontAndBack { type empty; faces ((0 3 2 1) (4 5 6 7)); }
);
```
Run `blockMesh` and `checkMesh`. `checkMesh` should report the mesh as OK with zero
non-orthogonality.

Notes:
- **Grading.** The course recommends that neighbouring cells differ in size by at most
  about 15 %. With n cells and a total expansion ratio R, the ratio between neighbours
  is R^(1/(n−1)). For 10 cells in each half and R = 3 this is 1.13.
- **Course meshes.** The course mesh generator can also write the mesh directly in
  OpenFOAM format (`constant/polyMesh`). Use that to get exactly the same mesh as in
  your own code (for example the validation mesh). Copy the `constant/polyMesh`
  directory into the case and skip `blockMesh`. If a side is split into several
  patches (`south_0`, `south_1`, …), use regular-expression patch names in the field
  files, e.g. `"south.*"`.
- **Per unit depth.** OpenFOAM integrates over the real face areas and cell volumes,
  so heat rates come out for the thickness of the mesh. Use thickness 1, or divide
  heat rates by the thickness, to get W/m as in the course code.
- **Nodes.** OpenFOAM is cell-centred. The cell centres are the nodes of the course
  code. The boundary face centres are the boundary nodes. The corner nodes of the
  course code are only used to hold values for visualization. OpenFOAM stores no
  values there, but ParaView shows values interpolated to all mesh points, including
  the corners, when *Create cell-to-point filtered data* is ticked.


## 3. Spatially varying temperature (Dirichlet) boundary conditions

Example: boundary 2 of case 1, T = 10 + 20 sin(πy/H).

**Recommended: an expression in the boundary condition.** `uniformFixedValue` takes
a function for its value. The function `expression` evaluates a formula on the patch,
in which `pos()` is the face centre. In `0.orig/T`:
```cpp
east
{
    type            uniformFixedValue;
    uniformValue
    {
        type        expression;
        variables   ("H = 0.5");
        expression  #{ 10 + 20*sin(pi()*pos().y()/H) #};
    }
    value           uniform 10;     // only used before the first evaluation
}
```
The expression language uses C++-like syntax: `pi()`, `sin`, `cos`, `exp`, `pow(a,b)`,
`sqr`, `mag`, `min`, `max`, `pos().x()`, `pos().y()`, and the conditional
`(cond ? a : b)`. Constants are defined in `variables` as `"name = value"`.

**Alternative: set the values once with a utility.** Keep the patch as an ordinary
`fixedValue` and let `setExprBoundaryFields` write the values into `0/T` before the
run. `system/setExprBoundaryFieldsDict`:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object setExprBoundaryFieldsDict; }

dirichletTemperatures
{
    field       T;
    expressions
    (
        {
            patch       east;
            target      value;
            variables   ("H = 0.5");
            expression  #{ 10 + 20*sin(pi()*pos().y()/H) #};
        }
        // ... one block per patch
    );
    keepPatches true;
}
```
Run it with `runApplication setExprBoundaryFields` in `Allrun` (after `restore0Dir`).
The result is an ordinary `fixedValue` patch with a `nonuniform` list of values,
which you can inspect in `0/T`.

A `fixedValue` patch contributes to the diagonal and the right-hand side of the
matrix for the adjacent cells. This is the same as setting the boundary node
temperature in the course code.

Other options, also working in older versions, are given in [Appendix A.1](#a1-spatially-varying-temperature-section-3).


## 4. Heat-flux (Neumann) boundary conditions

- Homogeneous (dT/dn = 0, insulated): `type zeroGradient;`. The boundary value is
  then equal to the temperature of the adjacent cell, as for the course code's
  boundary nodes.
- Prescribed gradient: `type fixedGradient; gradient uniform -50;`, or
  `uniformFixedGradient` with an `expression` (as in Section 3) for a varying gradient.
  The gradient is ∂T/∂n with **n pointing out of the domain**. A heat flux q into the
  domain therefore corresponds to `gradient = q/k`.


## 5. Spatially varying conductivity

Example: case 1, k = 5(1 + 100x/L).

The conductivity is needed in the cells and at the boundary faces. OpenFOAM
interpolates the cell values to the internal faces (Section 9), and uses the
boundary-face values of `DT` for the boundary faces.

**Cell values: `setExprFields`.** `system/setExprFieldsDict`:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object setExprFieldsDict; }

expressions
(
    DT
    {
        field       DT;
        variables   ("L = 1");
        expression  #{ 5*(1 + 100*pos().x()/L) #};
        dimensions  [0 2 -1 0 0 0 0];
    }
);
```

**Boundary values: `setExprBoundaryFields`.** Add a block to
`system/setExprBoundaryFieldsDict`, with one entry per patch:
```cpp
conductivity
{
    field       DT;
    expressions
    (
        {
            patch       south;
            target      value;
            variables   ("L = 1");
            expression  #{ 5*(1 + 100*pos().x()/L) #};
        }
        // ... same for east, north and west
    );
    keepPatches true;
}
```
Run `setExprBoundaryFields` and then `setExprFields` in `Allrun`, before the solver.
k doesn't change during the run, so this is all you need.

**Region-dependent conductivity.** Example: k = 0.01 in 0.7 < x < 1.1,
0.3 < y < 0.4, and k = 20 elsewhere. You can use a conditional expression in
`setExprFieldsDict`:
```cpp
expression  #{ (pos().x() > 0.7 && pos().x() < 1.1 && pos().y() > 0.3 && pos().y() < 0.4)
               ? 0.01 : 20 #};
```
Or use the classic `setFields` with `system/setFieldsDict`:
```cpp
defaultFieldValues ( volScalarFieldValue DT 20 );
regions
(
    boxToCell
    {
        box (0.7 0.3 -1) (1.1 0.4 2);
        fieldValues ( volScalarFieldValue DT 0.01 );
    }
);
```
Both select cells by their **cell centre**, like the nodes in the course code. The
region doesn't touch the boundary here, so the boundary values in `0.orig/DT` can
simply be `uniform 20`.

How k is interpolated to the faces matters a lot when k jumps between neighbouring
cells. See `laplacianSchemes` in Section 9.


## 6. Temperature-dependent conductivity

Example: case 11, k = 2(1 + 20T/T1).

The equation is now nonlinear. As in the course code, it is solved by Picard
iteration: k is computed from the latest temperature, the linear system is solved
with this k, k is updated again, and so on. In OpenFOAM, k is updated after each
iteration by a function object, and at the boundary faces by a boundary condition.

**Cell values: the `exprField` function object.** It re-evaluates `DT` after every
iteration. In `system/controlDict`:
```cpp
functions
{
    conductivity
    {
        type            exprField;
        libs            (fieldFunctionObjects);
        field           DT;
        action          modify;          // change the existing field DT
        variables       ("T1 = 10");
        expression      "2*(1 + 20*T/T1)";
        writeControl    writeTime;       // otherwise DT is written every iteration
    }
    // ... other function objects
}
```

**Boundary values: an expression boundary condition on `DT`.** In a patch expression,
`T` is the boundary value of T on that patch. `0.orig/DT`:
```cpp
boundaryField
{
    "(south|east|north|west)"
    {
        type            uniformFixedValue;
        uniformValue
        {
            type        expression;
            variables   ("T1 = 10");
            expression  #{ 2*(1 + 20*T/T1) #};
        }
        value           uniform 2;       // k(T = 0), used in the first iteration
    }
    frontAndBack
    {
        type            empty;
    }
}
```
The boundary values are updated when the function object modifies `DT`. For the
initial cell values, use `setExprFields` as in Section 5, with the same expression
(it reads the initial T = 0).

Notes:
- **Order.** Function objects are executed in the order they are listed. List
  `conductivity` before function objects that use k, such as the course residual
  (Section 10).
- **Fields in expressions.** Fields used in expressions must be registered (`T` and
  `DT` always are in `laplacianFoam`). For a utility like `setExprFields`, add
  `readFields (T);` to its dictionary.
- **No `setExprBoundaryFields` for `DT` with patterns.** Don't use
  `setExprBoundaryFields` on a field whose patches are given by a pattern such as
  `"(south|east|north|west)"` (see Section 13). Here it isn't needed anyway.
- **Same result, different path.** The converged result is the same whatever the
  first-iteration k is. Only the convergence history changes a little.

Other options, also working in older versions, are given in [Appendix A.2](#a2-temperature-dependent-conductivity-section-6).


## 7. Source terms, linearized and implicit

**Linearization.** In finite-volume form, the source in a cell is written
b = Su + Sp·T_P, as in the course:
- Su goes to the right-hand side.
- −Sp·ΔV goes to the diagonal coefficient a_P.

With **Sp ≤ 0** this makes the matrix more diagonally dominant, so the Gauss-Seidel
or CG iterations converge better. This is what "implicit" means for a source term.

For b(T) = 15(c1 − c2T²), linearize around the latest temperature T\*:

    b ≈ b(T*) + (db/dT)(T*)·(T − T*)
      = 15(c1 − c2T*²) − 30c2T*·(T − T*)

    Sp = −30 c2 T*                (≤ 0 for T* ≥ 0)
    Su = 15(c1 − c2T*²) − Sp·T* = 15(c1 + c2T*²)

At convergence, T = T\* and Su + Sp·T = b(T) exactly.

**Constant source: `semiImplicitSource`.** `system/fvOptions` for b = −1.5:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object fvOptions; }

source
{
    type            scalarSemiImplicitSource;   // note "scalar" in the type name
    selectionMode   all;                        // all cells
    volumeMode      specific;                   // values per m3 (W/m3)
    sources
    {
        T           (-1.5 0);                   // (Su Sp)
    }
}
```

**Temperature-dependent source.** The explicit (Su) and implicit (Sp) parts can be
expressions, evaluated with the latest T in each iteration:
```cpp
source
{
    type            scalarSemiImplicitSource;
    selectionMode   all;
    volumeMode      specific;
    sources
    {
        T
        {
            explicit
            {
                type        exprField;
                variables   ("c1 = 20" "c2 = 0.2");
                expression  "15*(c1 + c2*T*T)";         // Su
            }
            implicit
            {
                type        exprField;
                variables   ("c2 = 0.2");
                expression  "-30*c2*max(T, 0)";         // Sp, kept <= 0
            }
        }
    }
}
```
Use `max(T, 0)` so that Sp stays ≤ 0 also for negative temperatures during the
iterations. You could also put the whole source in `explicit` and use `implicit 0`.
That is fully explicit and converges more slowly, and may not converge at all for a
strongly temperature-dependent source.

A source in only part of the domain: use `selectionMode cellZone;` and
`cellZone myZone;`. Create the zone with `topoSet`, e.g. a `boxToCell` cellSet
converted to a cellZone with `setToCellZone`.

Other options, also working in older versions, are given in [Appendix A.3](#a3-temperature-dependent-source-section-7).


## 8. Convective boundary conditions

Example: boundary 1 of case 1, −k ∂T/∂n = h(T_b − T∞), with h = 1000 and T∞ = 35.

**Derivation.** Let T_P be the temperature in the adjacent cell and δ the distance
from its centre to the boundary face. The face is a node without volume, so the
conductive flux from the face into the cell equals the convective flux to the face:

    h (T∞ − T_b) = k_b (T_b − T_P) / δ

Solving for the face value:

    T_b = f T∞ + (1 − f) T_P,      f = h / (h + k_b/δ)

This is exactly OpenFOAM's `mixed` boundary condition:

    T_b = f·refValue + (1 − f)·(T_P + δ·refGradient)

with refValue = T∞, refGradient = 0 and valueFraction = f.

**Why this is implicit.** The heat rate through the face becomes

    Q = k_b (T_b − T_P)/δ · A = A (T∞ − T_P) / (1/h + δ/k_b)

which is linear in T_P. The mixed condition puts the T_P part on the diagonal of the
matrix and the T∞ part on the right-hand side, so the boundary condition is fully
implicit. This is the series resistance 1/h + δ/k of the convective film and the
half cell.

**`uniformMixed` with an expression.** The expression needs
δ. Patch expressions have no direct access to δ, so it is computed from the face
centre `pos()` and the cell centre. The cell centres must be available as a field
`C`, see below. In `0.orig/T`:
```cpp
south
{
    type            uniformMixed;
    uniformValue    constant 35;                // T_inf
    uniformGradient constant 0;
    uniformValueFraction
    {
        type        expression;
        variables
        (
            "h = 1000"
            "delta = mag((pos() - internalField(C)) & normal())"
        );
        expression  #{ h/(h + DT/delta) #};     // DT = k at the boundary face
    }
    value           uniform 35;
}
```

The field `C` has to be written before the run and loaded during it:
- In `Allrun`, after `restore0Dir`:
  ```sh
  runApplication postProcess -func writeCellCentres -time 0
  ```
- First in the `functions` of `controlDict`:
  ```cpp
  readC
  {
      type            readFields;
      libs            (fieldFunctionObjects);
      fields          (C);
  }
  ```

If k depends on T at the boundary, the condition uses the latest `DT` boundary values
from Section 6.

Other options, also working in older versions, are given in [Appendix A.4](#a4-convective-boundary-conditions-section-8).


## 9. Linear solver and discretization settings

**Course-like settings.** The course code does a fixed number of Gauss-Seidel sweeps
per iteration (`nLinSolIter`). In `system/fvSolution`:
```cpp
solvers
{
    T
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        nSweeps         1;
        tolerance       0;          // never stop early ...
        relTol          0;
        minIter         10;         // ... but always do exactly 10 sweeps
        maxIter         10;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
}
```
OpenFOAM sweeps through the cells in its own cell order, which can differ from the
loop order in your code. The convergence history is therefore similar but not
identical.

**Efficient settings.** The matrix is symmetric, so the preconditioned conjugate
gradient method is a good choice:
```cpp
T
{
    solver          PCG;
    preconditioner  DIC;
    tolerance       1e-12;
    relTol          0;
}
```
A linear case (k and b independent of T) then converges in one iteration. A
nonlinear case needs a few Picard iterations.

**Discretization** (`system/fvSchemes`):
```cpp
laplacianSchemes
{
    default         Gauss linear corrected;   // k: linear interpolation to the faces
}
snGradSchemes
{
    default         corrected;                // face gradient (T_N − T_P)/|d|
}
interpolationSchemes
{
    default         linear;
}
gradSchemes
{
    default         Gauss linear;             // only used in post-processing
}
divSchemes
{
    default         none;
}
```
- `linear` interpolation of k to a face uses the distances to the two cell centres,
  as in the course code on non-equidistant meshes.
- For a conductivity that jumps between cells (region-dependent k), try
  `Gauss harmonic corrected`. It gives the face conductivity of two resistances in
  series and is the physically correct choice there.
- The meshes are orthogonal, so `corrected` and `orthogonal` give the same result.
  `orthogonal` skips the (zero) correction.


## 10. Convergence: residuals and stopping the iterations

**OpenFOAM's residual.** The log reports for each iteration

    Solving for T, Initial residual = …, Final residual = …, No Iterations …

The *initial residual* is Σ|b − A·T| for the T of the previous iteration, divided by a
normalization factor computed from the matrix and the solution. This is *not* the
course residual, which normalizes by the total heat rate F. Both decrease as the
iterations converge, but the values differ.

**Stopping on OpenFOAM's residual.** `laplacianFoam` uses the `SIMPLE` dictionary, so
you can stop when the initial residual is small enough:
```cpp
SIMPLE
{
    nNonOrthogonalCorrectors 0;
    residualControl
    {
        T           1e-6;
    }
}
```
The log then says `SIMPLE solution converged in N iterations`, and the last iteration
is written.

**The course residual ε (coded function object).** The course residual is

    ε = Σ_cells |a_P T_P − (Σ a_nb T_nb + Su)| / F

where F is the total heat rate into the domain: through the boundaries and from
positive sources. OpenFOAM can give you the matrix of the latest iteration, so ε can
be computed with a short coded function object. Put it in `system/courseResidual`
and include it in the `functions` of `controlDict`, after `conductivity` if you have
one:
```cpp
courseResidual
{
    type            coded;
    libs            (utilityFunctionObjects);
    name            courseResidual;
    resTol          1e-3;

    codeInclude
    #{
        #include "fvCFD.H"
        #include "fvOptions.H"
    #};
    codeOptions
    #{
        -I$(LIB_SRC)/finiteVolume/lnInclude \
        -I$(LIB_SRC)/meshTools/lnInclude
    #};
    codeLibs
    #{
        -lfiniteVolume \
        -lmeshTools
    #};
    codeData
    #{
        scalar resTol_;
    #};
    codeRead
    #{
        resTol_ = dict.get<scalar>("resTol");
    #};
    codeExecute
    #{
        volScalarField& T = const_cast<volScalarField&>
            (mesh().lookupObject<volScalarField>("T"));
        const volScalarField& DT = mesh().lookupObject<volScalarField>("DT");

        // The discretized equation for the latest T, as in laplacianFoam
        fv::options& fvOptions = fv::options::New(mesh());
        tmp<fvScalarMatrix> tSource = fvOptions(T);
        fvScalarMatrix TEqn(-fvm::laplacian(DT, T));
        TEqn -= tSource();

        // F = heat rate into the domain through the boundaries + positive sources
        scalar F = 0;
        forAll(T.boundaryField(), patchi)
        {
            const fvPatchScalarField& Tp = T.boundaryField()[patchi];
            F += sum(max(DT.boundaryField()[patchi]*Tp.snGrad()*Tp.patch().magSf(),
                         scalar(0)));
        }
        const scalarField bV
        (
            tSource().diag()*T.primitiveField() - tSource().source()
        );
        F += sum(max(bV, scalar(0)));

        const scalar eps = sum(mag(TEqn.residual()))/F;
        Info<< "courseResidual: epsilon = " << eps << nl;

        if (eps < resTol_)
        {
            const_cast<Time&>(mesh().time()).writeAndEnd();
        }
    #};
}
```
Notes:
- `TEqn.residual()` is the residual of each cell. `bV` is the source b·ΔV of each
  cell. `DT·snGrad(T)·A` is the heat rate into the domain through each boundary face.
- Both the residual and F scale with the mesh thickness, so ε is independent of it.
- **Variables inside the code.** Values from `#include`d files (`$resTol`) are not
  visible inside the `#{ … #}` code. Read them from the function-object dictionary in
  `codeRead`, as above.
- **Fields written at the end.** `writeAndEnd()` writes the fields of the last
  iteration, but `laplacianFoam`'s own extra fields (`gradTx`, `flux`, …) are only
  written at regular write times. Section 11 therefore computes the heat flux with
  function objects.
- **Other stopping rules.** If neither a residual criterion nor `endTime` is reached,
  the run stops at `endTime`, i.e. after the maximum number of iterations.

**Plotting residual histories.** The `solverInfo` function object writes the
OpenFOAM residuals to `postProcessing/solverInfo/0/solverInfo.dat`:
```cpp
solverInfo
{
    type            solverInfo;
    libs            (utilityFunctionObjects);
    fields          (T);
}
```
The utility `foamLog log.laplacianFoam` extracts residuals and other values from the
log into `logs/`. `foamMonitor -l postProcessing/solverInfo/0/solverInfo.dat` plots
them during the run (it needs gnuplot). For ε, filter the log, e.g.
`grep 'courseResidual' log.laplacianFoam`.


## 11. Post-processing

Function objects can run during the simulation (in `functions` of `controlDict`) or
afterwards on the written results. For running them afterwards, use the solver in
post-processing mode:
```sh
laplacianFoam -postProcess -dict system/postProcessDict -latestTime
```
This reads `T`, `DT` and `fvOptions` exactly as the solver does. The utility
`postProcess` only reads the fields you name with `-fields '(T DT)'`.

`system/postProcessDict` holds a `functions` dictionary like the one in
`controlDict`. The function objects below can all go into it.

### Temperature distribution

Create an empty file `case.foam` and open it in ParaView. T is
cell data, as in the course code. Tick *Create cell-to-point filtered data* in
*Properties* (not ticked by default in ParaView 6.2), or use the filter
*Cell Data to Point Data*, for smooth contours
(*Contour* filter, or colouring with a discrete colour map). Use the *Mesh Regions*
list to show the boundary patches, which carry the boundary values.

The extreme values, including the boundary values, are given by:
```cpp
TminMax
{
    type            fieldMinMax;
    libs            (fieldFunctionObjects);
    fields          (T);
    location        true;
}
```

### Heat-flux vectors

The heat flux is q = −k∇T. Compute k∇T with two function objects:
```cpp
gradT
{
    type            grad;
    libs            (fieldFunctionObjects);
    field           T;
    result          gradT;
}
kGradT
{
    type            multiply;
    libs            (fieldFunctionObjects);
    fields          (DT gradT);
    result          kGradT;          // = k grad(T) = -q
}
```
In ParaView, use the *Calculator* with the expression `-kGradT` to get q, and then
*Glyph* (arrows) to show the vectors.

At the boundary faces, the normal component of `gradT` is the face-normal gradient
(T_b − T_P)/δ, so `kGradT` at the boundaries gives the wall heat flux directly (see
below). `laplacianFoam` also writes a field `flux` = k∇T, but only at regular write
times (Section 10).

### Wall heat flux and heat rate through each boundary

The heat rate *into* the domain through a boundary is ∫ k ∂T/∂n dA, with n pointing
out of the domain:
```cpp
heatRateSouth
{
    type            surfaceFieldValue;
    libs            (fieldFunctionObjects);
    regionType      patch;
    name            south;
    operation       areaNormalIntegrate;    // sum over faces of kGradT·n A
    fields          (kGradT);
    writeFields     true;                   // also write the values of each face ...
    surfaceFormat   raw;                    // ... as a text file
}
heatRateEast    { $heatRateSouth;  name east;  }   // inherits all other entries
heatRateNorth   { $heatRateSouth;  name north; }
heatRateWest    { $heatRateSouth;  name west;  }
```
- The heat rates are in `postProcessing/heatRate*/0/surfaceFieldValue.dat`. Positive
  means into the domain. Divide by the mesh thickness for W/m.
- The face values are in `postProcessing/heatRateSouth/surface/<time>/kGradT_patch_south.raw`,
  with columns x y z and the components of k∇T. The wall-normal heat flux out of the
  domain is −k∇T·n. On `south` the normal is n = (0, −1, 0), so q_wall = kGradT_y.

### Source heat rate and global heat balance

Evaluate b with the final temperature and integrate over the domain:
```cpp
b
{
    type            exprField;
    libs            (fieldFunctionObjects);
    field           b;
    expression      "15*(20 - 0.2*T*T)";
}
sourceHeatRate
{
    type            volFieldValue;
    libs            (fieldFunctionObjects);
    regionType      all;
    operation       volIntegrate;
    fields          (b);
    writeFields     false;
}
```
Global energy balance: the sum of the four boundary heat rates plus the source heat
rate should be close to zero. Divide by F to get the relative imbalance, as in the
course code. Its size depends on how well the iterations have converged (with
ε < 10⁻³, expect around 10⁻³).

To split each boundary into in- and outgoing parts (Din, Dout), sum the positive and
negative face values of the raw files. The coded `courseResidual` function object
(Section 10) already computes F this way and can easily print Din, Dout, Sin and Sout
too.

### Monitored temperature

The temperature in the cell that contains a point, after each iteration:
```cpp
probes
{
    type            probes;
    libs            (sampling);
    fields          (T);
    probeLocations
    (
        (0.43 0.43 0.5)      // z inside the mesh (thickness 1)
    );
}
```
Output: `postProcessing/probes/0/T`. Put this in `controlDict` (not in the
post-processing dictionary) to get the history over the iterations. A point exactly
on a mesh line is ambiguous (two cells contain it), so choose a point inside a cell.
This is also what the course code does: it monitors a node.

### Profiles along lines (mesh study)

```cpp
centreline
{
    type            sets;
    libs            (sampling);
    interpolationScheme cellPoint;
    setFormat       raw;
    fields          (T);
    sets
    {
        horizontal
        {
            type    face;           // one point at each crossed face
            axis    x;
            start   (0 0.5 0.5);
            end     (1 0.5 0.5);
        }
    }
}
```
Output: `postProcessing/centreline/<time>/horizontal_T.xy`. Use `type uniform;` with
`nPoints 100;` for equidistant points instead.

### Mesh study

Copy the case, change the mesh (cell numbers in `blockMeshDict`, or another mesh
from the mesh generator), and rerun. Compare the monitored temperatures, extreme
values, boundary heat rates and profiles from the files above. The `checkMesh` log
gives the number of cells, the minimum and maximum cell volumes (cell size times
thickness in 2D) and the maximum aspect ratio. The convergence history (number of iterations to reach ε <
resTol) can also be compared between meshes, e.g. equidistant vs non-equidistant
with the same number of cells.


## 12. Putting it together: Allrun

Files of a case like case 1, without compiled code:
```
0.orig/T                          boundary conditions (Sections 3, 4, 8), internalField 0
0.orig/DT                         conductivity field (Sections 1, 5, 6)
constant/polyMesh/                from blockMesh or the mesh generator
system/blockMeshDict              (Section 2)
system/controlDict                steady iterations, function objects (readC, conductivity,
                                  courseResidual, probes, solverInfo)
system/fvSchemes                  steadyState, Gauss linear corrected
system/fvSolution                 GaussSeidel sweeps or PCG, residualControl
system/fvOptions                  source term (Section 7)
system/setExprFieldsDict          initial conductivity in the cells
system/setExprBoundaryFieldsDict  Dirichlet profiles and boundary conductivity (if used)
system/courseResidual             course residual (Section 10, optional, compiled)
system/postProcessDict            heat flux, heat rates, profiles (Section 11)
```
`Allrun`:
```sh
#!/bin/sh
cd "${0%/*}" || exit                                # Run from this directory
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions

restore0Dir
runApplication blockMesh
runApplication checkMesh

# Cell centres, for the convective boundary condition (Section 8)
runApplication postProcess -func writeCellCentres -time 0

# Dirichlet profiles and boundary conductivity (Sections 3 and 5)
runApplication setExprBoundaryFields
# Initial conductivity in the cells (Sections 5 and 6)
runApplication setExprFields

runApplication $(getApplication)

# Heat flux, heat rates, profiles (Section 11)
runApplication -s post $(getApplication) -postProcess -dict system/postProcessDict -latestTime
```
`Allclean`:
```sh
#!/bin/sh
cd "${0%/*}" || exit
. ${WM_PROJECT_DIR:?}/bin/tools/CleanFunctions
cleanCase0      # removes time directories, 0/, logs, postProcessing, dynamicCode
                # and constant/polyMesh
```
Remove the lines you don't need, e.g. `writeCellCentres` if there is no convective
boundary. `cleanCase0` also deletes `constant/polyMesh`. If you use a mesh from the
mesh generator instead of `blockMesh`, keep it as `constant/polyMesh.orig` and
replace `runApplication blockMesh` in `Allrun` with
`cp -r constant/polyMesh.orig constant/polyMesh`.


## 13. Common errors

| Message or symptom | Cause and fix |
|---|---|
| `Unknown fvOption type semiImplicitSource` | The type name includes the field type: `scalarSemiImplicitSource`. |
| `Object C does not exist or wrong type in expression` | Write the cell centres to `0/` (`postProcess -func writeCellCentres -time 0`) and load them with the `readFields` function object (Section 8). |
| `compound has already been transferred from token` | `setExprBoundaryFields` was used on a field whose patch entry is a pattern like `"(south\|east)"`. List the patches separately, or don't use the utility for that field. |
| `Entry 'object' not found` | Broken `FoamFile` header, e.g. a missing `;` or line break. |
| A new time directory every iteration | A function object writes a field every iteration. Add `writeControl writeTime;` to it. |
| Compile errors in coded entries using `$name` | Only the dictionary entries of the coded object itself are available inside the code. Read them in `codeRead` (Section 10). |
| No `flux`/`gradTx` in the last time directory | The run stopped with `writeAndEnd()` or `residualControl`. Compute them with the function objects in Section 11. |
| Probe value jumps between meshes | The probe point lies on a mesh line. Move it slightly into a cell. |
| Heat rates a factor 10 too small or large | Mesh thickness is not 1. Divide by the thickness. |
| The case diverges with a temperature-dependent source | The source is treated explicitly, or Sp > 0. Linearize as in Section 7 with Sp ≤ 0. |

## Next

Now you can continue with [Task_1_02_all_cases.md](Task_1_02_all_cases.md).


## Appendix A: Other options, also for older OpenFOAM versions

The setup without any compiled code needs **v2306 or newer**; it has been tested with
v2312 and v2412. Older versions (v2012 and newer) need the coded alternatives shown in
some sections. These are compiled automatically at run time. The openfoam.org versions
(OpenFOAM-11, 12, …) use different syntax and are not covered.

### A.1 Spatially varying temperature (Section 3)

The `exprFixedValue` condition can be used instead of `uniformFixedValue` with an
expression. It still works in v2606, but is deprecated since v2212. Another option is
`codedFixedValue`, which needs compiling. It also works in v2606, but the setup in
Section 3 needs no compiling.

### A.2 Temperature-dependent conductivity (Section 6)

Before v2206, k can be updated in `codeCorrect` of a `scalarCodedSource` in
`system/fvOptions`. This also works in v2606, but the setup in Section 6 needs no
compiling. `codeCorrect` is called after each
solution of T:
```cpp
codeCorrect
#{
    volScalarField& DT =
        const_cast<volScalarField&>(mesh_.lookupObject<volScalarField>("DT"));
    forAll(DT, celli)
    {
        DT[celli] = 2*(1 + 20*fld[celli]/10);
    }
    forAll(DT.boundaryField(), patchi)
    {
        const scalarField& Tb = fld.boundaryField()[patchi];
        scalarField& DTb = DT.boundaryFieldRef()[patchi];
        forAll(DTb, facei)
        {
            DTb[facei] = 2*(1 + 20*Tb[facei]/10);
        }
    }
#};
```
(`fld` is the solved field T.) A complete `scalarCodedSource` also needs the entries
`codeAddSup` and `codeConstrain`, which can be empty (see [A.3](#a3-temperature-dependent-source-section-7)).

### A.3 Temperature-dependent source (Section 7)

Expressions in `scalarSemiImplicitSource` need v2206 or newer. In older versions, use a
coded fvOption instead. This also works in v2606, but the setup in Section 7 needs no
compiling. `codeAddSup` adds the linearized source to the
matrix. The matrix stores its right-hand side with the opposite sign, hence the
`-=`:
```cpp
caseProperties
{
    type            scalarCodedSource;
    name            caseProperties;
    selectionMode   all;
    fields          (T);

    codeAddSup
    #{
        const scalarField& V = mesh_.V();
        const scalarField& T = eqn.psi().primitiveField();
        scalarField& diag = eqn.diag();
        scalarField& source = eqn.source();
        forAll(V, celli)
        {
            const scalar Sp = -30*0.2*max(T[celli], scalar(0));
            const scalar Su = 15*(20 - 0.2*sqr(T[celli])) - Sp*T[celli];
            diag[celli] += Sp*V[celli];
            source[celli] -= Su*V[celli];
        }
    #};
    codeCorrect
    #{
    #};
    codeConstrain
    #{
    #};
}
```

### A.4 Convective boundary conditions (Section 8)

Before v2306, use `codedMixed` instead of `uniformMixed` with an expression (v2012
and newer, no extra files needed). This also works in v2606, but the setup in
Section 8 needs no compiling. `codedMixed` has direct access to the patch quantities. `deltaCoeffs()` is 1/δ:
```cpp
south
{
    type            codedMixed;
    name            convective_south;
    refValue        uniform 35;
    refGradient     uniform 0;
    valueFraction   uniform 1;
    value           uniform 35;
    code
    #{
        const scalar h = 1000;
        const scalarField& k =
            this->patch().template lookupPatchField<volScalarField, scalar>("DT");
        this->refValue() = 35;
        this->refGrad() = Zero;
        this->valueFraction() = h/(h + k*this->patch().deltaCoeffs());
    #};
}
```
It is compiled the first time the case runs (into `dynamicCode/`, which takes about
10–20 s).

## Next

Now you can continue with [Task_1_02_all_cases.md](Task_1_02_all_cases.md).
