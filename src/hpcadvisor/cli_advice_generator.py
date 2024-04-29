import os
import sys

from hpcadvisor import advice_generator, dataset_handler, logger, plot_generator, utils

log = logger.logger


def gen_advice_table(table_id, datapoints, datafilter_input):
    pareto_front = advice_generator.gen_advice_exectime_vs_cost(
        None, datapoints, datafilter_input
    )

    if pareto_front is None:
        log.error("No advice generated")
        return

    if datafilter_input:
        appinputs = datafilter_input["appinputs"]
        title = " ".join([f"{key}={value} " for key, value in appinputs.items()])
        print("Appinputs: " + title)

    print(f"{'Exectime(s)':<12} {'Cost($/h)':<12} {'Nodes':<6} SKU")
    for exectime, cost, nnodes, sku in pareto_front:
        cost = float(cost)
        print(f"{exectime:<12} {cost:<12.4f} {nnodes:<6} {sku}")
    print()


def generate_advice(datafilter_file):
    datafilter = dataset_handler.get_plotfilter(datafilter_file)

    dataset_file = utils.get_dataset_filename()
    log.debug("Generating plots from dataset file: " + dataset_file)

    appinputs = []
    if not os.path.exists(dataset_file):
        log.error("Dataset file not found: " + dataset_file)
        return

    datapoints = dataset_handler.get_datapoints(dataset_file, datafilter)

    if not datapoints:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    appinputs = dataset_handler.get_appinput_combinations(datapoints)

    datafilter_appinputs = []
    for appinput in appinputs:
        filter = {}
        filter["appinputs"] = appinput
        datafilter_appinputs.append(filter)

    table_id = 0

    if datafilter_appinputs:
        for datafilter_appinput_entry in datafilter_appinputs:
            gen_advice_table(table_id, datapoints, datafilter_appinput_entry)
            table_id += 1
    else:
        gen_advice_table(table_id, datapoints, datafilter_appinputs)
