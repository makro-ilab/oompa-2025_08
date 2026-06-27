"""OOMPA version of the Depot domain."""

from __future__ import annotations

from typing import override

from makro_utils.log_manager import LogManager
from oompa_types.action.action_descriptor import OompaAction
from oompa_types.condition.condition_bases import (
    AndCondition,
    Comparison,
    NullCondition,
    TypeMatches,
)
from oompa_types.domain.domain_bases import AbstractDomain
from oompa_types.domain.operator import NOT_EQUALS
from oompa_types.domain.problem import Problem
from oompa_types.effect.effect_bases import AndEffect, ConditionalEffect, ProbabilisticEffect
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method_bases import AbstractGoalMethod
from oompa_types.objects.named import AbstractNamed
from oompa_types.state_property.state_properties import HasStateProperties
from oompa_types.state_property.state_property_descriptor import StatePropertyFactory

logger = LogManager.get_logger("oompa.depot")
LogManager.set_root_level(LogManager.DEBUG)


class DepotDomain(AbstractDomain):
    def __init__(self) -> None:
        AbstractDomain.__init__(self, "depot")
        self.declare_type(Place)
        self.declare_type(Depot)
        self.declare_type(Distributor)
        self.declare_type(Moveable)
        self.declare_type(Surface)
        self.declare_type(Pallet)
        self.declare_type(Truck)
        self.declare_type(Crate)
        self.declare_type(Hoist)

    def test_create_problem_0(self):
        problem = self.instantiate_problem()
        depot_0 = self.test_add_depot(problem, "depot_0")
        distributor_0 = self.test_add_distributor(problem, "distributor_0")
        distributor_1 = self.test_add_distributor(problem, "distributor_1")

        hoist_0 = self.test_add_hoist(problem, "hoist_0", depot_0)
        hoist_1 = self.test_add_hoist(problem, "hoist_1", distributor_0)
        hoist_2 = self.test_add_hoist(problem, "hoist_2", distributor_1)

        pallet_0 = self.test_add_pallet(problem, "pallet_0", depot_0)
        pallet_1 = self.test_add_pallet(problem, "pallet_1", distributor_0)
        pallet_2 = self.test_add_pallet(problem, "pallet_2", distributor_1)

        truck_0 = self.test_add_truck(problem, "truck_0", distributor_0)
        truck_1 = self.test_add_truck(problem, "truck_1", depot_0)

        crate_0 = self.test_add_crate(problem, "crate_0", distributor_0, placed_on=pallet_1)
        crate_1 = self.test_add_crate(problem, "crate_1", depot_0, placed_on=pallet_0)
        return problem

    def test_add_depot(self, problem: Problem, name: str) -> Depot:
        depot = Depot(name)
        problem.add_objects(depot)
        return depot

    def test_add_distributor(self, problem: Problem, name: str) -> Distributor:
        distributor = Distributor(name)
        problem.add_objects(distributor)
        return distributor

    def test_add_truck(self, problem: Problem, name: str, place: Place) -> Truck:
        truck = Truck(name, place)
        problem.add_objects(truck)
        return truck

    def test_add_hoist(
        self, problem: Problem, name: str, place: Place, holding: Crate = None
    ) -> Hoist:
        hoist = Hoist(name, place, holding)
        problem.add_objects(hoist)
        return hoist

    def test_add_pallet(self, problem: Problem, name: str, place: Place) -> Pallet:
        pallet = Pallet(name, place)
        problem.add_objects(pallet)
        return pallet

    def test_add_crate(
        self,
        problem: Problem,
        name: str,
        at: Place,
        placed_on: Surface | Hoist | Truck | None = None,
        top: Crate | None = None,
    ) -> Crate:
        crate = Crate(name, at, placed_on, top)
        problem.add_objects(crate)
        return crate


class Place(AbstractNamed):
    def __init__(self, name: str):
        AbstractNamed.__init__(self, name)


class Depot(Place):
    def __init__(self, name):
        Place.__init__(self, name)


class Distributor(Place):
    def __init__(self, name):
        Place.__init__(self, name)


class Locatable(HasStateProperties):
    at: Place = StatePropertyFactory()

    def __init__(self, at: Place):
        self.at = at


class Surface(Locatable, HasStateProperties):
    top: Crate | None = StatePropertyFactory(None)
    height: int = StatePropertyFactory(0)

    def __init__(self, top: Crate | None = None):
        self.top = top

    def init_add_crate(self, crate: Crate):
        self.top = crate
        crate.on = self


class Located(Locatable, AbstractNamed, HasStateProperties):
    """Indicates the location of an object that does not move."""

    def __init__(self, name, at: Place):
        AbstractNamed.__init__(self, name)
        Locatable.__init__(self, at)
        self.at.freeze()


class Pallet(Located, Surface):
    """Holds containers, which can be stacked up to three high."""

    def __init__(self, name: str, at: Place, top: Crate = None):
        Located.__init__(self, name, at)
        Surface.__init__(self, top)


class Hoist(Located, HasStateProperties):
    holding: Crate | None = StatePropertyFactory(None)
    MAX_STACK_HEIGHT: int = StatePropertyFactory(3)

    def __init__(self, name: str, at: Place, holding: Crate = None) -> None:
        Located.__init__(self, name, at)
        if holding is not None:
            self.init_add_crate(holding)

    def init_add_crate(self, crate: Crate):
        self.holding = crate
        crate.on = self

    # =======================================================
    # region action lift

    @OompaAction
    def lift(self, crate: Crate):
        """Lifts a Crate off of its current Surface."""
        pass

    @lift.precondition
    def lift(self, crate: Crate):
        return AndCondition(
            crate.at.equals(self.at),
            self.holding.equals(None),
            crate.top.equals(None),
        )

    @lift.effect
    def lift(self, crate: Crate):
        return AndEffect(
            self.holding.assigned(crate),
            ConditionalEffect(TypeMatches(crate.on, Surface), crate.on.top.assigned(None)),
            crate.on.assigned(self),
            crate.height.assigned(0),
        )

    # endregion action lift
    # =======================================================

    # =======================================================
    # region action drop

    @OompaAction
    def drop(self, surface: Surface):
        """Drops the held Crate on the surface."""
        pass

    @drop.precondition
    def drop(self, surface: Surface):
        return AndCondition(
            self.at.equals(surface.at),
            self.holding.not_equals(None),
            surface.top.equals(None),
            surface.height.less_than(self.MAX_STACK_HEIGHT),
        )

    @drop.effect
    def drop(self, surface: Surface):
        return AndEffect(
            surface.top.assigned(self.holding),
            self.holding.at.assigned(surface.at),
            self.holding.top.assigned(None),
            self.holding.height.assigned(surface.height),
            self.holding.height.increased_by(1),
            self.holding.assigned(None),
        )

    # endregion action drop
    # =======================================================

    # =======================================================
    # region action load_unsupervised

    @OompaAction
    def load_unsupervised(self, truck: Truck):
        """Loads the held Crate onto Truck."""
        pass

    @load_unsupervised.precondition
    def load_unsupervised(self, truck: Truck):
        return AndCondition(
            self.holding.equals(None),
            truck.at.equals(self.at),
        )

    @load_unsupervised.effect
    def load_unsupervised(self, truck: Truck):
        success = AndEffect(
            truck.crate.assigned(self.holding),
            self.holding.assigned(None),
        )
        failure = SupervisedJobs.supervisor_needed(self, self.holding, truck).assigned(True)
        return ProbabilisticEffect(
            (success, 0.99),
            (failure, 0.01),
        )

    # endregion action load_unsupervised
    # =======================================================

    # =======================================================
    # region action load_supervised

    @OompaAction
    def load_supervised(self, truck: Truck):
        pass

    @load_supervised.precondition
    def load_supervised(self, truck: Truck):
        return AndCondition(
            self.holding.equals(None),
            truck.at.equals(self.at),
            SupervisedJobs.supervisor_needed(self, self.holding, truck).equals(True),
        )

    @load_supervised.effect
    def load_supervised(self, truck: Truck):
        return AndEffect(
            truck.crate.assigned(self.holding),
            self.holding.assigned(None),
            SupervisedJobs.supervisor_needed(self, self.holding, truck).assigned(False),
        )

    # endregion action load_supervised
    # =======================================================

    # =======================================================
    # region action unload_unsupervised

    @OompaAction
    def unload_unsupervised(self, truck: Truck):
        pass

    @unload_unsupervised.precondition
    def unload_unsupervised(self, truck: Truck):
        return AndCondition(
            self.holding.not_equals(None),
            truck.at.equals(self.at),
            SupervisedJobs.supervisor_needed(self, truck.crate, truck).equals(False),
        )

    @unload_unsupervised.effect
    def unload_unsupervised(self, truck: Truck):
        success = AndEffect(
            self.holding.assigned(truck.crate),
            truck.crate.assigned(None),
            self.holding.on.assigned(self),
            self.holding.on.assigned(self.at),
        )
        failure = SupervisedJobs.supervisor_needed(self, truck.crate, truck).equals(True)
        return ProbabilisticEffect((success, 0.5), (failure, 0.5))

    # endregion action unload_unsupervised
    # =======================================================

    # =======================================================
    # region action unload_supervised

    @OompaAction
    def unload_supervised(self, truck: Truck):
        pass

    @unload_supervised.precondition
    def unload_supervised(self, truck: Truck):
        return AndCondition(
            self.holding.not_equals(None),
            truck.at.equals(self.at),
            SupervisedJobs.supervisor_needed(self, truck.crate, truck).equals(True),
        )

    @unload_supervised.effect
    def unload_supervised(self, truck: Truck):
        return AndEffect(
            self.holding.assigned(truck.crate),
            truck.crate.assigned(None),
            self.holding.on.assigned(self),
            self.holding.on.assigned(self.at),
        )

    # endregion action unload_supervised
    # =======================================================


class Moveable(Locatable, AbstractNamed, HasStateProperties):
    def __init__(self, name: str, at: Place):
        AbstractNamed.__init__(self, name)
        self.at = at


class Crate(Moveable, Surface, HasStateProperties):
    """A can be on a surface, crane, or truck and it has its own surface.

    It is slight odd for the crate to have a place, since it could also be the case that its
    location is on any surface, which means the place could be inferred. Using both a place and
    a surface

    """

    on: Surface | Hoist | Truck | None = StatePropertyFactory(None)

    def __init__(
        self,
        name: str,
        at: Place,
        placed_on: Surface | Hoist | Truck | None = None,
        top: Crate = None,
    ) -> None:
        Moveable.__init__(self, name, at)
        Surface.__init__(self, top=top)
        if placed_on is not None:
            placed_on.init_add_crate(self)
        if top is not None:
            self.init_add_crate(top)


class Truck(Moveable, HasStateProperties):
    """Trucks are Moveable and can carry one Crate."""

    crate: Crate | None = StatePropertyFactory(None)

    def __init__(self, name: str, at: Place) -> None:
        Moveable.__init__(self, name, at)

    def init_add_crate(self, crate: Crate):
        self.crate = crate
        crate.on = self

    # =======================================================
    # region action drive

    @OompaAction
    def drive(self, start: Place, end: Place):
        pass

    @drive.precondition
    def drive(self, start: Place, end: Place):
        return AndCondition(
            Comparison(start, NOT_EQUALS, end),
            self.place.equals(start),
        )

    @drive.effect
    def drive(self, end: Place):
        return self.place.assigned(end)

    # endregion action drive
    # =======================================================


class SupervisorRequired(AbstractNamed):
    hoist: Hoist
    crate: Crate
    truck: Truck

    def __init__(self, hoist: Hoist, crate: Crate, truck: Truck) -> None:
        AbstractNamed.__init__(self, "supervisor_needed")
        self.hoist = hoist
        self.crate = crate
        self.truck = truck

    def __str__(self) -> str:
        return f"{self.name}({self.hoist},{self.crate},{self.truck}) = {self._value}"

    def __repr__(self) -> str:
        return self.__str__()


class SupervisedJobs:
    def __init__(self) -> None:
        self.jobs: dict[tuple[Hoist, Crate, Truck], SupervisorRequired] = {}

    @StatePropertyFactory
    def supervisor_needed(self, hoist: Hoist, crate: Crate, truck: Truck) -> bool:
        arg = (hoist, crate, truck)
        if arg not in self.jobs:
            self.jobs[arg] = SupervisorRequired(*arg)
        return self.jobs[arg].value


class GetCrate(AbstractGoalMethod[DepotDomain, "GetCrate"]):
    crate: Crate
    surface: Surface

    @override
    @property
    def args_types(self) -> list[type]:
        return [Crate, Surface]

    @property
    def goal(self):
        is_on = self.domain.is_on
        return is_on(self.crate).equals(self.surface)

    @override
    @property
    def precondition(self):
        is_at = self.domain.is_at
        return is_at(self.crate).not_equals(is_at(self.surface))

    @override
    @property
    def body(self):
        is_in = self.domain.is_in
        is_at = self.domain.is_at
        is_on = self.domain.is_on
        is_clear = self.domain.is_clear
        body = TotalOrderGoalTaskNetwork(
            is_clear(self.crate).equals(True),
            is_in(self.crate).not_equals(None),
            is_at(is_in(self.crate)).equals(is_at(self.surface)),
            is_clear(self.surface).equals(True),
            is_on(self.crate).equals(self.surface),
        )
        return body

    def __call__(
        self,
        crate: Crate,
        surface: Surface,
    ):
        instance = self.template.instance()
        instance.crate = crate
        instance.surface = surface
        return instance


class PutOn(AbstractGoalMethod[DepotDomain, "PutOn"]):
    crate: Crate
    surface: Surface

    @override
    @property
    def args_types(self) -> list[type]:
        return [Crate, Surface]

    @property
    def goal(self):
        is_on = self.domain.is_on
        return is_on(self.crate).equals(self.surface)

    @override
    @property
    def precondition(self):
        is_at = self.domain.is_at
        if self.crate == self.surface:
            return NullCondition()
        else:
            return is_at(self.crate).equals(is_at(self.surface))

    @override
    @property
    def body(self):
        is_on = self.domain.is_on
        is_clear = self.domain.is_clear
        holding = self.domain.holding
        body = TotalOrderGoalTaskNetwork(
            is_clear(self.crate).equals(True),
            is_clear(self.surface).equals(True),
            holding(self.hoist).equals(self.crate),
            is_on(self.crate).equals(self.surface),
        )
        return body

    def __call__(
        self,
        crate: Crate,
        surface: Surface,
    ):
        instance = self.template.instance()
        instance.crate = crate
        instance.surface = surface
        return instance


class LoadTruck(AbstractGoalMethod[DepotDomain, "LoadTruck"]):
    crate: Crate
    truck: Truck
    hoist: Hoist

    @override
    @property
    def args_types(self) -> list[type]:
        return [Crate, Truck, Hoist]

    @property
    def goal(self):
        is_in = self.domain.is_in
        return is_in(self.crate).equals(self.truck)

    @override
    @property
    def precondition(self):
        is_in = self.domain.is_in
        is_at = self.domain.is_at
        return AndCondition(
            is_in(self.crate).equals(None),
            is_at(self.crate).equals(is_at(self.hoist)),
        )

    @override
    @property
    def body(self):
        is_at = self.domain.is_at
        is_clear = self.domain.is_clear
        is_in = self.domain.is_in
        holding = self.domain.holding
        body = TotalOrderGoalTaskNetwork(
            is_at(self.truck).equals(is_at(self.hoist)),
            is_clear(self.crate).equals(True),
            holding(self.hoist).equals(self.crate),
            is_in(self.crate).equals(self.truck),
        )
        return body

    def __call__(
        self,
        crate: Crate,
        truck: Truck,
        hoist: Hoist,
    ):
        instance = self.template.instance()
        instance.crate = crate
        instance.truck = truck
        instance.hoist = hoist
        return instance


class UnloadTruck(AbstractGoalMethod[DepotDomain, "UnloadTruck"]):
    crate: Crate
    surface: Surface
    hoist: Hoist

    @override
    @property
    def args_types(self) -> list[type]:
        return [Crate, Surface, Hoist]

    @property
    def goal(self):
        is_on = self.domain.is_on
        return is_on(self.crate).equals(self.surface)

    @override
    @property
    def precondition(self):
        is_in = self.domain.is_in
        is_at = self.domain.is_at
        return AndCondition(
            is_in(self.crate).not_equals(None),
            is_at(is_in(self.crate)).equals(is_at(self.hoist)),
            is_at(self.hoist).equals(is_at(self.surface)),
        )

    @override
    @property
    def body(self):
        is_clear = self.domain.is_clear
        is_on = self.domain.is_on
        holding = self.domain.holding
        body = TotalOrderGoalTaskNetwork(
            is_clear(self.surface).equals(True),
            holding(self.hoist).equals(self.crate),
            is_on(self.crate).equals(self.surface),
        )
        return body

    def __call__(
        self,
        crate: Crate,
        surface: Surface,
        hoist: Hoist,
    ):
        instance = self.template.instance()
        instance.crate = crate
        instance.surface = surface
        instance.hoist = hoist
        return instance
