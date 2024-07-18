#!/usr/bin/env bash

hpcadvisor_setup() {
  echo "main setup $(pwd)"
  echo "Setting up data ..."

  if [[ -d GROMACS_TestCaseA ]]; then
    echo "Data already exists"
    ls -l GROMACS_TestCaseA
    return
  fi
  wget https://repository.prace-ri.eu/ueabs/GROMACS/2.2/GROMACS_TestCaseA.tar.xz
  tar -xf GROMACS_TestCaseA.tar.xz
}

hpcadvisor_run() {
  echo "main run $(pwd)"

  source /cvmfs/pilot.eessi-hpc.org/latest/init/bash
  #source /cvmfs/software.eessi.io/versions/2023.06/init/bash
  module load GROMACS
  module load OpenMPI

  set -x
  which gmx_mpi
  which mpirun

  ln -s "../GROMACS_TestCaseA/ion_channel.tpr" .
  ls -l ion_channel.tpr

  NP=$(($NODES * $PPN))

  APP_EXE=$(which gmx_mpi)
  echo "Running GROMACS with $NP processes ..."

  export UCX_NET_DEVICES=mlx5_ib0:1
  export OMP_NUM_THREADS=1
  #export OMP_NUM_THREADS=$PPN
  export OMPI_MCA_pml=ucx

  time mpirun -np $NP --host "$AZ_HOST_LIST_PPN" "$APP_EXE" mdrun \
    -s ion_channel.tpr \
    -cpt 1000 \
    -maxh 1.0 \
    -nsteps 50000 \
    -ntomp $OMP_NUM_THREADS

  if [[ -f md.log && $(grep "Finished mdrun" md.log) ]]; then
    echo "GROMACS run completed successfully"
    return 0
  else
    echo "GROMACS run failed"
    return 1
  fi
}
