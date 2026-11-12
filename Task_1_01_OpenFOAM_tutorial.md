# Setting up a Task 1 case in OpenFOAM

This tutorial shows, step by step, how to set up, run and post-process a 2D steady heat-conduction case like those of Task 1 in OpenFOAM. Everything is done with OpenFOAM dictionaries, utilities and function objects.

The tutorial is quite complex. The Task 1 cases have many features that are uncommon in practice, such as boundary temperatures given by formulas, a conductivity that depends on position, region and temperature, and a temperature-dependent source term. Setting them all up in OpenFOAM therefore gives a quite thorough learning experience.

You are assumed to know how to run the `flange` tutorial of `laplacianFoam`. If you are new to OpenFOAM, start with [04_The_OpenFOAM_flange_tutorial.md](04_The_OpenFOAM_flange_tutorial.md).

The tutorial is for OpenFOAM-v2606, installed as in [01_Install_OpenFOAM-v2606_WSL.md](01_Install_OpenFOAM-v2606_WSL.md).

**The finished case.** The case that you set up in this tutorial is also available, finished, in the directory `Task_1_OpenFOAM/Task1` of the course project. If something doesn't work, you can run it or compare your files with it (see [The finished case](#the-finished-case) at the end).

1. [The tutorial case](#1-the-tutorial-case)
2. [Copy the flange tutorial](#2-copy-the-flange-tutorial)
3. [Mesh](#3-mesh)
4. [Temperature initial guess and boundary conditions](#4-temperature-initial-guess-and-boundary-conditions)
5. [Conductivity](#5-conductivity)
6. [Source term](#6-source-term)
7. [Discretization and linear solver](#7-discretization-and-linear-solver)
8. [Course residual](#8-course-residual)
9. [Iterations, monitoring and results](#9-iterations-monitoring-and-results)
10. [Run the case](#10-run-the-case)
11. [Look at the results](#11-look-at-the-results)
12. [Set up your own case](#12-set-up-your-own-case)
13. [Common errors](#13-common-errors)


## 1. The tutorial case

The 40 cases of Task 1 are built from a small number of building blocks:

| Building block | Variants in the 40 cases |
|---|---|
| Domain | L = 1 or 1.5, H = 0.5, 1 or 2 |
| Dirichlet boundary | constant T, T varying with x, T varying with y |
| Neumann boundary | dT/dn = 0 |
| Convective boundary | −k dT/dn = h(T − T∞), h = 1000 |
| Conductivity | varying with x, region-dependent (a jump), T-dependent, varying with y and T |
| Source term | constant (also 0), quadratic in T |

The tutorial case is not one of the 40 cases. It is designed to contain all the building blocks:

| | Tutorial case |
|---|---|
| Domain | L = 1.5, H = 0.5 |
| Boundary 1 (south, y = 0) | convective, h = 1000, T∞ = 25 |
| Boundary 2 (east, x = L) | T = 10 + 20 sin(πy/H) |
| Boundary 3 (north, y = H) | T = 5(1 + x/L) |
| Boundary 4 (west, x = 0) | dT/dn = 0 |
| Conductivity | k = 0.01 for 0.7 < x < 1.1 and 0.3 < y < 0.4, k = 2(1 + 10x/L + 20T/T1) elsewhere, T1 = 10 |
| Source term | b = 15(c1 − c2T²), c1 = 20, c2 = 0.2 |
| Monitoring points | (0.43L, 0.43H) = (0.645, 0.215) and (0.77L, 0.77H) = (1.155, 0.385) |

The constant Dirichlet values and the constant source term are special cases of the varying ones. Section 12 shows how to change the blocks for your own case.

**The equation and the solver.** The cases are 2D steady heat-conduction problems, governed by the course equation

    ∂/∂x(k ∂T/∂x) + ∂/∂y(k ∂T/∂y) + b = 0.

The standard OpenFOAM solver `laplacianFoam` solves

    ddt(T) − laplacian(DT, T) = fvOptions(T)

This is the course equation if the time derivative `ddt(T)` is switched off (with `steadyState` in `system/fvSchemes`, Section 7), the field `DT` holds the conductivity k (the file `0.orig/DT`, Section 5), and the source term b is added as an fvOption, `fvOptions(T)` (the file `system/fvOptions`, Section 6). The cases can therefore be run with `laplacianFoam`, without changing the solver.

If you are interested, the top-level code of `laplacianFoam` is in `$FOAM_SOLVERS/basic/laplacianFoam/laplacianFoam.C`. The equation is written there as `fvm::ddt(T) - fvm::laplacian(DT, T) == fvOptions(T)`.


## 2. Copy the flange tutorial

Copy a fresh `flange` tutorial to a case directory named `Task1`, and go there:
```sh
cp -r $FOAM_TUTORIALS/basic/laplacianFoam/flange $FOAM_RUN/Task1
cd $FOAM_RUN/Task1
```
In the next sections, you create or replace the files of the case one at a time. Use `nano` (save with Ctrl+O and Enter, exit with Ctrl+X).

There is no `0/` directory. As in the flange tutorial, `Allrun` creates it by copying `0.orig/`. The utilities and the solver then modify the files in `0/`, while the files in `0.orig/` are kept unchanged.


## 3. Mesh

Create the file `system/blockMeshDict`:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }

L   1.5;
H   0.5;
D   0.1;            // thickness in z

vertices
(
    (0  0  0) ($L 0  0) ($L $H 0) (0 $H 0)
    (0  0  $D) ($L 0  $D) ($L $H $D) (0 $H $D)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (30 20 1)
    simpleGrading
    (
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
Run:
```sh
blockMesh
checkMesh
```
`checkMesh` should end with `Mesh OK.`

- **2D.** OpenFOAM meshes are always 3D. A 2D case has a mesh that is one cell thick in z, with the front and back faces in a patch of type `empty`.
- **Patch names.** The four sides are named after the boundaries of the task: `south` (boundary 1, y = 0), `east` (boundary 2, x = L), `north` (boundary 3, y = H) and `west` (boundary 4, x = 0).
- **Cells.** 30 × 20 cells, smaller near the boundaries. `((0.5 0.5 3) (0.5 0.5 0.333))` means: the first half of the length has half of the cells, and the last cell is 3 times larger than the first, and the other way around in the second half. The size ratio between neighbouring cells is then 3^(1/14) = 1.08 in x and 3^(1/9) = 1.13 in y, below the 15 % recommended in the course.
- **Thickness.** The mesh is `D` = 0.1 m thick, the same as from the course mesh generator. The heat rates are divided by the thickness in `system/controlDict` (Section 9), so that they come out per unit depth (W/m), as in the course code.
- **Nodes.** OpenFOAM stores the temperature in the cell centres, which are the nodes of the course code. The boundary face centres are the boundary nodes.


## 4. Temperature initial guess and boundary conditions

The initial guess and the boundary conditions of T can be set directly in `0.orig/T`.

Replace the content of `0.orig/T` with:
```cpp
FoamFile { version 2.0; format ascii; class volScalarField; object T; }

dimensions      [0 0 0 1 0 0 0];
internalField   uniform 0;

boundaryField
{
    south
    {
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        Ta              constant 25;
        h               uniform 1000;
        kappaMethod     lookup;
        kappa           DT;
        value           uniform 25;
    }
    east
    {
        type            uniformFixedValue;
        uniformValue
        {
            type        expression;
            variables   ("H = 0.5");
            expression  #{ 10 + 20*sin(pi()*pos().y()/H) #};
        }
        value           uniform 10;
    }
    north
    {
        type            uniformFixedValue;
        uniformValue
        {
            type        expression;
            variables   ("L = 1.5");
            expression  #{ 5*(1 + pos().x()/L) #};
        }
        value           uniform 5;
    }
    west
    {
        type            zeroGradient;
    }
    frontAndBack
    {
        type            empty;
    }
}
```
- **Initial guess.** `internalField uniform 0` starts the iterations from T = 0, as the course code.
- **Dirichlet boundaries (east and north).** `uniformFixedValue` with an `expression` evaluates a formula at each boundary face. `pos()` is the face centre, so `pos().x()` is x and `pos().y()` is y. Constants are set in `variables`. The expressions use C++-like syntax: `pi()`, `sin`, `cos`, `exp`, `pow(a,b)`, `sqr`, `min`, `max`.
- **Neumann boundary (west).** `zeroGradient` gives dT/dn = 0. The boundary value is equal to the temperature in the adjacent cell.
- **Convective boundary (south).** The heat flux from the cell to the face equals the convective heat flux from the face, h(T∞ − T_b) = k_b(T_b − T_P)/δ, where T_P is the temperature in the adjacent cell, T_b the boundary value, and δ the distance between the cell centre and the face. This gives T_b = f T∞ + (1 − f) T_P with f = h/(h + k_b/δ). The boundary condition `externalWallHeatFluxTemperature` with `mode coefficient` does exactly this, with T∞ given by `Ta` and h by `h`. It is implicit, i.e. the T_P part goes into the matrix.
- **`kappaMethod lookup`** and **`kappa DT`** make it take k_b from the boundary values of the field `DT` (Section 5).
- **`externalWallHeatFluxTemperature`** is in the library `thermoTools`. It requires the line `libs (thermoTools);` in `system/controlDict` (Section 9).
- **`value`** is a placeholder for the boundary values, e.g. for ParaView, which reads the values from the file without evaluating the boundary condition. OpenFOAM evaluates the boundary condition and writes the computed values in `value` in the result files.


## 5. Conductivity

The conductivity k in the course equation is the field `DT` in the equation solved by `laplacianFoam` (see "The equation and the solver" in Section 1). In the flange tutorial, DT is a constant in `constant/transportProperties`. If a file `0/DT` exists, `laplacianFoam` reads that field instead, so k can vary in space and change during the run.

The boundary values of k can be set directly in `0.orig/DT`, with expressions in the boundary conditions. The values in the cells can't be given as expressions in that file, so they are set with the utility `setExprFields` before the run (Section 10).

Create the file `0.orig/DT`:
```cpp
FoamFile { version 2.0; format ascii; class volScalarField; object DT; }

dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 2;

boundaryField
{
    "(south|east|north|west)"
    {
        type            uniformFixedValue;
        uniformValue
        {
            type        expression;
            variables   ("L = 1.5" "T1 = 10");
            expression  #{ 2*(1 + 10*pos().x()/L + 20*T/T1) #};
        }
        value           uniform 2;
    }
    frontAndBack
    {
        type            empty;
    }
}
```
- **Boundary values.** The boundary condition sets DT at each boundary face, from the boundary value of T.
- **`internalField uniform 2`** is only a placeholder. The cell values are set by `setExprFields`. The entries `value uniform 2` are placeholders for the boundary values, in the same way as `value` in `0.orig/T` (Section 4).
- **Unit.** OpenFOAM expects DT in m²/s (a diffusivity). Here DT simply holds the values of k in W/(m K), and the source term then has the unit W/m³. The dimension checks don't mind, since all terms are scaled in the same way.

Create the file `system/setExprFieldsDict`:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object setExprFieldsDict; }

readFields      (T);

expressions
(
    DT
    {
        field       DT;
        variables   ("L = 1.5" "T1 = 10");
        expression  #{ (pos().x() > 0.7 && pos().x() < 1.1 && pos().y() > 0.3 && pos().y() < 0.4) ? 0.01 : 2*(1 + 10*pos().x()/L + 20*T/T1) #};
        dimensions  [0 2 -1 0 0 0 0];
    }
);
```
- **Cell values.** The utility `setExprFields` reads `system/setExprFieldsDict` and sets DT in the cells only once, when it is run by `Allrun` before the simulation starts (Section 10). It uses the initial guess of the temperature, T = 0 (`internalField` in `0.orig/T`, Section 4). In a cell expression, `pos()` is the cell centre. The region is selected with a conditional expression `(condition) ? a : b`, which gives `a` where the condition is true and `b` elsewhere. A cell is in the region if its centre is, like a node in the course code. The region doesn't touch the boundary, so the expression in `0.orig/DT` has no condition.
- **`readFields (T);`** makes `setExprFields` read T, which is used in the expression.
- **T-dependent k.** During the simulation, DT is updated from the latest temperature after each iteration. In the cells, this is done by the function object `conductivity` in `system/controlDict` (Section 9), which uses the same expression as `system/setExprFieldsDict`. If you change the expression, change it in both files. At the boundary faces, it is done by the boundary condition in `0/DT`, with the latest boundary temperature. This is the Picard iteration of the course code.


## 6. Source term

The source term must be added directly to the coefficients of the discretized equations, i.e. we need to manipulate the discretization. We do that without touching the original solver `laplacianFoam`, using an fvOption of type `scalarCodedSource`. fvOptions are extra terms that `laplacianFoam` adds to its equation (the term `fvOptions(T)` in the equation solved by `laplacianFoam`, see "The equation and the solver" in Section 1).

The source term integrated over a cell, b·ΔV, is split as Su + Sp·T_P, as in the course, where T\* is the latest temperature:

    Su = 15 c1 ΔV
    Sp = −15 c2 T* ΔV                    (≤ 0 for T* ≥ 0)

As in the course code, Su goes to the right-hand side of the equation system, and −Sp goes to the diagonal coefficient a_P. This is done by the small piece of code in the fvOption, which OpenFOAM compiles the first time the case is run.

Create the file `system/fvOptions`:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object fvOptions; }

source
{
    type            scalarCodedSource;
    name            source;
    selectionMode   all;
    fields          (T);

    codeAddSup
    #{
        const scalar c1 = 20;
        const scalar c2 = 0.2;
        const scalarField& V = mesh_.V();
        const scalarField& T = eqn.psi().primitiveField();
        scalarField& diag = eqn.diag();
        scalarField& source = eqn.source();
        forAll(V, celli)
        {
            const scalar Su = 15*c1*V[celli];
            const scalar Sp = -15*c2*max(T[celli], scalar(0))*V[celli];
            diag[celli] += Sp;
            source[celli] -= Su;
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
- **`codeAddSup`** is called each time the equation for T is set up, i.e. once per iteration, with the latest temperature `T`.
- **`V`** is the cell volume ΔV.
- **`diag`** holds the coefficients of T in the source term, and `source` the rest, with the opposite sign. `diag += Sp` puts −Sp in a_P, since the source term is on the other side of the equation.
- **Sp ≤ 0** makes the matrix more diagonally dominant, which makes the iterations converge better. `max(T, 0)` keeps Sp ≤ 0 also if T becomes negative during the iterations. T is positive in the converged solution, so it doesn't change the result.
- At convergence, T_P = T\* and Su + Sp·T_P = b(T_P)·ΔV.
- **`codeCorrect`** and **`codeConstrain`** are not used, but must be there.


## 7. Discretization and linear solver

Replace the content of `system/fvSchemes` with:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }

ddtSchemes
{
    default         steadyState;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
}
laplacianSchemes
{
    default         Gauss linear orthogonal;
}
interpolationSchemes
{
    default         linear;
}
snGradSchemes
{
    default         orthogonal;
}
```
Replace the content of `system/fvSolution` with:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }

solvers
{
    T
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        nSweeps         1;
        tolerance       0;
        relTol          0;
        minIter         10;
        maxIter         10;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
}
```
- **`steadyState`** switches off the time derivative `ddt(T)` in the equation solved by `laplacianFoam` (see "The equation and the solver" in Section 1). Each "time step" is then one iteration: k and b are updated, and the linear solver is called once.
- **`Gauss linear orthogonal`** interpolates k linearly to the faces (`linear`), using the distances to the two cell centres, as in the course code. The face gradient is (T_N − T_P)/|d| (`orthogonal`).
- **`orthogonal`** is used because the mesh is orthogonal: the line between two cell centres is perpendicular to the face between them. On a non-orthogonal mesh, `corrected` must be used instead, which adds a correction for the non-orthogonality.
- **Linear solver.** As in the course code, each iteration does a fixed number of Gauss-Seidel sweeps (`nLinSolIter` = 10): `minIter` and `maxIter` are both 10, and `tolerance 0` and `relTol 0` make sure that the solver never stops earlier. OpenFOAM sweeps through the cells in its own order, so the convergence history is similar to, but not the same as, that of your code.


## 8. Course residual

Everything in this section is only for computing and printing the normalized residual in the same form as in Task 1, and stopping the simulation and writing out the result when the normalized residual reaches the convergence criterion. Without it, the simulation continues until `endTime` in `system/controlDict` (Section 9), i.e. 10000 iterations. OpenFOAM can also stop on its own residual, with `residualControl` in `system/fvSolution`, but that is not covered here.

OpenFOAM's own residual (`Initial residual` in the log) is normalized in another way than the course residual. The course residual is calculated as

    ε = Σ_cells |a_P T_P − (Σ a_nb T_nb + Su)| / F

where F is the total heat rate into the domain, through the boundaries and from positive source terms. The normalized residual ε is computed by a function object of type `coded`, i.e. a function object with a small piece of code, which OpenFOAM compiles the first time the case is run. Function objects are executed after each iteration (Section 9).

The function object is put in a separate file, which is included in `system/controlDict` (Section 9). It could also have been placed directly in `system/controlDict`, but a separate file keeps `controlDict` easier to read.

Create the file `system/courseResidual`:
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
- It sets up the discretized equation of the latest temperature, in the same way as `laplacianFoam`, and computes ε with the matrix residual `TEqn.residual()`.
- It writes `courseResidual: epsilon = …` to the log after each iteration.
- It stops the run when ε < `resTol`, and writes the results of the last iteration.


## 9. Iterations, monitoring and results

Replace the content of `system/controlDict` with:
```cpp
FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }

application     laplacianFoam;

thickness       0.1;            // mesh thickness in z

libs            (thermoTools);


startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         10000;          // maximum number of iterations
deltaT          1;              // one "time step" = one iteration

writeControl    timeStep;
writeInterval   10000;          // write only at the end
purgeWrite      0;
writeFormat     ascii;
writePrecision  12;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable false;

functions
{
    conductivity
    {
        type            exprField;
        libs            (fieldFunctionObjects);
        field           DT;
        action          modify;
        variables       ("L = 1.5" "T1 = 10");
        expression      "(pos().x() > 0.7 && pos().x() < 1.1 && pos().y() > 0.3 && pos().y() < 0.4) ? 0.01 : 2*(1 + 10*pos().x()/L + 20*T/T1)";
        writeControl    writeTime;
    }
    #include "courseResidual"
    probes
    {
        type            probes;
        libs            (sampling);
        fields          (T);
        probeLocations
        (
            (0.645 0.215 #eval{0.5*$thickness})
            (1.155 0.385 #eval{0.5*$thickness})
        );
    }
    TminMax
    {
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        fields          (T);
        location        true;
    }
    gradT
    {
        type            grad;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        field           T;
        result          gradT;
    }
    kGradT
    {
        type            multiply;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        fields          (DT gradT);
        result          kGradT;
    }
    heatRateSouth
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        regionType      patch;
        name            south;
        operation       areaNormalIntegrate;
        fields          (kGradT);
        writeFields     true;
        surfaceFormat   raw;
        scaleFactor     #eval{1/$thickness};   // per unit depth
    }
    heatRateEast    { $heatRateSouth;  name east;  }
    heatRateNorth   { $heatRateSouth;  name north; }
    heatRateWest    { $heatRateSouth;  name west;  }
    b
    {
        type            exprField;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        field           b;
        variables       ("c1 = 20" "c2 = 0.2");
        expression      "15*(c1 - c2*T*T)";
    }
    sourceHeatRate
    {
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        executeControl  writeTime;
        writeControl    writeTime;
        regionType      all;
        operation       volIntegrate;
        fields          (b);
        writeFields     false;
        scaleFactor     #eval{1/$thickness};   // per unit depth
    }
    centreline
    {
        type            sets;
        libs            (sampling);
        executeControl  writeTime;
        writeControl    writeTime;
        interpolationScheme cellPoint;
        setFormat       raw;
        fields          (T);
        sets
        {
            horizontal
            {
                type    face;
                axis    x;
                start   (0 0.25 #eval{0.5*$thickness});
                end     (1.5 0.25 #eval{0.5*$thickness});
            }
        }
    }
}
```
- **`libs (thermoTools)`** loads the library with the boundary condition `externalWallHeatFluxTemperature` (Section 4).
- **`thickness`** is the mesh thickness in z, the same as `D` in `system/blockMeshDict` (Section 3). It is used below as `$thickness`: `#eval{0.5*$thickness}` puts the monitoring points and the centreline in the middle of the mesh in z, and `scaleFactor #eval{1/$thickness}` divides the heat rates by the thickness, to get them per unit depth.
- **Iterations.** `deltaT 1` and `endTime 10000` give at most 10000 iterations. The results are written at the end, either when `courseResidual` stops the run or after the last iteration.
- **`functions`** are function objects, which are executed after each iteration, in the order they are listed:
  - `conductivity` updates DT in the cells from the latest T. `action modify` changes the existing field `DT`. `writeControl writeTime` makes it write DT only at the end.
  - `#include "courseResidual"` includes the file of Section 8. It comes after `conductivity`, so that it uses the latest DT.
  - `probes` writes the temperature at the monitoring points after each iteration. It gives the temperature in the cell that contains the point. Points exactly on a mesh line are ambiguous, so the points are chosen inside cells.
  - The others are only executed at the end (`executeControl writeTime`):
    - `TminMax` gives the minimum and maximum temperature, including the boundary values.
    - `gradT` and `kGradT` compute ∇T and k∇T. The heat flux is q = −k∇T. At the boundary faces, the normal component of `gradT` is the face-normal gradient (T_b − T_P)/δ.
    - `heatRateSouth`, … integrate k∇T·n over each boundary, which is the heat rate into the domain (n points out of the domain). `heatRateEast { $heatRateSouth; name east; }` copies all entries of `heatRateSouth`, except `name`.
    - `b` and `sourceHeatRate` evaluate the source term with the final temperature and integrate it over the domain.
    - `centreline` writes the temperature along the line y = H/2, at each crossed face, for the mesh study.


## 10. Run the case

Replace the content of `Allrun` with:
```sh
#!/bin/sh
cd "${0%/*}" || exit                                # Run from this directory
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions

restore0Dir
runApplication blockMesh
runApplication checkMesh
runApplication setExprFields
runApplication $(getApplication)
```
Replace the content of `Allclean` with:
```sh
#!/bin/sh
cd "${0%/*}" || exit                                # Run from this directory
. ${WM_PROJECT_DIR:?}/bin/tools/CleanFunctions      # Tutorial clean functions

cleanDynamicCode() { :; }                           # keep the compiled code
cleanCase0
```
`cleanCase0` removes everything that `Allrun` creates. The line before it makes it keep the compiled code in the directory `dynamicCode`, so that it doesn't have to be compiled again in the next run. The code is compiled again automatically if you change it.

Run the case. The first time, it takes some additional time, since the code in `system/fvOptions` and `system/courseResidual` is compiled:
```sh
./Allrun
```
The commands in `Allrun`:
- `restore0Dir` copies `0.orig/` to `0/`.
- `blockMesh` and `checkMesh` create and check the mesh.
- `setExprFields` sets DT in the cells from the initial guess of the temperature.
- `$(getApplication)` runs the solver given in `controlDict`, i.e. `laplacianFoam`.

Each command writes its output to a log file, e.g. `log.laplacianFoam`. Check the convergence:
```sh
grep epsilon log.laplacianFoam
```
ε should go below 0.001 after about 45 iterations, and the last time directory is then written. To run the case again, first remove all results with:
```sh
./Allclean
```


## 11. Look at the results

**Heat rates and energy balance.** Print the heat rates through the boundaries and from the source term:
```sh
grep 'areaNormalIntegrate(\|volIntegrate(' log.laplacianFoam
```
You should get approximately:
```
    areaNormalIntegrate(south) of kGradT = 2961
    areaNormalIntegrate(east) of kGradT = 1333
    areaNormalIntegrate(north) of kGradT = -3759
    areaNormalIntegrate(west) of kGradT = 0
    volIntegrate(region0) of b = -529
```
Positive values are into the domain, in W/m. The sum, about 5 W/m, is the global imbalance. Divided by F (approximately the sum of the positive boundary heat rates, see Section 8), it is about 0.001, as expected with ε < 0.001.

**Files.** All results are written to `postProcessing/`:

| File | Content |
|---|---|
| `probes/0/T` | T at the monitoring points, after each iteration |
| `TminMax/0/fieldMinMax.dat` | minimum and maximum T, and their locations |
| `heatRateSouth/0/surfaceFieldValue.dat`, … | heat rate through each boundary |
| `heatRateSouth/surface/<time>/kGradT_patch_south.raw`, … | k∇T at each boundary face: x, y, z and the three components. The wall heat flux out of the domain is −k∇T·n. On `south`, n = (0, −1, 0), so it is the y component of k∇T. |
| `sourceHeatRate/0/volFieldValue.dat` | heat rate from the source term |
| `centreline/<time>/horizontal_T.xy` | x and T along y = H/2 |

`<time>` is the number of the last iteration. The files are text files that you can plot, for example with Python.

**ParaView.** Create an empty file that tells ParaView that this is an OpenFOAM case:
```sh
touch Task1.foam
```
Open `Task1.foam` in ParaView, as in [02_Install_ParaView_Windows.md](02_Install_ParaView_Windows.md), and click *Apply*. Go to the last time.
- **Temperature.** Colour by `T`. Tick *Create cell-to-point filtered data* in *Properties* and click *Apply*, to get smooth colours from values interpolated to the mesh points. Use the *Mesh Regions* list to also show the boundary patches, which have the boundary values.
- **Heat-flux vectors.** Use the filter *Calculator* with the expression `-kGradT` (this is q), and then the filter *Glyph* to show arrows.
- **Conductivity.** Colour by `DT` to see k, including the region.

**Mesh study.** Copy the case and remove the results in the copy:
```sh
cp -r $FOAM_RUN/Task1 $FOAM_RUN/Task1_60x40
cd $FOAM_RUN/Task1_60x40
./Allclean
```
Change the number of cells in `system/blockMeshDict` to `(60 40 1)`, and run `./Allrun`. Compare the monitored temperatures, the extreme values, the heat rates and the centreline profiles. The `checkMesh` log, `log.checkMesh`, gives the number of cells and the minimum and maximum cell volumes.


## 12. Set up your own case

Copy the tutorial case and remove the results in the copy, here for case 5:
```sh
cp -r $FOAM_RUN/Task1 $FOAM_RUN/Case_05
cd $FOAM_RUN/Case_05
./Allclean
```
Change the building blocks to those of your case, and run `./Allrun`. The table shows which files to change. The monitoring points of all cases are (0.43L, 0.43H) and (0.77L, 0.77H).

| Building block | What to change |
|---|---|
| Domain L, H | `L` and `H` in `system/blockMeshDict`, and in the `variables` of all expressions. The monitoring points in `probes` and the line in `centreline` in `system/controlDict`. |
| Constant Dirichlet value | In `0.orig/T`: `type fixedValue; value uniform 10;` |
| Dirichlet value varying with x or y | In `0.orig/T`: `uniformFixedValue` with your formula in `expression`, as on `east` and `north` |
| dT/dn = 0 | In `0.orig/T`: `type zeroGradient;` |
| Convective boundary | In `0.orig/T`: copy the `south` entry to the boundary, and set T∞ in `Ta` and `value`, and h in `h` |
| Conductivity | The expressions in `system/setExprFieldsDict`, `system/controlDict` (`conductivity`) and `0.orig/DT`. Examples below. |
| Constant source b | In `system/fvOptions`: `const scalar Su = -1.5*V[celli];` (your value of b) and `const scalar Sp = 0;`. The same value in `b` in `system/controlDict`. |
| Quadratic source | `c1` and `c2` in `system/fvOptions`, and in the `variables` of `b` in `system/controlDict` |

Conductivity expressions of the 40 cases (`x` is `pos().x()` and `y` is `pos().y()`):

| k in the task | Expression |
|---|---|
| 5(1 + 100x/L) | `5*(1 + 100*pos().x()/L)` |
| 0.01 in 0.7 < x < 1.1, 0.3 < y < 0.4, 20 elsewhere | `(pos().x() > 0.7 && pos().x() < 1.1 && pos().y() > 0.3 && pos().y() < 0.4) ? 0.01 : 20` in the cells, `20` at the boundaries |
| 2(1 + 20T/T1) | `2*(1 + 20*T/T1)` |
| 16(y/H + 30T/T1) | `16*(pos().y()/H + 30*T/T1)` |

Add the constants that an expression uses (`L`, `H`, `T1`) to its `variables`, and remove the ones it doesn't use. In the cases with a region (cases 6–10 and 26–30), the source term is zero. Use the constant source row with b = 0.

**The course meshes.** To get exactly the same mesh as in your Python code (for example the validation mesh), let the course mesh generator write the mesh in OpenFOAM format (`constant/polyMesh`). Save it in the case as `constant/polyMesh.orig`. Set `thickness` in `system/controlDict` to the thickness of the mesh (0.1 by default). In `Allrun`, replace the lines `runApplication blockMesh` and `runApplication checkMesh` with:
```sh
cp -r constant/polyMesh.orig constant/polyMesh
runApplication checkMesh
```
`Allclean` removes `constant/polyMesh`, but not `constant/polyMesh.orig`. If a side of the mesh is split into several patches (`south_0`, `south_1`, …), give the entries in `0.orig/T` and `0.orig/DT` names that match all of them, e.g. `"south.*"`.


## 13. Common errors

| Message or symptom | Cause and fix |
|---|---|
| `Unknown patchField type externalWallHeatFluxTemperature` | The library is not loaded. Check `libs (thermoTools);` in `system/controlDict`. |
| `Entry 'object' not found` | Broken `FoamFile` header, e.g. a missing `;`. |
| `Floating point exception` after some iterations, ε grows | The iterations diverge. Check that Sp ≤ 0 and k > 0. |
| The monitored temperature jumps between meshes | The monitoring point is on a mesh line. Move it slightly into a cell. |
| Heat rates a factor 10 too small or large | `thickness` in `system/controlDict` is not the thickness of the mesh. |


## The finished case

The finished case of this tutorial is in `Task_1_OpenFOAM/Task1` of the course project. Copy it to your run directory, with another name than your own case:
```sh
cp -r ~/MTF073_CFD_Tasks/Task_1_OpenFOAM/Task1 $FOAM_RUN/Task1_finished
```
Run it as in Section 10, with `./Allrun` in `$FOAM_RUN/Task1_finished`. To find a mistake in your own case, compare a file with the same file in the finished case, e.g.:
```sh
diff $FOAM_RUN/Task1/0.orig/T $FOAM_RUN/Task1_finished/0.orig/T
```
`diff` prints the lines that differ, and nothing if the files are the same.


## Next

Now you can continue with [Task_1_02_all_cases.md](Task_1_02_all_cases.md), which runs all 40 cases with ready-made scripts.

---

© 2026 Håkan Nilsson. Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
