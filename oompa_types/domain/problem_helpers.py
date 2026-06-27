from typing import Protocol, runtime_checkable

from oompa_types.domain.problem import Problem


class StoresProblem(Protocol):
    def problem(self) -> Problem: ...


@runtime_checkable
class CreatesNewObjects(StoresProblem, Protocol):
    """Designates an object as one that can create new objects."""

    pass
