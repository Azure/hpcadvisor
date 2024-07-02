# Files and Dirs

## UI defaults

This JSON file is used as input for both CLI and GUI to deploy environments,
collect data, plot graphs, and get advice.

It currently has these fields:

- `subscription`: subscription name used to provision resources
- `rgprefix`: prefix of resource group name used to host all resources
- `region`: Azure geographical region of deployment (e.g. eastus,
  southcentralus,...)
- `appsetupurl`: url that contains the bash script with instructions on how to
  download input data and application, and how to run the application
- `skus`: Azure SKUs (VM types) to be tested
- `nnodes`: Number of nodes to be tested
- `ppr`: percentage of processes per resource
- `appinputs`: application inputs (e.g. matrix size and number of execution
  interactions for the matrix multiplication application)
- `vpnrg` (optional): existing resource group that contains a vpn setup
- `vpnvnet` (optional): existing vnet name for the vpn setup
- `peervpn` (optional): boolean for peering with vpn resource group / vnet
- `createjumpbox` (optional): boolean for creating a VM in the same resource
group




## Data filter

This JSON file specifies which parts of the dataset one wants to use for plotting
graphs or getting advice (pareto-front). You can specify the
application name, and the deployment environments, which can be useful in case
data was collected using a few deployments but one does not want to consider all
deployments for that particular application.

```
{
  "deployment": [
    "myresourcegroup"
  ],
  "appname": "wrf4"
}
```

##  Main HPCAdvisor dir

All files related to deployment, dataset, task output, among others are stored
in the main HPCAdvisor folder, located at:

```
$HOME/.hpcadvisor/
```


## Deployment dirs

Every deployment contains a directory located at:

```
$HOME/.hpcadvisor/<deploymentname>
```

## Task stderr and stdout

For each task executed, two files are collected:

Standard error and standard output:

```
$HOME/.hpcadvisor/<deploymentname/output-<taskname>/stderr.txt
$HOME/.hpcadvisor/<deploymentname/output-<taskname>/stdout.txt
```
