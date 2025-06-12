#!/usr/bin/env python3

import time

from hpcadvisor import batch_handler, logger, taskset_handler

log = logger.logger


def process_tasks_singletask(tasks_file, dataset_file, collector_config):

    previous_sku = ""
    jobname = ""
    poolname = ""

    taskselector_policy = collector_config.get("policy", None)

    taskcounter = 0
    log.debug("Starting task processing in single task mode")

    while True:
        tasks = taskset_handler.get_tasks_from_file(tasks_file)
        next_tasks = taskselector_policy.get_tasks(tasks)
        if len(tasks) == 0:
            log.info("No tasks found")
            break

        task = next_tasks.pop(0)
        taskcounter += 1

        log.debug(f"Processing task: {taskcounter}/{len(tasks) + taskcounter}")
        log.info(f"Processing task: {task}")
        sku = task["sku"]
        number_of_nodes = task["nnodes"]
        ppr_perc = task["ppr"]
        appinputs = task["appinputs"]
        appname = task["appname"]
        tags = task["tags"]
        appsetupurl = task["appsetupurl"]
        apprunscript = task["apprunscript"]

        if previous_sku != sku:
            log.debug(f"Got new sku: previous=[{previous_sku}] sku=[{sku}]")
            if poolname != "" and not collector_config["keeppools"]:
                log.info(f"Resizing pool: {poolname} to 0")
                batch_handler.resize_pool(poolname, 0)

            if collector_config["reusepools"]:
                poolname = batch_handler.get_existing_pool(sku, number_of_nodes)

            if not poolname or not collector_config["reusepools"]:
                poolname = batch_handler.create_pool(sku, 1)

            if poolname == None:
                log.error(f"Failed to create pool for sku: {sku}")
                log.error(f"Moving to another task")
                continue
            jobname = batch_handler.create_job(poolname)
            batch_handler.create_setup_task(jobname, appsetupurl)

        log.info(f"Resizing pool: {poolname} to {number_of_nodes}")

        # TODO: think if task should go to failed or keep pending state
        if not batch_handler.resize_pool_multi_attempt(poolname, number_of_nodes):
            log.error(f"Failed to resize pool: {poolname} to {number_of_nodes}")
            log.error(f"Moving to another task")
            continue

        taskid = batch_handler.create_compute_task(
            poolname, jobname, number_of_nodes, ppr_perc, sku, appinputs, apprunscript
        )

        batch_handler.wait_task_completion(jobname, taskid)
        task_status = batch_handler.get_task_execution_status(jobname, taskid)

        if task_status == taskset_handler.TaskStatus.COMPLETED:
            batch_handler.store_task_execution_data(
                poolname,
                jobname,
                taskid,
                ppr_perc,
                appinputs,
                dataset_file,
                appname,
                tags,
            )

        taskset_handler.update_task_status(task["id"], tasks_file, task_status)

        previous_sku = sku

    if poolname != "" and not collector_config["keeppools"]:
        batch_handler.resize_pool(poolname, 0)


def start_task_in_parallel(task, tasks_file, dataset_file, collector_config):
    sku = task["sku"]
    number_of_nodes = task["nnodes"]
    ppr_perc = task["ppr"]
    appinputs = task["appinputs"]
    appname = task["appname"]
    tags = task["tags"]
    appsetupurl = task["appsetupurl"]
    apprunscript = task["apprunscript"]

    # for parallel execution mode, we need to create a pool for each task
    # so we will not resize it any more
    poolname = batch_handler.create_pool(sku, number_of_nodes)
    if poolname is None:
        log.error(f"Failed to create pool for sku: {sku}")
        return

    task["tags"]["poolname"] = poolname

    jobname = batch_handler.create_job(poolname)
    batch_handler.create_setup_task(jobname, appsetupurl)

    task["tags"]["jobname"] = jobname

    # TODO: think if task should go to failed or keep pending state
    # batch_handler.wait_pool_ready(poolname)

    taskid = batch_handler.create_compute_task(
        poolname, jobname, number_of_nodes, ppr_perc, sku, appinputs, apprunscript
    )
    task["tags"]["taskid"] = taskid

    log.debug(f"Task started in parallel: {task}")
    taskset_handler.update_task_status(
        task["id"], tasks_file, taskset_handler.TaskStatus.RUNNING
    )


def check_task_completion(task):
    log.debug(
        f"Checking task completion: id={task['id']} poolid={task['tags']['poolname']} jobname={task['tags']['jobname']} taskid={task['tags']['taskid']} status={task['status']} nnodes={task['nnodes']}"
    )

    if task["status"] == taskset_handler.TaskStatus.COMPLETED:
        return True, task["status"]

    jobname = task["tags"]["jobname"]
    taskid = task["tags"]["taskid"]
    poolname = task["tags"]["poolname"]

    task_completed = batch_handler.wait_task_completion(
        jobname, taskid, wait_blocked=False
    )
    log.debug(f"Task status: {task_completed} {jobname} {taskid}")

    if not task_completed:
        return False, None

    task_status = batch_handler.get_task_execution_status(jobname, taskid)

    return True, task_status


def process_task_completion(
    task, task_status, tasks_file, dataset_file, collector_config
):

    jobname = task["tags"]["jobname"]
    taskid = task["tags"]["taskid"]
    poolname = task["tags"]["poolname"]
    ppr_perc = task["ppr"]
    appinputs = task["appinputs"]
    appname = task["appname"]
    tags = task["tags"]

    # TODO change signature for store_task_execution_data
    if task_status == taskset_handler.TaskStatus.COMPLETED:
        batch_handler.store_task_execution_data(
            poolname,
            jobname,
            taskid,
            ppr_perc,
            appinputs,
            dataset_file,
            appname,
            tags,
        )

    taskset_handler.update_task_status(task["id"], tasks_file, task_status)

    if not collector_config["keeppools"]:
        batch_handler.delete_pool(poolname)
    if not collector_config["keepjobs"]:
        batch_handler.delete_job(jobname)


def process_tasks_multitask(tasks_file, dataset_file, collector_config):

    log.debug("Starting task processing in multi task mode")

    tasks = taskset_handler.get_tasks_from_file(tasks_file)
    previous_sku = ""
    jobname = ""
    poolname = ""

    taskselector_policy = collector_config.get("policy", None)

    taskcounter = 0
    log.debug("Starting task processing in multi task mode")

    max_parallel_tasks = collector_config.get("policy", None).config.get(
        "paralleltasks"
    )

    log.debug(f"Max parallel tasks: {max_parallel_tasks}")

    num_running_tasks = 0
    pooling_delay_completion = 10

    running_tasks = []
    completed_tasks = []
    while True:
        all_pending_tasks = taskset_handler.get_tasks_from_file(tasks_file)

        num_new_tasks = max_parallel_tasks - num_running_tasks
        log.debug(f"Asking task selector for {num_new_tasks} new tasks")
        new_tasks = taskselector_policy.get_tasks(all_pending_tasks, num_new_tasks)

        if len(new_tasks) == 0 and len(running_tasks) == 0:
            log.info("No new tasks to be processed")
            break

        log.debug(f"Processing new {len(new_tasks)} tasks")
        for task in new_tasks:
            start_task_in_parallel(task, tasks_file, dataset_file, collector_config)
            running_tasks.append(task)
            num_running_tasks += 1

        while True:
            time.sleep(pooling_delay_completion)

            for task in running_tasks[:]:
                task_has_completed, task_status = check_task_completion(task)
                if task_has_completed:
                    process_task_completion(
                        task, task_status, tasks_file, dataset_file, collector_config
                    )
                    completed_tasks.append(task)
                    running_tasks.remove(task)
                    num_running_tasks -= 1
            if completed_tasks:
                completed_tasks = []
                log.debug("Some tasks completed, moving to next batch")
                break


def collect_data(tasks_file, dataset_file, env_file, collector_config):
    if batch_handler.setup_environment(env_file):
        log.debug("Environment setup completed")
        log.info("Starting tasks...this may take a while")

        if collector_config.get("policy", None).config.get("num_tasks") == 1:
            log.info("Single task mode")
            process_tasks_singletask(tasks_file, dataset_file, collector_config)
        else:
            process_tasks_multitask(tasks_file, dataset_file, collector_config)
            return
        if collector_config["cleardeployment"]:
            batch_handler.delete_environment()
        log.info("Tasks completed")
    else:
        log.error("Failed to setup environment")
