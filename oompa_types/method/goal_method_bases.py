from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, override

from makro_utils import class_utils
from makro_utils.class_utils import convert_to_snake_regex
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import QuantifiedCondition
from oompa_types.domain.arguments import AbstractArguments
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.goal import Goal
from oompa_types.goal_network.gtn import GoalTaskNetwork
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.goal_network.gtn_node_bases import GoalNode
from oompa_types.method.goal_method import GoalMethod, logger
from oompa_types.objects.named import AbstractNamed, Named

if TYPE_CHECKING:
    from oompa_types.method.goal_method_descriptor import MethodDescriptor


class AbstractGoalMethod[DOMAIN_T, TEMPLATE_T](
    GoalMethod[DOMAIN_T, TEMPLATE_T],
    AbstractNamed,
    AbstractArguments,
):
    """Provides an abstract base class to implement the Method Protocol."""

    def __init__(
        self,
        name: str = None,
    ) -> None:
        AbstractArguments.__init__(self)

        new_name = name
        if new_name is None:
            class_name = self.__class__.__name__
            new_name = convert_to_snake_regex.sub(r"_\1", class_name)
        AbstractNamed.__init__(self, new_name)
        self._domain: DOMAIN_T | None = None
        self._template: TEMPLATE_T | None = None

    def __repr__(self):
        return self.__str__()

    def __str__(self) -> str:
        args = self.args
        args_str = ", ".join([str(x) for x in args])
        return f"{self.name}({args_str})"

    @property
    def domain(self) -> DOMAIN_T:
        return self._domain

    @domain.setter
    def domain(self, domain: DOMAIN_T):
        self._domain = domain

    @property
    def template(self) -> TEMPLATE_T:
        return self._template

    def instance(self) -> TEMPLATE_T:
        cls = type(self)
        instance = cls()
        instance._domain = self.domain
        instance._template = self.template
        return instance

    def set_as_template(self, domain: DOMAIN_T | None = None):
        self._domain = domain
        self._template = self

    def subgoals_not_entailed(self, stateful: Stateful):
        logger.debug(f"Collecting not entailed subgoals of {self}")
        return self.subgoals_matching(lambda x: x.not_entailed_by(stateful))

    def subgoals_matching(self, predicate: Callable[[Condition], bool]) -> Iterator[Condition]:
        return filter(predicate, self.subgoals)

    def is_applicable(self, stateful: Stateful):
        logger.debug(f"checking precondition for {self}")
        precondition = self.precondition
        return precondition.is_entailed_by(stateful)

    def is_relevant(self, goal: Goal | Condition) -> bool:
        logger.debug(f"checking relevance for {self}")
        if isinstance(goal, Condition):
            condition = goal
        elif isinstance(goal, Goal):
            condition = goal.condition
        else:
            raise TypeError("method relevance must be with respect to a Goal or Condition")
        if isinstance(condition, QuantifiedCondition):
            return any(self.is_relevant(subcondition) for subcondition in condition.conditions)
        elif isinstance(self.goal, QuantifiedCondition):
            return any(subcondition == condition for subcondition in self.goal.conditions)
        else:
            method_goal_condition = self.goal
            return method_goal_condition == condition

    def effect_entailed(self, stateful: Stateful):
        logger.debug(f"checking effect is entailed for for {self}")
        return self.goal.is_entailed_by(stateful)

    @classmethod
    def method_name_from_class(cls):
        name = cls.__name__
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        name.replace("method", "m")
        return name

    def decompose(
        self,
        gtn: GoalTaskNetwork,
        stateful: Stateful,
        result: ApplyResult,
        unconstrained_goal: GoalNode = None,
        check_applicable: bool = True,
        check_relevant: bool = True,
    ):
        if unconstrained_goal is None:
            assert isinstance(gtn, TotalOrderGoalTaskNetwork)
            unconstrained_goal = gtn.get_unconstrained()
        if not check_applicable or self.is_applicable(stateful):
            if not check_relevant or self.is_relevant(unconstrained_goal):
                gtn.decompose(self.body, result)
                result.status = ApplyResult.Status.SUCCESS
            else:
                result.status = ApplyResult.Status.NOT_RELEVANT
        else:
            result.status = ApplyResult.Status.NOT_APPLICABLE


class AgentMethod[AGENT_T](AbstractGoalMethod):
    agent: AGENT_T

    def __init__(self, name: str, agent: AGENT_T) -> None:
        super().__init__(name)
        self.instantiate_parameters()

        self.agent = agent


class GoalMethodTemplate(AbstractGoalMethod):
    def __init__(
        self,
        descriptor: MethodDescriptor,
    ):
        AbstractGoalMethod.__init__(self, descriptor.name)
        self._descriptor: MethodDescriptor = descriptor
        self._instances: dict[tuple[Named], GoalMethodTemplate.Instance] = dict()

    @override
    @property
    def args_types(self) -> list[Named]:
        instantiation_func = self._descriptor._instantiate_func
        spec = inspect.getfullargspec(instantiation_func)
        annotations = spec.annotations
        arg_types = []

        for arg in spec.args:
            if arg == "self":
                cls = class_utils.get_class_that_defined_method(instantiation_func)
                arg_types.append(cls)
            else:
                annotation = annotations[arg]
                annotation_type = self.domain.get_type(annotation)
                arg_types.append(annotation_type)

        return arg_types

    def partially_bound_instance(self, owner: METHOD_OWNER_T):
        args_tuple = (owner,)
        if args_tuple not in self._instances:
            instance = GoalMethodTemplate.Instance(self, args_tuple)
            self._instances[args_tuple] = instance
        return self._instances[args_tuple]

    def fully_ground_instance(self, args_tuple):
        instance = None
        if args_tuple in self._instances:
            instance = self._instances[args_tuple]
        else:
            instance = GoalMethodTemplate.Instance(self, args_tuple)
            self._instances[args_tuple] = instance
        return instance

    def __call__(self, *args: list[Named], **kwds):
        args_tuple = tuple(args)
        return self.fully_ground_instance(args_tuple)

    class Instance(AbstractGoalMethod):
        def __init__(
            self,
            template: GoalMethodTemplate,
            args: list[Named] = None,
        ):
            AbstractGoalMethod.__init__(self, template._descriptor.name)
            self._template = template
            self._args: list[Named] = args if args is not None else []

        @property
        def args(self) -> list[Named]:
            return self._args

        @args.setter
        def args(self, value):
            self._args = value

        @property
        def num_args(self):
            return len(self._args)

        @property
        def precondition(self) -> Condition:
            precondition_func = self._template._descriptor.precondition_func
            arg_subset = self.get_arg_subset(precondition_func)
            precondition = precondition_func(*arg_subset)
            return precondition

        @precondition.setter
        def precondition(self, condition: Condition):
            self._precondition = condition

        @property
        def goal(self) -> Condition:
            goal_func = self._template._descriptor.goal_func
            arg_subset = self.get_arg_subset(goal_func)
            goal_condition = goal_func(*arg_subset)
            return goal_condition

        @property
        def body(self) -> Condition:
            body_func = self._template._descriptor.body_func
            arg_subset = self.get_arg_subset(body_func)
            gtn = body_func(*arg_subset)
            return gtn

        def get_arg_subset(self, func):
            # TODO review the arguments of the function and pull them out of self.args in order.
            return self.args

        def __call__(self, *args: list[Named], **kwds):
            full_args = self.args + args
            args_tuple = tuple(full_args)
            return self._template.fully_ground_instance(args_tuple)
