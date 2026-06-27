from typing import Any, Protocol, TypeVar

LIST_ARGS_BASE = TypeVar("LIST_ARGS_T", bound=list[type])


class HasArguments[LIST_ARGS_T: LIST_ARGS_BASE](Protocol):
    @property
    def args_types(self) -> LIST_ARGS_T:
        return LIST_ARGS_T

    @property
    def num_args(self) -> int: ...

    @property
    def args(self) -> list[Any]: ...


class SingleArgument[T](HasArguments[list[T]]):
    @property
    def num_args(self) -> int:
        return 1

    @property
    def args(self) -> list[T]: ...


class AbstractSingleArgument[T](SingleArgument[T]):
    def __init__(self, arg: T):
        self.arg = arg

    @property
    def args(self) -> list[T]:
        return [self.arg]


class AbstractArguments[LIST_ARGS_T: LIST_ARGS_BASE](HasArguments[LIST_ARGS_T]):
    def __init__(self, args: LIST_ARGS_T = []):
        self._args = args

    @property
    def args_types(self) -> LIST_ARGS_T:
        return LIST_ARGS_T

    @property
    def num_args(self):
        return len(self._args)

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args: list[Any]):
        self._args = args
