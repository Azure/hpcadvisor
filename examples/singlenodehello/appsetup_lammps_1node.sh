#!/usr/bin/env bash
hpcadvisor_setup() {
    echo "main LAMMPS locally setup $(pwd)"
    yum install epel-release -y
    yum install -y lammps
    wget https://www.lammps.org/inputs/in.lj.txt

}

hpcadvisor_run() {
    echo "main LAMMPS locally run $(pwd)"
    export OMP_NUM_THREADS=$(nproc)

    pwd
    ls -l
    ls -l ..
    inputfile="in.lj.txt"

    cp ../$inputfile .
    pwd
    ls -l
    BOXFACTOR=6
    sed -i "s/variable\s\+x\s\+index\s\+[0-9]\+/variable x index $BOXFACTOR/" $inputfile
    sed -i "s/variable\s\+y\s\+index\s\+[0-9]\+/variable y index $BOXFACTOR/" $inputfile
    sed -i "s/variable\s\+z\s\+index\s\+[0-9]\+/variable z index $BOXFACTOR/" $inputfile
    echo "BOXFACTOR=$BOXFACTOR"
    sed -i '/^[[:space:]]*run[[:space:]]\+[0-9]\+/i thermo 10' $inputfile

    echo "-------------"
    cat $inputfile
    echo "-------------"
    time lmp -in $inputfile
}
