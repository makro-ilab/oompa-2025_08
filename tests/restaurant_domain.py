"""Implements the Restaurant Script from Scripts, Plans, and Understanding (Schank, 1977, pp. 42ff).

Roughly, here is the script

Script: RESTAURANT
Track: Coffee Shop
Props: Tables, Menu, F-Food, Check, Money

Roles:  P-Patron (formerly S-Customer)
        V-Server (formerly W-Waiter)
        C-Cook
        M-Cashier
        O-Owner

Entry conditions:   P is hungry.
                    P has money.

Results:    P has less money
            O has more money
            P is not hungry


Scene 1: Entering
    P PTRANS P into restaurant
    P ATTEND eyes to tables
    P MBUILD where to sit
    P PTRANS P to table
    P MOVES to sitting position

Scene 2: Ordering

    a.1: (menu on table)
        P PTRANS menu to P
        goto 2.b

    a.2: (V brings menu)
        V PTRANS V to table
        V ATRANS menu to P
        goto 2.b

    a.3: (P asks for menu)
        P MTRANS signal to V
        V PTRANS V to table
        P MTRANS 'need menu' to V
        V PTRANS V to menu
        goto 2.b

    b: (P reviews menu)
        P MTRANS food list to CP(S)

    c: (P orders F)
        P MBUILD choice of F
        P MTRANS signal to V
        V PTRANS V to table
        P MTRANS 'I want F' to V

    d: (V places order with C)kl;
        V PTRANS V to C
        V MTRANS (ATRANS F) to C

    e.1: (food item is not available)
        C MTRANS 'no F' to V
        V PTRANS V to P
        V MTRANS 'no F' to P
        goto 2.c  or goto 4.no_pay_path

    g.2: (food item is available)
        C DO (prepare F script)
        goto 3

"""

from __future__ import annotations

from enum import StrEnum, auto

from oompa_types.action.action_descriptor import OompaAction
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import AndCondition
from oompa_types.domain.domain_bases import AbstractDomain
from oompa_types.domain.problem_bases import AbstractProblem
from oompa_types.domain.problem_helpers import CreatesNewObjects
from oompa_types.effect.effect_bases import AndEffect, InsertNewObjectEffect
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method import GoalMethod
from oompa_types.method.goal_method_descriptor import OompaMethod
from oompa_types.method.methods import HasOompaMethods
from oompa_types.objects.named import AbstractNamed
from oompa_types.state_property.state_properties import HasStateProperties
from oompa_types.state_property.state_property_descriptor import StatePropertyFactory


class RestaurantDomain(AbstractDomain):
    def __init__(self) -> None:
        AbstractDomain.__init__(self, "restaurant")
        self.declare_type(Table)
        self.declare_type(MenuItem)
        self.declare_type(Dish)
        self.declare_type(Menu)
        self.declare_type(Check)
        self.declare_type(Person)
        self.declare_type(Cook)
        self.declare_type(Owner)
        self.declare_type(Cashier)
        self.declare_type(Server)
        self.declare_type(Patron)

    def test_create_simple_problem(self):
        problem = self.instantiate_problem()

        sam = problem.sam = Server("sam")
        menu = problem.menu_breakfast = Menu("menu_breakfast")
        special = problem.special = MenuItem("veggie_omelette", 12)
        menu.add_special(special)
        pat = problem.pat = Patron("pat")
        chris = problem.chris = Cook("chris")
        table1 = problem.table1 = Table("table1", server=problem.sam, menu=problem.menu_breakfast)
        return problem


class Table(AbstractNamed, HasStateProperties):
    server: Server = StatePropertyFactory()
    occupied: bool = StatePropertyFactory(False)
    menu: Menu | None = StatePropertyFactory(None)

    def __init__(self, name, server: Server, menu: Menu, occupied=False):
        super().__init__(name)
        self.server = server
        self.menu = menu
        self.occupied = occupied

    def init_add_menu(self, menu: Menu):
        self.menu = menu

    def init_add_patron(self):
        self.occupied = True


class MenuItem(AbstractNamed, HasStateProperties):
    class Status(StrEnum):
        AVAILABLE = auto()
        UNAVAILABLE = auto()

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.__str__()

    cost: int = StatePropertyFactory()
    status: Status = StatePropertyFactory(Status.AVAILABLE)

    def __init__(self, name, cost: int, status: Status = Status.AVAILABLE):
        super().__init__(name)
        self.cost = cost
        self.status = status


class Menu(AbstractNamed):
    items: list[MenuItem] = StatePropertyFactory(default_factory=list)
    special: MenuItem | None = StatePropertyFactory(None)

    def __init__(self, name):
        super().__init__(name)

    def add_item(self, item: MenuItem):
        self.items.append(item)

    def add_special(self, special: MenuItem):
        self.special = special


class OrderedItem(AbstractNamed, HasStateProperties):
    class Status(StrEnum):
        UNORDERED = auto()
        SELECTED_BY_PATRON = auto()
        ORDERED = auto()
        PREPARING = auto()
        PREPARED = auto()
        TOTALED = auto()

    PREFIX = "ordered_"

    patron: Patron = StatePropertyFactory()
    item: MenuItem = StatePropertyFactory()
    status: Status = StatePropertyFactory(Status.UNORDERED)
    dish: Dish | None = StatePropertyFactory(None)

    def __init__(self, patron: Patron, item: MenuItem):
        super().__init__(OrderedItem.PREFIX + item.name)
        self.patron = patron
        self.item = item


class Dish(AbstractNamed, HasStateProperties):
    class Status(StrEnum):
        READY = ()
        DELIVERED = ()
        EATEN = ()
        BUSSED = ()

    status: Status = StatePropertyFactory(Status.READY)

    def __init__(self, name, cost: int, status: Status = Status.READY):
        super().__init__(name)
        self.cost = cost
        self.status = status


class Person(AbstractNamed): ...


class Cook(Person, CreatesNewObjects):
    problem: AbstractProblem
    ordered: OrderedItem | None = StatePropertyFactory(None)
    prepared: list[Dish] = StatePropertyFactory(default_factory=list)

    def __init__(self, name):
        AbstractNamed.__init__(self, name)

    # =======================================================
    # region action prepare

    @OompaAction
    def prepare(self):
        pass

    @prepare.precondition
    def prepare(self):
        return AndCondition(
            self.ordered.not_equals(None),
        )

    @prepare.effect
    def prepare(self):
        return AndEffect(
            self.ordered.status.assigned(OrderedItem.Status.PREPARED),
            InsertNewObjectEffect(
                self,
                Cook.prepared,
                Dish,
                [self.ordered.name, self.ordered.cost, Dish.Status.READY],
                self.problem,
                {},
            ),
        )

    # endregion action prepare
    # =======================================================


class Owner(Person):
    def __init__(self, name):
        AbstractNamed.__init__(self, name)


class Check(AbstractNamed, HasStateProperties):
    table: Table
    orders: list[OrderedItem]
    due: int = StatePropertyFactory(0)
    is_paid: bool = StatePropertyFactory(False)


class Cashier(Person):
    def __init__(self, name):
        AbstractNamed.__init__(self, name)


class Server(Person, HasStateProperties):
    near_to: Person | None = StatePropertyFactory(None)
    order: OrderedItem | None = StatePropertyFactory(None)
    menu: Menu | None = StatePropertyFactory(None)
    check: Check | None = StatePropertyFactory(None)

    def __init__(self, name):
        AbstractNamed.__init__(self, name)

    # =======================================================
    # region action move_near

    @OompaAction
    def move_near(self, person: Person):
        pass

    @move_near.precondition
    def move_near(self, person: Person):
        return AndCondition(
            self.near_to.not_equals(person),
        )

    @move_near.effect
    def move_near(self, person: Person):
        return AndEffect(
            self.near_to.assigned(person),
        )

    # endregion action move_near
    # =======================================================

    # =======================================================
    # region action convey_order

    @OompaAction
    def convey_order(self, cook: Cook):
        pass

    @convey_order.precondition
    def convey_order(self, cook: Cook):
        return AndCondition(
            self.order.not_equals(None),
            self.near_to.equals(cook),
        )

    @convey_order.effect
    def convey_order(self, cook: Cook):
        return AndEffect(
            self.order.status.assigned(OrderedItem.Status.PREPARING),
            cook.ordered.assigned(self.order),
        )

    # endregion action convey_order
    # =======================================================

    # =======================================================
    # region action pickup

    @OompaAction
    def pickup(self, dish: Dish):
        pass

    @pickup.precondition
    def pickup(self, dish: Dish):
        return AndCondition(
            condition,
        )

    @pickup.effect
    def pickup(self, dish: Dish):
        return AndEffect(
            effect,
        )

    # endregion action pickup
    # =======================================================


class Patron(Person, CreatesNewObjects, HasOompaMethods):
    problem: AbstractProblem
    money: int = StatePropertyFactory(50)
    is_hungry: bool = StatePropertyFactory(True)
    is_pleased: bool = StatePropertyFactory(False)
    table: Table | None = StatePropertyFactory(None)
    server: Server | None = StatePropertyFactory(None)
    menu: Menu | None = StatePropertyFactory(None)
    desired_order: OrderedItem | None = StatePropertyFactory(None)

    def __init__(self, name):
        AbstractNamed.__init__(self, name)

    # =======================================================
    # region action sit

    @OompaAction
    def sit(self, table: Table):
        pass

    @sit.precondition
    def sit(self, table: Table):
        return self.table.equals(None)

    @sit.effect
    def sit(self, table: Table):
        return AndEffect(
            self.table.assigned(table),
            self.server.assigned(table.server),
            table.occupied.assigned(True),
        )

    # endregion action sit
    # =======================================================

    # =======================================================
    # region action pickup_menu

    # TODO might also need put_down_menu, but we'll ignore it for now

    @OompaAction
    def pickup_menu(self):
        pass

    @pickup_menu.precondition
    def pickup_menu(self):
        return AndCondition(
            self.table.menu.not_equals(None),
            self.menu.equals(None),
        )

    @pickup_menu.effect
    def pickup_menu(self):
        return AndEffect(
            self.menu.assigned(self.table.menu),
        )

    # endregion action pickup_menu
    # =======================================================

    # =======================================================
    # region action review_menu

    @OompaAction
    def review_menu_for_special(self):
        pass

    @review_menu_for_special.precondition
    def review_menu_for_special(self):
        return AndCondition(
            self.menu.not_equals(None),
            self.desired_order.equals(None),
        )

    @review_menu_for_special.effect
    def review_menu_for_special(self):
        return AndEffect(
            InsertNewObjectEffect(
                self,
                self.desired_order,
                OrderedItem,
                [self, self.menu.special],
                self.problem,
                {},
            ),
            self.desired_order.status.assigned(OrderedItem.Status.SELECTED_BY_PATRON),
        )

    # endregion action review_menu
    # =======================================================

    # =======================================================
    # region action request_server

    @OompaAction
    def request_server(self):
        pass

    @request_server.precondition
    def request_server(self):
        return AndCondition(
            self.server.near_to.not_equals(self),
        )

    @request_server.effect
    def request_server(self):
        return AndEffect(
            self.server.near_to.assigned(self),
        )

    # endregion action request_server
    # =======================================================

    # =======================================================
    # region action place_order

    @OompaAction
    def place_order(self):
        pass

    @place_order.precondition
    def place_order(self):
        return AndCondition(
            self.desired_order.not_equals(None),
            self.server.near_to.equals(self),
        )

    @place_order.effect
    def place_order(self):
        return AndEffect(
            self.server.order.assigned(self.desired_order),
            self.desired_order.status.assigned(OrderedItem.Status.ORDERED),
        )

    # endregion action place_order
    # =======================================================

    # =======================================
    # region Method m_get_seated
    @OompaMethod
    def m_get_seated(self, table: Table) -> GoalMethod:
        pass

    @m_get_seated.goal
    def m_get_seated(self, table: Table) -> Condition:
        goal = self.table.equals(table)
        return goal

    @m_get_seated.precondition
    def m_get_seated(self, table: Table) -> Condition:
        return AndCondition(
            table.occupied.equals(False),
            self.table.equals(None),
        )

    @m_get_seated.body
    def m_get_seated(self, table: Table) -> TotalOrderGoalTaskNetwork:
        body = TotalOrderGoalTaskNetwork(
            self.sit(table),
        )
        return body

    # endregion Method m_get_seated
    # =======================================

    # =======================================
    # region Method m_order_special
    @OompaMethod
    def m_order_special(self, table: Table) -> GoalMethod:
        pass

    @m_order_special.goal
    def m_order_special(self, table: Table) -> Condition:
        goal = AndCondition(
            self.desired_order.not_equals(None),
            self.desired_order.status.equals(OrderedItem.Status.ORDERED),
        )
        return goal

    @m_order_special.precondition
    def m_order_special(self, table: Table) -> Condition:
        return AndCondition(
            self.desired_order.equals(None),
            table.menu.not_equals(None),
        )

    @m_order_special.body
    def m_order_special(self, table: Table) -> TotalOrderGoalTaskNetwork:
        body = TotalOrderGoalTaskNetwork(
            self.sit(table),
            self.pickup_menu(),
            self.review_menu_for_special(),
            self.request_server(),
            self.place_order(),
        )
        return body

    # endregion Method m_order_special
    # =======================================
