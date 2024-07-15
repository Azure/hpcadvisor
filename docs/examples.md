# Examples

Here we have a few examples how to use HPCAdvisor. For each example, we have
different mechanisms to setup the application. As the application setup is based
on bash script, users can install in different ways, using for instance source
code, binary download, easybuild, EESSI, spack, etc..

Examples of applications to be tested using hpcadvisor:


## Matrix Multiplication

As a "Hello World" example, we are gonna use matrix multiplication application,
which receives two parameters: size of the squared matrix (dimension) and number
of times such multiplication should happen (e.g. only once, 10 times, 100 times,
and so on).

The files for this example are in the [examples
folder](https://github.com/Azure/hpcadvisor/tree/main/examples/matrixmult)
which has three files:

- `mpi_matrix_mult.c`: source code of the application.
- `appsetup_matrix.sh`: shell script that downloads the source file, compiles
  it, and generates the application run script that will be used for each
  execution scenario.
- `plotfilter_matrixmult.json`: filter to consider only data for this
  application when generating the plots and the recommendation (pareto-front
  data).
- `ui_defaults.json`: user input to create the environment, setup application,
  and define scenarios to be explored.

```json title="ui_defaults.json"
--8<-- "https://raw.githubusercontent.com/Azure/hpcadvisor/main/examples/matrixmult/ui_defaults.json"
```


## WRF

The Weather Research and Forecasting (WRF) Model is a well known system for
meteorologists and researchers to simulate and predict weather patterns at
various spatial and temporal scales. WRF can simulate atmospheric processes,
including dynamics, thermodynamics, and microphysical processes. The model can
be configured for different domains, resolutions, and parameterizations, and it
is widely used for benchmarking HPC systems.

The example for this app ([files
here](https://github.com/Azure/hpcadvisor/tree/main/examples/wrf/)) is based on
installation using [EESSI](https://www.eessi.io/).


## GROMACS

The GROMACS (GROningen MAchine for Chemical Simulations) project originally
began in 1991 at Department of Biophysical Chemistry, University of Groningen,
Netherlands. GROMACS is widely used in computational chemistry, biochemistry,
and related fields for simulating the behavior of molecules at the atomic level.

The example for this app ([files
here](https://github.com/Azure/hpcadvisor/tree/main/examples/gromacs/)) is based on
installation using [EESSI](https://www.eessi.io/).

## OpenFOAM

OpenFOAM (Open Field Operation and Manipulation) is a free, open-source computational fluid dynamics (CFD) software package developed by the OpenFOAM Foundation. OpenFOAM has an extensive range of features to solve anything from complex fluid flows involving chemical reactions, turbulence and heat transfer, to acoustics, solid mechanics and electromagnetics. OpenFOAM uses the finite volume method to discretize and solve the governing equations of fluid flow and other related physical phenomena. OpenFOAM is used in several industries including automotive, aerospace, energy, environmental engineering, chemical processing, and academic research. OpenFOAM is professionally released every six months to include customer sponsored developments and contributions from the community. It is written in C++ is modular, which allows customizations.

The example for this app ([files
here](https://github.com/Azure/hpcadvisor/tree/main/examples/openfoam/)) is based on
installation using [EESSI](https://www.eessi.io/).


## NAMD

Nanoscale Molecular Dynamics (NAMD) is a parallel molecular dynamics code
designed for high-performance simulation of large biomolecular systems,
including proteins, nucleic acids, and membranes, at the atomic level over
time.It is particularly valuable for understanding processes such as protein
folding, biomolecular recognition, and drug binding, among others. NAMD is
developed and maintained by the Theoretical and Computational Biophysics Group
at the University of Illinois at Urbana-Champaign.

The example for this app ([files
here](https://github.com/Azure/hpcadvisor/tree/main/examples/namd/)) is based on
installation using the binary from NAMD official website.


## LAMMPS

Large-scale Atomic/Molecular Massively Parallel Simulator (LAMMPS) is
a molecular dynamics simulator designed to model particles in a variety of
scientific and engineering applications. Developed by Sandia National
Laboratories, it is highly scalable, so one can run it on single processors or
in parallel using message-passing techniques. LAMMPS uses spatial-decomposition
techniques to partition the simulation domain into small 3D sub-domains, one of
which is assigned to each processor.

The example for this app ([files
here](https://github.com/Azure/hpcadvisor/tree/main/examples/lammps/)) is based
on installation using [EESSI](https://www.eessi.io/).
