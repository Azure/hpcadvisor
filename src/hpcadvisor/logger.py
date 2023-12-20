import logging
import sys

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.WARNING,
    filename="hpcadvisor.log",
    format="%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)s >>> %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(message)s")
stdout_handler.setFormatter(formatter)

logging.getLogger().addHandler(stdout_handler)


def setup_debug_mode():
    external_logger = logging.getLogger(__name__)
    external_logger.setLevel(logging.DEBUG)
    logger.info("Debug mode enabled")
