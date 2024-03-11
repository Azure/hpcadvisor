## HPC Advisor: Overview

The goal of this tool is to assist users in selecting the cluster configuraton
based on actual application executions.

For now the tool focuses on testing:
- SKUs
- Number of cluster nodes
- Processes per node
- Application input parameters

For next versions we will explore other factors such as storage, gpus and
network.

#### Warning: This repo is still going through major changes!

---

### Execution using poetry

Poetry installation: <https://python-poetry.org/docs/>

Using terminal go inside the hpcadvisor root directory:

#### Install and create python virtual environment
```
poetry install
poetry shell
```

#### Run only data collector on CLI

Update `src/samples/cli_input.json` fields, in particular `mysubscription`

To start:
```
./bin/hpcadvisor -u src/samples/cli_input.json
```

#### Run GUI (browser) so data collector and data exploration can be used

Optional: Copy `src/samples/ui_defaults.json` to
`$HOME/.hpcadvisor/ui_defaults.json` and modify it accordingly.

To start:
```
./bin/hpcadvisor -g
```

#### Only test data exploration

If you want to only test the data exploration component and has not run any data
collection:


```
cp src/samples/dataset.json $HOME/.hpcadvisor/
./bin/hpcadvisor -g
```

Then click on the data exploration button.


---
### Notes

1) fix the process for data collection is interrupted, resources will not be
deleted automatically.

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
