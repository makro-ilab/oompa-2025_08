from typing import Protocol


class Typed[T](Protocol):
    @property
    def type(self) -> T:
        return type(T)

    @property
    def type_name(self) -> str:
        return str(type(T))


