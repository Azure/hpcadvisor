#!/usr/bin/env bash

[[ -f /etc/bashrc ]] && . /etc/bashrc

hpcadvisor_setup() {
    echo "main setup: $(pwd)"

    set -x
    echo "single node setup hello world"

    return 0
}

hpcadvisor_run() {
    echo "main run: $(pwd)"

    echo "Hello single node task!"

    return 0
}
