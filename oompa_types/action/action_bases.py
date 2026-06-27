from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, override

from makro_utils import class_utils
from makro_utils.class_utils import convert_to_snake_regex
from oompa_types.action.action import TEMPLATE_T, Action
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import AndCondition
from oompa_types.domain.domain import DOMAIN_BASE_T
from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.stateful import Stateful
from oompa_types.effect.effect import Effect
from oompa_types.objects.named import AbstractNamed, Named

if TYPE_CHECKING:
    from oompa_types.action.action_descriptor import ActionDescriptor


class ActionBase[DOMAIN_T: DOMAIN_BASE_T, TEMPLATE_T](
    Action[DOMAIN_T, TEMPLATE_T],
    AbstractNamed,
):
    def __init__(
        self,
        name: str = None,
        template: TEMPLATE_T | None = None,
    ) -> None:
        self._domain: DOMAIN_T | None = None
        self._template: TEMPLATE_T = template

        new_name = name
        if new_name is None:
            class_name = self.__class__.__name__
            new_name = convert_to_snake_regex.sub(r"_\1", class_name)
        AbstractNamed.__init__(self, new_name)

    def __repr__(self):
        return self.__str__()

    def __str__(self) -> str:
        args = self.args
        args_str = ", ".join([f"{str(x)}" for x in args])
        return f"{self.name}({args_str})"

    def str_dereferenced(self, state: Stateful, indent="", sep=""):
        args_deref = []
        for arg in self.args:
            if isinstance(arg, Placeholder):
                args_deref.append(arg.dereference(state))
            else:
                args_deref.append(arg)
        return f"{self.name}{tuple(args_deref)}"

    def set_as_template(self, domain: DOMAIN_T | None = None):
        self._domain = domain
        self._template = self

    @property
    def domain(self) -> DOMAIN_T:
        return self._domain

    @domain.setter
    def domain(self, value) -> DOMAIN_T:
        self._domain = value

    @property
    def template(self) -> TEMPLATE_T:
        return self._template

    @property
    def args(self) -> list[Any]:
        return []

    def apply(self, state: Stateful, result: ApplyResult, check_applicable=True):
        result.status = ApplyResult.Status.NO_OP
        if check_applicable and not self.is_applicable(state):
            result.status = ApplyResult.Status.NOT_APPLICABLE
        else:
            self.effect.apply(state, result)


class ForAllAction[OPERAND_T](ActionBase):
    def __init__(
        self,
        objs: list[OPERAND_T],
        action: Action,
    ) -> None:
        self.objs = objs
        self.action = action
        self._action_instances: list[Action] = []
        self._instantiate_actions()

    def __str__(self):
        return f"forall_action([..{len(self.objs)} objs..] do:{self.action})"

    def __repr__(self):
        return self.__str__()

    def _instantiate_actions(self):
        for obj in self.objs:
            action_instance = self.action(obj)
            self._action_instances.append(action_instance)

    def precondition(self) -> Condition:
        conditions: list[Condition] = list()
        for action_instance in self._action_instances:
            conditions.append(action_instance.precondition)
        return AndCondition(conditions)

    @override
    def effect(self) -> Effect:
        effects: list[Effect] = list()
        for action_instance in self._action_instances:
            effects.append(action_instance.effect)
        return AndCondition(effects)

    @override
    def apply(self, state: Stateful, result: ApplyResult, check_applicable=True):
        for action_instance in self._action_instances:
            action_instance.apply(state, result, check_applicable)


class ActionTemplate(ActionBase):
    def __init__(
        self,
        descriptor: ActionDescriptor,
    ):
        ActionBase.__init__(self, descriptor.name)
        self._descriptor: ActionDescriptor = descriptor
        self._instances: dict[tuple[Named], ActionTemplate.ActionInstance] = dict()

    # TODO move this to the descriptor since it is really there that this is done
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

    def partially_bound_instance(self, owner: ACTION_OWNER_T):
        args_tuple = (owner,)
        return self.get_instance(args_tuple)

    def get_instance(self, args_tuple):
        instance = None
        if args_tuple in self._instances:
            instance = self._instances[args_tuple]
        else:
            instance = ActionTemplate.ActionInstance(self, args_tuple)
            self._instances[args_tuple] = instance
        return instance

    def __call__(self, *args: list[Named], **kwds):
        args_tuple = tuple(args)
        return self.get_instance(args_tuple)

    class ActionInstance(ActionBase):
        def __init__(
            self,
            template: ActionTemplate,
            args: list[Named] = None,
        ):
            ActionBase.__init__(self, template._descriptor.name, template=template)
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
        def precondition(self, value):
            self._precondition = value

        @property
        def effect(self) -> Effect:
            effect_func = self._template._descriptor.effect_func
            arg_subset = self.get_arg_subset(effect_func)
            effect = effect_func(*arg_subset)
            return effect

        @effect.setter
        def effect(self, value):
            self._effect = value

        def get_arg_subset(self, func):
            # TODO review the arguments of the function and pull them out of self.args in order.
            return self.args

        def __call__(self, *args: list[Named], **kwds):
            full_args = self.args + args
            args_tuple = tuple(full_args)
            return self.template.get_instance(args_tuple)
