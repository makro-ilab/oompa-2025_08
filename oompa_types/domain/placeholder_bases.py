from typing import Any

from oompa_types.domain.placeholder import OPTIONAL_PH_OR_NAMED, Placeholder
from oompa_types.domain.stateful import Stateful


class AbstractPlaceholder(Placeholder):
    def __init__(self) -> None:
        self._placeholder_owner = None
        self._placeholder_parent: OPTIONAL_PH_OR_NAMED = None

    def __eq__(self, other: Any):
        if isinstance(other, Placeholder):
            return self.matches(other)
        return super().__eq__(other)

    @property
    def placeholder_parent(self) -> OPTIONAL_PH_OR_NAMED:
        return self._placeholder_parent

    @placeholder_parent.setter
    def placeholder_parent(self, parent: OPTIONAL_PH_OR_NAMED):
        self._placeholder_parent = parent

    @property
    def placeholder_owner(self):
        return self._placeholder_owner

    @placeholder_owner.setter
    def placeholder_owner(self, owner):
        self._placeholder_owner = owner

    def dereference(self, instance=None, state=None):
        raise NotImplementedError


class PropertyPlaceholder(AbstractPlaceholder):
    """A placeholder for instance of property."""

    def __init__(self, property_to_store: property):
        super().__init__()
        self._property = property_to_store

    def __str__(self):
        return self._property.__qualname__

    def __hash__(self):
        return hash(tuple("Placeholder", self._property))

    def dereference(self, instance=None, state=None):
        return self._property.fget(self.owner)


class AnyPlaceholder(AbstractPlaceholder):
    """A placeholder for Any objects."""

    def __init__(self, obj_to_store: any):
        super().__init__()
        self._obj: any = obj_to_store

    def __str__(self):
        return str(self._obj)

    def __hash__(self):
        return hash(("Placeholder", self._obj))

    def dereference(self, instance=None, state=None):
        return self._obj
