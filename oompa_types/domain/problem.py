from typing import Protocol

from oompa_types.action.action import Action
from oompa_types.domain.domain import Domain
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method import GoalMethod
from oompa_types.objects.named import Named
from oompa_types.state_property.state_property import StateProperty


class Problem[DOMAIN_T: Domain, STATE_T](Stateful[STATE_T], Protocol):
    @property
    def state_members(self) -> list[StateProperty]: ...

    @property
    def declared_state_members(self) -> list[StateProperty]:
        """Allows subclasses to specify the list of StateProperties for the state."""
        return None

    def current_state(self) -> STATE_T: ...

    def update_state_using_members(self, state: STATE_T): ...

    def update_state_for_object(self, state: STATE_T, obj: Named): ...

    def add_objects(self, *objs: Named, update_svs=True, setattr=True): ...

    def get_applicable_actions(self, state: Stateful) -> list[Action]: ...

    def get_applicable_goal_methods(self, state: Stateful) -> list[GoalMethod]: ...

    def get_relevant_and_applicable_goal_methods(
        self, gtn: TotalOrderGoalTaskNetwork, state: Stateful = None
    ): ...

    def get_relevant_goal_methods(self, gtn: TotalOrderGoalTaskNetwork): ...
