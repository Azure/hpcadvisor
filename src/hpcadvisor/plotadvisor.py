#!/usr/bin/env python3

import time

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib.patches import Rectangle

from hpcadvisor import dataset_handler


def gen_graph(st, datasetfile, appinput):
    style.use("dark_background")

    f = open(datasetfile, "r")
    lines = f.readlines()

    num_vms = []
    count = 0

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datasetfile, appinput
    )
    appinputtitle = " ".join([f"{key} {value}" for key, value in appinput.items()])

    df = pd.DataFrame(mydata)
    fig, ax = plt.subplots()

    for key in mydata:
        ax.plot(num_vms, df[key], label=key, marker="o")

    ax.set_ylabel("Execution time (seconds)")
    ax.set_xlabel("Number of VMs")

    plt.yticks(np.arange(0, max_exectime * 1.5, 50))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper right")

    title = f"Execution time (s) per SKU & Num Nodes\n{appinputtitle}"
    ax.set_title(title)

    if st:
        st.pyplot(fig)
    plt.savefig("my_plot.png")
