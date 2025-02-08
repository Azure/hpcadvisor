# How-To


## Add datapoint to dataset


Assume you have your own way of running a job, with your own way of setting up
the environment. You've learnt how the job behaved and would like to add this
datapoint to the HPCAdvisor dataset file. Here is how you can do it.

First, the dataset file is located at `$HOME/.hpcadvisor/dataset.json`. You
don't need to create this file; HPCAdvisor will create for you.

Now you need a json file with your data point created by yourself. For instance:

```json
    {
      "timestamp": "2024-07-28-10-46",
      "sku": "standard_hc44rs",
      "nnodes": 4,
      "total_cores": 176,
      "ppr_perc": 100,
      "cpu_usage": [
        33.079166666666666,
        33.547,
        33.17916666666667,
        40.756428571428565
      ],
      "exec_time": 432,
      "appinputs": {
        "BLOCKMESH_DIMENSIONS": "60 18 18"
      },
      "deployment": "myenvironment",
      "region": "southcentralus",
      "appname": "openfoam",
      "tags": {
        "appname": "openfoam",
        "version": "v8",
        "resolution": "60_18_18",
        "poolid": "pool-2407280944qsb",
        "taskid": "task-compute-2407281039pak"
      },
      "appexectime": 165,
      "appmetrics": {
        "FOAMRUNCLOCKTIME": "165",
        "FOAMMESHCELLS": "8257533",
        "APPEXECTIME": "165"
      }
    }
```

Once HPCAdvisor is installed or enabled via `poetry` (see installation guide), just run:

```bash
./bin/hpcadvisor  dataset add -i mydatapoint.json
```


