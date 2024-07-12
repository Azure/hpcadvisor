#!/usr/bin/env python3

import os

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

from hpcadvisor import dataset_handler, logger, price_puller

log = logger.logger


markers = ["o", "s", "^", "D", "*", "+", "x", "|", "_", "."]


def _get_appinput_title(appinput):
    if not appinput or not "appinputs" in appinput:
        return ""
    return " ".join([f"{key}={value} " for key, value in appinput["appinputs"].items()])


def get_tick_spacing(max_y, num_ticks=10):
    tick_spacing = max_y / (num_ticks - 1)
    order_of_magnitude = 10 ** (len(str(int(tick_spacing))) - 1)
    tick_spacing = round(tick_spacing / order_of_magnitude) * order_of_magnitude
    return tick_spacing


def gen_data_table(datapoints, dynamic_filter):

    print(f"{'SKU':<30}{'NumNodes':<10}{'PPRPerc':<10}{'NumCores':<10}{'ExecTime':<10}{'Cost':<10}")
    print("-" * 80)

    tablepoints = []

    for datapoint in datapoints:
        matched_dynamic_filter = dataset_handler.dynamic_filter_matches(
            datapoint, dynamic_filter
        )
        if not matched_dynamic_filter:
            continue
        new_datapoint = {}
        new_datapoint["sku"] = datapoint["sku"]
        new_datapoint["nnodes"] = datapoint["nnodes"]
        new_datapoint["ppr_perc"] = int(datapoint["ppr_perc"])
        new_datapoint["total_cores"] = datapoint["total_cores"]
        new_datapoint["exec_time"] = datapoint["exec_time"]
        cost = price_puller.get_price("eastus", datapoint["sku"]) * \
               datapoint["nnodes"] * \
               datapoint["exec_time"] / 3600
        new_datapoint["cost"] = cost
        tablepoints.append(new_datapoint)

    tablepoints = sorted(tablepoints, key=lambda x: x["exec_time"])
    for point in tablepoints:
        print(f"{point['sku']:<30}{point['nnodes']:<10}{point['ppr_perc']:<10}{point['total_cores']:<10}{point['exec_time']:<10}{point['cost']:<10.2f}")

     # print(f"{sku:<30}{num_vms:<10}{pprrperc:<10}{num_cores:<10}{exectime:<10}{cost:<10}")


def gen_plot_exectime_vs_numvms(
    st, datapoints, dynamic_filter, plotdir, plotfile="plot.png"
):
    style.use("dark_background")

    num_vms = []

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter
    )

    if len(mydata) == 0:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

    fig, ax = plt.subplots()

    markers = ["o", "s", "^", "D", "*", "+", "x", "|", "_", "."]
    for index, key in enumerate(mydata):
        marker = markers[index % len(markers)]
        ax.plot(
            num_vms[key], mydata[key], label=key, markerfacecolor="none", marker=marker
        )

    ax.set_ylabel("Execution time (seconds)")
    ax.set_xlabel("Number of VMs")

    ticking_spacing = get_tick_spacing(max_exectime)

    plt.yticks(np.arange(0, max_exectime * 1.5, ticking_spacing))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper right")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = f"Execution time (s) per SKU & Num Nodes\n{appinput_title}"
    ax.set_title(title)

    if st:
        st.pyplot(fig)
    else:
        plotfile = os.path.join(plotdir, plotfile)
        log.info("Saving file: " + plotfile)
        plt.savefig(plotfile)

def gen_plot_exectime_vs_cost(
    st, datapoints, dynamic_filter, plotdir, plotfile="plot.png"
):
    style.use("dark_background")

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter
    )

    if len(mydata) == 0:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

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
    ax.set_xlabel("Cost (USD/hour)")

    ticking_spacing = get_tick_spacing(max_exectime)

    plt.yticks(np.arange(0, max_exectime * 1.5, ticking_spacing))

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc="upper right")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = (
        f"Cost as function of execution time (s) per sku & num nodes\n{appinput_title}"
    )
    ax.set_title(title)

    if st:
        st.pyplot(fig)
    else:
        plotfile = os.path.join(plotdir, plotfile)
        log.info("Saving file: " + plotfile)
        plt.savefig(plotfile)

def gen_plot_scatter_exectime_vs_cost(
    st, datapoints, dynamic_filter, plotdir, plotfile="plot.png"
):
    style.use("dark_background")

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter
    )

    if len(mydata) == 0:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

    sku_costs = {}
    for key in mydata:
        sku_costs[key] = price_puller.get_price("eastus", key)

    exec_costs = {}
    scatter_data_x = []
    scatter_data_y = []
    for key in mydata:
        exec_costs[key] = []
        for i in range(len(mydata[key])):
            cost = (mydata[key][i] / 3600.0) * sku_costs[key] * num_vms[key][i]
            exec_costs[key].append(cost)
            scatter_data_x.append(mydata[key][i])
            scatter_data_y.append(cost)

    fig, ax = plt.subplots()

    print(mydata)
    print(exec_costs)
    plt.scatter(scatter_data_x, scatter_data_y)

    # for index, key in enumerate(mydata):
    #     marker = markers[index % len(markers)]
    #     ax.plot.scatter(
    #         exec_costs[key],
    #         mydata[key],
    #         label=key,
    #         markerfacecolor="none",
    #         marker=marker,
    #     )

    ax.set_xlabel("Execution time (seconds)")
    ax.set_ylabel("Cost (USD)")

    # ticking_spacing = get_tick_spacing(max_exectime)

    # plt.yticks(np.arange(0, max_exectime * 1.5, ticking_spacing))

    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles, labels, loc="upper right")
    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = (
        f"Cost as function of execution time (s)\n{appinput_title}"
    )
    ax.set_title(title)

    if st:
        st.pyplot(fig)
    else:
        plotfile = os.path.join(plotdir, plotfile)
        log.info("Saving file: " + plotfile)
        plt.savefig(plotfile)
