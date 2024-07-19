# Getting started


## Setup

The hpcadvisor setup is based on python poetry to handle dependencies and
a python virtual environment.

Check poetry installation guidelines [HERE](<https://python-poetry.org/docs/>).
Once poetry is installed run the following commands in your terminal to install
and create python virtual environment.

```bash
git clone https://github.com/Azure/hpcadvisor.git
cd hpcadvisor
poetry install
poetry shell
cd bin
```
### Generate standalone binary

Alternatively, you can generate a standalone binary file using:

- [poetry](https://python-poetry.org/docs/)
- [pyinstaller](https://pyinstaller.org/en/stable/)

From project root folder, type:

```
poetry run pyinstaller src/hpcadvisor/__main__.py  --onefile --name hpcadvisor
```


---


## Simple example

Follow the matrix multiplication example here for detailed instructions.


### CLI-based execution

Once the setup above (via poetry) is done, for the matrix multiplication
example, you just need to update `examples/matrixmult/ui_defaults.yaml` with
your preferences. For this example, you only need to update `subscription`,
and you should be good to go.

The follow two lines **deploy** a computing environment specified in ui defaults
file and start the data **collection** (i.e. run the jobs), respectively:

```bash
./hpcadvisor deploy create -u ../examples/matrixmult/ui_defaults.yaml
./hpcadvisor collect -n <deploymentname> -u ../examples/matrixmult/ui_defaults.yaml
```

If you want to only test the plot generator component, skipping the data
collection, you need to copy a dataset file to hpcadvisor directory:

```bash
mkdir $HOME/.hpcadvisor/
cp ../examples/matrixmult/dataset.json $HOME/.hpcadvisor/
```

Then request the plot generation:

```
./hpcadvisor plot -df ../examples/matrixmult/datafilter_matrixmult.yaml
```

To get the advice (based on pareto-front calculation):

```bash
./hpcadvisor advice -df examples/matrixmult/datafilter_matrixmult.yaml
```

### GUI-based execution

One can use the browser version and click the buttons for the different
operations. To pre-fill user input, specify the input file as showed below:

```bash
./hpcadvisor gui -u ../examples/matrixmult/ui_defaults.yaml
```

---


