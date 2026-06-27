from __future__ import annotations

import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.condition.condition_bases import NULL_CONDITION, AndCondition, TrueCondition
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from tests.restaurant_domain import (
    Cook,
    Menu,
    MenuItem,
    OrderedItem,
    Patron,
    RestaurantDomain,
    Server,
    Table,
)
from tests.test_helpers import test_and_reset

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class TestRestaurant(unittest.TestCase):
    def test_patron_ordering(self):
        domain = RestaurantDomain()
        problem = domain.test_create_simple_problem()

        sam: Server = problem.sam
        menu: Menu = problem.menu_breakfast
        pat: Patron = problem.pat
        chris: Cook = problem.chris
        table1: Table = problem.table1
        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"s_0:\n{s_0}")

        pat_sit_at_table1 = pat.sit(table1)
        s_1 = s_0.apply(pat_sit_at_table1, result)
        test_and_reset(self, logger, result, s_0, s_1, pat.table.equals(table1))

        jon_grabs_menu = pat.pickup_menu()
        s_2 = s_1.apply(jon_grabs_menu, result)
        test_and_reset(self, logger, result, s_1, s_2, pat.menu.equals(menu))

        pat_reviews_menu = pat.review_menu_for_special()
        s_3 = s_2.apply(pat_reviews_menu, result)
        special_order = result.added[0]
        test_and_reset(self, logger, result, s_2, s_3, pat.desired_order.equals(special_order))

        sam_moves_to_pat = sam.move_near(pat)
        s_4 = s_3.apply(sam_moves_to_pat, result)
        test_and_reset(self, logger, result, s_3, s_4, sam.near_to.equals(pat))

        pat_orders_special = pat.place_order()
        s_5 = s_4.apply(pat_orders_special, result)
        test_and_reset(self, logger, result, s_4, s_5, sam.order.equals(special_order))

        sam_moves_to_chris = sam.move_near(chris)
        s_6 = s_5.apply(sam_moves_to_chris, result)
        test_and_reset(self, logger, result, s_5, s_6, sam.near_to.equals(chris))

        sam_tells_chris = sam.convey_order(chris)
        s_7 = s_6.apply(sam_tells_chris, result)
        test_and_reset(self, logger, result, s_6, s_7, chris.ordered.equals(special_order))

        logger.debug("Done!")

    def test_method_sit_at_table(self):
        domain = RestaurantDomain()
        problem = domain.test_create_simple_problem()

        sam = problem.sam
        menu = problem.menu_breakfast
        special = problem.special
        pat: Patron = problem.pat
        chris = problem.chris
        table1 = problem.table1

        g_pat_is_seated = pat.table.not_equals(None)
        gn_1 = TotalOrderGoalTaskNetwork(g_pat_is_seated)

        s_0 = problem.current_state()
        rel_app_methods = problem.get_relevant_and_applicable_goal_methods(gn_1, s_0)
        self.assertEqual(len(rel_app_methods), 1)
        method = rel_app_methods[0]

        result = ApplyResult()
        method.decompose(gn_1, s_0, result)
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)

        s_1 = s_0.copy(freeze=False)
        gn_1.apply(s_1, result.reset())
        test_and_reset(self, logger, result, s_0, s_1, pat.table.equals(table1))

    def test_method_order_special(self):
        domain = RestaurantDomain()
        problem = domain.test_create_simple_problem()

        sam = problem.sam
        menu = problem.menu_breakfast
        special = problem.special
        pat: Patron = problem.pat
        chris = problem.chris
        table1 = problem.table1

        g_pat_has_ordered = AndCondition(
            pat.desired_order.not_equals(None),
            pat.desired_order.status.equals(OrderedItem.Status.ORDERED),
        )

        gn_1 = TotalOrderGoalTaskNetwork(g_pat_has_ordered)

        s_0 = problem.current_state()
        rel_app_methods = problem.get_relevant_and_applicable_goal_methods(gn_1, s_0)
        self.assertEqual(len(rel_app_methods), 1)
        method = rel_app_methods[0]

        result = ApplyResult()
        method.decompose(gn_1, s_0, result)
        test_and_reset(self, logger, result, s_0, s_0, TrueCondition())
        logger.debug(f"Network:\n{gn_1.str_dereferenced(s_0, '  ', '\n')}")

        s_1 = s_0.copy(freeze=False)
        gn_1.apply(s_1, result)
        pat_order_is_placed = pat.desired_order.status.equals(OrderedItem.Status.ORDERED)
        test_and_reset(self, logger, result, s_0, s_1, pat_order_is_placed)
