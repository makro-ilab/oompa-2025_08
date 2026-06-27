"""A Python 3.12.5+ OOMPA version of the travel domain from GTPyhop.

This is an OOMPA version of the test domain from GTPyhop, provided at
https://github.com/dananau/GTPyhop/blob/main/Examples/simple_htn.py
"""

from __future__ import annotations

from dataclasses import dataclass

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.action_descriptor import OompaAction
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import AndCondition, Comparison
from oompa_types.domain.domain_bases import AbstractDomain
from oompa_types.domain.operator import LESS_THAN_EQUALS
from oompa_types.domain.problem_bases import AbstractProblem
from oompa_types.effect.effect_bases import AndEffect, Effect
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method import GoalMethod
from oompa_types.method.goal_method_descriptor import OompaMethod
from oompa_types.objects.named import AbstractNamed
from oompa_types.objects.named_hash import NamedHash
from oompa_types.state_property.state_properties import HasStateProperties
from oompa_types.state_property.state_property_descriptor import (
    StatePropertyFactory,
    StaticStatePropertyFactory,
)

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class SimpleTravelDomain(AbstractDomain):
    def __init__(self, name="simple_travel") -> None:
        AbstractDomain.__init__(self, name)
        self.declare_type(Location)
        self.declare_type(Person)
        self.declare_type(Taxi)
        self.declare_type(Map)

    def test_add_default_locations(self, problem: AbstractProblem):
        map = problem.map = Map("city_map")
        map.locations = [LOC_HOME_A, LOC_HOME_B, LOC_PARK, LOC_STATION]
        problem.add_objects(*map.locations)
        map.add_edge(LOC_HOME_A, LOC_PARK, 8)
        map.add_edge(LOC_HOME_B, LOC_PARK, 2)
        map.add_edge(LOC_STATION, LOC_HOME_A, 1)
        map.add_edge(LOC_STATION, LOC_HOME_B, 7)
        map.add_edge(LOC_HOME_A, LOC_HOME_B, 7)
        map.add_edge(LOC_STATION, LOC_PARK, 9)

    def test_add_alice_and_taxi1(self, problem: AbstractProblem):
        alice = problem.alice = Person(name="alice", map=problem.map, cash=20, location=LOC_HOME_A)
        taxi1 = problem.taxi1 = Taxi(name="taxi1", map=problem.map, location=LOC_PARK)
        problem.add_objects(alice, taxi1)

    def test_add_bob_and_taxi2(self, problem: AbstractProblem):
        bob = problem.bob = Person(name="bob", map=problem.map, cash=15, location=LOC_HOME_B)
        taxi2 = problem.taxi2 = Taxi(name="taxi2", map=problem.map, location=LOC_STATION)
        problem.add_objects(bob, taxi2)


class Location(AbstractNamed):
    def __init__(self, name: str):
        AbstractNamed.__init__(self, name)


LOC_NONE = Location("no_location")
LOC_HOME_A = Location("home_a")
LOC_HOME_B = Location("home_b")
LOC_PARK = Location("park")
LOC_STATION = Location("station")


class Locatable(HasStateProperties):
    map: Map
    location: Location = StatePropertyFactory(LOC_NONE)

    def __init__(self, map: Map, location: Location):
        self.map: Map = map
        self.location: Location = location

    # TODO revise action in SimpleTravelDomain to use this helper
    def moves_to(self, destination: Location):
        return self.location.assigned(destination)


class Person(Locatable, HasStateProperties, NamedHash):
    name: str = "Person"
    cash: int = StatePropertyFactory(0)
    owe: int = StatePropertyFactory(0)
    taxi: Taxi | None = StatePropertyFactory(None)
    origin: Location = StatePropertyFactory(LOC_NONE)
    __hash__ = NamedHash.__hash__

    DEFAULT_MAX_WALKING_DISTANCE: int = 2

    def __init__(
        self,
        name: str,
        map: Map,
        location: Location,
        taxi: Taxi = None,
        cash: int = 0,
        owe: int = 0,
    ) -> None:
        self.name = name
        Locatable.__init__(self, map, location)
        self.cash = cash
        self.owe = owe
        self.taxi = taxi

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()

    # =======================================
    # region Action walk_to
    @OompaAction
    def walk_to(self, destination: Location) -> Action:
        pass

    @walk_to.precondition
    def walk_to(self, destination: Location) -> Condition:
        return self.location.not_equals(destination)

    @walk_to.effect
    def walk_to(self, destination: Location) -> Effect:
        return self.location.assigned(destination)

    # endregion Action walk_to
    # =======================================

    # =======================================
    # region Action hail
    @OompaAction
    def hail(self, taxi: Taxi) -> Action:
        pass

    @hail.precondition
    def hail(self, taxi: Taxi) -> Condition:
        return taxi.location.not_equals(self.location)

    @hail.effect
    def hail(self, taxi: Taxi) -> Effect:
        return taxi.location.assigned(self.location)

    # endregion Action hail
    # =======================================

    # =======================================
    # region Action pay_taxi
    @OompaAction
    def pay_taxi(self) -> Action:
        pass

    @pay_taxi.precondition
    def pay_taxi(self) -> Condition:
        precondition = self.owe.greater_than(0)
        return precondition

    @pay_taxi.effect
    def pay_taxi(self) -> Effect:
        effect = AndEffect(
            self.cash.decreased_by(self.owe),
            self.owe.decreased_by(self.owe),
        )
        return effect

    # endregion Action pay_taxi
    # =======================================

    # =======================================
    # region Method travel_by_foot
    @OompaMethod
    def travel_by_foot(self, destination: Location) -> GoalMethod:
        pass

    @travel_by_foot.goal
    def travel_by_foot(self, destination: Location) -> Condition:
        return self.location.equals(destination)

    @travel_by_foot.precondition
    def travel_by_foot(self, destination: Location) -> Condition:
        precondition = Comparison(
            self.map.distance[self.location, destination],
            LESS_THAN_EQUALS,
            Person.DEFAULT_MAX_WALKING_DISTANCE,
        )
        return precondition

    @travel_by_foot.body
    def travel_by_foot(self, destination: Location) -> TotalOrderGoalTaskNetwork:
        body = TotalOrderGoalTaskNetwork(
            self.walk_to(destination),
        )
        return body

    # endregion Method travel_by_foot
    # =======================================


class Taxi(Locatable, HasStateProperties, NamedHash):
    name: str = "Taxi"
    passenger: Person | None = StatePropertyFactory(None)
    __hash__ = NamedHash.__hash__

    def __init__(
        self,
        name: str,
        map: Map,
        location: Location,
        passenger: Person | None = None,
    ) -> None:
        self.name = name
        Locatable.__init__(self, map, location)
        self.passenger = passenger

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()

    @StaticStatePropertyFactory
    def fare(self, start: Location, end: Location) -> float:
        if start == end:
            return 0  # TODO rare if preconditions are correct; write tests for all cases; see #25
        distance = self.map.distance(start, end)
        fare = distance * 1.5
        return fare

    # =======================================
    # region Action transport

    @OompaAction
    def transport(self, person: Person, destination: Location) -> Action:
        pass

    @transport.precondition
    def transport(self, person: Person, destination: Location) -> Condition:
        precondition = AndCondition(
            person.location.not_equals(destination),
            self.location.equals(person.location),
            person.cash.greater_than_equals(self.fare[person.location, destination]),
        )
        return precondition

    @transport.effect
    def transport(self, person: Person, destination: Location) -> Effect:
        effect = AndEffect(
            person.owe.assigned(self.fare[person.location, destination]),
            person.location.assigned(destination),
            self.location.assigned(destination),
        )
        return effect

    # endregion Action transport
    # =======================================

    # =======================================
    # region Method travel_by_taxi
    @OompaMethod
    def travel_by_taxi(self, passenger: Person, destination: Location) -> GoalMethod:
        pass

    @travel_by_taxi.goal
    def travel_by_taxi(self, passenger: Person, destination: Location) -> Condition:
        goal = passenger.location.equals(destination)
        return goal

    @travel_by_taxi.precondition
    def travel_by_taxi(self, passenger: Person, destination: Location) -> Condition:
        return passenger.cash.gte(self.fare[passenger.location, destination])

    @travel_by_taxi.body
    def travel_by_taxi(self, passenger: Person, destination: Location) -> TotalOrderGoalTaskNetwork:
        body = TotalOrderGoalTaskNetwork(
            passenger.hail(self),
            self.transport(passenger, destination),
            passenger.pay_taxi(),
        )
        return body

    # endregion Method travel_by_taxi
    # =======================================


@dataclass
class Distance:
    name: str
    start: Location
    end: Location

    def __init__(self, start: Location, end: Location, value: int | None = None) -> None:
        self.name = "distance"
        self.start = start
        self.end = end
        self.value = value

    def __str__(self) -> str:
        return f"{self.name}({self.start},{self.end}) = {self.value}"

    def __repr__(self) -> str:
        return self.__str__()


class Map(AbstractNamed):
    # distance: int = RelationPropertyDescriptor[list[Location, Location], int]()

    def __init__(self, name) -> None:
        AbstractNamed.__init__(self, name)
        self.locations: list[Location] = []
        self.edges: dict[(Location, Location), Distance] = {}

    def add_edge(self, loc1: Location, loc2: Location, value: int, symmetric: bool = True):
        args = (loc1, loc2)
        literal = Distance(loc1, loc2, value)
        self.edges[args] = literal
        logger.debug(f"added edge: {literal}")
        if symmetric:
            args = (loc2, loc1)
            literal = Distance(loc2, loc1, value)
            self.edges[args] = literal
            logger.debug(f"added edge: {literal}")

    @StaticStatePropertyFactory
    def distance(self, start: Location, end: Location) -> int | None:
        """Returns the distance of two connected locations or None if they are disconnected."""
        arg = (start, end)
        if arg in self.edges:
            edge: Distance = self.edges[arg]
            return edge.value
        return None
