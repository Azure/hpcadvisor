#!/usr/bin/env python3

import argparse
import os
import sys

from hpcadvisor import logger, main_common


def _process_arguments():
    envfile = None
    userinput = None
    debug = False
    gui = False

    parser = argparse.ArgumentParser(prog="hpcadvisor", description="HPC Advisor")

    parser.add_argument("-e", "--envfile", help="Env File", required=False)
    parser.add_argument("-u", "--userinput", help="User Input File", required=False)
    parser.add_argument(
        "-g", "--gui", action="store_true", help="GUI enabled", required=False
    )
    parser.add_argument(
        "-p",
        "--plots",
        action="store_true",
        help="Generate plots in CLI",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--resettasks",
        help="Reset Task Status",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-d", "--debug", help="Debug Mode", action="store_true", default=False
    )

    args = parser.parse_args()

    if args.gui == False and (args.userinput == None):
        print("Need either GUI enabled OR ui_input file")
        parser.print_help()
        sys.exit(1)

    userinput = args.userinput
    envfile = args.envfile
    gui = args.gui
    debug = args.debug
    plots = args.plots
    resettasks = args.resettasks

    return userinput, envfile, gui, debug, plots, resettasks


def main():
    print("HPC Advisor tool starting...")
    userinput, envfile, gui, debug, plots, resettasks = _process_arguments()

    if debug:
        logger.setup_debug_mode()

    if resettasks and envfile:
        main_common.reset_tasks(envfile)

    if gui:
        print("Using GUI mode")
        from hpcadvisor import main_gui

        main_gui.main()
    else:
        print("Using CLI mode")
        from hpcadvisor import main_cli

        main_cli.main(userinput, envfile, plots)


if __name__ == "__main__":
    main()
