from warnings import deprecated

from actorsim_core.base.domain.statement import NULL_STATEMENT


@deprecated
class GoalNodeForStatement[STORED_T]:
    """A GoalNode allows a StateVariable to be held inside a GoalNetwork.

    A GoalNode allows a StateVariable to be treated as a Goal
    within a GoalMemory for an agent and links a StateVariable to a goal network.
    For that reason, it provides a mechanism to track whether
    a goal is completed.

    This class is a lightweight version of java ActorSim::GoalNetworkNode,
    and it only tracks goal completion.
    """

    def __init__(self, statement: STORED_T):
        self._stored: STORED_T = statement
        self._is_completed: bool = False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        done_str = " [SEL]"
        if self.is_completed:
            done_str = " [FIN]"
        return self._stored.__str__() + done_str

    @property
    def stored(self) -> STORED_T:
        return self._stored

    @property
    def is_completed(self):
        return self._is_completed

    # TODO what exactly is this here for?
    @is_completed.setter
    def is_completed(self, value=True):
        self._is_completed = value

    def clear_completed(self):
        self.is_completed = False

    # TODO change to check_completed
    def check_complete(self, statement_set):
        if (not self.is_completed) and self._stored.is_entailed_by(statement_set):
            self.is_completed = True
        return self.is_completed


NULL_GOAL_NODE = GoalNodeForStatement(NULL_STATEMENT)


class GoalNetwork:
    root: GoalNodeForStatement = NULL_GOAL_NODE
