import sys

from hpcadvisor import batch_handler, logger, main_cli, utils

logger.setup_debug_mode()
log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <userinput> <envfile> ")
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = utils.get_userinput_from_file(userinput_file)

    env_file = sys.argv[2]

    rg_prefix = utils.get_rg_prefix_from_file(env_file)

    batch_handler.setup_environment(env_file)

    batch_handler.delete_vnet_peering()
