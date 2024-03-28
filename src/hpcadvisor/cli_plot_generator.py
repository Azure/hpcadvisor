import os
import sys

from hpcadvisor import dataset_handler, logger, plot_generator, utils

log = logger.logger


def gen_core_plots(plot_id, datapoints, dynamic_filters):
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_numvms.pdf"

    plot_generator.gen_plot_exectime_vs_numvms(
        None, datapoints, dynamic_filters, plot_file
    )
    plot_id += 1
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_cost.pdf"

    plot_generator.gen_plot_exectime_vs_cost(
        None, datapoints, dynamic_filters, plot_file
    )


def generate_plots(plotfilter_file):
    plotfilter = dataset_handler.get_plotfilter(plotfilter_file)

    dataset_file = utils.get_dataset_filename()
    print("Generating plots from dataset file: " + dataset_file)

    appinputs = []
    if not os.path.exists(dataset_file):
        log.error("Dataset file not found: " + dataset_file)
        return

    datapoints = dataset_handler.get_datapoints(dataset_file, plotfilter)

    if not datapoints:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

    appinputs = dataset_handler.get_appinput_combinations(datapoints)

    dynamic_filter_items = []
    for appinput in appinputs:
        filter = {}
        filter["appinputs"] = appinput
        dynamic_filter_items.append(filter)

    plot_id = 0

    if dynamic_filter_items:
        for dynamic_filter in dynamic_filter_items:
            gen_core_plots(plot_id, datapoints, dynamic_filter)
            plot_id += 2
    else:
        gen_core_plots(plot_id, datapoints, dynamic_filter_items)
