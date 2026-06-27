import random
import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult
from tests.simple_travel_domain import SimpleTravelDomain

logger = LogManager.get_logger("oompa.test.applicable_actions")
LogManager.set_root_level(LogManager.DEBUG)


class TestApplicableActions(unittest.TestCase):
    def test_travel_hgn_applicable_actions(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        applicable = problem.get_applicable_actions(s_0)
        applicable_strs = "\n".join([f"  {str(x)}" for x in applicable])
        logger.debug(f"Applicable actions:\n{applicable_strs}")
        self.assertEqual(len(applicable), 10)

    def test_simple_travel_random_rollouts(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        result = ApplyResult()

        random.seed(42)
        # perform 100 random rollouts from s_0
        s_cur = s_0.copy(freeze=False)
        for i in range(100):
            applicable = problem.get_applicable_actions(s_cur)
            num_applicable = len(applicable)
            self.assertTrue(num_applicable > 0)  # this is an invertible domain
            random_action = random.choice(applicable)
            logger.debug(f"  i:{i} #_applicable:{num_applicable} chose:{random_action}")
            s_cur = s_cur.freeze()  # something one might do during an actual rollout to cache state
            new_state = s_cur.apply(random_action, result.reset())
            logger.debug(f"    applied result:{result} action:{random_action}")
            self.assertEqual(result.status, ApplyResult.Status.SUCCESS)
            s_cur = new_state
