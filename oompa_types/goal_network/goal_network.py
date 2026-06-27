from __future__ import annotations

from warnings import deprecated

from makro_utils.log_manager import LogManager

from oompa_types.action.apply_result import ApplyResult
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.goal import NULL_GOAL, Goal
from oompa_types.goal_network.node import Complex, Result

logger = LogManager.get_logger("oompa.goalnetwork")


@deprecated
class GoalNetwork:
    def __init__(self, root_goal: Goal = NULL_GOAL):
        self.root = Complex(root_goal)

    def __str__(self):
        return str(self.root)

    def __repr__(self):
        self.__str__()

    def apply(self, state: Stateful, result: ApplyResult):
        """Apply the actions of completely decomposed goal network."""
        result.status = Result.NO_OP
        if not self.root.is_fully_decomposed:
            logger.error("Cannot apply goal network to state because it is not fully decomposed")
            result.msg = str(Result.NETWORK_HAS_UNDECOMPOSED_NODES)
        else:
            self.root.apply(state, result)
