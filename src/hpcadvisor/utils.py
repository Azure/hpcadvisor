import datetime
import os
import random

from hpcadvisor import logger

log = logger.logger
environment_filename = "env.conf"
task_filename = "tasks.json"
dataset_filename = "dataset.json"
ui_default_filename = "ui_default.json"

hpcadvisor_dir = os.path.join(os.path.expanduser("~"), ".hpcadvisor")


def get_hpcadvisor_dir():
    return hpcadvisor_dir


def get_ui_default_filename():
    return os.path.join(hpcadvisor_dir, "ui_defaults.json")


def get_task_filename(rg_prefix):
    deployment_dir = _get_deployment_dir(rg_prefix)
    return os.path.join(deployment_dir, task_filename)


# for now, dataset is stored in hpcadvisor dir
# and deployment info is a tag into the dataset file
# to be able to filter data
# TODO: may change this in future
def get_dataset_filename():
    return os.path.join(hpcadvisor_dir, dataset_filename)


def _get_deployment_dir(rg_prefix):
    deployment_dir = os.path.join(hpcadvisor_dir, rg_prefix)
    if not os.path.exists(deployment_dir):
        log.info("Create deployment dir: " + deployment_dir)
        os.makedirs(deployment_dir)

    return deployment_dir


def get_random_code():
    random_number = random.randint(1000, 9999)
    timestamp = datetime.datetime.now().strftime("%m%d%H%M")
    return f"{timestamp}{random_number}"


def generate_env_file(rg_prefix, user_data):
    subscription = user_data["subscription"]
    region = user_data["region"]
    app_setup_url = user_data["appsetupurl"]
    app_run_script = user_data["apprunscript"]

    home_directory = os.path.expanduser("~")
    deployment_dir = os.path.join(hpcadvisor_dir, rg_prefix)

    if not os.path.exists(deployment_dir):
        log.info("Create deployment dir: " + deployment_dir)
        os.makedirs(deployment_dir)

    env_file = os.path.join(deployment_dir, environment_filename)

    with open(env_file, "w") as f:
        f.write("SUBSCRIPTION=" + subscription + "\n")
        f.write("REGION=" + region + "\n")
        f.write("APPSETUPURL=" + app_setup_url + "\n")
        f.write("APPRUNSCRIPT=" + app_run_script + "\n")

        f.write("RG=" + rg_prefix + "\n")
        f.write("BATCHACCOUNT=" + rg_prefix + "ba\n")
        f.write("STORAGEACCOUNT=" + rg_prefix + "sa\n")
        f.write("KEYVAULT=" + rg_prefix + "kv\n")
        f.write("VNETNAME=" + rg_prefix + "VNET\n")
        f.write("VSUBNETNAME=" + rg_prefix + "SUBNET\n")

        # TODO: some thougth is required here
        if "vpnrg" in user_data:
            f.write("VPNRG=" + user_data["vpnrg"] + "\n")
        if "vpnvnet" in user_data:
            f.write("VPNVNET=" + user_data["vpnvnet"] + "\n")
        if "vnetaddress" in user_data:
            f.write("VNETADDRESS=" + user_data["vnetaddress"] + "\n")
        else:
            # TODO: may improve this in future
            #
            # no particular reason for this range
            # this has some limitation as mask is fixed
            # and may conflict with other vnets for peering
            f.write(f"VNETADDRESS=10.{random.randint(35, 55)}.0.0\n")

    return env_file


def get_rg_prefix_from_file(env_file):
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("RG="):
                return line.split("=")[1].strip()
    return None


def execute_env_deployer(env_file, rg_prefix, debug=False):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "../scripts", "env_deployer.sh")

    if not os.path.exists(script_path):
        log.critical("env_deployer.sh not found")

    command = f"bash {script_path} {env_file}"
    if not debug:
        command += " > /dev/null 2>&1"
    log.info(f"Executing: {command}")
    os.system(command)
