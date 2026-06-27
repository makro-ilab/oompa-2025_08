"""A Python 3.12.5+ OOMPA version of the travel domain from GTPyhop.

This is an extended version of the test domain from GTPyhop, provided at
https://github.com/dananau/GTPyhop/blob/main/Examples/simple_htn.py

The extended version allows taxis to transport a set of passengers.
"""

from __future__ import annotations

from makro_utils.log_manager import LogManager
from oompa_types.action.action_descriptor import OompaAction
from oompa_types.condition.condition_bases import AndCondition, ForAllCondition
from oompa_types.domain.problem_bases import AbstractProblem
from oompa_types.effect.effect_bases import AndEffect, ForAllEffect
from oompa_types.objects.named_hash import NamedHash
from oompa_types.state_property.state_property_descriptor import (
    StatePropertyFactory,
    StaticStatePropertyFactory,
)
from tests.simple_travel_domain import (
    LOC_HOME_A,
    LOC_HOME_B,
    LOC_NONE,
    LOC_PARK,
    LOC_STATION,
    Locatable,
    Location,
    Person,
    SimpleTravelDomain,
)

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class TaxiVan(Locatable, NamedHash):
    name: str
    passengers: set[Person] = StatePropertyFactory(default_factory=set)
    MAX_CAPACITY: int = StatePropertyFactory(6)
    __hash__ = NamedHash.__hash__  # required because dataclasses don't set this by default

    def __init__(self, name, map, location):
        self.name = name
        super().__init__(map, location)

    @StaticStatePropertyFactory
    def fare(self, start: Location, end: Location) -> float:
        if start == end:
            return 0  # TODO rare if preconditions are correct; write tests for all cases; see #25
        distance = self.map.distance(start, end)
        return distance * 1.5

    # =======================================
    # region Action pickup

    @OompaAction
    def pickup(self, person: Person):
        pass

    @pickup.precondition
    def pickup(self, person: Person):
        precondition = AndCondition(
            self.passengers.fewer_than(self.MAX_CAPACITY),
            self.location.equals(person.location),
        )
        return precondition

    @pickup.effect
    def pickup(self, person: Person):
        effect = AndEffect(
            person.origin.assigned(person.location),
            person.location.assigned(LOC_NONE),
            self.passengers.inserts(person),
        )
        return effect

    @pickup.execute
    def pickup(self, person: Person):
        self.passengers.add(person)
        person.taxi = self
        person.location = LOC_NONE

    # endregion Action pickup
    # =======================================

    # =======================================
    # region Action dropoff
    @OompaAction
    def drop_off(self, person: Person, destination: Location):
        pass

    @drop_off.precondition
    def drop_off(self, person: Person, destination: Location):
        precondition = AndCondition(
            self.passengers.contains(person),
            person.cash.gte(self.fare[person.origin, destination]),
        )
        return precondition

    @drop_off.effect
    def drop_off(self, person: Person, destination: Location):
        effect = AndEffect(
            person.owe.assigned(self.fare[person.origin, destination]),
            self.location.assigned(destination),
            self.passengers.removes(person),
            person.location.assigned(destination),
        )
        return effect

    @drop_off.execute
    def drop_off(self, person: Person):
        self.passengers.remove(person)
        person.place = self.location

    # endregion Action drop_off
    # =======================================

    # =======================================
    # region Action drop_off_all
    @OompaAction
    def drop_off_all(self, destination: Location):
        pass

    @drop_off_all.precondition
    def drop_off_all(self, destination: Location):
        precondition = ForAllCondition(
            self.passengers,
            lambda p: p.cash.gte(self.fare[p.origin, destination]),
        )
        return precondition

    @drop_off_all.effect
    def drop_off_all(self, destination: Location):
        effect = AndEffect(
            self.location.assigned(destination),
            ForAllEffect(
                self.passengers,
                lambda p: AndEffect(
                    p.owe.assigned(self.fare[p.origin, destination]),
                    p.moves_to(destination),
                    self.passengers.removes(p),
                ),
            ),
        )
        return effect

    @drop_off_all.execute
    def drop_off_all(self, person: Person):
        self.passengers.remove(person)
        person.place = self.location

    # endregion Action drop_off_all
    # =======================================

    def leave_all(self):
        for person in self.passengers:
            self.drop(person)


"""
# ================================================================
# region Methods

class Rideshare(AbstractGoalMethod[ExtendedTravelDomain, "TravelByTaxi"], Parameters):
    people: list[Person] = ParameterDescriptor[list[Person]]()
    taxi: TaxiVan = ParameterDescriptor[TaxiVan]()
    destination: Location = ParameterDescriptor[Location]()

    @override
    @property
    def arg_types(self) -> list[type]:
        return [list[Person], TaxiVan, Location]

    def goal(self):
        ForAllCondition(self.people, lambda x: place_of(x).equals(self.destination))

    @override
    @property
    def precondition(self):
        precondition = ForAllCondition(
            self.people,
            lambda x: cash_of(self.person).greater_than_equals(
                taxi_van_fare(self.taxi, place_of(x), self.destination)
            ),
        )

        return precondition

    @override
    @property
    def body(self):
        body = [
            ForAllAction(self.people, lambda x: self.domain.action(PickUp)(self.taxi, self.person)),
            self.domain.action(DropOffAll)(self.taxi, self.destination),
        ]
        return body

    def __call__(
        self,
        people: list[Person],
        taxi: TaxiVan,
        destination: Location,
    ):
        instance: Rideshare = self.template.instance()
        instance.people = people
        instance.taxi = taxi
        instance.destination = destination
        return instance


# endregion Methods
# ================================================================
"""


class ExtendedTravelDomain(SimpleTravelDomain):
    def __init__(self) -> None:
        SimpleTravelDomain.__init__(self, name="extended_travel")
        self.declare_type(TaxiVan)

        """
        self.declare_goal_method(Rideshare)
        """

    def test_add_alice_and_taxivan1(self, problem: AbstractProblem):
        alice = Person(name="alice", map=problem.map, cash=20, location=LOC_HOME_A)
        taxivan1 = TaxiVan(name="taxivan1", map=problem.map, location=LOC_PARK)
        problem.add_objects(alice, taxivan1)

    def test_add_bob_and_taxivan2(self, problem: AbstractProblem):
        bob = Person(name="bob", map=problem.map, cash=15, location=LOC_HOME_B)
        taxivan2 = TaxiVan(name="taxivan2", map=problem.map, location=LOC_STATION)
        problem.add_objects(bob, taxivan2)
