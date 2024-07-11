
from hpcadvisor import dataset_handler, logger, plot_generator

log = logger.logger


def gen_core_plots(plot_id, datapoints, dynamic_filters, plotdir):
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_numvms.pdf"

    plot_generator.gen_plot_exectime_vs_numvms(
        None, datapoints, dynamic_filters, plotdir, plot_file
    )
    plot_id += 1
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_cost.pdf"

    plot_generator.gen_plot_exectime_vs_cost(
        None, datapoints, dynamic_filters, plotdir, plot_file
    )

    plot_id += 1
    plot_file = "plot_" + str(plot_id) + "_scatter_exectime_vs_cost.pdf"

    plot_generator.gen_plot_scatter_exectime_vs_cost(
        None, datapoints, dynamic_filters, plotdir, plot_file
    )


    #TODO generate scatter plot ... no lines for different skus

def get_dynamic_filter_items(datapoints):

    appinputs = dataset_handler.get_appinput_combinations(datapoints)
    dynamic_filter_items = []

    for appinput in appinputs:
        filter = {}
        filter["appinputs"] = appinput
        dynamic_filter_items.append(filter)

    return dynamic_filter_items

def generate_datatable(plotfilter_file):

    log.debug("Generating data table from dataset file")

    datapoints = dataset_handler.get_datapoints(plotfilter_file)

    if not datapoints:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

    dynamic_filter_items = get_dynamic_filter_items(datapoints)

    for dynamic_filter in dynamic_filter_items or [dynamic_filter_items]:
        plot_generator.gen_data_table(datapoints, dynamic_filter)

    return

def generate_plots(plotfilter_file, plotdir):

    log.debug("Generating plots from dataset file")

    datapoints = dataset_handler.get_datapoints(plotfilter_file)

    if not datapoints:
        log.error("No datapoints found. Check dataset and plotfilter files")
        return

    dynamic_filter_items = get_dynamic_filter_items(datapoints)

    log.info("Generating plots...")

    plot_id = 0
    for dynamic_filter in dynamic_filter_items or [dynamic_filter_items]:
        gen_core_plots(plot_id, datapoints, dynamic_filter, plotdir)
        plot_id += 3
