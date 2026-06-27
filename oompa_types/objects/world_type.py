from __future__ import annotations

from typing import Any

from .typed import Typed


class WorldType[T](Typed[T]):
    """A lightweight type class."""

    ANY: WorldType = None

    def __init__(self, type_name):
        self._type_name: str = type_name
        self._type = type(self)

    @property
    def type(self) -> T:
        return self._type

    @property
    def type_name(self) -> str:
        return self._type_name


WorldType.ANY = WorldType[Any]("ANY")
