# TODO add goal lifecycle from ActorSim
# TODO add temporal extent from ActorSim


from dataclasses import dataclass

from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import NULL_CONDITION
from oompa_types.domain.stateful import Stateful


@dataclass
class Goal:
    condition: Condition
    is_complete: bool = False

    def clear_completed(self):
        self.is_complete = False

    def check_complete(self, state: Stateful):
        return state.entails(self.condition)

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        return self.condition.str_dereferenced(state, indent, sep)


NULL_GOAL = Goal(NULL_CONDITION)
