from typing import Protocol, runtime_checkable

from oompa_types.action.action_descriptor import OompaAction
from oompa_types.utils.descriptor_helpers import descriptor_search


@runtime_checkable
class HasOompaActions(Protocol):
    pass


def collect_action_descriptors(obj, actions: list[OompaAction]):
    descriptor_search(actions, obj, HasOompaActions, OompaAction)
