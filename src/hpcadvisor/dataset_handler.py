import json
import os

data_set_path = "dataset.json"

datapoints_label = "datapoints"


def update_dataset(dataset_file, data):
    existing_data = {}

    if os.path.exists(dataset_file):
        with open(dataset_file, "r") as file:
            existing_data = json.load(file)

    if not datapoints_label in existing_data:
        existing_data[datapoints_label] = []

    existing_data[datapoints_label].append(data)

    with open(dataset_file, "w") as outfile:
        json.dump(existing_data, outfile)


def get_dataset(dataset_file):
    existing_data = {}

    if os.path.exists(dataset_file):
        with open(dataset_file, "r") as file:
            existing_data = json.load(file)

    return existing_data


def get_dataset_skus(dataset):
    skus = []
    for experiment in dataset[datapoints_label]:
        skus.append(experiment["sku"])

    skus = list(dict.fromkeys(skus))
    return skus


def get_value_list_from_key(dataset, match_key, match_value, return_key):
    values = []
    for experiment in dataset[datapoints_label]:
        if experiment[match_key] == match_value:
            values.append(experiment[return_key])

    return values


def get_appinput_combinations(dataset_file):
    print("dataset_file=", dataset_file)
    dataset = get_dataset(dataset_file)
    print("DATASET=", dataset)
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
        num_vms = []
        print("data", data)
        for datapoint in data[datapoints_label]:
            if "appinputs" in datapoint:
                if datapoint["appinputs"] == appinput:
                    sku = datapoint["sku"]
                    nnodes = datapoint["nnodes"]
                    exectime = datapoint["exec_time"]

                    if int(nnodes) not in num_vms:
                        num_vms.append(int(nnodes))

                    if mydata.get(sku) is None:
                        mydata[sku] = []
                    mydata[sku].append(int(exectime))
                    max_exectime = max(max_exectime, max(mydata[sku]))
        return mydata, num_vms, max_exectime


if __name__ == "__main__":
    appinputs = {}
    appinputs["APPMATRIXSIZE"] = "6000"
    appinputs["APPINTERACTIONS"] = "10"
    dataentry = {}
    dataentry["sku"] = "Standard_HB120-32rs_v3"
    dataentry["exec_time"] = 100
    dataentry["nnodes"] = 2
    dataentry["appinputs"] = appinputs

    # newdata = {}
    # newdata["experiment"] = []
    # newdata["experiment"].append(dataentry)
    # newdata["experiment"].append(dataentry)

    # update_dataset(dataentry)

    mydataset = get_dataset(data_set_path)
    print("--------------")
    print(mydataset)
    print(get_dataset_skus(mydataset))

    exec_time = []
    exec_times = get_value_list_from_key(
        mydataset, "sku", "Standard_HB120-32rs_v3", "exec_time"
    )
    print(exec_times)
    print(get_appinput_combinations(mydataset))
