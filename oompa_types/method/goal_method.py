from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import NULL_CONDITION
from oompa_types.domain.arguments import HasArguments
from oompa_types.domain.domain import DOMAIN_BASE_T
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.goal import Goal
from oompa_types.objects.named import Named

if TYPE_CHECKING:
    from oompa_types.goal_network.goal_network import GoalNetwork


logger = LogManager.get_logger("oompa.method")

METHOD_TEMPLATE_T = TypeVar("TEMPLATE_T", bound="GoalMethod")

"""
    # The following is a handy snippet to insert a goal method that conforms to the style guide.
    # You can insert it and replace: TEMPLATE with the name, ARGS with the arguments, etc.
    # Alternatively, in VSCode, the snippet oompa_method is defined in oompa.code-snippets

    # =======================================
    # region Method TEMPLATE
    @OompaMethod
    def TEMPLATE(self, ARGS) -> GoalMethod:
        pass

    @TEMPLATE.goal
    def TEMPLATE(self, ARGS) -> Condition:
        goal = GOAL
        return goal

    @TEMPLATE.precondition
    def TEMPLATE(self, ARGS) -> Condition:
        return AndCondition(
            ...
        )

    @TEMPLATE.body
    def TEMPLATE(self, ARGS) -> TotalOrderGoalTaskNetwork:
        body = TotalOrderGoalTaskNetwork(
            ...
        )
        return body

    # endregion Method TEMPLATE
    # =======================================
"""


class GoalMethod[
    DOMAIN_T: DOMAIN_BASE_T,
    METHOD_TEMPLATE_T,
](
    Named,
    HasArguments,
    Protocol,
):
    """A base class for an ordered goal method, which is a tuple (name, goal, precondition, body)."""

    @property
    def template(self) -> METHOD_TEMPLATE_T: ...

    @property
    def is_template(self) -> bool:
        return self.template == self

    @property
    def is_instance(self) -> bool:
        return self.template != self

    @property
    def domain(self) -> DOMAIN_T: ...

    @property
    def goal(self) -> Condition:
        return NULL_CONDITION

    @property
    def precondition(self) -> Condition:
        return NULL_CONDITION

    @property
    def body(self) -> list[Goal | Condition | Action]: ...

    def is_applicable(self, stateful: Stateful): ...

    def apply(self, stateful: Stateful, result: ApplyResult): ...

    def decompose(
        self,
        root: GoalNetwork.Node,
        stateful: Stateful,
        result: ApplyResult,
        check_applicable: bool = True,
    ): ...
