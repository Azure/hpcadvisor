#!/usr/bin/env python3


from hpcadvisor import batch_handler, logger, taskset_handler

log = logger.logger


def resize_pool(poolname, number_of_nodes):
    attempts = 3
    while attempts > 0:
        rc = batch_handler.resize_pool(poolname, number_of_nodes)
        if not rc:
            log.warning(
                f"Failed to resize pool: {poolname} to {number_of_nodes}. Attempts left: {attempts}"
            )
            batch_handler.resize_pool(poolname, 0)
            attempts -= 1
        else:
            return True

    log.warning(f"Failed to resize pool: {poolname} to {number_of_nodes}")
    batch_handler.resize_pool(poolname, 0)
    return False


def process_tasks(tasks_file, dataset_file):
    tasks = taskset_handler.get_tasks_from_file(tasks_file)
    previous_sku = ""
    jobname = ""
    poolname = ""

    for taskcounter, task in enumerate(tasks, start=1):
        print(f"Processing task: {taskcounter}/{len(tasks)}")
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
            if poolname != "":
                log.info(f"Resizing pool: {poolname} to 0")
                batch_handler.resize_pool(poolname, 0)

            poolname = batch_handler.create_pool(sku)
            if poolname == None:
                log.error(f"Failed to create pool for sku: {sku}")
                log.error(f"Moving to another task")
                continue
            jobname = batch_handler.create_job(poolname)
            batch_handler.create_setup_task(jobname, appsetupurl)

        log.info(f"Resizing pool: {poolname} to {number_of_nodes}")

        # TODO: think if task should go to failed or keep pending state
        if not resize_pool(poolname, number_of_nodes):
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

    if poolname != "":
        batch_handler.resize_pool(poolname, 0)


def collect_data(tasks_file, dataset_file, env_file, clear_deployment=False):
    if batch_handler.setup_environment(env_file):
        log.debug("Environment setup completed")
        log.info("Starting tasks...this may take a while")
        process_tasks(tasks_file, dataset_file)
        if clear_deployment:
            batch_handler.delete_environment()
        log.info("Tasks completed")
    else:
        log.error("Failed to setup environment")
