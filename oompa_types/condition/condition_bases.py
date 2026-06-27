from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, override

from makro_utils.log_manager import LogManager
from oompa_types.condition.condition import Condition, ConditionOwner
from oompa_types.domain.operator import Operator
from oompa_types.domain.placeholder import Placeholder

if TYPE_CHECKING:
    from oompa_types.domain.stateful import Stateful

logger = LogManager.get_logger("oompa.condition")


class AbstractCondition[VALUE_T](Condition[VALUE_T], ABC):
    def __init__(self, parent=None) -> None:
        super().__init__()
        self._owner: ConditionOwner | None = None
        self._parent: Condition | None = None

    @property
    def owner(self) -> ConditionOwner:
        return self._owner

    @owner.setter
    def owner(self, owner: ConditionOwner):
        self._owner = owner
        for child in self.children:
            child.owner = owner

    @property
    def parent(self) -> None | Condition:
        return self._parent

    @parent.setter
    def parent(self, parent) -> Condition:
        self._parent = parent
        for child in self.children:
            child.parent = self


class NullCondition(AbstractCondition):
    """To ensure this class works correctly, use NULL_CONDITION."""

    @override
    def is_entailed_by(self, state: Stateful, caller: Any = None) -> bool:
        return False


NULL_CONDITION = NullCondition()


def get_null_condition() -> NullCondition:
    return NULL_CONDITION


class TrueCondition(AbstractCondition):
    @override
    def is_entailed_by(self, state: Stateful, caller: Any = None) -> bool:
        return True


class QuantifiedCondition(AbstractCondition):
    conditions: list[Condition] = []

    def __init__(self, *conditions: Condition) -> None:
        self.conditions = conditions

    def __repr__(self):
        return self.__str__()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        result = ""
        for condition in self.conditions:
            result += f"{indent}{condition.str_dereferenced(state)}{sep}"
        return result

    def add(self, condition: Condition):
        self.conditions.append(condition)

    def is_entailed_by_all(self, state: Stateful, caller: Any = None):
        for condition in self.conditions:
            if not condition.is_entailed_by(state, caller):
                return False
        return True

    @override
    def is_entailed_by_any(self, state: Stateful, caller: Any = None):
        for condition in self.conditions:
            if condition.is_entailed_by(state, caller):
                return True
        return False

    def __hash__(self):
        return hash(tuple(self.conditions))

    @override
    def matches(self, other: Condition):
        """Returns true when other is the same type and all subconditions match."""
        if super().matches(other):
            if isinstance(other, AndCondition) or isinstance(other, OrCondition):
                return self.matches_all(other)
        return False

    def matches_contains(self, other: Condition):
        result = False
        for condition in self.conditions:
            if condition == other:
                result = True
                break  # stop on first match
        return result

    def matches_all(self, other: AndCondition | OrCondition):
        result = False
        for condition in other.conditions:
            if self.matches_contains(condition):
                result = True
            else:
                result = False
                break  # stop on first failed match
        return result

    @override
    @property
    def children(self):
        return self.conditions


class AndCondition(QuantifiedCondition):
    def __init__(self, *conditions: Condition) -> None:
        QuantifiedCondition.__init__(self, *conditions)

    def __str__(self):
        return f"and([..{len(self.conditions)} conditions..])"

    @override
    def is_entailed_by(self, state: Stateful, caller: Any = None):
        return self.is_entailed_by_all(state, caller)


class OrCondition(QuantifiedCondition):
    def __init__(self, *conditions: Condition) -> None:
        QuantifiedCondition.__init__(self, *conditions)

    def __str__(self):
        return f"or([..{len(self.conditions)} conditions..])"

    @override
    def is_entailed_by(self, state: Stateful, caller: Any = None):
        return self.is_entailed_by_any(state, caller)


class ForAllCondition[OPERAND_T](AbstractCondition):
    def __init__(
        self,
        objs: list[OPERAND_T],
        functor: Callable[[OPERAND_T], Condition],
    ) -> None:
        self.objs = objs
        self.functor = functor

    def __str__(self):
        return f"forall([..{len(self.objs)} objs..])"

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        result = ""
        deref_objs = self.objs
        if isinstance(self.objs, Placeholder):
            deref_objs = self.objs.dereference(self, state)
        for obj in deref_objs:
            deref_obj = obj
            if isinstance(obj, Placeholder):
                deref_obj = obj.dereference(state)
            condition = self.functor(deref_obj)
            result += f"{indent}{condition.str_dereferenced(state)}{sep}"
        return result

    @override
    def is_entailed_by(self, state: Stateful, caller: Any = None):
        deref_objs = self.objs
        if isinstance(self.objs, Placeholder):
            deref_objs = self.objs.dereference(self, state)
        for obj in deref_objs:
            deref_obj = obj
            if isinstance(obj, Placeholder):
                deref_obj = obj.dereference(state)
            condition = self.functor(deref_obj)
            if not condition.is_entailed_by(state, caller):
                return False
        return True


class Comparison(AbstractCondition):
    """Performs a binary comparison given by `op` for two objects.

    Warning: this does not access the state!
    """

    def __init__(self, left, op: Operator, right, parent=None):
        super().__init__(parent)
        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def __repr__(self):
        return self.__str__()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        if isinstance(self.left, Placeholder):
            left_str = self.left.dereference(state)
        else:
            left_str = str(self.left)

        if isinstance(self.right, Placeholder):
            right_str = self.right.dereference(state)
        else:
            right_str = str(self.right)
        return f"{indent}{left_str} {self.op} {right_str}{sep}"

    def is_entailed_by(self, state, caller=None):
        left = self.left
        if isinstance(self.left, Placeholder):
            left = self.left.dereference(self, state)
        right = self.right
        if isinstance(self.right, Placeholder):
            right = self.right.dereference(state)
        return self.op.compare(left, right)


class TypeMatches(AbstractCondition):
    def __init__(self, context: Any, type_to_check: type, parent=None):
        super().__init__(parent)
        self.context: Any = context
        self.type_to_check: type = type_to_check

    def str_dereferenced(self, state=None):
        if isinstance(self.context, Placeholder):
            context_str = self.context.dereference(None, state)
        else:
            context_str = str(self.context)
        return f"{context_str} isa {self.type_to_check}"

    def is_entailed_by(self, state, caller=None):
        value = self.context
        if isinstance(self.context, Placeholder):
            value = self.context.dereference(None, state)
        type_matches = isinstance(value, self.type_to_check)
        return type_matches
