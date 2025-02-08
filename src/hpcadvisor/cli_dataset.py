#!/usr/bin/env python3

import itertools

from hpcadvisor import dataset_handler, logger, price_puller, taskset_handler, utils

log = logger.logger


def filter(datafilter, exportfile):

    datapoints = dataset_handler.get_datapoints(datafilter)
    dataset_handler.store_datapoints(exportfile, datapoints)


def add(newdatapoints_file):

    datasetfile = utils.get_dataset_filename()

    dataset_handler.add_datapoints_fromfile(datasetfile, newdatapoints_file)
