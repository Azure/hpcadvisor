#!/usr/bin/env python3

import json
import os
import sys

from hpcadvisor import (
    cli_plot_generator,
    data_collector,
    logger,
    taskset_handler,
    utils,
)

log = logger.logger


def get_userinput_from_file(user_input_file):
    required_variables = [
        "region",
        "skus",
        "nnodes",
        "appinputs",
        "ppr",
        "subscription",
        "appsetupurl",
        "apprunscript",
    ]

    try:
        with open(user_input_file, "r") as json_file:
            json_data = json.load(json_file)
    except json.JSONDecodeError:
        log.critical(f"User input not valid json file: " + user_input_file)
        sys.exit(1)
    except FileNotFoundError:
        log.critical("File not found: " + user_input_file)
        sys.exit(1)

    missing_variables = [var for var in required_variables if var not in json_data]

    if missing_variables:
        log.critical("Missing variables in user input file:")
        for var in missing_variables:
            log.critical(f"missing variable: {var}")
        sys.exit(1)

    return json_data


def main(user_input_file, env_file, plots, debug):
    # TODO: stil not a great place to be doing this
    if plots:
        cli_plot_generator.gent_plots()
        sys.exit(0)

    user_input = get_userinput_from_file(user_input_file)

    data_system = {}
    data_system["sku"] = user_input["skus"]
    data_system["nnodes"] = user_input["nnodes"]
    data_system["ppr"] = user_input["ppr"]

    data_app_input = user_input["appinputs"]

    if env_file and os.path.exists(env_file):
        log.warning(f"Using existing env file: {env_file}")
        rg_prefix = utils.get_rg_prefix_from_file(env_file)
        task_filename = utils.get_task_filename(rg_prefix)
        log.info(f"Env file specified. Reusing existing tasks file {task_filename}.")
    else:
        log.warning("Generating new env file and deploying environment")
        rg_prefix = user_input["rgprefix"] + utils.get_random_code()
        print(f"Resource group (deployment) name: {rg_prefix}")
        env_file = utils.generate_env_file(rg_prefix, user_input)
        print(f"Environment file: {env_file}")
        utils.execute_env_deployer(env_file, rg_prefix, debug)
        task_filename = utils.get_task_filename(rg_prefix)
        log.info(
            f"Env file NOT specified or does not exist. Generating new tasks file {task_filename}."
        )
        taskset_handler.generate_tasks(task_filename, data_system, data_app_input)

    dataset_filename = utils.get_dataset_filename()
    data_collector.collect_data(task_filename, dataset_filename, env_file)
