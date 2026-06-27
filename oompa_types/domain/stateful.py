from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from oompa_types.action.apply_result import ApplyResult

if TYPE_CHECKING:
    from oompa_types.action.action import Action
    from oompa_types.condition.condition import Condition


class Stateful[SUBCLASS_T: Stateful](Protocol):
    def entails(self, condition: Condition) -> bool:
        return condition.is_entailed_by(self)

    def entailsfalse(self, condition: Condition) -> bool:
        return not self.entails(condition)

    @property
    def is_static_state(self) -> bool: ...

    def matching_svs(self, filter: Callable[[Any], bool]) -> set[Condition]: ...

    def get(self, *keys: str) -> Any: ...

    def copy(self, freeze: bool) -> SUBCLASS_T: ...

    def frozen_copy(self, freeze: bool) -> SUBCLASS_T: ...

    def apply(self, action: Action, result=ApplyResult, force_copy=True) -> SUBCLASS_T:
        """Applies action to a copy of this state; returns the possibly changed copy."""
        state_copy: SUBCLASS_T = self.thaw(force_copy)
        action.apply(state_copy, result)
        return state_copy

    def apply_and_freeze(self, action: Action, result=ApplyResult, force_copy=True) -> SUBCLASS_T:
        """Applies action to a copy of this state; returns the possibly changed _frozen_ copy."""
        state_copy = self.apply(action, result, force_copy)
        frozen_copy = state_copy.freeze()
        return frozen_copy

    @property
    def is_mutable(self) -> bool:
        """Returns whether this state is mutable."""
        return not self.is_frozen()

    @property
    def is_frozen(self) -> bool:
        """Returns whether this state is immutable."""
        ...

    def freeze(self) -> SUBCLASS_T:
        """Returns a _new_ copy of this state that is immutable."""
        return self.frozen_copy()

    def thaw(self, force_copy=False) -> SUBCLASS_T:
        """Returns self if already mutable and not force_copy; otherwise returns a copy that is mutable."""
        new_copy = self
        if self.is_frozen:
            new_copy = self.copy(freeze=False)
        else:
            if force_copy:
                new_copy = self.copy(freeze=False)
        return new_copy
