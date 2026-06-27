from __future__ import annotations

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.action_bases import ActionTemplate
from oompa_types.action.action_descriptor import ActionDescriptor, OompaAction
from oompa_types.action.actions import HasOompaActions, collect_action_descriptors
from oompa_types.domain.domain import Domain
from oompa_types.domain.problem_bases import AbstractProblem
from oompa_types.domain.state import AutoState, StaticState
from oompa_types.method.goal_method import GoalMethod
from oompa_types.method.goal_method_bases import GoalMethodTemplate
from oompa_types.method.goal_method_descriptor import MethodDescriptor
from oompa_types.method.methods import HasOompaMethods, collect_method_descriptors

logger = LogManager.get_logger("oompa.domain")


class AbstractDomain(Domain):
    def __init__(self, name: str) -> None:
        self._name = name
        self.types: list[type] = []
        self._action_templates: dict[str, Action] = dict()
        self._functional_action_templates: dict[str, ActionTemplate] = dict()
        self._goal_method_templates: dict[str, GoalMethod] = dict()
        self._functional_goal_method_templates: dict[str, GoalMethodTemplate] = dict()

    @property
    def name(self) -> str:
        return self._name

    def declare_type(
        self,
        type: type,
        auto_discover_vars=True,
        auto_discover_actions=True,
        auto_discover_methods=True,
        exclude_vars=["name"],
    ):
        self.types.append(type)
        if auto_discover_actions and issubclass(type, HasOompaActions):
            action_descriptors: list[OompaAction] = []
            collect_action_descriptors(type, action_descriptors)
            for action_descriptor in action_descriptors:
                if action_descriptor.name not in exclude_vars:
                    self.declare_functional_action(action_descriptor)

        if auto_discover_methods and issubclass(type, HasOompaMethods):
            method_descriptors: list[OompaAction] = []
            collect_method_descriptors(type, method_descriptors)
            for method_descriptor in method_descriptors:
                if method_descriptor.name not in exclude_vars:
                    self.declare_functional_goal_method(method_descriptor)

    def get_type(self, type_name: str, error_if_missing=True) -> type | None:
        for type in self.types:
            if type.__name__ == type_name:
                return type

        if error_if_missing is True:
            msg = f"Could not find type {type_name} in domain {self}"
            logger.error(msg)
            raise TypeError(msg)
        return None

    def has_type(self, type: type):
        if type in self.types:
            return True
        return False

    def validate_parameters(self):
        """Validate that the parameters of StateProperties, Actions, and Methods are valid types."""
        pass

    def declare_functional_action(self, context: ActionTemplate | ActionDescriptor):
        template_to_add = context
        if isinstance(context, ActionDescriptor):
            template_to_add = context.get_action_template()

        template_to_add.domain = self
        self._functional_action_templates[template_to_add.name] = template_to_add

    def declare_action(self, action_class: type[Action]):
        action_template = action_class()
        action_template.set_as_template(self)
        self._action_templates[action_class] = action_template

    @property
    def action_templates(self) -> list[Action]:
        return self._action_templates.values()

    @property
    def functional_action_templates(self) -> list[ActionTemplate]:
        return self._functional_action_templates.values()

    def action(self, action_class: type[Action]):
        action_template = self._action_templates[action_class]
        return action_template

    def functional_action(self, context: ActionTemplate | ActionDescriptor) -> ActionTemplate:
        action_template = self._functional_action_templates[context.name]
        return action_template

    def declare_goal_method(self, goal_method_class: type[GoalMethod]):
        method_template = goal_method_class()
        method_template.set_as_template(self)
        self._goal_method_templates[goal_method_class] = method_template

    def declare_functional_goal_method(self, context: GoalMethodTemplate | MethodDescriptor):
        template_to_add = context
        if isinstance(context, MethodDescriptor):
            template_to_add = context.get_method_template()
        template_to_add.domain = self
        self._functional_goal_method_templates[template_to_add.name] = template_to_add

    @property
    def method_templates(self) -> list[GoalMethod]:
        return self._functional_goal_method_templates.values()

    def method(self, goal_method_class: type[GoalMethod]):
        method_template = self._goal_method_templates[goal_method_class]
        return method_template

    # ====================================
    # region problem
    def instantiate_problem(self):
        domain_type = type(self)
        problem_config = AbstractProblem.Config(self, AutoState, StaticState)
        return AbstractProblem[domain_type, AutoState](problem_config)

    # endregion problem
    # ====================================
