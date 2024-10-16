#!/usr/bin/env python3

import itertools

from hpcadvisor import dataset_handler, logger, price_puller, taskset_handler

log = logger.logger


def export(datafilter, exportfile):

    datapoints = dataset_handler.get_datapoints(datafilter)
    dataset_handler.store_datapoints(exportfile, datapoints)
