from __future__ import annotations

import networkx as nx

from oompa_types.action.action import Action
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.domain.state import Stateful
from oompa_types.goal_network.goal import Goal
from oompa_types.goal_network.gtn import GoalTaskNetwork
from oompa_types.goal_network.gtn_node_bases import ActionNode, GoalNode, GTNNode


class PartialOrderGoalTaskNetwork(GoalTaskNetwork):
    def __init__(self):
        """Create an empty partially ordered goal-task network."""
        self.network = nx.DiGraph()

    def __eq__(self, other):
        return isinstance(other, PartialOrderGoalTaskNetwork) and self.network == other.network

    def add(self, goal_or_task: Goal | Condition | Action) -> GTNNode:
        """Add goal_or_task to this goal-task network with no ordering constraints.

        :param goal_or_task: the goal or task to be added to this goal-task network.
        :returns: the added GTNNode
        """
        if isinstance(goal_or_task, Goal):
            node = GoalNode(goal_or_task)
        elif isinstance(goal_or_task, Condition):
            node = GoalNode(Goal(goal_or_task))
        elif isinstance(goal_or_task, Action):
            node = ActionNode(goal_or_task)
        else:
            raise NotImplementedError()
        self.network.add(node)
        return node

    def add_ordering(self, n1: GTNNode, n2: GTNNode) -> None:
        """Adds an ordering constraint from node n1 to node n2."""
        if not isinstance(n1, GTNNode):
            raise TypeError("n1 must be a GTNNode.")
        if not isinstance(n2, GTNNode):
            raise TypeError("n2 must be a GTNNode.")
        self.network.add_edge(n1, n2)

    def release(self, node: GTNNode) -> None:
        """Remove a node from the goal-task network."""
        self.network.remove_node(node)

    def get_unconstrained(self) -> set[Action | Goal]:
        """Returns a collection of unconstrained nodes in this goal-task network."""
        unconstrained = set(
            node.get_content()
            for node in self.network.nodes
            if isinstance(node, GoalNode) and self.network.out_degree(node) == 0
        )
        return unconstrained

    def decompose(self, n: GTNNode, gtn: GoalTaskNetwork) -> None:
        """Adds the goal-task network gtn to this goal-task network as a descendant of node n."""
        for node in gtn.network.nodes:
            self.add(node)
        for u, v in gtn.network.edges:
            self.add_ordering(u, v)

        for node in gtn.network.nodes:
            if gtn.network.in_degree(node) == 0:
                self.add_ordering(n, node)

    def copy(self) -> GoalTaskNetwork:
        """Create and return a copy of this GoalTaskNetwork.

        :returns: a copy of this goal-task network.
        """
        new_gtn = PartialOrderGoalTaskNetwork()
        new_gtn.network = self.network.copy()
        return new_gtn


class TotalOrderGoalTaskNetwork(GoalTaskNetwork):
    def __init__(self, *initial_network):
        """Create a totally ordered goal-task network.

        :param *initial_network: a sequence of goals and tasks
        """
        self.network: list[GTNNode] = []
        for goal_or_task in reversed(initial_network):
            self.add(goal_or_task)

    def __str__(self):
        s = ", ".join([str(node.get_content()) for node in reversed(self.network)])
        return "[" + s + "]"

    def __repr__(self):
        return self.__str__()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        result_str = ""
        for node in reversed(self.network):
            content = node.get_content()
            if isinstance(content, Goal):
                result_str += content.str_dereferenced(state, indent, sep)
            elif isinstance(content, Action):
                result_str += f"{indent}{content.str_dereferenced(state, indent, sep)}{sep}"
            elif hasattr(content, "str_dereferenced"):
                result_str += f"{indent}{content.str_dereferenced(state, indent, sep)}{sep}"
            else:
                result_str += f"{indent}{str(content)}{sep}"
        return result_str

    def __eq__(self, other):
        return isinstance(other, TotalOrderGoalTaskNetwork) and self.network == other.network

    def add(self, goal_or_task: Goal | Action) -> GTNNode:
        """Add goal_or_task to this goal-task network as an unconstrained node.

        The goal or task will be added as a predecessor of the only unconstrained node in this
        goal-task network.

        :param goal_or_task: the goal or task to be added to this goal-task network.
        :returns: the added GTNNode
        """
        if isinstance(goal_or_task, Goal):
            node = GoalNode(goal_or_task)
        elif isinstance(goal_or_task, Condition):
            node = GoalNode(Goal(goal_or_task))
        elif isinstance(goal_or_task, Action):
            node = ActionNode(goal_or_task)
        else:
            # goal_or_task is a compound task
            raise NotImplementedError()
        self.network.append(node)
        return node

    def release(self):
        """Remove the only unconstrained node from the goal-task network.

        Note that a totally-ordered goal-task network only has one unconstrained node.
        """
        self.network.pop()

    def get_unconstrained(self) -> Action | Goal:
        """Return the unconstrained node of this goal task network or None if there is not one.

        Note that a totally-ordered goal-task network only has one unconstrained node.
        """
        if len(self.network) > 0:
            node: GTNNode = self.network[-1]
            return node.get_content()

        return None

    def decompose(self, gtn: TotalOrderGoalTaskNetwork, result: ApplyResult) -> None:
        """Decomposes the only unconstrained node of this goal-task network using gtn.

        :param gtn: the goal-task network to decompose the unconstrained node with.
        """
        self.network += gtn.network

    def copy(self) -> TotalOrderGoalTaskNetwork:
        """Create and return a copy of this GoalTaskNetwork.

        :returns: a copy of this goal-task network.
        """
        new_gtn = TotalOrderGoalTaskNetwork()
        new_gtn.network = self.network.copy()
        return new_gtn

    def apply(self, state: Stateful, result: ApplyResult):
        """Apply and release all unconstrained primitive actions in GTN; directly modifies state."""
        unconstrained = self.get_unconstrained()
        while isinstance(unconstrained, Action):
            action: Action = unconstrained
            action.apply(state, result)
            if result.status == ApplyResult.Status.NOT_APPLICABLE:
                return
            self.release()
            unconstrained = self.get_unconstrained()
        result.status = ApplyResult.Status.SUCCESS
