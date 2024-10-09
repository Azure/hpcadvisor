import random
from abc import ABC, abstractmethod
from hpcadvisor.utils import log
import sys


class TaskPolicy(ABC):
    @abstractmethod
    def apply(self, tasks, num_tasks):
        pass

class SequentialPolicy(TaskPolicy):
    def apply(self, tasks, num_tasks):
        return tasks[:num_tasks]

class RandomPolicy(TaskPolicy):
    def apply(self, tasks, num_tasks):
        return random.sample(tasks, num_tasks)
    
# Dictionary to map policy names to classes
POLICY_MAP = {
    "sequential": SequentialPolicy,
    "random": RandomPolicy
}

def get_policy_class(policy_name: str):
    
    policy_class = POLICY_MAP.get(policy_name.lower())

    if not policy_class:
        log.error(f"Unknown policy: {policy_name}")
        sys.exit(1)
    return policy_class