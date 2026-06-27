from __future__ import annotations

import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult

logger = LogManager.get_logger("oompa.test.transport")
LogManager.set_root_level(LogManager.DEBUG)


class TestTransportProbabilistic(unittest.TestCase):
    def test_probabilistic_effects(self):
        logger.debug("")
        problem = TransportProblem()
        l0 = problem.test_add_location("0")
        l1 = problem.test_add_location("1")
        l2 = problem.test_add_location("2")
        problem.test_add_road(l0, l1)
        problem.test_add_road(l1, l0)
        problem.test_add_road(l1, l2)
        problem.test_add_road(l2, l1)
        t0 = problem.test_add_vehicle("t0", 2, l2)
        p0 = problem.test_add_package("p0", l1)
        problem.test_add_package("p1", l1)

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        a0 = problem.domain.action(Drive)(t0, l2, l1)
        s_1 = s_0.copy()
        result = a0.apply(s_1)
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)

        a1 = problem.domain.action(PickUp)(t0, p0)
        s_2 = s_1.copy()
        result = a1.apply(s_2)
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)

        a2 = problem.domain.action(DropOff)(p0)
        s_3 = s_2.copy()
        success_condition = problem.domain.on_vehicle(p0).equals(True)
        failure_condition = problem.domain.on_vehicle(p0).equals(False)
        success, failure = False, False
        # 1 / 2^20 chance of test failure.
        for _ in range(20):
            s_3 = s_2.copy()
            result = a2.apply(s_3)
            if success_condition.is_entailed_by(s_3):
                success = True
            if failure_condition.is_entailed_by(s_3):
                failure = True
        self.assertTrue(success and failure)
