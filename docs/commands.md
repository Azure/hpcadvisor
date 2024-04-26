# Commands


There are five hpcadvisor commands:

- `deploy`: operations related to a deployment
- `plot`: operation(s) related to generation of plots
- `collect`: operation(s) related to data collection (i.e. execution of tasks)
- `advice`: operations(s) related to generation of advice
- `gui`: trigger of the graphical user interface (gui) via browser

These commands can use the debug mode via `-d` flag.

A deployment is a resource group that contains all computing resources.

So in general the usage of the hpcadvisor is gonna be:





```
./hpcadvisor [-d] <command> [ <command parameters> ]
```

## deploy


Create a new deployment using user input from file (mandatory) and name of the
deployment (optional):

```
./hpcadvisor deploy create -u <ui_defaults_file> [-n <name>]
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

to-be-documented

## plot

to-be-documented

## advice

to-be-documented

## gui

to-be-documented


---


