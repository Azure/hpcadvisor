#!/usr/bin/env bash

APP_EXE=mpi_matrix_mult
APP_CODE=mpi_matrix_mult.c
APP_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"

set -x

echo "APP_EXE_PATH=$APP_EXE_PATH"

function setup_app_and_data {

  source /etc/profile.d/modules.sh

  module load gcc-9.2.0
  module load mpi/hpcx

  CODEURL=https://raw.githubusercontent.com/marconetto/testbed/main/mpi_matrix_mult.c

  echo "APP_EXE_PATH=$MPI_EXE_PATH"
  curl -sL $CODEURL -o "$APP_EXE_PATH"/"$APP_CODE"

  echo "Compiling mpi code"
  mpicc -o ${APP_EXE} ${APP_CODE}
  ls -l ${APP_EXE}

}

function generate_run_script {

  cat <<EOF >run_app.sh

#!/bin/bash

APP_EXE=${APP_EXE}
APP_CODE=${APP_CODE}
APP_EXE_PATH="\${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
cd \$APP_EXE_PATH
APP_EXE_PATH=\${APP_EXE_PATH}/\${APP_EXE}



APPINTERACTIONS=\${APPINTERACTIONS}
APPMATRIXSIZE=\${APPMATRIXSIZE}
[[ -z \$APPINTERACTIONS ]] && APPINTERACTIONS=10
[[ -z \$APPMATRIXSIZE ]] && APPMATRIXSIZE=3000

[[ -f /etc/bashrc ]] && . /etc/bashrc

source /etc/profile.d/modules.sh

module load gcc-9.2.0
module load mpi/hpcx

# Create host file
batch_hosts=hosts.batch
rm -rf \$batch_hosts

IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

[[ -z \$PPN ]] && echo "PPN not defined"
PPN=\$PPN

hostprocmap=""

for host in "\${ADDR[@]}"; do
    echo $host >> \$batch_hosts
    hostprocmap="\$hostprocmap,\$host:\${PPN}"
done

hostprocmap="\${hostprocmap:1}"

NODES=\$(cat \$batch_hosts | wc -l)

NP=\$((\$NODES*\$PPN))

echo "NODES=\$NODES PPN=\$PPN"
echo "hostprocmap=\$hostprocmap"
set -x

echo "=========VARIABLES======="
set
echo "========================="
mpirun -np \$NP --oversubscribe --host \$hostprocmap --map-by ppr:\${PPN}:node \${APP_EXE_PATH} \${APPMATRIXSIZE} \${APPINTERACTIONS}

EOF

  chmod +x run_app.sh

}

[[ -f /etc/bashrc ]] && . /etc/bashrc

cd "$APP_EXE_PATH" || exit
setup_app_and_data
generate_run_script
