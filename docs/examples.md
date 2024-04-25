# Examples


Examples of applications to be tested using hpcadvisor:




## Matrix Multiplication

As a starting example, here we have a matrix multiplication application. This
"hello world" application receives two parameters: size of the squared matrix
(dimension) and number of times such multiplication should happen (e.g. only
once, or 10, or 100, etc).

The files for this example are in the [examples
folder](https://github.com/Azure/hpcadvisor/tree/main/examples/matrixmult)
which has three files:

- `mpi_matrix_mult.c`: source code of the application.
- `appsetup_matrix.sh`: shell script that downloads the source file,
  compiles it, and generates the application run script that will be used for
  each execution scenario.
- `plotfilter_matrixmult.json`: filter to get consider only data for
  this application when generating the plots and the recommendation
  (pareto-front data).
- `ui_defaults.json`: user input to create the environment,
  setup application, scenarios to be explored.

```json title="ui_defaults.json"
{
  "subscription": "mysubscription",
  "skus": [
    "Standard_HC44rs",
    "Standard_HB120rs_v2",
    "Standard_HB120rs_v3"
  ],
  "rgprefix": "nettoaha",
  "appsetupurl": "https://raw.githubusercontent.com/Azure/hpcadvisor/main/examples/matrixmult/appsetup_matrix.sh",
  "nnodes": [
    2,
    3,
    4
  ],
  "appname": "matrixmult",
  "tags": {
    "appname": "matrixmult",
    "version": "v1"
  },
  "region": "southcentralus",
  "createjumpbox": true,
  "ppr": 100,
  "appinputs": {
    "appinteractions": "3",
    "appmatrixsize": [
      "4000",
      "7000"
    ]
  }
}
```

``` title="ui_defaults.json"
--8<-- "https://raw.githubusercontent.com/Azure/hpcadvisor/main/examples/matrixmult/ui_defaults.json"
```


## WRF

- [Weather Research & Forecasting Model (WRF)](examples/wrf)

## GROMACS

- [GROningen MAchine for Chemical Simulations (GROMACS)](examples/gromacs)

## OpenFOAM

- [Open Field Operation and Manipulation (OpenFOAM)](examples/openfoam)

## NAMD

- [Nanoscale Molecular Dynamics (NAMD)](examples/namd)
