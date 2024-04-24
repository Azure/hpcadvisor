#!/usr/bin/env bash

set -x

APP_EXE_PATH="${AZ_BATCH_NODE_MOUNTS_DIR}/data/"
echo "APP_EXE_PATH=$APP_EXE_PATH"

function setup_data {

  namdurl=https://www.ks.uiuc.edu/Research/namd/3.0b6/download/120834/NAMD_3.0b6_Linux-x86_64-verbs-smp.tar.gz
  namddir=NAMD_3.0b6_Linux-x86_64-verbs-smp

  echo "setup data at dir: $(pwd)"

  if [ ! -d $namddir ]; then
    wget "$namdurl"
    namdtgz=$(basename $namdurl)
    tar zxvf "$namdtgz"
    caseurl=https://www.ks.uiuc.edu/Research/namd/utilities/stmv.tar.gz
    wget "$caseurl"
    casetgz=$(basename $caseurl)
    tar zxvf "$casetgz"
    sed -i 's| .*stmv-output| ./stmv-output|g' stmv/stmv.namd
    sed -i 's|numsteps.*|numsteps 5000|g' stmv/stmv.namd
  else
    echo "nothing to be done. App and data all ready"
  fi

}

function generate_run_script {

  cat <<EOF >run_app.sh
#!/bin/bash

APP_EXE_PATH="\${AZ_BATCH_NODE_MOUNTS_DIR}/data/"

IFS=';' read -ra ADDR <<< "\$AZ_BATCH_NODE_LIST"

echo "APP_EXE_PATH=\$APP_EXE_PATH"
pwd
cd \$APP_EXE_PATH
pwd
execdir="run_\$((RANDOM % 90000 + 10000))"

mkdir \$execdir
cd \$execdir || exit
echo "Execution directory: \$execdir"

namddir=NAMD_3.0b6_Linux-x86_64-verbs-smp
export PATH="\$APP_EXE_PATH/\$namddir:\$PATH"

pwd

[[ -z \$PPN ]] && echo "PPN not defined"
PPN=\$PPN

# Create host file
batch_hosts=hosts.batch
rm -rf \$batch_hosts

hostprocmap=""
for host in "\${ADDR[@]}"; do
    echo "host \$host ++cpus \$PPN" >> \$batch_hosts
    hostprocmap="\$hostprocmap,\$host:\${PPN}"
done

echo "------- hostfile"
cat \$batch_hosts
echo "-------"

NODES=\$(cat \$batch_hosts | wc -l)

NP=\$((\$NODES*\$PPN))

echo "NODES=\$NODES PPN=\$PPN"
echo "hostprocmap=\$hostprocmap"

APP_EXE=\$(which namd3)

echo "APP_EXE=\$APP_EXE"


########################### APP EXECUTION #####################################
cp \$APP_EXE_PATH/stmv/* .
ls -l
time charmrun \$APP_EXE ++p \$NP ++nodelist \$batch_hosts +setcpuaffinity stmv.namd
#############################################################################


########################### TEST OUTPUT #####################################
OUTPUTFILE=stmv-output.coor

if [ -f "\$OUTPUTFILE" ]; then
    echo "Output file found: \$OUTPUTFILE"
    exit 0
else
    echo "Output file not found: \$OUTPUTFILE"
    exit 1
fi
#############################################################################

EOF
  chmod +x run_app.sh
}

cd "$APP_EXE_PATH" || exit
setup_data
generate_run_script
