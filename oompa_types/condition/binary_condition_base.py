from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, override

from oompa_types.condition.condition_bases import AbstractCondition
from oompa_types.domain.operator import Operator
from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.placeholder_factories import PlaceholderFactory
from oompa_types.domain.stateful import Stateful
from oompa_types.state_property.state_property import StateProperty

if TYPE_CHECKING:
    from oompa_types.condition.condition import Condition
    from oompa_types.domain.stateful import Stateful


TARGET_T = TypeVar("TARGET_T", bound=Placeholder)
DESIRED_T = TypeVar("DESIRED_T", bound=Placeholder)


class BinaryConditionBase[TARGET_T, DESIRED_T](AbstractCondition[DESIRED_T]):
    target: TARGET_T
    op: Operator
    desired: DESIRED_T

    def __init__(
        self,
        target: TARGET_T,
        op: Operator,
        desired: DESIRED_T,
    ):
        super().__init__()
        self._target: TARGET_T = target
        self._op = op
        self.desired = PlaceholderFactory.build(desired)

    def __str__(self) -> str:
        return self.str_dereferenced()

    def __repr__(self) -> str:
        return self.str_dereferenced()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        if isinstance(self._target, StateProperty):
            target_str = self._target.dereference(self, state)
        else:
            target_str = str(self._target)

        desired_str = str(self.desired_dereferenced(state))
        return f"{indent}{target_str} {self.op} {desired_str}{sep}"

    @property
    def op(self) -> Operator:
        return self._op

    @override
    @AbstractCondition.parent.setter
    def parent(self, parent):
        """Adapted from https://stackoverflow.com/a/59313599."""
        AbstractCondition.parent.fset(self, parent)
        self.target.placeholder_parent = self
        self.desired.placeholder_parent = self

    @override
    @AbstractCondition.owner.setter
    def owner(self, owner):
        """Adapted from https://stackoverflow.com/a/59313599."""
        AbstractCondition.owner.fset(self, owner)
        self.target.placeholder_owner = owner
        self.desired.placeholder_owner = owner

    def desired_dereferenced(self, state: Stateful = None):
        result = self.desired.dereference(self.owner, state)
        return result

    def __hash__(self):
        return hash((self._target, self.op, self.desired))

    @override
    def matches(self, other: Condition):
        if super().matches(other):
            if isinstance(other, BinaryConditionBase):
                return self._matches(other)
        else:
            return False

    def _matches(self, other: BinaryConditionBase):
        # check for self.target.assigned(x) will match with other.target != None
        if other.op == Operator.NOT_EQUALS:
            other_desired = other.desired
            if isinstance(other.desired, Placeholder):
                other_desired = other.desired.dereference()
            if other_desired is None:
                return (
                    self.matches_type(other)
                    and self.matches_target(other)
                    and self.op == Operator.EQUALS
                    and self.desired is not None
                )
        return (
            self.matches_type(other)
            and self.matches_target(other)
            and self.matches_op(other)
            and self.matches_desired(other)
        )

    def matches_target(self, other: BinaryConditionBase):
        result = self._target == other._target
        return result

    def matches_op(self, other: BinaryConditionBase):
        result = self.op == other.op
        return result

    def matches_desired(self, other: BinaryConditionBase):
        result = self.desired == other.desired
        return result
