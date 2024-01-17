#!/usr/bin/env python3

import datetime
import io
import json
import os
import time

import azure.batch.models as batchmodels
import numpy as np
from azure.batch import BatchServiceClient
from azure.cli.core.util import b64encode
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import (
    DiskCreateOption,
    LinuxConfiguration,
    OSProfile,
    SshConfiguration,
    SshPublicKey,
    VirtualMachine,
    VirtualMachineImage,
)
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient

from hpcadvisor import dataset_handler, logger, utils
from hpcadvisor.azure_identity_credential_adapter import AzureIdentityCredentialAdapter

batch_supported_images = "batch_supported_images.txt"
VMIMAGE = "OpenLogic:CentOS-HPC:7_9-gen2:7.9.2022040101"

env = {}

DEFAULT_ENCODING = "utf-8"
STANDARD_OUT_FILE_NAME = "stdout.txt"

log = logger.logger
batch_client = None


def get_subscription_id(subscription_name):
    credential = DefaultAzureCredential()

    subscription_client = SubscriptionClient(credential)

    for sub in subscription_client.subscriptions.list():
        if sub.display_name == subscription_name:
            return sub.subscription_id

    return None


def _get_batch_endpoint(credentials, subscription_id, resource_group):
    """assumes single batch account in resource group"""

    rm_client = ResourceManagementClient(credentials, subscription_id)
    items = rm_client.resources.list_by_resource_group(resource_group)

    for resource in items:
        if resource.type == "Microsoft.Batch/batchAccounts":
            return f"https://{resource.name}.{resource.location}.batch.azure.com"

    log.critical("Cannot obtain batch endpoint.")

    return None


def _get_credentials():
    return DefaultAzureCredential()


def resource_group_exists(subscription_id, resource_group):
    credentials = DefaultAzureCredential()
    client = ResourceManagementClient(credentials, subscription_id)

    for item in client.resource_groups.list():
        if item.name == resource_group:
            log.info(f"Resource group {resource_group} exists")
            return True

    log.critical(f"Resource group {resource_group} does not exist")
    return False


def resize_pool(poolid, target_nodes, wait_resize=True):
    # TODO: need to add a maximum amount of time for pool resizing
    log.info(f"Resizing pool '{poolid}' to {target_nodes} nodes...")

    if not batch_client:
        log.critical("batch_client is None")
        return
    if not poolid:
        log.critical("poolid is None and cannot resize pool")
        return

    current_nodes = batch_client.pool.get(poolid).current_dedicated_nodes
    log.info(f"current nodes={current_nodes} target nodes={target_nodes}")

    pool = batch_client.pool.get(poolid)
    log.debug(f"Pool state={pool.allocation_state}")

    # TODO: revisit this
    # need to wait until the current resizing is completed
    # it seems batch does not queue resizing requests
    while True:
        pool = batch_client.pool.get(poolid)
        log.debug(f"before asking resize. pool state={pool.allocation_state}")
        if pool.allocation_state == "steady":
            break
        time.sleep(5)

    batch_client.pool.resize(
        pool_id=poolid,
        pool_resize_parameter=batchmodels.PoolResizeParameter(
            target_dedicated_nodes=target_nodes,
            target_low_priority_nodes=0,
            resize_timeout=pool.resize_timeout,
            # node_deallocation_option=pool.resize_deallocation_option,
        ),
    )

    if wait_resize:
        while True:
            pool = batch_client.pool.get(poolid)
            log.debug(f"pool state={pool.allocation_state}")
            if pool.allocation_state == "steady":
                break
            time.sleep(5)


def _get_batch_client(subscription_id, resource_group):
    """https://github.com/Azure/azure-sdk-for-python/issues/15330
    https://github.com/Azure/azure-sdk-for-python/issues/14499
    """

    log.debug(f"Getting batch client sub={subscription_id}, rg={resource_group}")
    credentials = _get_credentials()
    log.debug(credentials)
    batch_endpoint = _get_batch_endpoint(credentials, subscription_id, resource_group)

    batch_client = BatchServiceClient(
        AzureIdentityCredentialAdapter(
            credentials, resource_id="https://batch.core.windows.net/"
        ),
        batch_endpoint,
    )

    return batch_client


def get_file_content(filename):
    # content = string_or_file
    content = None
    if os.path.exists(filename):
        with open(filename, "r") as f:
            content = f.read()
    return content


def create_testvm(subscription_id, resource_group, vmname, sku):
    cloudinitfile = "cloud-init.txt"

    cloudinitcontent = f"""#cloud-config

runcmd:
- echo "mounting shared storage on vm"
- mkdir /nfs
- mount {env["STORAGEACCOUNT"]}.file.core.windows.net:/{env["STORAGEACCOUNT"]}/data /nfs"""

    with open(cloudinitfile, "w") as w:
        w.write(cloudinitcontent)

    adminuser = "azureuser"
    ssh_key = open(os.path.expanduser("~/.ssh/id_rsa.pub")).read()

    credentials = _get_credentials()

    compute_client = ComputeManagementClient(credentials, subscription_id)
    network_client = NetworkManagementClient(credentials, subscription_id)

    nicname = f"{resource_group}{vmname}nic"
    nic_poller = network_client.network_interfaces.begin_create_or_update(
        resource_group,
        nicname,
        {
            "location": env["REGION"],
            "ip_configurations": [
                {
                    "name": "myipconfig",
                    "subnet": {
                        "id": "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}".format(
                            subscription_id,
                            resource_group,
                            env["VNETNAME"],
                            env["VSUBNETNAME"],
                        )
                    },
                    "public_ip_address": None,
                }
            ],
        },
    )

    nic_result = nic_poller.result()

    os_profile = OSProfile(computer_name=vmname, admin_username=adminuser)

    os_profile.linux_configuration = LinuxConfiguration(
        ssh=SshConfiguration(
            public_keys=[
                SshPublicKey(
                    path=f"/home/{adminuser}/.ssh/authorized_keys", key_data=ssh_key
                ),
            ],
        )
    )

    custom_data = get_file_content(cloudinitfile)
    os_profile.custom_data = b64encode(custom_data)

    vm_poller = compute_client.virtual_machines.begin_create_or_update(
        resource_group,
        vmname,
        {
            "location": env["REGION"],
            "storage_profile": {
                "image_reference": {
                    "publisher": "OpenLogic",
                    "offer": "CentOS-HPC",
                    "sku": "7_9-gen2",
                    "version": "7.9.2022040101",
                }
            },
            "hardware_profile": {"vm_size": sku},
            "os_profile": os_profile,
            "network_profile": {"network_interfaces": [{"id": nic_result.id}]},
            # "identity": {
            #     "type": "UserAssigned",
            #     "user_assigned_identities": None,  # VirtualMachineIdentityUserAssignedIdentitiesValue
            # },
        },
    )

    vm_result = vm_poller.result()

    log.info(f"Provisioned virtual machine {vm_result.name}")


def get_job(batch_client, jobid):
    for job in batch_client.job.list():
        if job.id == jobid:
            return job
    return None


def create_job(poolid, jobid=None):
    if jobid is None:
        random_code = utils.get_random_code()
        jobid = f"job-{random_code}"

    if not batch_client:
        log.error("batch_client is None")
        return

    if not poolid:
        log.error(f"poolid is None and cannot create job {jobid}")
        return None

    log.info(f"create job: {jobid}")

    if get_job(batch_client, jobid):
        log.warning(f"Job [{jobid}] already exists...")
        return

    job = batchmodels.JobAddParameter(
        id=jobid,
        pool_info=batchmodels.PoolInformation(pool_id=poolid),
    )

    batch_client.job.add(job)
    log.info(f"Job [{jobid}] created!")

    return jobid


def _get_node_agent_sku(vm_image):
    """VMIMAGE=OpenLogic:CentOS-HPC:7_9-gen2:7.9.2022040101
    example of output=batch.node.centos 7
    """

    _, offer, sku, _ = vm_image.lower().split(":")

    if not batch_client:
        log.critical("batch_client is None")
        sys.exit(1)

    supported_images = batch_client.account.list_supported_images()

    for image in supported_images:
        if image.image_reference.offer == offer and image.image_reference.sku == sku:
            log.debug(f"Found image: {image.node_agent_sku_id}")
            result = image.node_agent_sku_id
            break

    # TODO: store the output as file so we can use the result as cache
    # f = open(batch_supported_images)
    # data = json.load(f)
    #
    # result = [
    #     item["nodeAgentSkuId"]
    #     for item in data
    #     if item["imageReference"]["offer"] == offer
    #     and item["imageReference"]["sku"] == sku
    # ]

    return result


def _get_subnet_id(subscription_id, resource_group, vnet_name, subnet_name):
    credentials = _get_credentials()
    network_client = NetworkManagementClient(credentials, subscription_id)
    subnet = network_client.subnets.get(resource_group, vnet_name, subnet_name)

    return subnet.id


def create_pool(sku, poolname=None, number_of_nodes=1):
    if poolname is None:
        random_code = utils.get_random_code()
        poolname = f"pool-{random_code}"

    if not batch_client:
        log.critical("batch_client is None")
        return

    log.info(f"Create pool: {poolname}")

    storage_account = env["STORAGEACCOUNT"]
    storage_file_dir = "data"
    nfs_fileshare = storage_file_dir
    nfs_share_hostname = f"{storage_account}.file.core.windows.net"
    nfs_share_directory = f"/{storage_account}/{nfs_fileshare}"

    subnetid = env["SUBVNETID"]

    pool_id = poolname

    mount_configuration = batchmodels.MountConfiguration(
        nfs_mount_configuration=batchmodels.NFSMountConfiguration(
            source=f"{nfs_share_hostname}:{nfs_share_directory}",
            relative_mount_path=nfs_fileshare,
            mount_options="-o rw,hard,rsize=65536,wsize=65536,vers=4,minorversion=1,tcp,sec=sys",
        )
    )

    task_commands = ["/bin/bash -c hostname; env; pwd"]

    user = batchmodels.AutoUserSpecification(
        scope=batchmodels.AutoUserScope.pool,
        elevation_level=batchmodels.ElevationLevel.admin,
    )

    start_task = batchmodels.StartTask(
        command_line=task_commands[0],
        user_identity=batchmodels.UserIdentity(auto_user=user),
        wait_for_success=True,
        max_task_retry_count=1,
    )

    network_configuration = batchmodels.NetworkConfiguration(
        subnet_id=subnetid,
        public_ip_address_configuration=batchmodels.PublicIPAddressConfiguration(
            provision="noPublicIPAddresses"
        ),
    )

    new_pool = batchmodels.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(
                publisher="OpenLogic",
                offer="CentOS-HPC",
                sku="7_9-gen2",
                version="7.9.2022040101",
            ),
            node_agent_sku_id="batch.node.centos 7",
        ),
        vm_size=sku,
        target_dedicated_nodes=number_of_nodes,
        enable_inter_node_communication=True,
        target_node_communication_mode="simplified",
        mount_configuration=[mount_configuration],
        start_task=start_task,
        network_configuration=network_configuration,
        task_scheduling_policy=batchmodels.TaskSchedulingPolicy(
            node_fill_type=batchmodels.ComputeNodeFillType.pack
        ),
    )

    try:
        batch_client.pool.add(new_pool)
    except batchmodels.BatchErrorException as err:
        if err.error.code == "PoolExists":
            log.warning("Pool %s already exists", pool_id)
        else:
            log.error(f"CANNOT CREATE POOL {pool_id}. Error code: {err.error.code}")
            for detail in err.error.values:
                log.error(detail.key + ": " + detail.value)
            return None

    return poolname


def create_setup_task(jobid):
    log.info(f"Creating setup task for jobid={jobid}")

    if not batch_client:
        log.critical("batch_client is None")
        return

    app_setup_url = env["APPSETUPURL"]
    log.debug(app_setup_url)

    random_code = utils.get_random_code()
    task_id = f"task-app-setup-{random_code}"

    if not jobid:
        log.critical(f"jobid is None and cannot create setup task {task_id}")
        return

    script_name = os.path.basename(app_setup_url)
    log.debug(script_name)

    task_commands = [
        f"/bin/bash -c 'cd $AZ_BATCH_NODE_MOUNTS_DIR/data ; pwd ; curl -sLO {app_setup_url} ; chmod +x {script_name} ; ./{script_name}'"
    ]

    log.debug(task_commands)

    user = batchmodels.UserIdentity(
        auto_user=batchmodels.AutoUserSpecification(
            scope=batchmodels.AutoUserScope.pool,
            elevation_level=batchmodels.ElevationLevel.admin,
        )
    )

    task = batchmodels.TaskAddParameter(
        id=task_id,
        user_identity=user,
        command_line=task_commands[0],
    )

    batch_client.task.add(job_id=jobid, task=task)
    log.info(f"Task [{task_id}] created!")


def _append_environment_settings(environment_settings, name, value):
    """
    Appends environment variable to be used by the application.
    All variables are converted to upper case for app execution.

    """
    environment_settings.append(
        batchmodels.EnvironmentSetting(
            name=name.upper(),
            value=str(value),
        )
    )


def _get_environment_settings(appinputs):
    environment_settings = []

    for key, value in appinputs.items():
        _append_environment_settings(environment_settings, key, value)

    return environment_settings


def create_compute_task(jobid, number_of_nodes, ppr_perc, sku, appinputs):
    if not batch_client:
        log.critical("batch_client is None")
        return

    ppn = _get_process_per_node(ppr_perc, sku)
    random_code = utils.get_random_code()
    task_id = f"mpi-compute-{random_code}"
    log.info(f"Creating compute task: {task_id}")

    user = batchmodels.UserIdentity(
        auto_user=batchmodels.AutoUserSpecification(
            scope=batchmodels.AutoUserScope.pool,
            elevation_level=batchmodels.ElevationLevel.non_admin,
        )
    )

    app_run_script = env["APPRUNSCRIPT"]
    task_commands = [
        f"/bin/bash -c '$AZ_BATCH_NODE_MOUNTS_DIR/data/{app_run_script}'",
    ]

    log.debug(task_commands)

    multi_instance_settings = batchmodels.MultiInstanceSettings(
        number_of_instances=number_of_nodes,
        coordination_command_line="/bin/bash -c env",
    )

    environment_settings = _get_environment_settings(appinputs)
    _append_environment_settings(environment_settings, "NODES", number_of_nodes)
    _append_environment_settings(environment_settings, "PPN", ppn)

    task = batchmodels.TaskAddParameter(
        id=task_id,
        user_identity=user,
        command_line=task_commands[0],
        multi_instance_settings=multi_instance_settings,
        environment_settings=environment_settings,
    )

    batch_client.task.add(job_id=jobid, task=task)
    log.info(f"Task [{task_id}] created!")
    return task_id


def _get_process_per_node(ppn_perc, sku):
    """
    Assumes that the sku is in the form of Standard_HB60rs and is valid
    """
    log.debug(f"get_process_per_node for sku={sku}")

    ppn_perc = float(ppn_perc)
    total_cores = _get_total_cores(sku)
    ppn = int(total_cores * ppn_perc / 100)

    return ppn


def get_environment():
    return env


def setup_environment(filename):
    global batch_client

    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            if "#" in line or "=" not in line:
                continue
            line = line.strip()

            variable = line.split("=")[0]
            value = line.split("=")[1]
            env[variable] = value

    required_env_vars = [
        "SUBSCRIPTION",
        "RG",
        "BATCHACCOUNT",
        "STORAGEACCOUNT",
        "VNETNAME",
        "VSUBNETNAME",
        "REGION",
        "APPSETUPURL",
        "APPRUNSCRIPT",
    ]

    for var in required_env_vars:
        if var not in env:
            log.critical(f"{filename}: Environment variable {var} is not set")
            log.critical("Perhaps environment deployer script was not run?")
            sys.exit(1)

    # TODO: need more testing here
    # perhaps create subscription and subscriptionid variables
    env["SUBSCRIPTION"] = get_subscription_id(env["SUBSCRIPTION"])

    if not resource_group_exists(env["SUBSCRIPTION"], env["RG"]):
        return False

    env["SUBVNETID"] = _get_subnet_id(
        env["SUBSCRIPTION"], env["RG"], env["VNETNAME"], env["VSUBNETNAME"]
    )

    batch_client = _get_batch_client(env["SUBSCRIPTION"], env["RG"])

    env["NODEAGENTSKU"] = _get_node_agent_sku(VMIMAGE)

    # TODO: need to check if environment is indeed setup

    log.info(f"Environment setup finished: {env}")
    return True


def delete_environment():
    if not batch_client:
        log.critical("batch_client is None")
        return

    resource_group = env["RG"]
    credential = DefaultAzureCredential()
    subscription_id = env["SUBSCRIPTION"]

    log.debug(f"Deleting resource group {resource_group}")
    resource_client = ResourceManagementClient(credential, subscription_id)

    rg_result = resource_client.resource_groups.begin_delete(resource_group)
    log.debug(f"resource group deleted result={rg_result}")

    log.info("Environment deleted")


def wait_task_completion(jobid, taskid):
    log.info(f"Waiting for task completion {taskid}")

    if not batch_client:
        log.critical("batch_client is None")
        return

    while True:
        task = batch_client.task.get(jobid, taskid)
        log.info(f"task state={task.state}")
        if task.state == batchmodels.TaskState.completed:
            break
        time.sleep(5)


def _get_total_cores(vm_size):
    log.debug(f"Get total cores for sku={vm_size}")

    credentials = DefaultAzureCredential()

    subscription_id = env["SUBSCRIPTION"]
    region = env["REGION"]

    compute_client = ComputeManagementClient(credentials, subscription_id)

    results = compute_client.resource_skus.list(
        filter="location eq '{}'".format(region)
    )

    resourceSkusList = [result.as_dict() for result in results]
    filtered_sku = next(
        sku for sku in resourceSkusList if sku["name"].lower() == vm_size.lower()
    )

    if filtered_sku:
        vcpus_available = next(
            capability["value"]
            for capability in filtered_sku["capabilities"]
            if capability["name"] == "vCPUsAvailable"
        )
        log.debug(f"vcpus_available={vcpus_available} for sku={vm_size}")
        return int(vcpus_available)
    else:
        log.critical(f"Cannot find sku={vm_size} to obtain its total cores")
        return None


def _read_stream_as_string(stream, encoding) -> str:
    """
    Read stream as string

    :param stream: input stream generator
    :param str encoding: The encoding of the file. The default is utf-8.
    :return: The file content.
    """
    output = io.BytesIO()
    try:
        for data in stream:
            output.write(data)
        if encoding is None:
            encoding = DEFAULT_ENCODING
        return output.getvalue().decode(encoding)
    finally:
        output.close()


def _get_average_value(metrics_data):
    values = []
    if metrics_data.value is None:
        return None

    for item in metrics_data.value:
        for timeserie in item.timeseries:
            for data in timeserie.data:
                if data.average is not None:
                    values.append(data.average)

    log.debug(f"metric values={values}")
    numbers = np.array(values)
    n = len(numbers)
    numbers.sort()

    if n == 0:
        log.warn("zero values coming from collected metric data")
    else:
        cut_off_low = numbers[int(0.1 * n)]
        cut_off_high = numbers[int(0.9 * n)]

    filtered_numbers = [x for x in numbers if x > cut_off_low and x < cut_off_high]

    return np.average(filtered_numbers)


def get_pool_resource_ids(batch_client, poolid):
    resource_ids = []
    nodes = list(batch_client.compute_node.list(poolid))
    for node in nodes:
        resource_id = f"/subscriptions/{env['SUBSCRIPTION']}/resourceGroups/{env['RG']}/providers/Microsoft.Batch/batchAccounts/{env['BATCHACCOUNT']}/pools/{poolid}/nodes/{node.id}"
        resource_ids.append(resource_id)

    return resource_ids


def _get_batch_resource_group(poolid):
    credentials = DefaultAzureCredential()

    subscription_id = env["SUBSCRIPTION"]
    resource_group = env["RG"]

    resource_client = ResourceManagementClient(credentials, subscription_id)

    resource_groups = list(resource_client.resource_groups.list())
    tag_key = "BatchAccountName"
    tag_value = env["BATCHACCOUNT"]

    target_resource_group = None
    for rg in resource_groups:
        tags = rg.tags or {}
        if (
            tag_key in tags
            and tags[tag_key] == tag_value
            and "PoolName" in tags
            and tags["PoolName"] == poolid
        ):
            target_resource_group = rg
            break

    if target_resource_group:
        log.debug(
            f"Resource group with '{tag_key}={tag_value}' and PoolName={poolid} is found:"
        )

        log.debug(f"Name: {target_resource_group.name}")
        log.debug(f"Location: {target_resource_group.location}")
        return target_resource_group.name
    else:
        log.critical(
            f"No resource group with '{tag_key}={tag_value} and PoolName={poolid}' found."
        )
        return None


def get_vmss_batch_resource_ids(batch_client, poolid):
    batch_resource_group = _get_batch_resource_group(poolid)

    resource_ids = []
    credentials = DefaultAzureCredential()
    subscription_id = env["SUBSCRIPTION"]

    rclient = ResourceManagementClient(credentials, subscription_id)
    items = rclient.resources.list_by_resource_group(batch_resource_group)
    vmss = None
    for resource in items:
        if resource.type == "Microsoft.Compute/virtualMachineScaleSets":
            vmss = resource
        break

    if vmss:
        compute_client = ComputeManagementClient(credentials, subscription_id)
        instances = compute_client.virtual_machine_scale_set_vms.list(
            batch_resource_group, vmss.name
        )
        resource_ids = [instance.id for instance in instances]
        return resource_ids

    return None


def _get_monitoring_data(batch_client, poolid, jobid, taskid):
    task = batch_client.task.get(jobid, taskid)

    if task.state != batchmodels.TaskState.completed:
        log.debug(f"task not completed state={task.state} taskid={taskid}")
        return

    credentials = DefaultAzureCredential()
    subscription_id = env["SUBSCRIPTION"]
    client = MonitorManagementClient(credentials, subscription_id)

    # Azure monitor logs metrics by UTC time
    start_time = str(task.execution_info.start_time).replace("+00:00", "")
    end_time = str(task.execution_info.end_time).replace("+00:00", "")

    resource_ids = get_vmss_batch_resource_ids(batch_client, poolid)

    cpu_usage_list = []
    for resource_id in resource_ids:
        average_cpu = None
        while average_cpu is None:
            metrics_data = client.metrics.list(
                resource_id,
                timespan="{}/{}".format(start_time, end_time),
                interval="PT1M",
                metricnames="Percentage CPU",
                aggregation="average",
            )

            log.debug(f"Metric data: {metrics_data}")
            average_cpu = _get_average_value(metrics_data)
            if average_cpu is None:
                log.debug("average_cpu is None, retrying...")

            time.sleep(5)

        cpu_usage_list.append(float(average_cpu))

    return cpu_usage_list


def _get_appinputs_str(appinputs):
    str_appinputs = ""
    for key, value in appinputs:
        str_appinputs += f"{key} {value} "

    return str_appinputs


def get_task_stdout(batch_client, jobid, taskid):
    stream = batch_client.file.get_from_task(jobid, taskid, STANDARD_OUT_FILE_NAME)
    file_text = _read_stream_as_string(stream, DEFAULT_ENCODING)
    return file_text


# TODO: may move this to data_collector.py in future
def store_task_execution_data(poolid, jobid, taskid, ppr_perc, appinputs, dataset_file):
    log.info(f"collecting task execution data: {taskid}")

    if batch_client is None:
        log.critical("batch_client is None")
        return

    datapoint = {}
    task = batch_client.task.get(jobid, taskid)

    if task.state != batchmodels.TaskState.completed:
        log.debug(f"task not completed state={task.state} taskid={taskid}")
        return

    total_elapsed = task.execution_info.end_time - task.execution_info.start_time
    total_elapsed_in_seconds = int(total_elapsed.total_seconds())
    cpu_usage = _get_monitoring_data(batch_client, poolid, jobid, taskid)
    log.debug(f"cpu usage={cpu_usage}")

    # TODO: may be required to get the list of nodes used by the task
    # for now we assume that the task is using all nodes in the pool
    #
    # stdout = get_task_stdout(batch_client, jobid, taskid)
    # log.debug(f"stdout={stdout}")

    pool_info = batch_client.pool.get(poolid)
    sku = pool_info.vm_size
    number_of_nodes = task.multi_instance_settings.number_of_instances
    total_cores = _get_total_cores(sku) * number_of_nodes

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

    datapoint["timestamp"] = timestamp
    datapoint["sku"] = sku
    datapoint["nnodes"] = number_of_nodes
    datapoint["total_cores"] = total_cores
    datapoint["ppr_perc"] = float(ppr_perc)
    datapoint["cpu_usage"] = cpu_usage
    datapoint["exec_time"] = total_elapsed_in_seconds
    datapoint["appinputs"] = appinputs
    datapoint["deployment"] = env["RG"]
    datapoint["region"] = env["REGION"]

    log.debug(f"data point = {datapoint}")
    dataset_handler.add_datapoint(dataset_file, datapoint)
