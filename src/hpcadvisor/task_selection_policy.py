import random
from abc import ABC, abstractmethod
from hpcadvisor.utils import log
import sys


class TaskPolicy(ABC):
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @abstractmethod
    def get_tasks(self, tasks):
        pass

class SequentialPolicy(TaskPolicy):
    def __init__(self, config):
        super().__init__("sequential", config)

    def get_tasks(self, tasks):
        print("SequentialPolicy.get_tasks", tasks)
        num_tasks = self.config.get('num_tasks', 1)
        return tasks[:num_tasks]

class RandomPolicy(TaskPolicy):
    def __init__(self, config):
        super().__init__("random", config)

    def get_tasks(self, tasks):
        num_tasks = self.config.get('num_tasks', 1)
        return random.sample(tasks, num_tasks)

POLICY_MAP = {
    "sequential": SequentialPolicy,
    "random": RandomPolicy
}

def get_policy_class(policy_name, policy_config):
    policy_class = POLICY_MAP.get(policy_name.lower())

    if not policy_class:
        log.error(f"Unknown policy: {policy_name}")
        sys.exit(1)
    return policy_class(policy_config)
