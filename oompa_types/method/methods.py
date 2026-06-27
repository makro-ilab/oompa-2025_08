from typing import Protocol, runtime_checkable

from oompa_types.method.goal_method_descriptor import OompaMethod
from oompa_types.utils.descriptor_helpers import descriptor_search


@runtime_checkable
class HasOompaMethods(Protocol):
    pass


def collect_method_descriptors(obj, actions: list[OompaMethod]):
    descriptor_search(actions, obj, HasOompaMethods, OompaMethod)
