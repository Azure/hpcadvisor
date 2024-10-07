import sys

from hpcadvisor import logger, main_cli, utils, taskset_handler

logger.setup_debug_mode()
log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            f"Usage: python {sys.argv[0]} <userinput> <tasksfile>"
        )
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = utils.get_userinput_from_file(userinput_file)

    task_filename = sys.argv[2]

    data_system = {}
    data_system["sku"] = user_input["skus"]
    data_system["nnodes"] = user_input["nnodes"]
    data_system["ppr"] = user_input["ppr"]

    data_app_input = user_input["appinputs"]

    taskset_handler.generate_tasks(
            task_filename,
            data_system,
            data_app_input,
            user_input["appname"],
            user_input["tags"],
            user_input["appsetupurl"]
        )