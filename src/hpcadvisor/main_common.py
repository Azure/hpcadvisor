import os

from hpcadvisor import logger, taskset_handler, utils

log = logger.logger


def reset_tasks(envfile):
    log.info("Resetting status of all tasks")

    if not os.path.exists(envfile):
        log.error(f"Environment file {envfile} not found")
        return

    deployment_name = os.path.basename(os.path.dirname(envfile))
    task_filename = utils.get_task_filename(deployment_name)
    taskset_handler.reset_alltasks_status(task_filename)
