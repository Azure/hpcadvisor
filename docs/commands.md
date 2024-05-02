# Commands


There are five hpcadvisor commands:

- `deploy`: operations related to a deployment
- `collect`: operation(s) related to data collection (i.e. execution of tasks)
- `plot`: operation(s) related to generation of plots
- `advice`: operations(s) related to generation of advice
- `gui`: trigger of the graphical user interface (gui) via browser

These commands can use the debug mode via `-d` flag and show help using `-h`.

A deployment is a resource group that contains all computing resources.

So in general the usage of the hpcadvisor is gonna be:

```
./hpcadvisor [-d] <command> [ <command parameters> ]
```

## deploy


Create a new deployment using user input from file (mandatory) and name of the
deployment (optional):

```
./hpcadvisor deploy create [-h] [-n NAME] [-u USERINPUT] operation


options:
  -n NAME, --name NAME  Deployment name
  -u USERINPUT, --userinput USERINPUT
                        User input
```

List deployments:

```
./hpcadvisor deploy list
```

Shutdown a deployment, which means deleting all resources and resource group.

```
./hpcadvisor deploy shutdown -n <name>
```

## collect

Collect data (i.e. run jobs). The option `cleardeployment` is to delete all
resources and resource group once the collection is completed and option
`cleartasks` is to run all new tasks that are created, as some tasks may have
already been completed for another data collection operation on the same
deployment.

```
./hpcadvisor collect [-h] -n NAME -u USERINPUT [-cd CLEARDEPLOYMENT] [-ct CLEARTASKS]

options:
  -n NAME, --name NAME  Deployment name
  -u USERINPUT, --userinput USERINPUT
                        User input
  -cd CLEARDEPLOYMENT, --cleardeployment CLEARDEPLOYMENT
                        Clear deployment
  -ct CLEARTASKS, --cleartasks CLEARTASKS
                        Clear tasks
```


## plot

Generate plots.

```
./hpcadvisor plot [-h] -df DATAFILTER

options:
  -df DATAFILTER, --datafilter DATAFILTER
                        Data filter
```

## advice


Generate advice (pareto-front).

```
hpcadvisor advice [-h] [-n NAME] [-df DATAFILTER]

options:
  -n NAME, --name NAME  Deployment name
  -df DATAFILTER, --datafilter DATAFILTER
                        Data filter
```


## gui

Run the hpcadvisor using browser (GUI).

```
./hpcadvisor gui [-h] [-u USERINPUT]

options:
  -u USERINPUT, --userinput USERINPUT
                        User input
```


---


