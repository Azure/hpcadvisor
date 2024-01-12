#!/usr/bin/env python3

import time

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

from hpcadvisor import dataset_handler, logger, price_puller

log = logger.logger


markers = ["o", "s", "^", "D", "*", "+", "x", "|", "_", "."]


def _get_appinput_title(appinput):
    return " ".join([f"{key}:{value} " for key, value in appinput.items()])


def gen_plot_exectime_vs_numvms(st, datasetfile, appinput, plotfile="plot.png"):
    style.use("dark_background")

    num_vms = []

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datasetfile, appinput
    )

    fig, ax = plt.subplots()

    markers = ["o", "s", "^", "D", "*", "+", "x", "|", "_", "."]
    for index, key in enumerate(mydata):
        marker = markers[index % len(markers)]
        ax.plot(
            num_vms[key], mydata[key], label=key, markerfacecolor="none", marker=marker
        )

    ax.set_ylabel("Execution time (seconds)")
    ax.set_xlabel("Number of VMs")

    plt.yticks(np.arange(0, max_exectime * 1.5, 50))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper right")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(appinput)
    title = f"Execution time (s) per SKU & Num Nodes\n{appinput_title}"
    ax.set_title(title)

    if st:
        st.pyplot(fig)
    log.info("Generating plot: " + plotfile)
    plt.savefig(plotfile)


def gen_plot_exectime_vs_cost(st, datasetfile, appinput, plotfile="plot.png"):
    style.use("dark_background")

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datasetfile, appinput
    )

    sku_costs = {}
    for key in mydata:
        sku_costs[key] = price_puller.get_price("eastus", key)

    exec_costs = {}
    for key in mydata:
        exec_costs[key] = []
        for i in range(len(mydata[key])):
            exec_costs[key].append(
                (mydata[key][i] / 3600.0) * sku_costs[key] * num_vms[key][i]
            )

    fig, ax = plt.subplots()

    for index, key in enumerate(mydata):
        marker = markers[index % len(markers)]
        ax.plot(
            exec_costs[key],
            mydata[key],
            label=key,
            markerfacecolor="none",
            marker=marker,
        )

    ax.set_ylabel("Execution time (seconds)")
    ax.set_xlabel("Cost (USD)")

    plt.yticks(np.arange(0, max_exectime * 1.5, 50))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper right")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(appinput)
    title = (
        f"Cost as function of execution time (s) per sku & num nodes\n{appinput_title}"
    )
    ax.set_title(title)

    if st:
        st.pyplot(fig)

    log.info("Generating plot: " + plotfile)
    plt.savefig(plotfile)
