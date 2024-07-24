#!/usr/bin/env python3

import itertools
import math
import os

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

from hpcadvisor import dataset_handler, logger, price_puller

log = logger.logger

markers = ["o", "s", "^", "D", "*", "+", "x", "|", "_", "."]
default_colors = ['orange', 'red', 'yellow', 'green', 'blue', 'purple', 'brown', 'pink']
color_cycle = itertools.cycle(default_colors)
marker_cycle = itertools.cycle(markers)

color_map = {}
marker_map = {}

style.use("dark_background")

# TODO: remove hardcoded region
# TODO: refactor code as there are many duplicate function calls
def handle_plot_output(st, fig, plotdir, plotfile):
    if st:
        st.pyplot(fig)
    else:
        plotfile = os.path.join(plotdir, plotfile)
        log.info("Saving file: " + plotfile)
        plt.savefig(plotfile)

def _get_appinput_title(appinput):
    if not appinput or not "appinputs" in appinput:
        return ""
    return " ".join([f"{key}={value} " for key, value in appinput["appinputs"].items()])

def get_tick_spacing(max_y, num_ticks=10):
    if num_ticks <= 1:
        raise ValueError("num_ticks must be greater than 1")

    if max_y <= 0:
        raise ValueError("max_y must be greater than 0")

    # Calculate initial tick spacing
    tick_spacing = max_y / (num_ticks - 1)

    # Determine the order of magnitude
    order_of_magnitude = 10 ** math.floor(math.log10(tick_spacing))

    # Adjust tick_spacing to a more readable value
    tick_spacing = round(tick_spacing / order_of_magnitude) * order_of_magnitude

    # Ensure tick_spacing is positive and reasonable
    if tick_spacing <= 0:
        tick_spacing = order_of_magnitude

    return tick_spacing

# def get_tick_spacing(max_y, num_ticks=10):
#     tick_spacing = max_y / float(num_ticks - 1)
#     order_of_magnitude = 10 ** (len(str(int(tick_spacing))) - 1)
#     tick_spacing = round(tick_spacing / order_of_magnitude) * order_of_magnitude
#     return tick_spacing

def setup_plot_legend(ax):
    handles, labels = ax.get_legend_handles_labels()
    sorted_labels_handles = sorted(zip(labels, handles), key=lambda x: x[0])
    labels, handles = zip(*sorted_labels_handles)
    ax.legend(handles, labels, loc="upper right")

def get_color_marker_maps(mydata):
    global color_map
    global marker_map

    for sku in sorted(mydata.keys()):
        if sku not in color_map:
            color_map[sku] = next(color_cycle)
            marker_map[sku] = next(marker_cycle)

    return color_map, marker_map

def gen_data_table(datapoints, dynamic_filter, appexectime=False):

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
        new_datapoint["exec_time"] = datapoint["exec_time"]
        if appexectime:
            new_datapoint["exec_time"] = datapoint["appexectime"]

        new_datapoint["sku"] = datapoint["sku"]
        new_datapoint["nnodes"] = datapoint["nnodes"]
        new_datapoint["ppr_perc"] = int(datapoint["ppr_perc"])
        new_datapoint["total_cores"] = datapoint["total_cores"]

        cost = price_puller.get_price("eastus", datapoint["sku"]) * \
               datapoint["nnodes"] * \
               new_datapoint["exec_time"] / 3600.0

        new_datapoint["cost"] = cost
        tablepoints.append(new_datapoint)

    tablepoints = sorted(tablepoints, key=lambda x: x["exec_time"])
    for point in tablepoints:
        print(f"{point['sku']:<30}{point['nnodes']:<10}{point['ppr_perc']:<10}{point['total_cores']:<10}{point['exec_time']:<10}{point['cost']:<10.2f}")

def gen_plot_efficiency(
    st, datapoints, dynamic_filter, appexectime, plotdir, plotfile="plot.png"
):
    num_vms = []

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter, appexectime
    )

    if not mydata:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    fig, ax = plt.subplots()

    color_map, marker_map = get_color_marker_maps(mydata)

    max_y = 0
    for index, key in enumerate(mydata):
        speedup = [mydata[key][0] / x for x in mydata[key]]
        efficiency = np.array(speedup) / np.array(num_vms[key])
        max_y = max(max_y, max(efficiency))
        ax.plot(
            num_vms[key], efficiency, label=key, markerfacecolor="none", marker=marker_map[key], color=color_map[key]
        )

    ax.set_ylabel("Efficiency")
    ax.set_xlabel("Number of VMs")

    ticking_spacing = get_tick_spacing(max_y)

    plt.yticks(np.arange(0, max_y * 1.5, ticking_spacing))

    setup_plot_legend(ax)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = f"Efficiency\n{appinput_title}"
    ax.set_title(title)

    handle_plot_output(st, fig, plotdir, plotfile)



def gen_plot_speedup(
    st, datapoints, dynamic_filter, appexectime, plotdir, plotfile="plot.png"
):
    num_vms = []

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter, appexectime
    )

    if not mydata:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    fig, ax = plt.subplots()

    color_map, marker_map = get_color_marker_maps(mydata)

    max_speedup = 0
    for index, key in enumerate(mydata):
        speedup = [mydata[key][0] / x for x in mydata[key]]
        max_speedup = max(max_speedup, max(speedup))
        ax.plot(
            num_vms[key], speedup, label=key, markerfacecolor="none", marker=marker_map[key], color=color_map[key]
        )
        #ax.plot(
        #    num_vms[key], mydata[key], label=key, markerfacecolor="none", marker=marker_map[key], color=color_map[key]
        #)

    ax.set_ylabel("Speedup")
    ax.set_xlabel("Number of VMs")

    ticking_spacing = get_tick_spacing(max_exectime)

    plt.yticks(np.arange(0, max_speedup * 1.5, ticking_spacing))

    setup_plot_legend(ax)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = f"Speedup\n{appinput_title}"
    ax.set_title(title)

    handle_plot_output(st, fig, plotdir, plotfile)


def gen_plot_exectime_vs_numvms(
    st, datapoints, dynamic_filter, appexectime, plotdir, plotfile="plot.png"
):
    num_vms = []

    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter, appexectime
    )

    if not mydata:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    fig, ax = plt.subplots()

    color_map, marker_map = get_color_marker_maps(mydata)

    for index, key in enumerate(mydata):
        ax.plot(
            num_vms[key], mydata[key], label=key, markerfacecolor="none", marker=marker_map[key], color=color_map[key]
        )

    ax.set_ylabel("Execution time (seconds)")
    ax.set_xlabel("Number of VMs")

    ticking_spacing = get_tick_spacing(max_exectime)

    plt.yticks(np.arange(0, max_exectime * 1.5, ticking_spacing))

    setup_plot_legend(ax)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = f"Execution time (s) per SKU & Num Nodes\n{appinput_title}"
    ax.set_title(title)

    handle_plot_output(st, fig, plotdir, plotfile)

def gen_plot_exectime_vs_cost(
    st, datapoints, dynamic_filter, appexectime, plotdir, plotfile="plot.png"
):
    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter, appexectime
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

    global color_map
    global marker_map

    for sku in sorted(mydata.keys()):
        if sku not in color_map:
            color_map[sku] = next(color_cycle)
            marker_map[sku] = next(marker_cycle)

    for index, key in enumerate(mydata):
        ax.plot(
            mydata[key],
            exec_costs[key],
            label=key,
            markerfacecolor="none",
            marker=marker_map[key],
            color=color_map[key]
        )

    ax.set_xlabel("Execution time (seconds)")
    ax.set_ylabel("Cost (USD)")

    ticking_spacing = get_tick_spacing(max_exectime)

    # plt.yticks(np.arange(0, max_exectime * 1.5, ticking_spacing))

    setup_plot_legend(ax)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    appinput_title = _get_appinput_title(dynamic_filter)
    title = (
        f"Cost as function of execution time (s) per sku & num nodes\n{appinput_title}"
    )
    ax.set_title(title)

    handle_plot_output(st, fig, plotdir, plotfile)

def gen_plot_scatter_exectime_vs_cost(
    st, datapoints, dynamic_filter, appexectime, plotdir, plotfile="plot.png"
):
    mydata, num_vms, max_exectime = dataset_handler.get_sku_nnodes_exec_time(
        datapoints, dynamic_filter, appexectime
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

    plt.scatter(scatter_data_x, scatter_data_y)

    ax.set_xlabel("Execution time (seconds)")
    ax.set_ylabel("Cost (USD)")

    appinput_title = _get_appinput_title(dynamic_filter)
    title = (
        f"Cost as function of execution time (s)\n{appinput_title}"
    )

    ax.set_title(title)

    handle_plot_output(st, fig, plotdir, plotfile)
