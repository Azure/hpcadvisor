import random
import sys

from hpcadvisor import logger, main_cli, taskset_handler, utils

log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <userinput> ")
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = utils.get_userinput_from_file(userinput_file)

    rg_prefix = "test"
    env_file = utils.generate_env_file(rg_prefix, user_input)

    data_system = {}
    data_system["sku"] = user_input["skus"]
    data_system["nnodes"] = user_input["nnodes"]
    data_system["ppr"] = user_input["ppr"]

    data_app_input = user_input["appinputs"]

    task_filename = utils.get_task_filename(rg_prefix)
    print(f"task_filename: {task_filename}")

    taskset_handler.generate_tasks(task_filename, data_system, data_app_input)
    tasks = taskset_handler.get_tasks_from_file(task_filename)

    num_tasks = len(tasks)
    print(f"num_tasks: {num_tasks}")

    num_completed_tasks = int(num_tasks * 0.3)
    print("num_completed_tasks: ", num_completed_tasks)

    randomlist = random.sample(range(0, num_tasks), num_completed_tasks)
    print("tasks to be removed: ", randomlist)

    for t in randomlist:
        taskset_handler.update_task_status(t, task_filename)

    tasks = taskset_handler.get_tasks_from_file(task_filename)
    print(f"new num_tasks: {len(tasks)}")
    assert len(tasks) == num_tasks - num_completed_tasks

    taskset_handler.reset_alltasks_status(task_filename)
    reset_num_tasks = len(taskset_handler.get_tasks_from_file(task_filename))

    assert num_tasks == reset_num_tasks
    print(f"reset num_tasks: {reset_num_tasks}")
