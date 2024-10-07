import json
import os

import yaml

from hpcadvisor import logger, utils

log = logger.logger

datapoints_label = "datapoints"


def add_datapoint(dataset_file, datapoint):
    existing_data = {}

    if os.path.exists(dataset_file):
        with open(dataset_file, "r") as file:
            existing_data = json.load(file)

    if not datapoints_label in existing_data:
        existing_data[datapoints_label] = []

    existing_data[datapoints_label].append(datapoint)

    with open(dataset_file, "w") as outfile:
        json.dump(existing_data, outfile, indent=2)


def get_plotfilter(plotfilter_file):
    plotfilter = {}
    if plotfilter_file and os.path.exists(plotfilter_file):
        plotfilter = utils.get_data_from_file(plotfilter_file)

        for key, value in plotfilter.items():
            if not isinstance(value, list):
                plotfilter[key] = [value]
    else:
        log.warning("Plotfilter file not provided or does not exist. Consuming entire dataset")
    return plotfilter


def get_dataset_from_file(dataset_file):
    existing_data = {}

    if os.path.exists(dataset_file):
        with open(dataset_file, "r") as file:
            existing_data = json.load(file)
    else:
        log.error("Dataset file not found: " + dataset_file)

    return existing_data


def get_dataset_skus(dataset):
    skus = []
    for datapoint in dataset[datapoints_label]:
        skus.append(datapoint["sku"])

    skus = list(dict.fromkeys(skus))
    return skus


def is_valid_datapoint(datapoint, plotfilter):
    for key, valuelist in plotfilter.items():
        if key in datapoint:
            if key == "tags":
                anymatch = False
                if any(all(tag_name in datapoint[key] and datapoint[key][tag_name] == tag_value
                               for tag_name, tag_value in values_dict.items())
                           for values_dict in valuelist):
                            anymatch = True
                if not anymatch:
                    return False
            elif  datapoint[key] not in valuelist:
                return False
        else:
            return False

    return True


def get_datapoints(plotfilter_file):

    dataset_file = utils.get_dataset_filename()

    dataset = get_dataset_from_file(dataset_file)

    plotfilter = get_plotfilter(plotfilter_file)

    datapoints = []
    for datapoint in dataset[datapoints_label]:
        if not is_valid_datapoint(datapoint, plotfilter):
            continue
        else:
            datapoints.append(datapoint)

    datapoints = sorted(datapoints, key=lambda x: x["nnodes"])
    return datapoints


def get_appinput_combinations(datapoints):
    appinput_combinations = []
    for datapoint in datapoints:
        if "appinputs" in datapoint and datapoint["appinputs"]:
            appinputs = datapoint["appinputs"]
            if appinputs not in appinput_combinations:
                appinput_combinations.append(appinputs)

    return appinput_combinations


# TODO: RETHINK THESE FILTERS
def static_filter_matches(datapoint, static_filters):
    for key, value in static_filters.items():
        if datapoint[key] != value:
            return False

    return True


def dynamic_filter_matches(datapoint, dynamic_filters):
    if len(dynamic_filters) == 0:
        return True
    for value in dynamic_filters.values():
        if datapoint["appinputs"] != value:
            return False

    return True


def get_sku_nnodes_exec_time(datapoints, dynamic_filters, appexectime):
    if not datapoints:
        return {}, {}, 0

    max_exectime = 0
    mydata = {}
    num_vms = {}
    # sort datapoints by nnodes

    for datapoint in datapoints:
        matched_dynamic_filter = dynamic_filter_matches(datapoint, dynamic_filters)
        if not matched_dynamic_filter:
            continue

        sku = datapoint["sku"]
        nnodes = datapoint["nnodes"]
        if appexectime:
            exectime = datapoint["appexectime"]
        else:
            exectime = datapoint["exec_time"]

        if mydata.get(sku) is None:
            mydata[sku] = []
            num_vms[sku] = []
        mydata[sku].append(int(exectime))
        num_vms[sku].append(int(nnodes))
        max_exectime = max(max_exectime, max(mydata[sku]))
    return mydata, num_vms, max_exectime
