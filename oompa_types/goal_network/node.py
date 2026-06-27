from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from warnings import deprecated

import aenum
from makro_utils.log_manager import LogManager

from oompa_types.action.action import Action
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition import Condition
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.goal import NULL_GOAL, Goal
from oompa_types.method.goal_method import GoalMethod

logger = LogManager.get_logger("oompa.goalnetwork")


class OrderType(aenum.IntEnum):
    TOTAL_ORDER = ()
    PARTIAL_ORDER = ()


class Result(aenum.AutoNumberEnum):
    NO_OP = ()
    ALL_ACTIONS_APPLIED = ()
    NOT_APPLICABLE = ()
    NETWORK_HAS_UNDECOMPOSED_NODES = ()


@deprecated
@dataclass
class Node[T]:
    content: T
    parent: Node = None
    children: list[Node] = field(default_factory=list)
    order_type: OrderType = OrderType.TOTAL_ORDER
    order: None | list[tuple[Node, Node]] = None
    method: None | GoalMethod = None

    def __str__(self):
        return self._str_impl()

    def __repr__(self):
        return self.__str__()

    def _str_impl(self, indent=""):
        method_str = str(self.method)
        return_str = f"  goal:{str(self.content)}\n  method:{method_str}\n"
        for child in self.children:
            return_str += child._str_impl(indent + "    ")
        return return_str

    def add(self, new_child: Goal | Action):
        if isinstance(new_child, Action):
            self.add_action(new_child)
        elif isinstance(new_child, Goal):
            self.add_subgoal(new_child)
        elif isinstance(new_child, Condition):
            new_subgoal = Goal(new_child)
            self.add_subgoal(new_subgoal)
        else:
            msg = f"Unrecognized node type; cannot add new child {new_child}"
            logger.error(msg)
            raise TypeError(msg)

    def add_subgoal(self, subgoal: Goal):
        """Appends subgoal to the end of the body."""
        self.children.append(Complex(subgoal))

    def add_action(self, action: Action):
        """Appends action to the end of body."""
        self.children.append(Primitive(action))

    @property
    def is_fully_decomposed(self) -> bool:
        """Returns whether this node is fully decomposed."""
        ...

    def apply(self, state: Stateful, result: ApplyResult): ...

    @property
    def has_children(self) -> bool:
        return len(self.children) > 0


@deprecated
@dataclass
class Complex(Node[Goal]):
    @override
    @property
    def is_fully_decomposed(self) -> bool:
        """Returns whether this node is fully decomposed.

        A complex node is fully decomposed if all its leaves are Primitive.
        """
        is_decomposed = False
        for child in self.children:
            if child.is_fully_decomposed:
                is_decomposed = True
            else:
                is_decomposed = False
                break
        return is_decomposed

    @override
    def apply(self, state: Stateful, result: ApplyResult):
        for child in self.children:
            child.apply(state, result)
            if result != ApplyResult.Status.SUCCESS:
                break


@deprecated
@dataclass
class Primitive(Node[Action]):
    def _str_impl(self, indent=""):
        return f"{indent}action:{str(self.content)}\n"

    @override
    @property
    def is_fully_decomposed(self) -> bool:
        return True

    @override
    def apply(self, state: Stateful, result: ApplyResult) -> Result:
        action = self.content
        action.apply(state, result)


NULL_NODE = Node(NULL_GOAL)
