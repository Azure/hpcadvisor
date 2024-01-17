import logging
import sys

loggername = "hpcadvisor"
loggerfilename = "hpcadvisor.log"


def _init_logger():
    logging.basicConfig(
        level=logging.WARNING,
        filename=loggerfilename,
        format="%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)s >>> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(loggername)
    logger.setLevel(logging.INFO)

    handler_stdout = logging.StreamHandler(sys.stdout)

    logger.addHandler(handler_stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)s >>> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler_file = logging.FileHandler(loggerfilename)
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_file)


_init_logger()

logger = logging.getLogger(loggername)


def setup_debug_mode():
    for handler in logging.getLogger(loggername).handlers:
        handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")
