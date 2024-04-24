#!/usr/bin/env bash

set -x

MPI_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
MPI_EXE=wrf.exe
#MPI_CODE=mpi_matrix_mult.c
echo "MPI_EXE_PATH=$MPI_EXE_PATH"

function setup_data {
  if [[ -d v4.4_bench_conus12km/ ]]; then
    echo "Data already exists"
    return
  fi
  curl -k -O https://www2.mmm.ucar.edu/wrf/users/benchmark/v44/v4.4_bench_conus12km.tar.gz
  tar zxvf v4.4_bench_conus12km.tar.gz
}

function generate_run_script {

  cat <<EOF >run_app.sh
#!/bin/bash

MPI_EXE_PATH="\${AZ_BATCH_NODE_MOUNTS_DIR}/data/"

set -x
IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

#for host in "\${ADDR[@]}"; do
#    ssh \$host 'sudo mount -t cvmfs software.eessi.io /cvmfs/software.eessi.io'
#done



source /cvmfs/software.eessi.io/versions/2023.06/init/bash
module load WRF/4.4.1-foss-2022b-dmpar
#module load mpi/openmpi
module load OpenMPI/4.1.6-GCC-13.2.0

which wrf.exe
which mpirun

echo "MPI_EXE_PATH=\$MPI_EXE_PATH"
pwd
cd \$MPI_EXE_PATH
pwd
execdir="run_\$((RANDOM % 90000 + 10000))"
mkdir -p \$execdir
cd \$execdir || exit
echo "Execution directory: \$execdir"

wrfrundir=\$(which wrf.exe | sed 's/\/main\/wrf.exe/\/run\//')
ln -s "\$wrfrundir"/* .
ln -sf ../v4.4_bench_conus12km/* .

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
set -x

APP_EXE=\$(which wrf.exe)
echo "Running WRF with \$NP processes ..."
export UCX_NET_DEVICES=mlx5_ib0:1
time mpirun -np \$NP --host \$hostprocmap \$APP_EXE

echo "WRF run completed... confirming"

cat rsl.error.0000
if [[ \$(grep "SUCCESS COMPLETE WRF" rsl.error.0000) ]]; then
  echo "WRF run completed successfully"
  exit 0
else
  echo "WRF run failed"
  exit 1
fi

EOF
  chmod +x run_app.sh
}

cd "$MPI_EXE_PATH" || exit
setup_data
generate_run_script
