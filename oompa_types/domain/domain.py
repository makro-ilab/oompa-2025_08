from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from makro_utils.log_manager import LogManager
from oompa_types.objects.named import Named

if TYPE_CHECKING:
    from oompa_types.action.action import Action
    from oompa_types.action.action_bases import ActionTemplate
    from oompa_types.method.goal_method import GoalMethod


logger = LogManager.get_logger("oompa.domain")


class Domain(Named, Protocol):
    def declare_type(self, type: type, auto_discover_vars=True, exclude_vars=["name"]): ...

    def get_type(self, type_name: str, error_if_missing=True) -> type | None:
        """Returns the type of the type_name; raises error or returns None if type is not found."""
        ...

    def has_type(self, type: type): ...

    def validate_parameters(self): ...

    def declare_action(self, action_class: type[Action]): ...

    @property
    def action_templates(self) -> list[Action]: ...

    @property
    def functional_action_templates(self) -> list[ActionTemplate]: ...

    def action(self, action_class: type[Action]): ...

    def declare_goal_method(self, action_class: type[GoalMethod]): ...

    @property
    def method_templates(self) -> list[GoalMethod]: ...

    def method(self, goal_method_class: type[GoalMethod]): ...


DOMAIN_BASE_T = TypeVar("DOMAIN_BASE_T", bound=Domain)
