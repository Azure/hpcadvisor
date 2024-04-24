# Examples


Examples of applications to be tested using hpcadvisor:




## Matrix Multiplication

As a starting example, here we have a matrix multiplication application. This
"hello world" application receives two parameters: size of the squared matrix
(dimension) and number of times such multiplication should happen (e.g. only
once, or 10, or 100, etc).

The files for this example are in the [examples folder](../examples/matrixmult),
which has three files:

- `mpi_matrix_mult.c`: which contains the source code of the application.
- `appsetup_matrix.sh`: which is a shell script that downloads the source file,
  compiles it, and generates the application run script that will be used for
  each execution scenario.
- `plotfilter_matrixmult.json`: which is a filter to get consider only data for
  this application when generating the plots and the recommendation
  (pareto-front data).


## WRF

- [Weather Research & Forecasting Model (WRF)](examples/wrf)

## GROMACS

- [GROningen MAchine for Chemical Simulations (GROMACS)](examples/gromacs)

## OpenFOAM

- [Open Field Operation and Manipulation (OpenFOAM)](examples/openfoam)

## NAMD

- [Nanoscale Molecular Dynamics (NAMD)](examples/namd)
