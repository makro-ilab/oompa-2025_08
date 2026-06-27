from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from inspect import isclass
from types import UnionType
from typing import TYPE_CHECKING, Union, get_args, get_origin, override

from makro_utils.class_utils import expand_type_to_list
from makro_utils.log_manager import LogManager
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_of_state_property import ConditionOfStateProperty
from oompa_types.domain.arguments import LIST_ARGS_BASE, AbstractArguments
from oompa_types.domain.operator import (
    APPENDS,
    ASSIGNED,
    CONTAINS,
    DECREASED_BY,
    EQUALS,
    FEWER_THAN,
    FEWER_THAN_EQUALS,
    GREATER_THAN,
    GREATER_THAN_EQUALS,
    INCREASED_BY,
    INSERTS,
    LESS_THAN,
    LESS_THAN_EQUALS,
    MORE_THAN,
    MORE_THAN_EQUALS,
    NOT_CONTAINS,
    NOT_EQUALS,
    POPS,
    PUSHES,
    REMOVES,
)
from oompa_types.domain.operator_bases import SupportsOperators
from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.stateful import Stateful
from oompa_types.effect.effect import Effect
from oompa_types.effect.effect_bases import EffectOfStateProperty
from oompa_types.objects.named import AbstractNamed, Named
from oompa_types.state_property.state_property import StateProperty

if TYPE_CHECKING:
    from oompa_types.state_property.state_property import StateProperty
    from oompa_types.state_property.state_property_descriptor import StatePropertyDescriptor

logger = LogManager.get_logger("oompa.sp")


class StatePropertyBase[
    LIST_ARGS_T: LIST_ARGS_BASE,
    VALUE_T,
](
    AbstractNamed,
    AbstractArguments[LIST_ARGS_T],
    StateProperty[LIST_ARGS_T, VALUE_T],
    SupportsOperators,
):
    type_check_value: bool = True

    def __init__(
        self,
        name: str,
        args: LIST_ARGS_T = None,
        value: VALUE_T | None = None,
        default: VALUE_T | None = None,
        value_type: VALUE_T | None = None,
    ):
        AbstractNamed.__init__(self, name)
        AbstractArguments.__init__(self, args)
        self._value = value
        self._default = default
        self._value_type = value_type
        self._is_bindable: bool = True
        self._is_assignable: bool = True

    def __repr__(self) -> str:
        return self.str_detail()

    def __str__(self) -> str:
        return self.str_detail()

    def str_detail(self, include_value=False, include_default=False) -> str:
        name_str = str(self.name)
        args_str = ", ".join(map(str, [f"{x.name}" for x in self.args]))
        value_str = ""
        default_str = ""
        if include_value:
            value_str = f"={self.value}"
        if include_default:
            default_str = f"[default:{self.default}]"
        return f"{name_str}({args_str}){value_str}{default_str}"

    def __lt__(self, other):
        if isinstance(other, StateProperty):
            return self.name < other.name
        return self < other

    def __getattr__(self, name: str):
        """Manages the special case of chaining access of more than one StateProperty."""
        logger.debug(f"getting StateProperty {self}.{name}")
        value_type = self.value_type
        value_types = expand_type_to_list(value_type)
        if len(value_types) > 1:
            missing_property = []
            for value_t in value_types:
                if not hasattr(value_t, name):
                    missing_property.append(value_t)
            if len(missing_property) > 0:
                msg = f"{self}.{name} is a missing property for: {missing_property}. You may want to wrap this access with a ConditionalEffect."
                logger.warning(msg)
        value_type = value_types[0]

        spd: StatePropertyDescriptor = getattr(value_type, name)
        return spd.get_state_property_instance(self)

    @property
    def is_attribute(self) -> bool:
        args_type = self.args_types
        return len(args_type) == 1

    @property
    def is_relation(self) -> bool:
        return len(self.args_types) > 1

    @property
    def is_container(self) -> bool:
        value_type = self.value_type
        return (
            isinstance(value_type, list)
            or isinstance(value_type, set)
            or isinstance(value_type, dict)
            or isinstance(value_type, Iterable)
        )

    @property
    def is_bindable(self) -> bool:
        return self._is_bindable

    @property
    def is_assignable(self) -> bool:
        return self._is_assignable

    def freeze(self):
        self._is_assignable = False

    def set_as_template(self):
        self._is_assignable = False
        self._is_bindable = False

    def allows_value_type(self, new_value: VALUE_T):
        # TODO incorporate [Identifying Generic Types at Runtime · python/typing · Discussion #1099](https://github.com/python/typing/discussions/1099)
        # TODO eventually remove once generics are confirmed to be working properly via mypy
        new_value_t = type(new_value)
        value_t = self.value_type
        if new_value_t == value_t:
            return True
        if new_value is None:
            return self._check_if_none_value_is_allowed()

        if value_t is not None:
            if isclass(value_t) and isclass(new_value_t):
                if issubclass(new_value_t, value_t):
                    return True
            if isclass(value_t) and issubclass(value_t, Enum):
                return new_value in value_t
            origin = get_origin(value_t)
            if isinstance(origin, UnionType) or origin is Union or origin is UnionType:
                value_t = get_args(value_t)
                if isinstance(new_value, value_t):
                    return True
            if origin is tuple:
                args = get_args(value_t)
                if len(args) > 0:
                    return len(new_value) == len(args)
                return True
            if isclass(new_value) and isclass(origin):
                if issubclass(new_value, origin):
                    return True
            if isclass(new_value_t) and isclass(origin):
                if issubclass(new_value_t, origin):
                    return True
        return False

    def _check_if_none_value_is_allowed(self) -> bool:
        self_value = self.value
        if self_value is None:
            return True
        has_origin = get_origin(self_value)
        if has_origin is not None:
            origin_args = get_args(self_value)
            if None in origin_args:
                return True
        return False

    @property
    def default(self):
        return self._default

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value: VALUE_T):
        if self.is_assignable:
            self._value = new_value
        else:
            raise TypeError(f"StateProperty {self} is not assignable.")

    @override
    @property
    def value_type(self) -> VALUE_T | None:
        return self.template._descriptor.value_type

    # ==============================================================
    # region  Placeholder
    def dereferenced_args(self, state: Stateful | None = None) -> LIST_ARGS_T:
        args_deref = []
        for arg in self.args:
            if isinstance(arg, Placeholder):
                arg_deref = arg.dereference(self, state)
                args_deref.append(arg_deref)
            else:
                args_deref.append(arg)
        return args_deref

    def dereferenced_arg_name(self, instance, state: Stateful | None = None) -> str:
        dereferenced_args = self.dereferenced_args(state)
        if hasattr(dereferenced_args, "_name"):
            return dereferenced_args._name
        elif hasattr(dereferenced_args, "name"):
            return dereferenced_args.name
        else:
            if len(dereferenced_args) == 1:
                return str(dereferenced_args[0])
            return str(dereferenced_args)

    def dereference(self, instance: Named = None, state: Stateful | None = None) -> Named:
        deref_args = self.dereferenced_arg_name(instance, state)
        if state is not None:
            if hasattr(state, self.name):
                name_dict = getattr(state, self.name)
                if deref_args in name_dict:
                    return name_dict[deref_args]
            else:
                logger.error(f"state is missing a dictionary for deref_arg:{self.name}.")
                return None
        return None

    # endregion Placeholder
    # ==============================================================

    # ===================================================================================
    # region Operators

    def equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, EQUALS, desired)

    def ne(self, desired) -> Condition:
        return self.not_equals(desired)

    def not_equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, NOT_EQUALS, desired)

    def lt(self, desired) -> Condition:
        return self.less_than(desired)

    def less_than(self, desired) -> Condition:
        return ConditionOfStateProperty(self, LESS_THAN, desired)

    def lte(self, desired) -> Condition:
        return self.less_than_equals(desired)

    def less_than_equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, LESS_THAN_EQUALS, desired)

    def gt(self, desired) -> Condition:
        return self.greater_than(desired)

    def greater_than(self, desired) -> Condition:
        return ConditionOfStateProperty(self, GREATER_THAN, desired)

    def gte(self, desired) -> Condition:
        return self.greater_than_equals(desired)

    def greater_than_equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, GREATER_THAN_EQUALS, desired)

    def contains(self, desired) -> Condition:
        return ConditionOfStateProperty(self, CONTAINS, desired)

    def fewer_than(self, desired) -> Condition:
        return ConditionOfStateProperty(self, FEWER_THAN, desired)

    def fewer_than_equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, FEWER_THAN_EQUALS, desired)

    def more_than(self, desired) -> Condition:
        return ConditionOfStateProperty(self, MORE_THAN, desired)

    def more_than_equals(self, desired) -> Condition:
        return ConditionOfStateProperty(self, MORE_THAN_EQUALS, desired)

    def not_contains(self, desired) -> Condition:
        return ConditionOfStateProperty(self, NOT_CONTAINS, desired)

    def assigned(self, desired) -> Effect:
        return EffectOfStateProperty(self, ASSIGNED, desired)

    def increased_by(self, desired) -> Effect:
        return EffectOfStateProperty(self, INCREASED_BY, desired)

    def decreased_by(self, desired) -> Effect:
        return EffectOfStateProperty(self, DECREASED_BY, desired)

    def reduced_by(self, desired) -> Effect:
        return EffectOfStateProperty(self, DECREASED_BY, desired)

    def inserts(self, desired) -> Effect:
        return EffectOfStateProperty(self, INSERTS, desired)

    def removes(self, desired) -> Effect:
        return EffectOfStateProperty(self, REMOVES, desired)

    def appends(self, desired) -> Effect:
        return EffectOfStateProperty(self, APPENDS, desired)

    def pushes(self, desired) -> Effect:
        return EffectOfStateProperty(self, PUSHES, desired)

    def pops(self, desired) -> Effect:
        return EffectOfStateProperty(self, POPS, desired)

    # endregion Operators
    # ===================================================================================


class StatePropertyTemplate[LIST_ARGS_T: LIST_ARGS_BASE, VALUE_T](
    StatePropertyBase[LIST_ARGS_T, VALUE_T],
):
    descriptor: StatePropertyDescriptor = None

    def __init__(
        self,
        name,
        args,
        args_type: LIST_ARGS_T,
        value_type: VALUE_T,
        instance=None,
        descriptor: StatePropertyDescriptor = None,
    ):
        super().__init__(name, args)
        self.set_as_template()
        self._instance = instance
        self.descriptor = descriptor
        self._instances: dict[tuple, StatePropertyInstanceBase] = dict()
        self._args_type = args_type
        self._value_type = value_type

        # Templates are neither bindable nor assignable
        self._is_bindable = False
        self._is_assignable = False

    @property
    def is_relation(self) -> bool:
        return len(self.args_types) > 1 and self.descriptor.fget is not None

    @override
    @property
    def args_types(self) -> list[Named]:
        return self.descriptor.args_type

    @override
    @property
    def value_type(self):
        return self.descriptor.value_type

    @override
    @StatePropertyBase.value.getter
    def value(self):
        raise TypeError("Cannot call value on a StatePropertyTemplate; use an instance instead.")

    def partially_bound_instance(self, owner):
        args_tuple = (owner,)
        return self.get_instance(args_tuple)

    def get_instance(self, args_tuple):
        instance = None
        if args_tuple in self._instances:
            instance = self._instances[args_tuple]
        else:
            if self.is_attribute:
                instance = StatePropertyOfAttribute(self, args_tuple)
            else:  # is_relation == True
                instance = StatePropertyOfRelation(self, args_tuple)
            self._instances[args_tuple] = instance
        return instance

    def __call__(self, *args: list[Named], **kwds):
        args_tuple = tuple(args)
        return self.get_instance(args_tuple)


class StatePropertyInstanceBase[LIST_ARGS_T: LIST_ARGS_BASE, VALUE_T](
    StatePropertyBase[LIST_ARGS_T, VALUE_T],
):
    template: StatePropertyTemplate
    descriptor: StatePropertyDescriptor

    def __init__(self, template: StatePropertyTemplate, args):
        self.template = template
        self.descriptor = template.descriptor
        StatePropertyBase.__init__(self, template.descriptor.name, args=args)
        self.value = template.descriptor.initial_value
        if template.descriptor.is_read_only:
            self.freeze()

    @override
    @property
    def args_types(self) -> list[Named]:
        return self.descriptor.args_type

    @override
    @property
    def value_type(self):
        return self.descriptor.value_type


class StatePropertyOfAttribute[LIST_ARGS_T: LIST_ARGS_BASE, VALUE_T](
    StatePropertyInstanceBase[LIST_ARGS_T, VALUE_T],
):
    def __init__(self, template: StatePropertyTemplate, args_tuple):
        StatePropertyInstanceBase.__init__(self, template, args=args_tuple)

    def __call__(self):
        return self.value

    @override
    @StatePropertyBase.value.getter
    def value(self) -> VALUE_T:
        fget = self.descriptor.fget
        if fget is None:
            return super().value

        # if fget references a property, call property.fget(self._instance)
        if isinstance(fget, property):
            prop = fget
            value = prop.fget(self.template._instance)
            return value
        # if the function only takes one argument, self, then call fget(self._instance)
        if len(self.args_types) == 1:
            return fget(self.template._instance)
        # Otherwise, we can't take the value; log a warning
        msg = (
            f"Getting the value of StatePropertyTemplate.{self.name}{tuple(self.args)} is not"
            " possible because there are no bound arguments!; "
            "instead use get_instance(args) to get an instance and take the value of that."
        )
        logger.warn(msg)
        return None

    def dereference(self, instance: Named = None, state: Stateful | None = None) -> Named:
        value = super().dereference(instance, state)
        return value


class StatePropertyOfRelation[LIST_ARGS_T: LIST_ARGS_BASE, VALUE_T](
    StatePropertyInstanceBase[LIST_ARGS_T, VALUE_T],
):
    def __init__(self, template: StatePropertyTemplate, args_tuple: tuple[Named, ...] = None):
        actual_args = args_tuple if args_tuple is not None else tuple()
        StatePropertyInstanceBase.__init__(self, template, args=actual_args)

    def __str__(self):
        return self.str_detail()

    def __repr__(self):
        return self.str_detail()

    def __getitem__(self, args_in: tuple[Named], **kwds):
        new_args = []
        self_args = self.args
        new_args.extend(self_args)
        new_args.extend(args_in)
        return self.template.get_instance(tuple(new_args))
        return self

    def __call__(self, *args_in: list[Named], **kwds):
        new_args = []
        self_args = self.args
        new_args.extend(self_args)
        new_args.extend(args_in)
        spi = self.template.get_instance(tuple(new_args))
        value = spi.value
        return value

    @override
    @StatePropertyBase.value.getter
    def value(self):
        """Return the value this StateProperty if it actually uses fget from the descriptor."""
        fget = self.descriptor.fget
        owning_instance = self.template._instance
        if fget is None or owning_instance is None:
            return super().value
        expanded_args = self.get_expanded_args()
        owning_instance = self.template._instance
        return fget(*expanded_args)

    def get_expanded_args(self):
        expanded_args = []
        args = self.args
        for arg in args:
            expanded_arg = arg
            if isinstance(arg, StatePropertyInstanceBase):
                expanded_arg = arg.value
            expanded_args.append(expanded_arg)
        return expanded_args

    def dereference(self, instance: Named = None, state: Stateful | None = None) -> Named:
        value = super().dereference(instance, state)
        if value is None:
            fget = self.descriptor.fget
            owning_instance = self.template._instance
            if fget is not None and owning_instance is not None:
                deref_args = self.dereferenced_args(state)
                value = fget(*deref_args)
        return value
