#!/usr/bin/env python3

import argparse
import sys

from hpcadvisor import logger, main_common


class CustomHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        return super().start_section("Commands/flags")


def gui_handler(args):
    from hpcadvisor import main_gui

    debug = args.debug
    userinput = args.userinput

    main_gui.main(debug, userinput)


def deployment_handler(args):
    from hpcadvisor import main_cli

    if args.operation == "create":
        if not args.userinput:
            print("User input file required (-u):")
            sys.exit(1)
        main_cli.main_create_deployment(args.name, args.userinput, args.debug)
        return
    elif args.operation == "list":
        main_cli.main_list_deployments()
        return
    elif args.operation == "shutdown":
        main_cli.main_shutdown_deployment(args.name)
        return


def collect_handler(args):
    name = args.name
    userinput = args.userinput
    cleardeployment = args.cleardeployment
    cleartasks = args.cleartasks

    from hpcadvisor import main_cli

    main_cli.main_collect_data(name, userinput, cleardeployment, cleartasks)


def plot_handler(args):
    plotfilter = args.datafilter

    from hpcadvisor import main_cli

    main_cli.main_plot(plotfilter)


def advice_handler(args):
    datafilter = args.datafilter

    from hpcadvisor import main_cli

    main_cli.main_advice(datafilter)


def _process_arguments():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug mode"
    )

    parser = argparse.ArgumentParser(
        prog="hpcadvisor", formatter_class=CustomHelpFormatter, parents=[parent_parser]
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Commands to run", required=True
    )

    deploy = subparsers.add_parser("deploy", help="Deployment help")
    deploy.add_argument("operation", type=str)
    deploy.add_argument("-n", "--name", help="Deployment name", required=False)
    deploy.add_argument("-u", "--userinput", help="User input", required=False)
    deploy.set_defaults(func=deployment_handler)

    collect = subparsers.add_parser("collect", help="Data collection help")
    collect.add_argument("-n", "--name", help="Deployment name", required=True)
    collect.add_argument("-u", "--userinput", help="User input", required=True)
    collect.add_argument(
        "-cd", "--cleardeployment", help="Clear deployment", required=False
    )
    collect.add_argument("-ct", "--cleartasks", help="Clear tasks", required=False)
    collect.set_defaults(func=collect_handler)

    plot = subparsers.add_parser("plot", help="Plot generator help")
    plot.add_argument("-df", "--datafilter", help="Data filter", required=True)
    plot.set_defaults(func=plot_handler)

    advice = subparsers.add_parser("advice", help="Advice generator help")
    advice.add_argument("-n", "--name", help="Deployment name", required=False)
    advice.add_argument("-df", "--datafilter", help="Data filter", required=False)
    advice.set_defaults(func=advice_handler)

    gui = subparsers.add_parser("gui", help="GUI mode help")
    gui.add_argument("-u", "--userinput", help="User input", required=False)
    gui.set_defaults(func=gui_handler)

    args = parser.parse_args()

    debug = args.debug
    if debug:
        logger.setup_debug_mode()

    args.func(args)


def main():
    _process_arguments()


if __name__ == "__main__":
    main()
