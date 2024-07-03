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

#[[ -z \$PPN ]] && echo "PPN not defined"
#PPN=\$PPN
echo "PPN=\$PPN"




# Create host file
batch_hosts=hostfile
rm -rf \$batch_hosts

hostprocmap=""
for host in "\${ADDR[@]}"; do
    echo "\$host slots=\${PPN}" >> \$batch_hosts
    hostprocmap="\$hostprocmap,\$host:\${PPN}"
done

echo "hostfile start"
cat \$batch_hosts
echo "hostfile end"

#hostprocmap="\${hostprocmap:1}"

NODES=\$(cat \$batch_hosts | wc -l)

NP=\$((\$NODES*\$PPN))

echo "NODES=\$NODES PPN=\$PPN"
echo "hostprocmap=\$hostprocmap"

echo "Running OpenFOAM with \$NP processes ..."
export UCX_NET_DEVICES=mlx5_ib0:1

#export OMP_NUM_THREADS=1
#export OMP_NUM_THREADS=\$PPN
export OMPI_MCA_pml=ucx

# allow flags to be added to the mpirun command through FOAM_MPIRUN_FLAGS environment variable
sed -i '/RunFunctions/a source <(declare -f runParallel | sed "s/mpirun/mpirun \\\\\\\$FOAM_MPIRUN_FLAGS/g")' Allrun

sed -i 's#/bin/sh#/bin/bash#g' Allrun
sed -i '/bash/a set -x' Allrun


#export FOAM_MPIRUN_FLAGS="-mca pml ucx $(env | grep 'WM_\|FOAM_' | cut -d'=' -f1 | sed 's/^/-x /g' | tr '\n' ' ') -x MPI_BUFFER_SIZE -x UCX_IB_MLX5_DEVX=n -x UCX_POSIX_USE_PROC_LINK=n -x PATH -x LD_LIBRARY_PATH --oversubscribe"

export FOAM_MPIRUN_FLAGS="--hostfile \$batch_hosts \$(env | grep 'WM_\|FOAM_' | cut -d'=' -f1 | sed 's/^/-x /g' | tr '\n' ' ') -x PATH -x LD_LIBRARY_PATH -x MPI_BUFFER_SIZE -x UCX_IB_MLX5_DEVX=n -x UCX_POSIX_USE_PROC_LINK=n --report-bindings --verbose --map-by core --bind-to core "
echo \$FOAM_MPIRUN_FLAGS

########################### APP EXECUTION #####################################
BLOCKMESH_DIMENSIONS="40 16 16"
#BLOCKMESH_DIMENSIONS="20 8 8" # 0.35M cells

NTASKS=\$NP

X=\$((\$NTASKS / 4))
Y=2
Z=2

foamDictionary -entry numberOfSubdomains -set "\$NTASKS" system/decomposeParDict

foamDictionary -entry "hierarchicalCoeffs/n" -set "( \$X \$Y \$Z )" system/decomposeParDict

foamDictionary -entry blocks -set "( hex ( 0 1 2 3 4 5 6 7 ) ( \$BLOCKMESH_DIMENSIONS ) simpleGrading ( 1 1 1 ) )" system/blockMeshDict

cat Allrun
time ./Allrun
#############################################################################


########################### TEST OUTPUT #####################################
LOGFILE="log.foamRun"
if [[ -f \$LOGFILE && \$(tail -n 1 "\$LOGFILE") == 'Finalising parallel run' ]]; then
  echo "Simulation completed"
#  reconstructPar -constant
  touch case.foam
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
