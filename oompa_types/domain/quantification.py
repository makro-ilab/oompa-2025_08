from collections.abc import Callable

from oompa_types.condition.condition import Condition
from oompa_types.domain.placeholder_bases import AbstractPlaceholder


class ExistsList[OPERAND_T](AbstractPlaceholder):
    def __init__(
        self,
        operand_class: OPERAND_T,
        functor: Callable[[OPERAND_T], Condition],
    ):
        self.operand_class = operand_class
        self.functor = functor

    def dereference(self, instance=None, state=None):
        pass
