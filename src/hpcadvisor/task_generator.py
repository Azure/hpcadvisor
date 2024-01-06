#!/usr/bin/env python3

import argparse
import itertools
import logging
import sys

from hpcadvisor import data_collector, logger

log = logger.logger


def reset_task_file(filename):
    if filename:
        open(filename, "w").close()


def append_task(task_dict, filename):
    task_str = ", ".join([f"{key}={value}" for key, value in task_dict.items()])
    task_str = f"{task_str}" + "\n"
    file1 = open(filename, "a")
    file1.write(task_str)
    file1.close()


def _ensure_list(value):
    if isinstance(value, int) or isinstance(value, str) or isinstance(value, float):
        return [value]
    else:
        return value


def generate_tasks(filename, var_system, var_appinputs):
    reset_task_file(filename)

    variables = []
    for varname, value in var_system.items():
        variables.append((varname, value))

    for varname, value in var_appinputs.items():
        variables.append((varname, value))

    variables = [(name, _ensure_list(values)) for name, values in variables]

    parameter_combinations = list(
        itertools.product(*[values for _, values in variables])
    )

    tota_tasks = 0
    task_dict_array = []
    for task in parameter_combinations:
        task_dict = {
            name: value for name, value in zip([name for name, _ in variables], task)
        }
        task_dict_array.append(task_dict)
        append_task(task_dict, filename)

    print(f"{filename}: file generated with {len(task_dict_array)} tasks")
    return task_dict_array


def get_parameters(env_file):
    raw_sku_text = ""
    raw_ppr_text = ""
    raw_nnodes_text = ""
    raw_app_text = ""

    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("SKU"):
                raw_sku_text = line.split("=")[1].strip()
            elif line.startswith("PPR"):
                raw_ppr_text = line.split("=")[1].strip()
            elif line.startswith("NNODES"):
                raw_nnodes_text = line.split("=")[1].strip()
            elif line.startswith("APPINPUTS"):
                raw_app_text = line.replace("APPINPUTS=", "").strip()
                raw_app_text = raw_app_text.replace("|", "\n")

    return (
        raw_sku_text,
        raw_ppr_text,
        raw_nnodes_text,
        raw_app_text,
    )


def _get_input_files():
    tasks_file = None
    userinput_file = None

    parser = argparse.ArgumentParser(description="Collect data script")

    parser.add_argument("-t", "--taskfile", help="Tasks File", required=True)
    # parser.add_argument("-u", "--userinput", help="UI Inputs", required=True)

    try:
        args = parser.parse_args()
        tasks_file = args.taskfile
        # userinput_file = args.userinput
    except:
        parser.print_help()
        sys.exit(1)

    log.info(f"Tasks file: {tasks_file}")
    # log.info(f"User input file: {userinput_file}")

    return tasks_file


if __name__ == "__main__":
    tasks_file = _get_input_files()
    print(tasks_file)

    # tasks_file, userinput_file = _get_input_files()
    #
    # (raw_sku_text, raw_ppr_text, raw_nnodes_text, raw_app_text) = get_parameters(
    #     userinput_file
    # )
    #
    # log.info(raw_sku_text, raw_ppr_text, raw_nnodes_text, raw_app_text)
    #
    # generate_tasks(
    #     tasks_file, raw_sku_text, raw_ppr_text, raw_nnodes_text, raw_app_text
    # )
