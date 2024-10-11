#!/usr/bin/env python3

from hpcadvisor import batch_handler, logger, taskset_handler

log = logger.logger


def process_tasks_singletask(tasks_file, dataset_file, collector_config):
    tasks = taskset_handler.get_tasks_from_file(tasks_file)
    previous_sku = ""
    jobname = ""
    poolname = ""

    taskselector_policy = collector_config.get("policy", None)
    
    taskcounter = 0
    log.debug("Starting task processing in single task mode")

    while True:
        next_tasks = taskselector_policy.get_tasks(tasks)
        if len(tasks) == 0:
            log.info("No tasks found")
            break
       
        task= next_tasks.pop(0)    
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
                poolname = batch_handler.create_pool(sku)

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


def process_tasks_multitask(tasks_file, dataset_file, collector_config):

    log.debug("Starting task processing in multi task mode")

    tasks = taskset_handler.get_tasks_from_file(tasks_file)
    previous_sku = ""
    jobname = ""
    poolname = ""
       

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
