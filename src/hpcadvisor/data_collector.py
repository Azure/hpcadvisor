#!/usr/bin/env python3

import sys

from hpcadvisor import batch_handler, logger

log = logger.logger


def get_task_property_value(task_str, property_name):
    for line in task_str.split(","):
        if property_name in line:
            return line.split("=")[1]

    return None


def get_task_appinputs(task_str):
    appinputs = []
    for line in task_str.split(","):
        line = line.partition("#")[0]
        line = line.rstrip()
        if "=" not in line:
            continue
        if "sku" in line or "nnodes" in line or "ppr" in line:
            continue
        appinputs.append((line.split("=")[0], line.split("=")[1]))

    return appinputs


def get_tasks_from_file(tasks_file):
    tasks = []
    with open(tasks_file) as f:
        lines = f.readlines()

        for line in lines:
            if "#" in line or "=" not in line:
                continue
            line = line.strip()
            tasks.append(line)

    return tasks


def process_tasks(tasks_file, dataset_file):
    tasks = get_tasks_from_file(tasks_file)
    previous_sku = ""
    jobname = ""
    poolname = ""

    taskcounter = 0
    for task in tasks:
        print(f"Processing task: {taskcounter}/{len(tasks)}")
        log.info(f"Processing task: {task}")

        sku = get_task_property_value(task, "sku")
        number_of_nodes = get_task_property_value(task, "nnodes")
        ppr_perc = get_task_property_value(task, "ppr")
        appinputs = get_task_appinputs(task)
        # TODO: needs to have proper format for appinputs in create_compute_task
        appinputs_dict = dict(appinputs)

        if previous_sku != sku:
            log.debug(f"Got new sku: previous=[{previous_sku}] sku=[{sku}]")
            if poolname != "":
                batch_handler.resize_pool(poolname, 0)

            poolname = batch_handler.create_pool(sku)
            if poolname == None:
                log.error(f"Failed to create pool for sku: {sku}")
                log.error(f"Moving to another task")
                continue
            jobname = batch_handler.create_job(poolname)
            batch_handler.create_setup_task(jobname)

        batch_handler.resize_pool(poolname, number_of_nodes)

        taskid = batch_handler.create_compute_task(
            jobname, number_of_nodes, ppr_perc, sku, appinputs
        )

        batch_handler.wait_task_completion(jobname, taskid)
        batch_handler.store_task_execution_data(
            poolname, jobname, taskid, ppr_perc, appinputs_dict, dataset_file
        )

        previous_sku = sku
        taskcounter += 1

    if poolname != "":
        batch_handler.resize_pool(poolname, 0)


def collect_data(tasks_file, dataset_file, env_file):
    # logger.setup_debug_mode() if debug else None

    if batch_handler.setup_environment(env_file):
        log.info("Environment setup completed")
        log.info("Starting tasks...this may take a while")
        deployment_name = batch_handler.get_deployment_name()
        process_tasks(tasks_file, dataset_file, deployment_name)
        batch_handler.delete_environment()
        log.info("Tasks completed")
    else:
        log.error("Failed to setup environment")
