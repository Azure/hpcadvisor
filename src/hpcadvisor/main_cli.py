#!/usr/bin/env python3

import json
import os
import sys

from hpcadvisor import (
    batch_handler,
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
        "appname",
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


def main_shutdown_deployment(name):
    env_file = utils.get_deployments_file(name)
    log.debug(f"Deployment file: {env_file}")

    if not os.path.exists(env_file):
        log.error(f"Deployment file not found: {name}")
        return

    print(f"Shutting down deployment: {name}")

    if batch_handler.setup_environment(env_file):
        batch_handler.delete_environment()
    else:
        log.error("Failed to setup environment.")


def main_list_deployments():
    deployments = utils.list_deployments()

    if deployments:
        print("Deployments:")
        for deployment in deployments:
            print(deployment)


def main_create_deployment(name, user_input_file, debug):
    user_input = get_userinput_from_file(user_input_file)

    if name:
        rg_prefix = name
    else:
        rg_prefix = user_input["rgprefix"] + utils.get_random_code()

    env_file = utils.generate_env_file(rg_prefix, user_input)

    print(f"Deployment name: {rg_prefix}")
    print(f"Deployment details: {env_file}")
    print("This operation may take a few minutes...")

    utils.execute_env_deployer(env_file, rg_prefix, debug)


def main_plot(plotfilter):
    log.info("Generating plots...")
    cli_plot_generator.generate_plots(plotfilter)


def main_collect_data(
    deployment_name, user_input_file, clear_deployment=False, clear_tasks=False
):
    user_input = get_userinput_from_file(user_input_file)

    data_system = {}
    data_system["sku"] = user_input["skus"]
    data_system["nnodes"] = user_input["nnodes"]
    data_system["ppr"] = user_input["ppr"]

    data_app_input = user_input["appinputs"]

    task_filename = utils.get_task_filename(deployment_name)
    if clear_tasks or not os.path.exists(task_filename):
        log.info(f"Generating new tasks file: {task_filename}")
        taskset_handler.generate_tasks(
            task_filename,
            data_system,
            data_app_input,
            user_input["appname"],
            user_input["tags"],
        )

    env_file = utils.get_deployments_file(deployment_name)
    dataset_filename = utils.get_dataset_filename()
    data_collector.collect_data(
        task_filename, dataset_filename, env_file, clear_deployment
    )
