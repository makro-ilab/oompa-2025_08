from warnings import deprecated

from ..statement import NULL_STATEMENT, Statement


@deprecated
class GoalNetworkNodeForStatement:
    """A GoalNetworkNode allows a Statement to be treated as a Goal.

    A GoalNetworkNode allows a Statement to be treated as a Goal
    within a GoalMemory for an agent and links a Statement to a goal network.
    For that reason, it provides a mechanism to track whether
    a goal is completed.

    This class is a lightweight version of java ActorSim::GoalNetworkNode,
    and it only tracks goal completion.
    If more sophisticated goal tracking is desired,
    the full java ActorSim would be a better choice.
    ActorSim:GoalNetworkNode supports a SimpleGoalNetwork,
    which tracks goal completion and goal release.
    ActorSim::GoalLifecycleNode adds the ability to track goal mode
    and execute goal strategies.
    """

    def __init__(self, statement: Statement = NULL_STATEMENT):
        self._stored: Statement = statement
        self._is_completed: bool = False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        done_str = " [SEL]"
        if self.is_completed:
            done_str = " [FIN]"
        return self._stored.__str__() + done_str

    @property
    def stored(self) -> Statement:
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


NULL_GOAL_NETWORK_NODE = GoalNetworkNodeForStatement()
