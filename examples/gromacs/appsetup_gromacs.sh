#!/usr/bin/env bash

set -x

MPI_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
MPI_EXE=gmx_mpi
#MPI_CODE=mpi_matrix_mult.c
echo "MPI_EXE_PATH=$MPI_EXE_PATH"

function setup_data {
  echo "Setting up data ..."
  pwd

  if [[ -d GROMACS_TestCaseA ]]; then
    echo "Data already exists"
    ls -l GROMACS_TestCaseA
    return
  fi
  wget https://repository.prace-ri.eu/ueabs/GROMACS/2.2/GROMACS_TestCaseA.tar.xz
  tar -xf GROMACS_TestCaseA.tar.xz
}

function generate_run_script {

  cat <<EOF >run_app.sh
#!/bin/bash

MPI_EXE_PATH="\${AZ_BATCH_NODE_MOUNTS_DIR}/data/"

IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

source /cvmfs/pilot.eessi-hpc.org/latest/init/bash
#source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load GROMACS
module load OpenMPI

set -x
which gmx_mpi
which mpirun

echo "MPI_EXE_PATH=\$MPI_EXE_PATH"
pwd
cd \$MPI_EXE_PATH
pwd
execdir="run_\$((RANDOM % 90000 + 10000))"
mkdir -p \$execdir
cd \$execdir || exit
echo "Execution directory: \$execdir"

pwd
ls -l "\$MPI_EXE_PATH/"
ln -s "\$MPI_EXE_PATH/GROMACS_TestCaseA/ion_channel.tpr" .
ls -l ion_channel.tpr

# Create host file
batch_hosts=hosts.batch
rm -rf \$batch_hosts

IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

[[ -z \$PPN ]] && echo "PPN not defined"
PPN=\$PPN

hostprocmap=""

for host in "\${ADDR[@]}"; do
    echo \$host >> \$batch_hosts
    hostprocmap="\$hostprocmap,\$host:\${PPN}"
done

hostprocmap="\${hostprocmap:1}"

NODES=\$(cat \$batch_hosts | wc -l)

NP=\$((\$NODES*\$PPN))

echo "NODES=\$NODES PPN=\$PPN"
echo "hostprocmap=\$hostprocmap"

APP_EXE=\$(which gmx_mpi)
echo "Running GROMACS with \$NP processes ..."
export UCX_NET_DEVICES=mlx5_ib0:1

export OMP_NUM_THREADS=1
#export OMP_NUM_THREADS=\$PPN
export OMPI_MCA_pml=ucx

time mpirun -np \$NP --host \$hostprocmap \$APP_EXE mdrun \
    -s ion_channel.tpr \
    -cpt 1000 \
    -maxh 1.0 \
    -nsteps 50000 \
    -ntomp \$OMP_NUM_THREADS

if [[ -f md.log && \$(grep "Finished mdrun" md.log) ]]; then
    echo "GROMACS run completed successfully"
    exit 0
else
    echo "GROMACS run failed"
    exit 1
fi

EOF
  chmod +x run_app.sh
}

cd "$MPI_EXE_PATH" || exit
setup_data
generate_run_script
