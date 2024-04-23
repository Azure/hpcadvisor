## HPC Advisor

### Goal and overview

The goal of this tool is to assist users in selecting a cluster configuration
based on actual application executions. Underneath, the execution of the
application is based on resources provisioned by [Azure
Batch](https://learn.microsoft.com/en-us/azure/batch/); but the data collected
can be used to make decisions for other environments including Azure CycleCloud,
Azure VMSS, Azure VMs, AKS, etc.

For now the tool focuses on testing:
- SKUs
- Number of cluster nodes
- Processes per node
- Application input parameters

For next versions we will explore other factors such as storage and gpus in
addition to other features related to avoiding scenarios to optimize unnecessary
tests.

The tool offers three operations:

**1.** **Data collector.** Run the application under multiple scenarios to
collect execution times and other metric data (for now cpu usage).

**2.** **Plot generator.** Generate several plots considering the collected
data, including exec time as a function of skus and number of nodes, cost as
a function of skus and number of nodes. In addition, plots all of these metrics
as a function of the application input parameters.

**3.** **Recommendation generator.** Generate the pareto front considering
execution time and costs. We leave to the user to make the final decision that
balances both metrics, as users may be willing to sacrifice execution time in
favor of cost for instance. We also provide as output the best time and best
cost.


It also has two execution modes, one via CLI (Command Line Interface) and the
other via web browser (GUI).


In this code we have examples to run tests with actual applications, including
WRF, OpenFOAM, NAMD, and GROMACS. Other apps will become available on the way.

---

#### Warning: This tool is still under major changes.

---

### Setup

The hpcadvisor setup is based on python poetry to handle dependencies and
a python virtual environment.

Check poetry installation guidelines [HERE](<https://python-poetry.org/docs/>).
Once poetry is installed run the following commands in your terminal to install
and create python virtual environment.

```
git clone https://github.com/Azure/hpcadvisor.git
cd hpcadvisor
poetry install
poetry shell
cd bin
```

---

### Getting started

Follow the matrix multiplication example here for detailed instructions.

##### CLI-based execution

Once the setup above (via poetry) is done, for the matrix multiplication
example, you just need to update `examples/matrixmult/ui_defaults.json` with
your preferences. For this example, you only need to update `subscription`,
and you should be good to go:

```
./hpcadvisor -u ../examples/matrixmult/ui_defaults.json
```

If you want to only test the plot generator component, skipping the data
collection, you need to copy a dataset file to hpcadvisor directory:

```
cp src/samples/dataset.json $HOME/.hpcadvisor/
./hpcadvisor -u ../examples/matrixmult/ui_defaults.json  \
                 -p \
                 -pf ../examples/matrixmult/plotfilter.json
```

To get the recommendation (pareto-front), just replace the flag `-p` (plot) to
`-r` (recommendation).

##### GUI-based execution (browser)

One can use the browser version and click the buttons for the different
operations. To pre-fill user input, specify the input file as showed below:

```
./hpcadvisor -g -u ../examples/matrixmult/ui_defaults.json
```

---

### Examples

Examples of applications to be tested using hpcadvisor:

- [Matrix Multiplication (Hello World)](examples/matrixmult)
- [Weather Research & Forecasting Model (WRF)](examples/wrf)
- [GROningen MAchine for Chemical Simulations (GROMACS)](examples/gromacs)
- [Open Field Operation and Manipulation (OpenFOAM)](examples/openfoam)
- [Nanoscale Molecular Dynamics (NAMD)](examples/namd)


### Configuration files


---
### Notes

1) If there is a problem while collecting data, resources may not be
auto-deleted. Watch out for that.

---
### Generate standalone binary

You can generate a standalone binary file using:
- poetry (https://python-poetry.org/docs/)
- pyinstaller (https://pyinstaller.org/en/stable/)

From project root folder, type:

```
poetry run pyinstaller src/hpcadvisor/__main__.py  --onefile --name hpcadvisor
```

---
## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
