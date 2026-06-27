from __future__ import annotations

from abc import ABC

from .named import AbstractNamed
from .world_type import WorldType


class WorldObject(WorldType, AbstractNamed, ABC):
    def __init__(self, type_name=None, name: str = ""):
        if type_name is None:
            type_name = str(type(self))
        super(WorldType, self).__init__(type_name)
        super(AbstractNamed, self).__init__(name)
