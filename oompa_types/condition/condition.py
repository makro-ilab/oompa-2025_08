from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import aenum
from makro_utils.log_manager import LogManager

if TYPE_CHECKING:
    from oompa_types.domain.stateful import Stateful


logger = LogManager.get_logger("oompa.condition")


class ConditionOwner(Protocol): ...


# TODO figure out why ConditionProtocol has a VALUE_T generic; is it supposed to implement Valued?
@runtime_checkable
class Condition[VALUE_T](Protocol):
    class Result(aenum.AutoNumberEnum):
        NO_OP = ()
        SUCCESS = ()
        FAILED = ()

    def is_entailed_by(self, state: Stateful, caller: Any = None) -> bool:
        return False

    def not_entailed_by(self, state: Stateful, caller: Any = None) -> bool:
        return not self.is_entailed_by(state, caller)

    def __str__(self):
        return self.str_dereferenced()

    def __repr__(self):
        return self.str_dereferenced()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""): ...

    """Subclasses of Condition must implement __hash__ to parallel what matches(..) calculates."""
    __hash__ = None

    def __eq__(self, other: Any):
        """Returns whether a ground instance of a condition is equal to some other object.

        If other is an instance of Condition, it calls self.matches(other).
        """
        if isinstance(other, Condition):
            return self.matches(other)
        else:
            return super.__eq__(self, other)

    def matches(self, other: Condition):
        """The default match for Condition is to check that type is the same.

        Only works on ground instances; checking matches for a lifted Condition is undefined.

        Subclasses of Condition should extend matches and __hash__, as appropriate.


        """
        if self.matches_type(other):
            return True
        return False

    def matches_id(self, other: Condition):
        return id(self) == id(other)

    def matches_type(self, other: Condition):
        if type(self) is type(other):
            return True
        return False

    @property
    def children(self) -> list[Condition]:
        return []

    @property
    def owner(self) -> None | ConditionOwner:
        return None

    @owner.setter
    def owner(self, owner: ConditionOwner): ...

    @property
    def parent(self) -> None | ConditionOwner:
        return None

    @parent.setter
    def parent(self, parent): ...
