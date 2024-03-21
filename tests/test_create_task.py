import random
import sys

from hpcadvisor import batch_handler, logger, main_cli, utils

logger.setup_debug_mode()
log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(
            f"Usage: python {sys.argv[0]} <userinput> <envfile> <sku> <numnodes> <ppr_perc> <jobname>"
        )
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = main_cli.get_userinput_from_file(userinput_file)

    env_file = sys.argv[2]
    sku = sys.argv[3]
    number_of_nodes = int(sys.argv[4])
    ppr_perc = int(sys.argv[5])
    jobname = sys.argv[6]

    rg_prefix = utils.get_rg_prefix_from_file(env_file)
    # dataset_file = utils.get_dataset_filename()

    batch_handler.setup_environment(env_file)
    taskid = batch_handler.create_compute_task(
        jobname, number_of_nodes, ppr_perc, sku, {}
    )

    batch_handler.wait_task_completion(jobname, taskid)
    task_status = batch_handler.get_task_status(jobname, taskid)
    print(task_status)
    task_status = batch_handler.get_task_execution_status(jobname, taskid)
    print(task_status)

    # poolname = batch_handler.create_pool(sku)
    # print(f"Pool {poolname} created")
