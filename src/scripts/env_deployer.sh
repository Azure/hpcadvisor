#!/usr/bin/env bash

set -ue

TESTVMSKU=Standard_HB120-16rs_v3
# VMIMAGE=OpenLogic:CentOS-HPC:7_9-gen2:7.9.2022040101
VMIMAGE="almalinux:almalinux-hpc:8-hpc-gen2:latest"
# VMIMAGE=microsoft-dsvm:ubuntu-hpc:2204:latest

ADMINUSER=azureuser
DNSZONENAME="privatelink.file.core.windows.net"
STORAGEFILE=data

PROGRESSFILE="env_progress.txt"
VMJUMPBOXNAME="jumpbox"

get_var() {

  ENV_VARS_FILE=$1
  varname=$2

  value=$(sed -n "s/^${varname}=\(.*\)/\1/p" "${ENV_VARS_FILE}")
  echo "$value"
}

setup_vars() {

  ENV_VARS_FILE=$1

  REGION=$(get_var "$ENV_VARS_FILE" "REGION")
  RG=$(get_var "$ENV_VARS_FILE" "RG")
  BATCHACCOUNT=$(get_var "$ENV_VARS_FILE" "BATCHACCOUNT")
  STORAGEACCOUNT=$(get_var "$ENV_VARS_FILE" "STORAGEACCOUNT")
  KEYVAULT=$(get_var "$ENV_VARS_FILE" "KEYVAULT")
  VNETNAME=$(get_var "$ENV_VARS_FILE" "VNETNAME")
  VSUBNETNAME=$(get_var "$ENV_VARS_FILE" "VSUBNETNAME")
  VNETADDRESS=$(get_var "$ENV_VARS_FILE" "VNETADDRESS")

  # optional
  VPNRG=$(get_var "$ENV_VARS_FILE" "VPNRG")
  VPNVNET=$(get_var "$ENV_VARS_FILE" "VPNVNET")
  CREATEJUMPBOX=$(get_var "$ENV_VARS_FILE" "CREATEJUMPBOX")
  PEERVPN=$(get_var "$ENV_VARS_FILE" "PEERVPN")

  PROGRESSFILE=$(dirname "$ENV_VARS_FILE")"/${PROGRESSFILE}"
}

get_random_code() {

  random_number=$((RANDOM % 9000 + 1000))
  timestamp=$(date "+%m%d%H%M")
  echo "${timestamp}""${random_number}"
}

update_progress() {
  message=$1

  echo "$message" >>"${PROGRESSFILE}"
}

create_resource_group() {

  az group create --location "$REGION" \
    --name "$RG"

  update_progress "created resource group"
}

create_vnet_subnet() {

  az network vnet create -g "$RG" \
    -n "$VNETNAME" \
    --address-prefix "$VNETADDRESS"/16 \
    --subnet-name "$VSUBNETNAME" \
    --subnet-prefixes "$VNETADDRESS"/24

  update_progress "created vnet/subnet"
}

create_vm() {

  sku=$1
  vmname="${VMJUMPBOXNAME}"$(get_random_code)
  echo "creating $vmname for testing"

  cloudinitfile=/tmp/vmcreate.$$
  cat <<EOF >"$cloudinitfile"
#cloud-config

runcmd:
- echo "mounting shared storage on the vm"
- mkdir /nfs
- mount $STORAGEACCOUNT.file.core.windows.net:/$STORAGEACCOUNT/$STORAGEFILE /nfs/
EOF

  az vm create -n "$vmname" \
    -g "$RG" \
    --image "$VMIMAGE" \
    --size "$sku" \
    --vnet-name "$VNETNAME" \
    --subnet "$VSUBNETNAME" \
    --public-ip-address "" \
    --admin-username "$ADMINUSER" \
    --generate-ssh-keys \
    --custom-data "$cloudinitfile"

  private_ip=$(az vm show -g "$RG" -n "$vmname" -d --query privateIps -otsv)
  echo "Private IP of $vmname: ${private_ip}"
}

peer_vpn() {

  echo "Peering vpn with created vnet"

  curl -LO https://raw.githubusercontent.com/marconetto/azadventures/main/chapter3/create_peering_vpn.sh

  peername=$(az network vnet peering list --vnet-name "$VPNVNET" --resource-group "$VPNRG" | jq -r --arg vnetip "$VNETADDRESS" '.[] | select(.remoteAddressSpace.addressPrefixes[] | contains($vnetip)) | .name')

  if [ -z "$peername" ]; then
    echo "No peer found"
  else
    echo "Peer found: $peername. Deleting existing peering"
    az network vnet peering delete --name "$peername" --resource-group "$VPNRG" --vnet-name "$VPNVNET"
  fi

  bash ./create_peering_vpn.sh "$VPNRG" "$VPNVNET" "$RG" "$VNETNAME"
  rm create_peering_vpn.sh
}

get_subnetid() {

  subnetid=$(az network vnet subnet show \
    --resource-group "$RG" --vnet-name "$VNETNAME" \
    --name "$VSUBNETNAME" \
    --query "id" -o tsv)

  echo "$subnetid"
}

create_storage_account_files_nfs() {

  az storage account create \
    --resource-group "$RG" \
    --name "$STORAGEACCOUNT" \
    --location "$REGION" \
    --kind FileStorage \
    --sku Premium_LRS \
    --output none

  # disable secure transfer is required for nfs support
  az storage account update --https-only false \
    --name "$STORAGEACCOUNT" --resource-group "$RG"

  az storage share-rm create \
    --storage-account "$STORAGEACCOUNT" \
    --enabled-protocol NFS \
    --root-squash NoRootSquash \
    --name "$STORAGEFILE" \
    --quota 100

  storage_account_id=$(az storage account show \
    --resource-group "$RG" --name "$STORAGEACCOUNT" \
    --query "id" -o tsv)

  update_progress "created storage account"

  subnetid=$(get_subnetid)

  endpoint=$(az network private-endpoint create \
    --resource-group "$RG" --name "$STORAGEACCOUNT-PrivateEndpoint" \
    --location "$REGION" \
    --subnet "$subnetid" \
    --private-connection-resource-id "${storage_account_id}" \
    --group-id "file" \
    --connection-name "$STORAGEACCOUNT-Connection" \
    --query "id" -o tsv)

  dns_zone=$(az network private-dns zone create \
    --resource-group "$RG" \
    --name "$DNSZONENAME" \
    --query "id" -o tsv)

  vnetid=$(az network vnet show \
    --resource-group "$RG" \
    --name "$VNETNAME" \
    --query "id" -o tsv)

  az network private-dns link vnet create \
    --resource-group "$RG" \
    --zone-name "$DNSZONENAME" \
    --name "$VNETNAME-DnsLink" \
    --virtual-network "$vnetid" \
    --registration-enabled false

  endpoint_nic=$(az network private-endpoint show \
    --ids "$endpoint" \
    --query "networkInterfaces[0].id" -o tsv)

  endpoint_ip=$(az network nic show \
    --ids "${endpoint_nic}" \
    --query "ipConfigurations[0].privateIPAddress" -o tsv)

  az network private-dns record-set a create \
    --resource-group "$RG" \
    --zone-name "$DNSZONENAME" \
    --name "$STORAGEACCOUNT"

  az network private-dns record-set a add-record \
    --resource-group "$RG" \
    --zone-name "$DNSZONENAME" \
    --record-set-name "$STORAGEACCOUNT" \
    --ipv4-address "${endpoint_ip}"

  az storage share-rm list -g "$RG" \
    --storage-account "$STORAGEACCOUNT"

  echo "inside the test VM:"
  echo "sudo mkdir /nfs ; sudo mount $STORAGEACCOUNT.file.core.windows.net:/$STORAGEACCOUNT/$STORAGEFILE /nfs/"
  update_progress "created private network endpoints"
}

create_keyvault() {

  echo "Creating keyVault"

  az keyvault create --resource-group "$RG" \
    --name "$KEYVAULT" \
    --location "$REGION" \
    --enabled-for-deployment true \
    --enabled-for-disk-encryption true \
    --enabled-for-template-deployment true

  az keyvault set-policy --resource-group "$RG" \
    --name "$KEYVAULT" \
    --spn ddbf3205-c6bd-46ae-8127-60eb93363864 \
    --key-permissions all \
    --secret-permissions all
  update_progress "created keyvault"
}

create_batch_account_with_usersubscription() {

  # Allow Azure Batch to access the subscription (one-time operation).
  # az role assignment create --assignee ddbf3205-c6bd-46ae-8127-60eb93363864 --role contributor

  create_keyvault

  # Create the Batch account, referencing the Key Vault either by name (if they
  # exist in the same resource group) or by its full resource ID.
  echo "Creating batchAccount"
  az batch account create --resource-group "$RG" \
    --name "$BATCHACCOUNT" \
    --location "$REGION" \
    --keyvault "$KEYVAULT"
  # --storage-account $STORAGEACCOUNT    # does not support azure fileshare
  error=$?
  if [ $error -ne 0 ]; then
    echo "Error creating batch account"
    update_progress "error creating batch account"
    exit 1
  fi
  update_progress "created batch account"
}

# login_batch_with_usersubcription() {
#
#   # Authenticate directly against the account for further CLI interaction.
#   # Batch accounts that allocate pools in the user's subscription must be
#   # authenticated via an Azure Active Directory token.
#
#   echo "login into the batch account with user subscription"
#   az batch account login \
#     --name "$BATCHACCOUNT" \
#     --resource-group "$RG"
#   update_progress "logged into batch account"
# }

main() {

  if [ $# -ne 1 ]; then
    echo "Usage: $0 <env_file>"
    exit 1
  fi

  env_file=$1

  # TODO: move to bicep ---------------------
  setup_vars "$env_file"

  >"$PROGRESSFILE"
  create_resource_group
  create_vnet_subnet
  create_storage_account_files_nfs

  [ "$CREATEJUMPBOX" == "True" ] && create_vm "$TESTVMSKU"
  [ "$PEERVPN" == "True" ] && peer_vpn

  create_batch_account_with_usersubscription
  # login_batch_with_usersubcription
  update_progress "environment created"
  echo "Environment deployer execution completed."
}

main "$@"
