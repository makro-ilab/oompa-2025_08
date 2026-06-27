from typing import Protocol, runtime_checkable

from .typed import Typed


@runtime_checkable
class Named[T](Typed[T], Protocol):
    def name(self) -> str: ...

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class AbstractNamed[T](Named[T]):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name


NULL_NAMED = AbstractNamed("NULL_NAMED")
