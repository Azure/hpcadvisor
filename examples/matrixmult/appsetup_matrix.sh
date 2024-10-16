#!/usr/bin/env bash

export APPEXEC=mpi_matrix_mult

[[ -f /etc/bashrc ]] && . /etc/bashrc

source /etc/profile.d/modules.sh
module load gcc-9.2.0
module load mpi/openmpi

hpcadvisor_setup() {
  echo "main setup: $(pwd)"

  set -x

  CODEURL=https://raw.githubusercontent.com/marconetto/testbed/main/mpi_matrix_mult.c
  APPCODE=$(basename $CODEURL)
  curl -sL $CODEURL -o "$APPCODE"

  mpicc -o "${APPEXEC}" "${APPCODE}"

  [[ $? -ne 0 ]] && return 1

  return 0
}

hpcadvisor_run() {
  echo "main run: $(pwd)"

  ln -sf "../${APPEXEC}" .

  [[ -z $APPINTERACTIONS ]] && APPINTERACTIONS=5
  [[ -z $APPMATRIXSIZE ]] && APPMATRIXSIZE=1000

  NP=$(($NNODES * $PPN))
  EXECPATH=$(realpath "${APPEXEC}")

  mpirun -np $NP --host "$HOSTLIST_PPN" --map-by ppr:"${PPN}":node "$EXECPATH" "${APPMATRIXSIZE}" "${APPINTERACTIONS}"
  [[ $? -ne 0 ]] && return 1

  return 0
}
