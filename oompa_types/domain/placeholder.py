from __future__ import annotations

from typing import Any, Protocol, TypeVar, Union, runtime_checkable

from ..objects.named import Named
from .stateful import Stateful

PH_OR_NAMED = TypeVar("PH_OR_NAMED", bound=Union[Named, "Placeholder"])
PH_OR_NAMED_LIST = list[PH_OR_NAMED]

OPTIONAL_PH_OR_NAMED = TypeVar("OPTIONAL_PH_OR_NAMED", bound=PH_OR_NAMED | None)


@runtime_checkable
class Placeholder(Protocol):
    """Provides an uniform interface for dereferencing a bound attribute or function variable.

    For example, suppose the following action is defined:

    1  Move(AbstractAction):    # this is the owner
    2    robot : Robot = ParameterDescriptor[Robot]()
    3    destination: Location = ParameterDescriptor[Location]()
    4    precondition:
    5      and(  # this is the root condition and its parent is None
    6           location(Move.robot).not_equals(destination)

    Line 1: declares this as an Action template
    Line 2: declares a parameter robot
    Line 3: declares a paerameter destination
    Line 4: declares the precondition for the action
    Line 5: declares an "and condintion" that includes Lines 4 and 5
    Line 6: declares a condition that the robot is not already in the destination

    Normally, accessing a descriptor (i.e., property) directly dereferences it,
    which is why, in Line 6, the code uses `Move.robot` instead of `self.robot`.
    When this action template is declared, robot and destination are unbound variables

    Let r1: Robot, loc1: Location, and let r1.location = loc1
    Suppose the action is instantiated using __call__:
        move = Move()
        move_r1_loc1 = move(r1, loc1)

    In order to properly dereference Move.robot and Move.destination in move_r1_loc1,
    conditions, attributes, or state variables implement Placeholder.
    In the example, the action would be the owner, while the condition tree
    would be represented as a tree data structure with a root.

    Each Placeholder can dereference itself, which will be object dependent.
    Thus, when the precondition location(Move.robot) != Move.destination is checked,
    the following takes place:
      - dereference the value of Move.robot, which has the instantiated value of r1
        - let r be the dereferenced value, then r = r1
      - dereference the value of location(..) which has the instantiated value of loc1
        - let r.location indicate the dereferenced value
      - dereference the value of Move.destination, which has the instantiated value of loc1
        - let d be the dereferenced value of Move.destination, so d = loc1
      - check the precondition for the instantiated values
        - this is equivalent to testing whether r.location equals d, which is True in this instance
    """

    def matches(self, other: Placeholder, instance: Any = None, state: Stateful = None):
        result = self.dereference(instance, state) == other.dereference(instance, state)
        return result

    @property
    def placeholder_parent(self) -> OPTIONAL_PH_OR_NAMED:
        return None

    @placeholder_parent.setter
    def placeholder_parent(self, parent: OPTIONAL_PH_OR_NAMED): ...

    @property
    def placeholder_owner(self):
        return None

    @placeholder_owner.setter
    def placeholder_owner(self, owner): ...

    def dereference(self, instance: Named = None, state: Stateful | None = None) -> Named: ...
