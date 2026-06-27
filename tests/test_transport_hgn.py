from __future__ import annotations

import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition_bases import AndCondition
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from tests.transport_domain import TransportDomain

logger = LogManager.get_logger("oompa.test.transport")
LogManager.set_root_level(LogManager.DEBUG)


class TestTransportHGN(unittest.TestCase):
    def test_hgn_applicable_methods(self):
        logger.debug("")
        domain = TransportDomain()
        problem = domain.test_create_problem_0()
        loc_0 = problem.loc_0
        loc_1 = problem.loc_1
        loc_2 = problem.loc_2
        veh_0 = problem.veh_0
        p0 = problem.p_0
        p1 = problem.p_1

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")
        applicable_methods = problem.get_applicable_goal_methods(s_0)
        self.assertEqual(len(applicable_methods), 4)

        m1 = veh_0.deliver(p0, loc_0)
        m2 = veh_0.deliver(p0, loc_2)
        m3 = veh_0.deliver(p1, loc_0)
        m4 = veh_0.deliver(p1, loc_2)
        applicable_methods_strs = map(str, applicable_methods)
        self.assertIn(str(m1), applicable_methods_strs)
        self.assertIn(str(m2), applicable_methods_strs)
        self.assertIn(str(m3), applicable_methods_strs)
        self.assertIn(str(m4), applicable_methods_strs)

    def test_hgn_method(self):
        logger.debug("")
        domain = TransportDomain()
        problem = domain.test_create_problem_0()
        loc_0 = problem.loc_0
        loc_1 = problem.loc_1
        loc_2 = problem.loc_2
        veh_0 = problem.veh_0
        p0 = problem.p_0
        p1 = problem.p_1

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        gn = TotalOrderGoalTaskNetwork(p0.location.equals(loc_0))
        m = veh_0.deliver(p0, loc_0)

        result = ApplyResult()
        m.decompose(gn, s_0, result)
        logger.debug(f"GoalNetwork:\n{gn.str_dereferenced(s_0)}")
        self.assertEqual(
            str(gn.get_unconstrained().condition.str_dereferenced(s_0)),
            str(veh_0.location.equals(loc_1)),
        )
        gn.release()
        self.assertEqual(
            str(gn.get_unconstrained().condition.str_dereferenced(s_0)),
            str(p0.vehicle.equals(veh_0)),
        )
        gn.release()
        self.assertEqual(
            str(gn.get_unconstrained().condition.str_dereferenced(s_0)),
            str(veh_0.location.equals(loc_0)),
        )
        gn.release()
        self.assertEqual(
            str(gn.get_unconstrained().condition.str_dereferenced(s_0)),
            str(p0.location.equals(loc_0)),
        )

    def test_method_relevance(self):
        logger.debug("")
        domain = TransportDomain()
        problem = domain.test_create_problem_0()
        loc_0 = problem.loc_0
        loc_1 = problem.loc_1
        loc_2 = problem.loc_2
        veh_0 = problem.veh_0
        p0 = problem.p_0
        p1 = problem.p_1

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        gn1 = TotalOrderGoalTaskNetwork(p0.location.equals(loc_0))
        gn2 = TotalOrderGoalTaskNetwork(
            AndCondition(
                p0.location.equals(loc_0),
                p1.location.equals(loc_0),
            )
        )
        m1 = veh_0.deliver(p0, loc_0)
        m2 = veh_0.deliver(p0, loc_2)

        self.assertTrue(m1.is_relevant(gn1.get_unconstrained()))
        self.assertTrue(m1.is_applicable(s_0))
        self.assertFalse(m2.is_relevant(gn1.get_unconstrained()))
        self.assertTrue(m2.is_applicable(s_0))
        self.assertTrue(m1.is_relevant(gn2.get_unconstrained()))
        self.assertTrue(m1.is_applicable(s_0))
        self.assertFalse(m2.is_relevant(gn2.get_unconstrained()))
        self.assertTrue(m2.is_applicable(s_0))
