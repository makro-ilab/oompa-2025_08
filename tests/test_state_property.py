from __future__ import annotations

import unittest
from enum import IntEnum, auto

from makro_utils.log_manager import LogManager
from oompa_types.action.action_descriptor import ActionDescriptor
from oompa_types.objects.world_object import WorldObject
from oompa_types.state_property.state_properties import HasStateProperties, log_state_properties
from oompa_types.state_property.state_property_descriptor import StatePropertyFactory

logger = LogManager.get_logger("oompa.test.sp")
LogManager.set_root_level(LogManager.DEBUG)


class Color(IntEnum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


LocationType = tuple[int, int]


class TestStateProperties(unittest.TestCase):
    def test_basic_state_property(self):
        logger.debug("")
        agent1 = AgentWithStateProperties("agent1")
        called_value = agent1.location()
        accessed_value = agent1.location.value
        self.assertEqual(called_value, accessed_value)
        self.assertEqual(agent1.location.value, AgentWithStateProperties.DEFAULT_START_POS)
        default_location = (1, 1)
        agent1.location = default_location
        agent1.room_number = 2
        next_to = agent1.next_to.value

        self.assertEqual(agent1.location.value, default_location)
        self.assertEqual(len(next_to), 4)
        cond = agent1.next_to.contains((2, 1))
        fake_state = {"next_to": {"agent1": set([(1, 2), (1, 0), (2, 1), (0, 1)])}}
        self.assertTrue(cond.is_entailed_by(fake_state))

        agent1.agent_color = Color.GREEN  # The internal data structure can be set directly
        with self.assertRaises(TypeError):
            agent1.color = Color.RED  # but the StateProperty AgentTest.color is read-only

        with self.assertRaises(TypeError):
            agent1.has_axe = True  # AgentTest.has_axe is a custom read_only attribute

        # TODO: this test is currently failing and it should not!
        with self.assertRaises(TypeError):
            agent1.location = None  # None is not an allowed type of location

        log_state_properties(agent1)

        agent2 = AgentWithStateProperties("agent2")
        self.assertEqual(agent2.location.value, AgentWithStateProperties.DEFAULT_START_POS)
        agent2.grid_location = (5, 5)

        log_state_properties(agent2)
        # assert that agent2 didn't impact agent1 and vice-versa
        self.assertEqual(agent1.location.value, default_location)  # agent.location did not change
        self.assertEqual(agent2.location.value, (5, 5))  # agent2.location is (5, 5)

    def test_state_property_in_super_class_is_instantiated_correctly(self):
        agent3 = SubclassOfAgentTest("agent3")
        agent3.location = (3, 3)  # ensure that an SV of the super class is instantiated

        logger.debug("Test finished!")

    def test_state_property_initializes_correctly(self):
        agent3 = SubclassOfAgentTest("agent3")
        self.assertEqual(agent3.cash.value, agent3.START_UP_CASH)

        logger.debug("Test finished!")

    def test_sp_subclassing_for_truck(self):
        """A regression test to ensure that location can initially be None."""
        truck1 = Truck(name="truck1", location=Place("place1"))
        truck2 = Truck(name="truck2", location=Depot("depot1"))


class AgentBase:
    DEFAULT_START_POS: LocationType = (0, 0)

    def __init__(self) -> None:
        self._agent_color: Color = None
        self._grid_location: LocationType = AgentBase.DEFAULT_START_POS

    @property
    def agent_color(self) -> Color:
        return self._agent_color

    @agent_color.setter
    def agent_color(self, value: Color):
        self._agent_color = value

    @property
    def grid_location(self) -> LocationType:
        return self._grid_location

    @grid_location.setter
    def grid_location(self, value: LocationType):
        self._grid_location = value


class AgentWithStateProperties(AgentBase, HasStateProperties):
    """Provides codes examples for integrating a OompaProperty into a class.

    An OompaProperty is a helper subclass of a StatePropertyDescriptorBase, so we will
    often refer to an OompaProperty as a StateProperty.  It can be either an attribute
    of a single object or a relationship between multiple objects.

    TODO: these partial descriptions may be incorrect; complete them once the class is stable

    color: demonstrates a SP with an in-class custom getter function that returns its value
           from the super class.  This SP is a read-only property and cannot be set
           because it does not provide a setter.  But the value can still be set by setting the
           AgentBase.agent_color.

    location: shows and a custom getter to the base class established through a parameter
              and an in-class custom setter function that validates the value and notifies after
              the value is set.

    next_to: demonstrates a OP with a custom getter that performs a calculation.

    room_number: shows that a property that is dynamically injected into a class during init.
                 Note: injection will probably break mypy since the instance member
                 is dynamically added and only discoverable during runtime.
    """

    color: Color = StatePropertyFactory(is_read_only=True)
    location: LocationType = StatePropertyFactory(fget=AgentBase.grid_location)
    # next_to: set[LocationType] = ...  # see next_to function below
    # room_number: int | None = ... # see inject below

    AXE_NAME: str = "axe"

    def __init__(self, name) -> None:
        self.name = name
        AgentBase.__init__(self)

        StatePropertyFactory(initial_value=None, value_type=int | None).inject(
            self,
            "room_number",
        )

        # self._sv_room_number.default = None
        self._inventory: set[str] = set()
        self._has_axe = False

    def __repr__(self) -> str:
        return self.name

    @StatePropertyFactory
    def has_axe(self) -> bool:
        """An example of a read-only custom StateProperty."""
        return AgentWithStateProperties.AXE_NAME in self._inventory

    @ActionDescriptor
    def craft_axe(self):
        self._inventory.add(AgentWithStateProperties.AXE_NAME)

    @color.getter
    def color(self):
        return super().agent_color

    @StatePropertyFactory
    def next_to(self) -> set[LocationType]:
        loc = self.location.value
        mask = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        next_to = set()
        for offset in mask:
            result = tuple(sum(x) for x in zip(loc, offset))
            next_to.add(result)
        return next_to

    @location.setter
    def location(self, new_location: LocationType) -> bool:
        self.grid_location = new_location

    @location.setter_post_hook
    def location(self, new_location: LocationType):
        logger.info(f"Notifying of location change from {self.location.value} to {new_location}")


class SubclassOfAgentTest(AgentWithStateProperties, HasStateProperties):
    START_UP_CASH: int = 20
    cash: int = StatePropertyFactory(START_UP_CASH)

    def __init__(self, name):
        AgentWithStateProperties.__init__(self, name)


class Place(WorldObject): ...


class Depot(Place): ...


class Truck(HasStateProperties):
    name: str = "Truck"
    location: Place | None = StatePropertyFactory(None)

    def __init__(self, name: str, location: Place):
        self.name = name
        self.location = location
