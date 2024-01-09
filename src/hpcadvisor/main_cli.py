#!/usr/bin/env python3

import json
import os
import sys

from hpcadvisor import cli_plot_generator, data_collector, logger, task_generator, utils

log = logger.logger


def _get_parameters(user_input_file):
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


def main(user_input_file, env_file, debug, plots):
    if debug:
        logger.setup_debug_mode()

    # TODO: stil not a great place to be doing this
    if plots:
        cli_plot_generator.gent_plots()
        sys.exit(0)

    user_data = _get_parameters(user_input_file)

    data_system = {}
    data_system["sku"] = user_data["skus"]
    data_system["nnodes"] = user_data["nnodes"]
    data_system["ppr"] = user_data["ppr"]

    data_app_input = user_data["appinputs"]

    if env_file and os.path.exists(env_file):
        log.warning(f"Using existing env file: {env_file}")
        rg_prefix = utils.get_rg_prefix_from_file(env_file)
    else:
        log.warning("Generating new env file and deploying environment")
        rg_prefix = user_data["rgprefix"] + utils.get_random_code()
        env_file = utils.generate_env_file(rg_prefix, user_data)
        utils.execute_env_deployer(env_file, rg_prefix)

    task_filename = utils.get_task_filename(rg_prefix)
    task_generator.generate_tasks(task_filename, data_system, data_app_input)

    dataset_filename = utils.get_dataset_filename()
    data_collector.collect_data(task_filename, dataset_filename, env_file)
