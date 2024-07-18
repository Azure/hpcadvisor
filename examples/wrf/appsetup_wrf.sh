#!/usr/bin/env bash

hpcadvisor_setup() {
  echo "main setup $(pwd)"
  echo "Setting up data ..."

  if [[ -d v4.4_bench_conus12km/ ]]; then
    echo "Data already exists"
    return
  fi
  curl -k -O https://www2.mmm.ucar.edu/wrf/users/benchmark/v44/v4.4_bench_conus12km.tar.gz
  tar zxvf v4.4_bench_conus12km.tar.gz
}

hpcadvisor_run() {
  echo "main run $(pwd)"

  source /cvmfs/software.eessi.io/versions/2023.06/init/bash
  module load WRF/4.4.1-foss-2022b-dmpar
  #module load mpi/openmpi
  module load OpenMPI/4.1.6-GCC-13.2.0

  which wrf.exe
  which mpirun

  wrfrundir=$(which wrf.exe | sed 's/\/main\/wrf.exe/\/run\//')
  ln -s "\$wrfrundir"/* .
  ln -sf ../v4.4_bench_conus12km/* .

  NP=$(($NODES * $PPN))

  APP_EXE=$(which wrf.exe)

  echo "Running WRF with $NP processes ..."
  export UCX_NET_DEVICES=mlx5_ib0:1
  time mpirun -np $NP --host "$AZ_HOST_LIST_PPN" "$APP_EXE"

  echo "WRF run completed... confirming"

  cat rsl.error.0000
  if [[ $(grep "SUCCESS COMPLETE WRF" rsl.error.0000) ]]; then
    echo "WRF run completed successfully"
    return 0
  else
    echo "WRF run failed"
    return 1
  fi
}
