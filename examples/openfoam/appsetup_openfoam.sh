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

cd \$AZ_TASKRUN_DIR
echo "Execution directory: \$(pwd)"

source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load OpenFOAM
source "\$FOAM_BASH"

which mpirun
which simpleFoam

cp -r "\$FOAM_TUTORIALS"/incompressibleFluid/motorBike/motorBike/* .
chmod -R u+w .

NP=\$((\$NODES*\$PPN))

echo "Running OpenFOAM with \$NP processes ..."
export UCX_NET_DEVICES=mlx5_ib0:1

#export OMP_NUM_THREADS=1
#export OMP_NUM_THREADS=\$PPN
export OMPI_MCA_pml=ucx

# allow flags to be added to the mpirun command through FOAM_MPIRUN_FLAGS environment variable
sed -i '/RunFunctions/a source <(declare -f runParallel | sed "s/mpirun/mpirun \\\\\\\$FOAM_MPIRUN_FLAGS/g")' Allrun

sed -i 's#/bin/sh#/bin/bash#g' Allrun
sed -i '/bash/a set -x' Allrun


# export FOAM_MPIRUN_FLAGS="--host \$AZ_HOST_LIST_PPN \$(env | grep 'WM_\|FOAM_' | cut -d'=' -f1 | sed 's/^/-x /g' | tr '\n' ' ') -x PATH -x LD_LIBRARY_PATH -x MPI_BUFFER_SIZE -x UCX_IB_MLX5_DEVX=n -x UCX_POSIX_USE_PROC_LINK=n --report-bindings --verbose --map-by core --bind-to core "

export FOAM_MPIRUN_FLAGS="--hostfile \$AZ_HOSTFILE_PATH \$(env | grep 'WM_\|FOAM_' | cut -d'=' -f1 | sed 's/^/-x /g' | tr '\n' ' ') -x PATH -x LD_LIBRARY_PATH -x MPI_BUFFER_SIZE -x UCX_IB_MLX5_DEVX=n -x UCX_POSIX_USE_PROC_LINK=n --report-bindings --verbose --map-by core --bind-to core "
echo \$FOAM_MPIRUN_FLAGS

########################### APP EXECUTION #####################################
BLOCKMESH_DIMENSIONS="80 32 32"
# BLOCKMESH_DIMENSIONS="40 16 16"
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
