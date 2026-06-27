"""A Python 3.12.5+ OOMPA version of the Transport domain.

This is an OOMPA version of the FOND HTN test domain from the Koala Planner, provided at
https://github.com/koala-planner/domains
"""

from __future__ import annotations

from makro_utils.log_manager import LogManager
from oompa_types.action.action_descriptor import OompaAction
from oompa_types.action.actions import HasOompaActions
from oompa_types.condition.condition_bases import AndCondition
from oompa_types.domain.domain_bases import AbstractDomain
from oompa_types.domain.problem import Problem
from oompa_types.effect.effect_bases import AndEffect
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method_descriptor import OompaMethod
from oompa_types.method.methods import HasOompaMethods
from oompa_types.objects.named import AbstractNamed
from oompa_types.state_property.state_properties import HasStateProperties
from oompa_types.state_property.state_property_descriptor import StatePropertyFactory

logger = LogManager.get_logger("oompa.test.transport")
LogManager.set_root_level(LogManager.DEBUG)


class TransportDomain(AbstractDomain):
    def __init__(self) -> None:
        AbstractDomain.__init__(self, "transport")
        self.declare_type(Location)
        self.declare_type(Package)
        self.declare_type(Vehicle)
        self.declare_type(Map)

    @property
    def problem(self) -> TransportDomain:
        return self._problem

    def test_add_location(self, problem: Problem, name: str) -> Location:
        loc = Location(name)
        problem.map.add_location(loc)
        problem.add_objects(loc)
        return loc

    def test_add_road(self, problem: Problem, loc1: Location, loc2: Location) -> Road:
        arg = (loc1, loc2)
        problem.map.add_edge(*arg)
        return problem.map.edges[arg]

    def test_add_vehicle(self, problem: Problem, name: str, capacity: int, location: Location):
        vehicle = Vehicle(name, capacity, problem.map, location)
        problem.add_objects(vehicle)
        return vehicle

    def test_add_package(self, problem: Problem, name: str, location: Location):
        package = Package(name, location)
        problem.add_objects(package)
        return package

    def test_create_problem_0(self):
        problem = self.instantiate_problem()
        problem.map = Map("map_1")

        loc_0 = self.test_add_location(problem, "loc_0")
        loc_1 = self.test_add_location(problem, "loc_1")
        loc_2 = self.test_add_location(problem, "loc_2")
        self.test_add_road(problem, loc_0, loc_1)
        self.test_add_road(problem, loc_1, loc_0)
        self.test_add_road(problem, loc_1, loc_2)
        self.test_add_road(problem, loc_2, loc_1)
        self.test_add_vehicle(problem, "veh_0", 2, loc_2)
        self.test_add_package(problem, "p_0", loc_1)
        self.test_add_package(problem, "p_1", loc_1)
        return problem


class Location(AbstractNamed):
    def __init__(self, name: str):
        AbstractNamed.__init__(self, name)


# TODO make into dataclass
class Locatable(HasStateProperties):
    map: Map
    location: Location | None = StatePropertyFactory(None)

    def __init__(self, map: Map, location: Location):
        self.map: Map = map
        self.location: Location = location


class Vehicle(Locatable, AbstractNamed, HasStateProperties, HasOompaActions, HasOompaMethods):
    capacity: int = StatePropertyFactory(1)
    packages: set[Package] = StatePropertyFactory(default_factory=set)

    def __init__(self, name: str, capacity: int, map: Map, location: Location) -> None:
        AbstractNamed.__init__(self, name)
        Locatable.__init__(self, map, location)
        self.capacity = capacity

    # ============================================================
    # region Action drive

    @OompaAction
    def drive(self, start: Location, destination: Location):
        pass

    @drive.precondition
    def drive(self, start: Location, destination: Location):
        precondition = AndCondition(
            self.location.equals(self.start),
            self.map.road(start, destination).exists(),
        )
        return precondition

    @drive.effect
    def drive(self, destination: Location):
        return self.location.assigned(destination)

    # endregion Action drive
    # ============================================================

    # ============================================================
    # region Action pick_up

    @OompaAction
    def pick_up(self, package: Package):
        pass

    @pick_up.precondition
    def pick_up(self, package: Package):
        precondition = AndCondition(
            self.location.equals(package.location),
            self.packages.fewer_than(self.capacity),
        )
        return precondition

    @pick_up.effect
    def pick_up(self, package: Package):
        return AndEffect(
            self.packages.inserts(package),
            package.location.assigned(None),
            package.vehicle.assigned(self),
        )

    # endregion Action pick_up
    # ============================================================

    # ============================================================
    # region Action drop_off

    @OompaAction
    def drop_off(self, package: Package, destination: Location):
        pass

    @drop_off.precondition
    def drop_off(self, package: Package):
        return package.vehicle.equals(self)

    @drop_off.effect
    def drop_off(self, package: Package):
        effect = AndEffect(
            self.packages.removes(package),
            package.vehicle.assigned(None),
            package.location.assigned(self.location),
        )
        return effect

    # endregion Action drop_off
    # ============================================================

    # ============================================================
    # region method deliver

    @OompaMethod
    def deliver(self, package: Package, destination: Location):
        pass

    @deliver.goal
    def deliver(self, package: Package, destination: Location):
        return package.location.equals(destination)

    @deliver.precondition
    def deliver(self, package: Package, destination: Location):
        return package.location.not_equals(destination)

    @deliver.body
    def deliver(self, package: Package, destination: Location):
        body = TotalOrderGoalTaskNetwork(
            self.location.equals(package.location),
            package.vehicle.equals(self),
            self.location.equals(destination),
            package.location.equals(destination),
        )
        return body

    # endregion method deliver
    # ============================================================


class Package(Locatable, AbstractNamed, HasStateProperties):
    vehicle: Vehicle | None = StatePropertyFactory(None)

    def __init__(self, name: str, location: Location | Vehicle) -> None:
        AbstractNamed.__init__(self, name)
        Locatable.__init__(self, map, location)


class Road(AbstractNamed):
    start: Location
    end: Location

    def __init__(self, start: Location, end: Location):
        AbstractNamed.__init__(self, f"road_{start}_{end}")
        self.start = start
        self.end = end
        self.value = True


class Map(AbstractNamed):
    def __init__(self, name: str) -> None:
        AbstractNamed.__init__(self, name)
        self.locations: set[Location] = []
        self.edges: dict[(Location, Location), Road] = {}

    def add_edge(self, loc1: Location, loc2: Location):
        if loc1 in self.locations and loc2 in self.locations:
            args = (loc1, loc2)
            self.edges[args] = Road(*args)

    def add_location(self, loc: Location):
        self.locations.append(loc)

    @StatePropertyFactory
    def road(self, loc1: Location, loc2: Location) -> Road:
        arg = (loc1, loc2)
        if arg in self.edges:
            edge: Road = self.edges[arg]
            return edge.value
