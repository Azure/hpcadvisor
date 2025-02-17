#!/usr/bin/env python3

import os

from hpcadvisor import (
    batch_handler,
    cli_advice_generator,
    cli_dataset,
    cli_plot_generator,
    cli_task_selector,
    data_collector,
    logger,
    taskset_handler,
    utils,
)

log = logger.logger


def main_shutdown_deployment(name, options):
    env_file = utils.get_deployments_file(name)
    log.debug(f"Deployment file: {env_file}")

    if not os.path.exists(env_file):
        log.error(f"Deployment file not found: {name}")
        return

    print(f"Shutting down deployment: {name}")
    if options["deletepools"]:
        print("Deleting pools only...")
    elif options["deletejobs"]:
        print("Deleting jobs only...")

    if batch_handler.setup_environment(env_file):
        if options["deletepools"]:
            batch_handler.delete_pools()
        if options["deletejobs"]:
            batch_handler.delete_jobs()
        if not options["deletepools"] and not options["deletejobs"]:
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
    user_input = utils.get_userinput_from_file(user_input_file)

    if name:
        rg_prefix = name
    else:
        rg_prefix = user_input["rgprefix"] + utils.get_random_code()

    env_file = utils.generate_env_file(rg_prefix, user_input)

    print(f"Deployment name: {rg_prefix}")
    print(f"Deployment details: {env_file}")
    print("This operation may take a few minutes...")

    utils.execute_env_deployer(env_file, rg_prefix, debug)


def main_plot(plotfilter, showtable, appexectime, subtitle):
    if showtable:
        cli_plot_generator.generate_datatable(plotfilter, appexectime)
    else:
        plotdir = utils.get_plot_dir()
        cli_plot_generator.generate_plots(plotfilter, plotdir, appexectime, subtitle)


def main_advice(datafilter, appexectime):
    log.info("Generating advice...")
    # plotdir = utils.get_plot_dir()
    cli_advice_generator.generate_advice(datafilter, appexectime)


def main_dataset(operation, input, output):
    if operation == "filter":
        log.info("Filtering data...")
        if not input or not output:
            log.error("Input and output files are required for filtering.")
            return
        cli_dataset.filter(input, output)
    elif operation == "add":
        log.info("Adding data...")
        cli_dataset.add(input)


def main_selecttask(operation, userinput, taskfile, policy_name, num_tasks):

    if operation == "gettasks":
        cli_task_selector.get_next_tasks(taskfile, policy_name, num_tasks)
    elif operation == "show":
        cli_task_selector.show_tasks(taskfile)
    else:
        log.error(f"Unknown operation: {operation}. Supported: gettasks|show")


def main_collect_data(deployment_name, user_input_file, collector_config):
    user_input = utils.get_userinput_from_file(user_input_file)

    data_system = {}
    data_system["sku"] = user_input["skus"]
    data_system["nnodes"] = user_input["nnodes"]
    data_system["ppr"] = user_input["ppr"]

    data_app_input = user_input["appinputs"]

    task_filename = utils.get_task_filename(deployment_name)
    if (
        collector_config["cleartasks"]
        or not os.path.exists(task_filename)
        or os.path.getsize(task_filename) == 0
    ):
        log.info(f"Generating new tasks file: {task_filename}")
        taskset_handler.generate_tasks(
            task_filename,
            data_system,
            data_app_input,
            user_input["appname"],
            user_input["tags"],
            user_input["appsetupurl"],
        )
    else:
        log.info(f"Using existing tasks file: {task_filename}")

    env_file = utils.get_deployments_file(deployment_name)
    dataset_filename = utils.get_dataset_filename()
    data_collector.collect_data(
        task_filename, dataset_filename, env_file, collector_config
    )
