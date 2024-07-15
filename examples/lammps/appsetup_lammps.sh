#!/usr/bin/env bash

set -x

APP_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
echo "APP_EXE_PATH=$APP_EXE_PATH"

function setup_data {
  echo "Downloading data for lammps"
  wget https://www.lammps.org/inputs/in.lj.txt

}

function generate_run_script {

  cat <<EOF >run_app.sh
#!/bin/bash

set -x
cd \$AZ_TASKRUN_DIR
echo "Execution directory: \$(pwd)"

source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load LAMMPS
which mpirun
which lmp

cp ../in.lj.txt .

NP=\$((\$NODES*\$PPN))
export UCX_NET_DEVICES=mlx5_ib0:1

input_file="in.lj.txt"

new_x=10
new_y=10
new_z=10

sed -i "s/variable\s\+x\s\+index\s\+[0-9]\+/variable x index \$new_x/" \$input_file
sed -i "s/variable\s\+y\s\+index\s\+[0-9]\+/variable y index \$new_y/" \$input_file
sed -i "s/variable\s\+z\s\+index\s\+[0-9]\+/variable z index \$new_z/" \$input_file

time mpirun -np \$NP lmp -i in.lj.txt


###

log_file="log.lammps"

if grep -q "Total wall time:" "\$log_file"; then
  echo "Simulation completed successfully."
  exit 0
else
  echo "Simulation did not complete successfully."
  exit 1
fi

EOF
  chmod +x run_app.sh
}

cd "$APP_EXE_PATH" || exit
setup_data
generate_run_script
