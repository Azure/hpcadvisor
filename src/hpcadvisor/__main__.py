#!/usr/bin/env python3

import argparse
import sys

from hpcadvisor import main_cli, main_gui


# TODO: need better way to handle these options
def _process_arguments():
    envfile = None
    userinput = None
    debug = False
    gui = False

    parser = argparse.ArgumentParser(
        prog="hpcadvisor", description="HPC Advisor", exit_on_error=False
    )

    parser.add_argument("-e", "--envfile", help="Env File", required=False)
    parser.add_argument("-u", "--userinput", help="User Input File", required=False)
    parser.add_argument(
        "-g", "--gui", action="store_true", help="GUI enabled", required=False
    )
    parser.add_argument(
        "-d", "--debug", help="Debug Mode", action="store_true", default=False
    )

    args = parser.parse_args()

    # print(args)
    if args.gui == False and (args.userinput == None):
        print("Need either GUI enabled OR ui_input file")
        parser.print_help()
        sys.exit(1)

    userinput = args.userinput
    envfile = args.envfile
    gui = args.gui
    debug = args.debug

    return userinput, envfile, gui, debug


def main():
    print("HPC Advisor tool starting...")
    userinput, envfile, gui, debug = _process_arguments()

    if gui:
        print("Using GUI mode")
        main_gui.main(debug)
    else:
        print("Using CLI mode")
        main_cli.main(userinput, envfile, debug)
    # main_cli.test(sys.argv[1:])


if __name__ == "__main__":
    main()
