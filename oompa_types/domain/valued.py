from typing import Protocol


class Valued[VALUE_T](Protocol):
    @property
    def value(self) -> VALUE_T: ...

    @property
    def default(self) -> VALUE_T: ...

    @property
    def value_type(self) -> type[VALUE_T]: ...
