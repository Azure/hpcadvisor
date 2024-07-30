#!/usr/bin/env python3


# import matplotlib.pyplot as plt
# import matplotlib.style as style
import numpy as np
import pandas as pd

from hpcadvisor import dataset_handler, logger, price_puller

# from matplotlib.ticker import MaxNLocator


log = logger.logger


def calculate_pareto_front(data):
    pareto_front = []
    for _, (exectime, cost, nnodes, sku) in enumerate(data):
        is_pareto = True
        for _, (other_exectime, other_cost, other_nnodes, other_sku) in enumerate(data):
            if exectime > other_exectime and cost > other_cost:
                is_pareto = False
                break
        if is_pareto:
            pareto_front.append((exectime, cost, nnodes, sku))
    return np.array(pareto_front)


def gen_advice_exectime_vs_cost(st, datapoints, dynamic_filter, appexectime):
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
    data_for_pareto = []
    for key in mydata:
        exec_costs[key] = []
        for i in range(len(mydata[key])):
            cost = (mydata[key][i] / 3600.0) * sku_costs[key] * num_vms[key][i]
            sku = key
            exec_costs[key].append(cost)
            data_for_pareto.append((mydata[key][i], cost, num_vms[key][i], sku))

    pareto_front = calculate_pareto_front(data_for_pareto)
    # sort by execution time
    sorted_pareto_front = sorted(pareto_front, key=lambda x: float(x[0]))

    return sorted_pareto_front
