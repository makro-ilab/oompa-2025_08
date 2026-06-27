from __future__ import annotations

import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult
from tests.depot_domain import DepotDomain

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class TestDepot(unittest.TestCase):
    def test_lift_drop(self):
        domain = DepotDomain()
        problem = domain.test_create_problem_0()
        crate_0 = problem.crate_0
        hoist_1 = problem.hoist_1
        pallet_1 = problem.pallet_1

        result = ApplyResult()

        print(crate_0.__dict__)

        s_0 = problem.current_state()

        a_1 = hoist_1.lift(crate_0)
        s_1 = s_0.apply(a_1, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

        a_2 = hoist_1.drop(pallet_1)
        s_2 = s_1.apply(a_2, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

        a_3 = hoist_1.lift(crate_0)
        s_3 = s_2.apply(a_3, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

        # a_2 = problem.domain.action(UnsupervisedLoad)(hoist_1, truck_0)
        # s_2 = s_1.apply(a_2, result.reset())
        # self.assertEqual(result.status, Action.Result.SUCCESS)

        # a_3 = problem.domain.action(SupervisedLoad)(hoist_1, truck_0)
        # s_3 = s_2.apply(a_3, result.reset())
        # self.assertEqual(result.status, Action.Result.SUCCESS)


# TODO start here and expand the tests for all the key actions
