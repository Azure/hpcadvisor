#!/usr/bin/env python3

import sys

from hpcadvisor import batch_handler, logger, taskset_handler

log = logger.logger


def process_tasks(tasks_file, dataset_file):
    tasks = taskset_handler.get_tasks_from_file(tasks_file, "pending")
    previous_sku = ""
    jobname = ""
    poolname = ""

    taskcounter = 0
    for task in tasks:
        print(f"Processing task: {taskcounter}/{len(tasks)}")
        log.info(f"Processing task: {task}")
        sku = task["sku"]
        number_of_nodes = task["nnodes"]
        ppr_perc = task["ppr"]
        appinputs = task["appinputs"]
        appname = task["appname"]
        tags = task["tags"]

        if previous_sku != sku:
            log.debug(f"Got new sku: previous=[{previous_sku}] sku=[{sku}]")
            if poolname != "":
                log.info(f"Resizing pool: {poolname} to 0")
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
            poolname, jobname, taskid, ppr_perc, appinputs, dataset_file, appname, tags
        )
        taskset_handler.update_task_status(task["id"], tasks_file)

        previous_sku = sku
        taskcounter += 1

    if poolname != "":
        batch_handler.resize_pool(poolname, 0)


def collect_data(tasks_file, dataset_file, env_file, clear_rg=False):
    if batch_handler.setup_environment(env_file):
        log.info("Environment setup completed")
        log.info("Starting tasks...this may take a while")
        process_tasks(tasks_file, dataset_file)
        if clear_rg:
            batch_handler.delete_environment()
        log.info("Tasks completed")
    else:
        log.error("Failed to setup environment")
