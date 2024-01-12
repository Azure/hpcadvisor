import json
import os

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
        json.dump(existing_data, outfile)


def get_dataset_from_file(dataset_file):
    existing_data = {}

    if os.path.exists(dataset_file):
        with open(dataset_file, "r") as file:
            existing_data = json.load(file)

    return existing_data


def get_dataset_skus(dataset):
    skus = []
    for datapoint in dataset[datapoints_label]:
        skus.append(datapoint["sku"])

    skus = list(dict.fromkeys(skus))
    return skus


def get_appinput_combinations(dataset_file):
    dataset = get_dataset_from_file(dataset_file)
    appinput_combinations = []
    for datapoint in dataset[datapoints_label]:
        if "appinputs" in datapoint:
            appinputs = datapoint["appinputs"]
            if appinputs not in appinput_combinations:
                appinput_combinations.append(appinputs)

    return appinput_combinations


def get_sku_nnodes_exec_time(dataset_file, appinput):
    if not os.path.exists(dataset_file):
        return [], [], 0

    with open(dataset_file, "r") as file:
        data = json.load(file)
        max_exectime = 0
        mydata = {}
        num_vms = {}
        for datapoint in data[datapoints_label]:
            if "appinputs" in datapoint:
                if datapoint["appinputs"] == appinput:
                    sku = datapoint["sku"]
                    nnodes = datapoint["nnodes"]
                    exectime = datapoint["exec_time"]

                    if mydata.get(sku) is None:
                        mydata[sku] = []
                        num_vms[sku] = []
                    mydata[sku].append(int(exectime))
                    num_vms[sku].append(int(nnodes))
                    max_exectime = max(max_exectime, max(mydata[sku]))
        return mydata, num_vms, max_exectime
