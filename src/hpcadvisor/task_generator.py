#!/usr/bin/env python3

import argparse
import itertools
import json
import logging
import sys

from hpcadvisor import data_collector, logger, utils

log = logger.logger


def reset_task_file(filename):
    if filename:
        open(filename, "w").close()


def _ensure_list(value):
    if isinstance(value, int) or isinstance(value, str) or isinstance(value, float):
        return [value]
    else:
        return value


def _store_tasks(task_dict, filename):
    with open(filename, "w") as outfile:
        json.dump(task_dict, outfile)
    log.info(f"{filename}: file generated with {len(task_dict)} tasks")


def generate_tasks(filename, var_system, var_appinputs):
    reset_task_file(filename)

    main_task_dict = []
    variables = []
    for varname, value in var_system.items():
        variables.append((varname, value))

    for varname, value in var_appinputs.items():
        variables.append((varname, value))

    variables = [(name, _ensure_list(values)) for name, values in variables]

    parameter_combinations = list(
        itertools.product(*[values for _, values in variables])
    )

    task_dict_array = []
    for task in parameter_combinations:
        task_dict = {
            name: value for name, value in zip([name for name, _ in variables], task)
        }

        task_dict_entry = {}
        task_dict_entry["sku"] = task_dict["sku"]
        task_dict_entry["ppr"] = task_dict["ppr"]
        task_dict_entry["nnodes"] = task_dict["nnodes"]
        task_dict_entry["appinputs"] = {}
        for varname, _ in var_appinputs.items():
            task_dict_entry["appinputs"][varname] = task_dict[varname]
        main_task_dict.append(task_dict_entry)
        task_dict_array.append(task_dict)

    _store_tasks(main_task_dict, filename)
    return task_dict_array


def get_tasks_from_file(tasks_file):
    with open(tasks_file, "r") as json_file:
        tasks = json.load(json_file)

    return tasks


# TODO: move to test code
def _get_input_files_from_cli():
    tasks_file = None
    userinput_file = None

    parser = argparse.ArgumentParser(description="Collect data script")

    parser.add_argument("-t", "--taskfile", help="Tasks File", required=True)
    parser.add_argument("-u", "--userinput", help="UI Inputs", required=True)

    try:
        args = parser.parse_args()
        tasks_file = args.taskfile
        userinput_file = args.userinput
    except:
        parser.print_help()
        sys.exit(1)

    log.info(f"Tasks file: {tasks_file}")
    log.info(f"User input file: {userinput_file}")

    return tasks_file, userinput_file
