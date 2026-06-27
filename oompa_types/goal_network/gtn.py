from __future__ import annotations

from typing import Protocol

from oompa_types.action.action import Action
from oompa_types.condition.condition import Condition
from oompa_types.goal_network.goal import Goal
from oompa_types.goal_network.gtn_node import GTNNode


class GoalTaskNetwork(Protocol):
    def add(self, goal_or_task: Goal | Action | Condition): ...

    def get_unconstrained(self) -> set[GTNNode] | GTNNode: ...

    def release(self) -> None: ...

    def copy(self) -> GoalTaskNetwork: ...
