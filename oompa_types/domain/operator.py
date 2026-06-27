from dataclasses import dataclass
from typing import Any

from aenum import StrEnum
from makro_utils.log_manager import LogManager

logger = LogManager.get_logger("oompa.operator")


class Operator(StrEnum):
    # The following are used for a PersistenceStatement
    EQUALS = "=="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_EQUALS = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUALS = ">="

    # The following is used for an Assignment Statement
    ASSIGNED = ":="

    # The following is used for a Transition Statement; currently not implemented
    # TRANSITION = "->"

    DECREASED_BY = "-="
    INCREASED_BY = "+="

    # The following are used for CompoundStatement
    AND = "^"
    OR = "|"

    # The following are used for container membership and comparison
    CONTAINS = "contains"
    NOT_CONTAINS = "not-contains"
    FEWER_THAN = "fewer-than"
    FEWER_THAN_EQUALS = "fewer-than-equals"
    MORE_THAN = "more-than"
    MORE_THAN_EQUALS = "more-than-equals"

    # The following are used for set modification
    INSERTS = "inserts"
    REMOVES = "removes"

    # The following are used for list modification
    APPENDS = "appends"
    PUSHES = "pushes"
    POPS = "pops"

    def __str__(self) -> str:
        return self.value

    def invert(self):
        match self.value:
            case Operator.EQUALS:
                return Operator.NOT_EQUALS
            case Operator.NOT_EQUALS:
                return Operator.EQUALS
            case Operator.LESS_THAN:
                return Operator.GREATER_THAN_EQUALS
            case Operator.LESS_THAN_EQUALS:
                return Operator.GREATER_THAN
            case Operator.GREATER_THAN:
                return Operator.LESS_THAN_EQUALS
            case Operator.GREATER_THAN_EQUALS:
                return Operator.LESS_THAN
            case Operator.AND:
                # TODO if this is used, it should probably use DeMorgan's law..
                return Operator.OR
            case Operator.OR:
                # TODO if this is used, it should probably use DeMorgan's law..
                return Operator.AND
            case Operator.CONTAINS:
                return Operator.NOT_CONTAINS
            case Operator.NOT_CONTAINS:
                return Operator.CONTAINS

    def compare(self, left, right):
        """A helper function that calls the correct comparison."""
        if self.compares_value:
            return self.compare_value_no_check(left, right)
        elif self.compares_container:
            return self.compare_container_no_check(left, right)

    @property
    def compares_value(self) -> bool:
        return (
            self == EQUALS
            or self == NOT_EQUALS
            or self == LESS_THAN
            or self == LESS_THAN_EQUALS
            or self == GREATER_THAN
            or self == GREATER_THAN_EQUALS
        )

    def compare_value(self, left, right):
        """Compares left OP right for the binary operators."""
        if not self.compares_value:
            msg = "compare_value(..) only works on operators listed by Operator.compares_vaule."
            logger.error(msg)
            raise TypeError(msg)
        return self.compare_value_no_check(left, right)

    def compare_value_no_check(self, left, right):
        match self:
            case Operator.EQUALS:
                return left == right
            case Operator.NOT_EQUALS:
                return left != right
            case Operator.LESS_THAN:
                return left < right
            case Operator.LESS_THAN_EQUALS:
                return left <= right
            case Operator.GREATER_THAN:
                return left > right
            case Operator.GREATER_THAN_EQUALS:
                return left >= right
            case _:
                logger.error(f"there is no evaluator for operator {self}")

    @property
    def modifies_value(self) -> bool:
        return self == ASSIGNED or self == DECREASED_BY or self == INCREASED_BY

    def calculate(self, left, right):
        """Applies left OP right for the assignment operators."""
        if not self.modifies_value:
            msg = "calculate(..) only works on operators listed by Operator.modifies_primitive."
            logger.error(msg)
            raise TypeError(msg)

        match self:
            case Operator.ASSIGNED:
                return right
            case Operator.INCREASED_BY:
                return left + right
            case Operator.DECREASED_BY:
                return left - right

    @property
    def compares_container(self) -> bool:
        return (
            self == CONTAINS
            or self == NOT_CONTAINS
            or self == FEWER_THAN
            or self == FEWER_THAN_EQUALS
            or self == MORE_THAN
            or self == MORE_THAN_EQUALS
        )

    def compare_container(self, left, right):
        """Compares left OP right for the binary operators."""
        if not self.compares_container:
            msg = "compare_container() works on operators listed by Operator.compares_container."
            logger.error(msg)
            raise TypeError(msg)
        return self.compare_container_no_check(left, right)

    def compare_container_no_check(self, left, right):
        """Compares left OP right for the binary operators."""
        match self:
            case Operator.CONTAINS:
                return right in left
            case Operator.NOT_CONTAINS:
                return right not in left
            case Operator.FEWER_THAN:
                return len(left) < right
            case Operator.FEWER_THAN_EQUALS:
                return len(left) <= right
            case Operator.MORE_THAN:
                return len(left) > right
            case Operator.MORE_THAN_EQUALS:
                return len(left) >= right
            case _:
                logger.error(f"there is no evaluator for operator {self}")

    @property
    def modifies_container(self) -> bool:
        return (
            self == INSERTS or self == REMOVES or self == APPENDS or self == PUSHES or self == POPS
        )

    def update(self, container, item):
        if not self.modifies_container:
            msg = "update(..) only works on operators listed by Operator.modifies_container."
            logger.error(msg)
            raise TypeError(msg)
        wrapper = ContainerWrapper(container)
        match self:
            case Operator.INSERTS:
                wrapper.insert(item)
            case Operator.REMOVES:
                wrapper.remove(item)
            case Operator.APPENDS:
                wrapper.append(item)
            case Operator.PUSHES:
                wrapper.push(item)
            case Operator.POPS:
                wrapper.pop(item)


@dataclass
class ContainerWrapper:
    container: Any
    container_type = None

    def __post_init__(self):
        self.container_type = type(self.container)

    def insert(self, item):
        if isinstance(self.container, set):
            self.container.add(item)
        elif isinstance(self.container, list):
            self.container.append(item)
        else:
            raise TypeError(f"Cannot call insert on containers of type {self.container_type}")

    def remove(self, item):
        if isinstance(self.container, set):
            self.container.remove(item)
        elif isinstance(self.container, list):
            self.container.remove(item)
        else:
            raise TypeError(f"Cannot call remove on containers of type {self.container_type}")

    def append(self, item):
        if isinstance(self.container, list):
            self.container.append(item)
        else:
            raise TypeError(f"Cannot call append on containers of type {self.container_type}")

    def push(self, item):
        if isinstance(self.container, list):
            self.container.insert(0, item)
        else:
            raise TypeError(f"Cannot call append on containers of type {self.container_type}")

    def pop(self, item):
        if isinstance(self.container, list):
            self.container.pop(0)
        else:
            raise TypeError(f"Cannot call append on containers of type {self.container_type}")


EQUALS = Operator.EQUALS
NOT_EQUALS = Operator.NOT_EQUALS
LESS_THAN = Operator.LESS_THAN
LESS_THAN_EQUALS = Operator.LESS_THAN_EQUALS
GREATER_THAN = Operator.GREATER_THAN
GREATER_THAN_EQUALS = Operator.GREATER_THAN_EQUALS

ASSIGNED = Operator.ASSIGNED
DECREASED_BY = Operator.DECREASED_BY
INCREASED_BY = Operator.INCREASED_BY

AND = Operator.AND
OR = Operator.OR

CONTAINS = Operator.CONTAINS
NOT_CONTAINS = Operator.NOT_CONTAINS
FEWER_THAN = Operator.FEWER_THAN
FEWER_THAN_EQUALS = Operator.FEWER_THAN_EQUALS
MORE_THAN = Operator.MORE_THAN
MORE_THAN_EQUALS = Operator.FEWER_THAN_EQUALS

INSERTS = Operator.INSERTS
REMOVES = Operator.REMOVES

APPENDS = Operator.APPENDS
PUSHES = Operator.PUSHES
POPS = Operator.POPS

EQUALITY_OPS = [EQUALS, NOT_EQUALS]
ASSIGNMENT_OPS = [ASSIGNED, INCREASED_BY, DECREASED_BY]
