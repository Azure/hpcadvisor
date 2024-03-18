#!/usr/bin/env python3

import itertools
import json
import os
from enum import Enum

from hpcadvisor import logger

log = logger.logger


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ALL = "all"


def clear_task_file(filename):
    if filename:
        open(filename, "w").close()


def _ensure_list(value):
    if isinstance(value, int) or isinstance(value, str) or isinstance(value, float):
        return [value]
    else:
        return value


def _store_tasks(task_dict, filename):
    with open(filename, "w") as outfile:
        json.dump(task_dict, outfile)
    log.info(f"{filename}: file created/updated with {len(task_dict)} tasks")


def update_task_status(id, filename, status=TaskStatus.COMPLETED):
    tasks = get_tasks_from_file(filename, status=TaskStatus.ALL)
    for task in tasks:
        if task["id"] == id:
            task["status"] = status
    _store_tasks(tasks, filename)


def reset_alltasks_status(filename, status=TaskStatus.PENDING):
    tasks = get_tasks_from_file(filename, status=TaskStatus.ALL)
    for task in tasks:
        task["status"] = status
    _store_tasks(tasks, filename)


def generate_tasks(filename, var_system, var_appinputs, appname, tags):
    clear_task_file(filename)

    main_task_dict = []
    variables = []
    for varname, value in var_system.items():
        variables.append((varname, value))

    for varname, value in var_appinputs.items():
        variables.append((varname, value))

    variables = [(name, _ensure_list(values)) for name, values in variables]

    parameter_combinations = list(
        itertools.product(*[values for _, values in variables])
    )

    id = 0
    for task in parameter_combinations:
        task_dict = {
            name: value for name, value in zip([name for name, _ in variables], task)
        }

        task_dict_entry = {}
        task_dict_entry["id"] = id
        task_dict_entry["sku"] = task_dict["sku"]
        task_dict_entry["ppr"] = task_dict["ppr"]
        task_dict_entry["nnodes"] = task_dict["nnodes"]
        task_dict_entry["appinputs"] = {}
        for varname, _ in var_appinputs.items():
            task_dict_entry["appinputs"][varname] = task_dict[varname]
        task_dict_entry["status"] = TaskStatus.PENDING
        task_dict_entry["appname"] = appname
        task_dict_entry["tags"] = tags
        main_task_dict.append(task_dict_entry)
        id += 1

    _store_tasks(main_task_dict, filename)
    return main_task_dict


def get_tasks_from_file(tasks_file, status=TaskStatus.PENDING):
    if os.path.isfile(tasks_file) == False:
        log.critical(f"Tasks file not found: {tasks_file}")
        return []

    with open(tasks_file, "r") as json_file:
        tasks = json.load(json_file)

    filtered_tasks = []
    for task in tasks:
        if status == TaskStatus.ALL or task["status"] == status:
            filtered_tasks.append(task)

    log.info(f"Loaded {len(filtered_tasks)} tasks from file")
    return filtered_tasks
