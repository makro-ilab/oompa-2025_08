import itertools
from dataclasses import dataclass
from inspect import isclass
from typing import TYPE_CHECKING

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import QuantifiedCondition
from oompa_types.domain.domain import Domain
from oompa_types.domain.problem import Problem
from oompa_types.domain.problem_helpers import CreatesNewObjects
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.goal import Goal
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method import GoalMethod
from oompa_types.objects.named import Named
from oompa_types.state_property.state_properties import (
    HasStateProperties,
    collect_state_property_descriptors,
)
from oompa_types.state_property.state_property import StateProperty
from oompa_types.state_property.state_property_bases import (
    StatePropertyOfAttribute,
    StatePropertyOfRelation,
)
from oompa_types.state_property.state_property_descriptor import StatePropertyDescriptor

if TYPE_CHECKING:
    from oompa_types.domain.state import AbstractState


logger = LogManager.get_logger("oompa.test.travel")


class AbstractProblem[
    DOMAIN_T: Domain,
    STATE_T: AbstractState,
](
    Problem[DOMAIN_T, STATE_T],
):
    @dataclass
    class Config[DOMAIN_T, STATE_T: AbstractState]:
        domain: DOMAIN_T
        state_class: STATE_T
        static_state_class: STATE_T = None

    def __init__(
        self,
        config: Config,
    ) -> None:
        self.config: AbstractProblem.Config = config
        self.domain: DOMAIN_T = config.domain
        self._objects: dict[str, Named] = dict()
        self.goal: Condition = None
        self._calculated_members: set[StatePropertyDescriptor] = None
        self._calculated_members_static: set[StatePropertyDescriptor] = None
        self.static_state: STATE_T = None

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        value_t = type(value)
        if isclass(value_t) and self.config.domain.has_type(value_t):
            self.add_objects(value, call_setattr=False)
            if issubclass(value_t, CreatesNewObjects):
                value.problem = self
        return value

    # ====================================
    # region State

    @property
    def state_members(self) -> list[StatePropertyDescriptor]:
        if self._calculated_members is None:
            new_members = self.declared_state_members
            if new_members is None:
                new_members = set()
                logger.debug("Calculating state members")
                for obj in self._objects.values():
                    if issubclass(type(obj), HasStateProperties):
                        collect_state_property_descriptors(obj, new_members)
            self._calculated_members = sorted(new_members)
        return self._calculated_members

    @property
    def state_members_static(self) -> list[StatePropertyDescriptor]:
        if self._calculated_members_static is None:
            new_static_members = self.declared_state_members_static
            if new_static_members is None:
                logger.debug("Calculating static state members")
                new_static_members = set([x for x in self.state_members if x.is_read_only])
            self._calculated_members_static = sorted(new_static_members)
        return self._calculated_members_static

    @property
    def declared_state_members(self) -> list[StateProperty]:
        """Allows subclasses to specify the list of StateProperties for the state."""
        return None

    @property
    def declared_state_members_static(self) -> list[StateProperty]:
        """Allows subclasses to specify the list of static StateProperties for the state."""
        return None

    def current_state(self) -> STATE_T:
        if self.config.static_state_class and self.static_state is None:
            self.static_state = self.config.static_state_class(self)
            self.update_static_state_using_members()

        state: STATE_T = self.config.state_class(self, self.static_state)
        self.update_state_using_members(state, skip_static=True)
        return state

    def update_static_state_using_members(self):
        for member in self.state_members_static:
            self.update_state_for_member(self.static_state, member)

    def update_state_using_members(self, state: STATE_T, skip_static=True):
        for member in self.state_members:
            if skip_static and member.is_read_only:
                continue
            self.update_state_for_member(state, member)

    def update_state_for_member(self, state: STATE_T, member_spd: StatePropertyDescriptor):
        name = member_spd.name
        objs = self.objects(member_spd.owning_class)
        if not hasattr(state, name):
            setattr(state, name, dict())
        state_var_dict = getattr(state, name)

        for obj in objs:
            sp = getattr(obj, name)
            if isinstance(sp, StatePropertyOfAttribute):
                sp_value = sp.value
                state_var_dict[obj.name] = sp_value
            elif isinstance(sp, StatePropertyOfRelation):
                args_types = sp.args_types
                args_product = self._create_object_product(args_types)
                for args in args_product:
                    sp_instance = sp.template.get_instance(args)
                    sp_value = sp_instance.value
                    args_str = str(args).strip("()[]")
                    state_var_dict[args_str] = sp_value

    def update_state_for_object(self, state: STATE_T, obj: Named):
        for member in self.state_members:
            name = member.name
            if not hasattr(state, name):
                setattr(state, name, dict())
            if hasattr(obj, name):
                state_var_dict = getattr(state, name)
                sp_value = getattr(obj, name).value
                state_var_dict[obj.name] = sp_value

    # endregion State
    # ====================================

    # ====================================
    # region objects

    def add_objects(self, *objs: Named, update_svs=True, call_setattr=True):
        for obj in objs:
            self._objects[obj.name] = obj
            if call_setattr:
                setattr(self, obj.name, obj)

    def objects(self, type_filter: type | None = None):
        """Returns a iterator over the objects, using type_filter if provided."""
        if type_filter is not None:
            return filter(lambda x: isinstance(x, type_filter), self._objects.values())
        return iter(self._objects)

    # endregion objects
    # ====================================

    # ====================================
    # region actions and methods

    def get_applicable_actions(self, state: Stateful) -> list[Action]:
        applicable: list[Action] = []
        for action_template in self.domain.action_templates:
            logger.debug(f"checking action template {action_template}")
            args_type = action_template.args_types
            args_product = self._create_object_product(args_type)

            for args in args_product:
                action: Action = action_template(*args)
                logger.trace(f"  checking action {action}")
                if action.precondition.is_entailed_by(state):
                    logger.debug(f"  applicable action {action}")
                    applicable.append(action)

        for action_template in self.domain.functional_action_templates:
            logger.debug(f"checking functional action template {action_template}")
            args_type = action_template.args_types
            args_product = self._create_object_product(args_type)
            for args in args_product:
                action: Action = action_template(*args)
                logger.trace(f"  checking action {action}")
                if action.precondition.is_entailed_by(state):
                    logger.debug(f"  applicable action {action}")
                    applicable.append(action)

        return applicable

    def get_applicable_goal_methods(self, state: Stateful) -> list[GoalMethod]:
        applicable: list[GoalMethod] = []
        for method_template in self.domain.method_templates:
            logger.debug(f"checking method template {method_template}")
            args_type = method_template.args_types
            args_product = self._create_object_product(args_type)

            for args in args_product:
                method: GoalMethod = method_template(*args)
                logger.trace(f"  checking method {method}")
                if method.precondition.is_entailed_by(state):
                    logger.debug(f"  applicable method {method}")
                    applicable.append(method)

        return applicable

    def get_relevant_and_applicable_goal_methods(
        self, gtn: TotalOrderGoalTaskNetwork, state: Stateful
    ):
        result: list[GoalMethod] = []
        unconstrained: Action | Goal = gtn.get_unconstrained()
        if isinstance(unconstrained, Action):
            return result

        if isinstance(unconstrained.condition, QuantifiedCondition):
            for condition in unconstrained.condition.children:
                self.get_relevant_and_applicable_goal_methods_by_condition(condition, state, result)
        else:
            condition = unconstrained.condition
            self.get_relevant_and_applicable_goal_methods_by_condition(condition, state, result)
        return result

    def get_relevant_and_applicable_goal_methods_by_condition(
        self,
        condition: Condition,
        state: Stateful,
        result: list[GoalMethod] = [],
    ):
        for method_template in self.domain.method_templates:
            logger.debug(f"checking method template {method_template}")
            args_type = method_template.args_types
            args_product = self._create_object_product(args_type)

            for args in args_product:
                method: GoalMethod = method_template(*args)
                logger.trace(f"  checking method {method}")
                if method.is_relevant(condition):
                    logger.debug(f"  relevant method {method}")
                    if method.is_applicable(state):
                        result.append(method)

    def _create_object_product(self, type_list: list[type]):
        problem_objects = list[list[Named]]()
        for arg_type in type_list:
            arg_type_objects = self.objects(type_filter=arg_type)
            problem_objects.append(arg_type_objects)
        args_product = itertools.product(*problem_objects)
        return args_product

    # endregion actions and methods
    # ====================================
