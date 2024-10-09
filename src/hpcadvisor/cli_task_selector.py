#!/usr/bin/env python3

import itertools

from hpcadvisor import dataset_handler, logger, price_puller, taskset_handler

log = logger.logger




def get_next_tasks(tasks_filename, policy_name, num_tasks=1):

    num_tasks = num_tasks if num_tasks is not None else 1
    policy_name = policy_name if policy_name is not None else "sequential"
    # all_tasks = taskset_handler.get_tasks_from_file(tasks_filename)

    selected_tasks = taskset_handler.get_tasks(tasks_filename, policy_name, num_tasks)

    for task in selected_tasks:
        print(task)
