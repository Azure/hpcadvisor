#!/usr/bin/env bash

set -x

APP_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
echo "APP_EXE_PATH=$APP_EXE_PATH"

function setup_data {
  echo "data will be used from openfoam installation"
  echo "nothing to be done"
  pwd
}

function generate_run_script {

  cat <<EOF >run_app.sh
#!/bin/bash

APP_EXE_PATH="\${AZ_BATCH_NODE_MOUNTS_DIR}/data/"

IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

#source /cvmfs/pilot.eessi-hpc.org/latest/init/bash
source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load OpenFOAM
source "\$FOAM_BASH"

set -x
which mpirun
which simpleFoam

echo "APP_EXE_PATH=\$APP_EXE_PATH"
pwd
cd \$APP_EXE_PATH
pwd
execdir="run_\$((RANDOM % 90000 + 10000))"

cp -r "\$FOAM_TUTORIALS"/incompressibleFluid/motorBike/motorBike \$execdir
chmod -R u+w \$execdir
cd \$execdir || exit
echo "Execution directory: \$execdir"

pwd

[[ -z \$PPN ]] && echo "PPN not defined"
PPN=\$PPN

# Create host file
batch_hosts=hosts.batch
rm -rf \$batch_hosts

hostprocmap=""
for host in "\${ADDR[@]}"; do
    echo \$host >> \$batch_hosts
    hostprocmap="\$hostprocmap,\$host:\${PPN}"
done

#hostprocmap="\${hostprocmap:1}"

NODES=\$(cat \$batch_hosts | wc -l)

NP=\$((\$NODES*\$PPN))

echo "NODES=\$NODES PPN=\$PPN"
echo "hostprocmap=\$hostprocmap"

APP_EXE=\$(which gmx_mpi)
echo "Running OpenFOAM with \$NP processes ..."
export UCX_NET_DEVICES=mlx5_ib0:1

#export OMP_NUM_THREADS=1
#export OMP_NUM_THREADS=\$PPN
export OMPI_MCA_pml=ucx


########################### APP EXECUTION #####################################
BLOCKMESH_DIMENSIONS="20 8 8" # 0.35M cells

mpiopts="\$mpiopts -np \$NP --hostfile \$batch_hosts"

TASKS_PER_NODE=\$SLURM_NTASKS_PER_NODE
NTASKS=\$NP

X=\$((\$NTASKS / 4))
Y=2
Z=2

foamDictionary -entry numberOfSubdomains -set "\$NTASKS" system/decomposeParDict

foamDictionary -entry "hierarchicalCoeffs/n" -set "( \$X \$Y \$Z )" system/decomposeParDict

foamDictionary -entry blocks -set "( hex ( 0 1 2 3 4 5 6 7 ) ( \$BLOCKMESH_DIMENSIONS ) simpleGrading ( 1 1 1 ) )" system/blockMeshDict

time ./Allrun
#############################################################################


########################### TEST OUTPUT #####################################
LOGFILE="log.foamRun"
if [[ -f \$LOGFILE && \$(tail -n 1 "\$LOGFILE") == 'Finalising parallel run' ]]; then
  echo "Simulation completed"
  exit 0
else
  echo "Simulation failed"
  exit 1
fi
#############################################################################

EOF
  chmod +x run_app.sh
}

cd "$APP_EXE_PATH" || exit
setup_data
generate_run_script
