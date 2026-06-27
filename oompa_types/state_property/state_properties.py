from typing import Protocol, runtime_checkable

from makro_utils.log_manager import LogManager
from oompa_types.state_property.state_property import StateProperty
from oompa_types.state_property.state_property_descriptor import StatePropertyDescriptor
from oompa_types.utils.descriptor_helpers import descriptor_search

logger = LogManager.get_logger("oompa.sp")


def collect_state_property_descriptors(obj, spds: list[StateProperty]):
    descriptor_search(spds, obj, HasStateProperties, StatePropertyDescriptor)


def collect_state_properties(obj, sps: list[StateProperty]):
    spds: list[StateProperty] = []
    collect_state_property_descriptors(obj, spds)
    for spd in spds:
        sps.append(spd.get_state_property_instance(obj))


def log_state_properties(obj, level=LogManager.DEBUG):
    logger.log(level, f"State properties for {obj} include:")
    sps: list[StateProperty] = []
    collect_state_properties(obj, sps)
    for sp in sps:
        logger.log(level, f"  {sp.__str__()}")


@runtime_checkable
class HasStateProperties(Protocol):
    pass


class StateProperties(HasStateProperties):
    """Some base class helpers for classes with one or more StateProperty members."""

    def instantiate_sps(self):
        """Initializes all the StateProperties for this class. (This is optional).

        StateProperty members automatically initialize themselves on access, but this
        could be called by the constructor of a base class to get this done prior to use.
        """
        spds: list[StateProperty] = []
        collect_state_property_descriptors(self, spds)
        for spd in spds:
            spd.init_state_property_template(self)

    @property
    def sps(self) -> list[StateProperty]:
        sps: list[StateProperty] = []
        collect_state_properties(self, sps)
        return sps

    @property
    def spds(self) -> list[StateProperty]:
        return self.sp_descriptors

    @property
    def sp_descriptors(self) -> list[StateProperty]:
        spds: list[StateProperty] = []
        collect_state_property_descriptors(self, spds)
        return spds
