import random
import sys

from hpcadvisor import batch_handler, logger, main_cli, utils

logger.setup_debug_mode()
log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(
            f"Usage: python {sys.argv[0]} <userinput> <envfile> <poolname> <jobname> <taskid> "
        )
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = utils.get_userinput_from_file(userinput_file)

    env_file = sys.argv[2]
    poolname = sys.argv[3]
    jobname = sys.argv[4]
    taskid = sys.argv[5]

    ppr_perc = user_input["ppr"]

    appinputs = user_input["appinputs"]
    rg_prefix = utils.get_rg_prefix_from_file(env_file)
    dataset_file = utils.get_dataset_filename()

    batch_handler.setup_environment(env_file)

    batch_handler.store_task_execution_data(
        poolname, jobname, taskid, ppr_perc, appinputs, dataset_file, "appname", []
    )
