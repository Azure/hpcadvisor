#!/usr/bin/env bash

hpcadvisor_setup() {
  echo "main setup $(pwd)"

  echo "Setting up data ..."

  if [[ -f in.lj.txt ]]; then
    echo "Data already exists"
    return 0
  fi
  wget https://www.lammps.org/inputs/in.lj.txt
}

hpcadvisor_run() {
  echo "main run $(pwd)"

  source /cvmfs/software.eessi.io/versions/2023.06/init/bash
  module load LAMMPS

  APP=$(which lmp)

  inputfile="in.lj.txt"
  cp ../$inputfile .

  NP=$(($NNODES * $PPN))
  export UCX_NET_DEVICES=mlx5_ib0:1

  [ -z "$BOXFACTOR" ] && BOXFACTOR="30"

  sed -i "s/variable\s\+x\s\+index\s\+[0-9]\+/variable x index $BOXFACTOR/" $inputfile
  sed -i "s/variable\s\+y\s\+index\s\+[0-9]\+/variable y index $BOXFACTOR/" $inputfile
  sed -i "s/variable\s\+z\s\+index\s\+[0-9]\+/variable z index $BOXFACTOR/" $inputfile

  time mpirun -np $NP --host "$HOSTLIST_PPN" "$APP" -i $inputfile

  log_file="log.lammps"

  if grep -q "Total wall time:" "$log_file"; then
    echo "Simulation completed successfully."
    LAMMPSCLOCKTIME=$(cat log.lammps | grep Loop | awk '{print $4}')
    LAMMPSATOMS=$(cat log.lammps | grep Loop | awk '{print $12}')
    LAMMPSSTEPS=$(cat log.lammps | grep Loop | awk '{print $9}')
    echo "HPCADVISORVAR LAMMPSCLOCKTIME=$LAMMPSCLOCKTIME"
    echo "HPCADVISORVAR APPEXECTIME=$LAMMPSCLOCKTIME"
    echo "HPCADVISORVAR LAMMPSATOMS=$LAMMPSATOMS"
    echo "HPCADVISORVAR LAMMPSSTEPS=$LAMMPSSTEPS"
    return 0
  else
    echo "Simulation did not complete successfully."
    return 1
  fi
}
