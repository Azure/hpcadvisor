import random
import sys
from abc import ABC, abstractmethod

from hpcadvisor import logger, taskset_handler

log = logger.logger


class TaskPolicy(ABC):
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @abstractmethod
    def get_tasks(self, tasks, num_tasks):
        pass


class SequentialPolicy(TaskPolicy):
    def __init__(self, config):
        super().__init__("sequential", config)

    def get_tasks(self, tasks, num_tasks=None):
        paralleltasks = self.config.get("paralleltasks", 1)

        pending_tasks = taskset_handler.get_pending_tasks(tasks)

        if num_tasks is None:
            num_tasks = paralleltasks

        return pending_tasks[:num_tasks]


class RandomPolicy(TaskPolicy):
    def __init__(self, config):
        super().__init__("random", config)

    def get_tasks(self, tasks, num_tasks=None):
        paralleltasks = self.config.get("paralleltasks", 1)

        pending_tasks = taskset_handler.get_pending_tasks(tasks)

        if num_tasks is None:
            num_tasks = paralleltasks

        return random.sample(pending_tasks, num_tasks)


POLICY_MAP = {"sequential": SequentialPolicy, "random": RandomPolicy}


def get_policy_class(policy_name, policy_config):
    policy_class = POLICY_MAP.get(policy_name.lower())

    if not policy_class:
        log.error(f"Unknown policy: {policy_name}")
        sys.exit(1)
    return policy_class(policy_config)
