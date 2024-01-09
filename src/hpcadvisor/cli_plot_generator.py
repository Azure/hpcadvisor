import os

from hpcadvisor import dataset_handler, logger, plot_generator, utils

log = logger.logger


def gent_plots():
    dataset_file = utils.get_dataset_filename()
    print("Generating plots from dataset file: " + dataset_file)

    appinputs = []
    if os.path.exists(dataset_file):
        appinputs = dataset_handler.get_appinput_combinations(dataset_file)

    plot_id = 0
    for appinput in appinputs:
        plot_file = "plot_" + str(plot_id) + "_exectime_vs_numvms.pdf"
        print("Generating plot: " + plot_file)
        plot_generator.gen_plot_exectime_vs_numvms(
            None, dataset_file, appinput, plot_file
        )
        plot_id += 1
        plot_file = "plot_" + str(plot_id) + "_exectime_vs_cost.pdf"
        print("Generating plot: " + plot_file)
        plot_generator.gen_plot_exectime_vs_cost(
            None, dataset_file, appinput, plot_file
        )
