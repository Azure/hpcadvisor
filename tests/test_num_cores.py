import sys

from hpcadvisor import batch_handler, logger, main_cli, utils

log = logger.logger

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_num_cores.py <userinput> <sku>")
        sys.exit(0)

    userinput_file = sys.argv[1]
    user_input = main_cli.get_userinput_from_file(userinput_file)

    rg_prefix = "test"
    env_file = utils.generate_env_file(rg_prefix, user_input)

    batch_handler.env["SUBSCRIPTION"] = batch_handler.get_subscription_id(
        user_input["subscription"]
    )
    batch_handler.env["REGION"] = user_input["region"]

    sku = "Standard_D2s_v3"
    cores = batch_handler._get_total_cores(sku)
    print("sku: {}, cores: {}".format(sku, cores))
    assert cores == 2

    sku = "Standard_HB120-32rs_v2"
    cores = batch_handler._get_total_cores(sku)
    print("sku: {}, cores: {}".format(sku, cores))
    assert cores == 32
