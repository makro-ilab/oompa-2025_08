from __future__ import annotations

import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition_bases import ForAllCondition
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from tests.extended_travel_domain import (
    ExtendedTravelDomain,
    TaxiVan,
)
from tests.simple_travel_domain import (
    LOC_HOME_A,
    LOC_HOME_B,
    LOC_PARK,
    Location,
    Person,
)

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class TestExtendedTravelHGN(unittest.TestCase):
    def test_condition_for_small_problem(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)

        alice: Person = problem.alice
        taxi1: TaxiVan = problem.taxivan1

        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        logger.debug("Create some true conditions and check entailment")
        condition1 = alice.location.equals(LOC_HOME_A)
        logger.debug(f"condition: {condition1}")
        entails_result = s_0.entails(condition1)
        self.assertTrue(entails_result)

        condition2 = taxi1.location.equals(LOC_PARK)
        entails_result = s_0.entails(condition2)
        self.assertTrue(entails_result)

        logger.debug("Creating some false conditions and check entailment")
        condition3 = alice.location.equals(LOC_PARK)
        entails_result = s_0.entails(condition3)
        self.assertFalse(entails_result)

        condition4 = taxi1.location.equals(LOC_HOME_A)
        entails_result = s_0.entails(condition4)
        self.assertFalse(entails_result)

    def test_condition_for_full_problem(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        logger.debug("Creating some true conditions and check entailment")
        condition1 = alice.location.equals(LOC_HOME_A)
        entails_result = s_0.entails(condition1)
        self.assertTrue(entails_result)

        condition2 = bob.location.equals(LOC_HOME_B)
        entails_result = s_0.entails(condition2)
        self.assertTrue(entails_result)

        logger.debug("Creating some false conditions and check entailment")
        condition3 = alice.location.equals(LOC_PARK)
        entails_result = s_0.entails(condition3)
        self.assertFalse(entails_result)

        condition4 = bob.location.equals(LOC_PARK)
        entails_result = s_0.entails(condition4)
        self.assertFalse(entails_result)

    def test_non_numeric_actions_for_full_problem(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: TaxiVan = problem.taxivan1
        park: Location = problem.park

        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        logger.debug("Creating some true conditions and check entailment")
        condition1 = alice.location.equals(LOC_HOME_A)
        self.assertTrue(s_0.entails(condition1))

        condition2 = bob.location.equals(LOC_HOME_B)
        self.assertTrue(s_0.entails(condition2))

        logger.debug("Creating some false conditions and check entailment")
        condition3 = alice.location.equals(LOC_PARK)
        self.assertFalse(s_0.entails(condition3))

        logger.debug("Taking actions to move the people")
        bob_walk_to_park = bob.walk_to(park)
        s_1 = s_0.copy(freeze=False)
        bob_walk_to_park.apply(s_1, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)

        condition4 = bob.location.equals(LOC_PARK)
        self.assertTrue(s_1.entails(condition4))

        alice_hail_taxi = alice.hail(taxi1)
        s_2 = s_1.copy(freeze=False)

        logger.debug(f"state:\n{s_2}")
        alice_hail_taxi.apply(s_2, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition5 = taxi1.location.equals(alice.location)
        self.assertTrue(s_2.entails(condition5))

    def test_numeric_actions_for_full_problem(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: TaxiVan = problem.taxivan1
        park: Location = problem.park

        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        alice_hail_taxi = alice.hail(taxi1)
        s_2 = s_0.copy(freeze=False)

        logger.debug(f"state:\n{s_2}")
        alice_hail_taxi.apply(s_2, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition5 = taxi1.location.equals(alice.location)
        self.assertTrue(s_2.entails(condition5))

        # confirm the passenger list is unique for each state
        taxi_dict = s_2.taxi
        taxi_dict["mak"] = "taxi3"
        s0_taxi_dict = s_0.taxi
        self.assertFalse(hasattr(s0_taxi_dict, "mak"))

        taxi_pickup_alice = taxi1.pickup(alice)
        s_3 = s_2.copy(freeze=False)
        taxi_pickup_alice.apply(s_3, result.reset())
        logger.debug(f"after taxi1.pickup(alice), state:\n{s_3}")
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition6 = taxi1.passengers.contains(alice)
        self.assertTrue(s_3.entails(condition6))

        taxi_dropoff_alice = taxi1.drop_off(alice, park)
        s_4 = s_3.copy(freeze=False)
        taxi_dropoff_alice.apply(s_4, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition7 = alice.location.equals(park)
        self.assertTrue(condition7.is_entailed_by(s_4))
        self.assertTrue(s_4.owe[alice.name], 12)
        condition8 = taxi1.location.equals(park)
        self.assertTrue(condition8.is_entailed_by(s_4))

        alice_pay_taxi = alice.pay_taxi()
        s_5 = s_4.copy(freeze=False)
        alice_pay_taxi.apply(s_5, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)
        self.assertEqual(s_5.owe[alice.name], 0)
        self.assertEqual(s_5.cash[alice.name], 8)

    def test_method_travel_by_foot(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        bob: Person = problem.bob
        park: Location = problem.park

        result = ApplyResult()

        g_bob_at_park = bob.location.equals(park)
        gn1: TotalOrderGoalTaskNetwork = TotalOrderGoalTaskNetwork(g_bob_at_park)
        bob_travel_by_foot_to_park = bob.travel_by_foot(park)

        s_0 = problem.current_state()
        bob_travel_by_foot_to_park.decompose(gn1, s_0, result.reset())

        a_bob_walk_to_park = bob.walk_to(park)
        self.assertEqual(str(gn1.get_unconstrained()), str(a_bob_walk_to_park))

        s_1 = s_0.copy(freeze=False)
        gn1.get_unconstrained().apply(s_1, result.reset())
        self.assertTrue(g_bob_at_park.is_entailed_by(s_1))

        # create a method instance that will not be applicable and test it
        # e.g., alice cannot walk to the park because it is too far
        s_2 = s_0.copy(freeze=False)
        alice: Person = problem.alice
        g_alice_at_park = alice.location.equals(park)
        gn2 = TotalOrderGoalTaskNetwork(g_alice_at_park)
        gn2_copy = gn2.copy()
        alice_travel_by_foot = alice.travel_by_foot(park)
        alice_travel_by_foot.decompose(gn2, s_2, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.NOT_APPLICABLE)
        self.assertEqual(gn2, gn2_copy)

    def test_pickup_multiple_and_dropoff(self):
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        result = ApplyResult()

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: TaxiVan = problem.taxivan1
        park: Location = problem.park

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        bob_hail_taxi1 = bob.hail(taxi1)
        s_1 = s_0.apply(bob_hail_taxi1, result.reset())
        pickup_bob = taxi1.pickup(bob)
        s_1b = s_1.apply(pickup_bob, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

        alice_hail_taxi1 = alice.hail(taxi1)
        s_2 = s_1b.apply(alice_hail_taxi1, result.reset())
        pickup_alice = taxi1.pickup(alice)
        s_2b = s_2.apply(pickup_alice, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

        dropoff_all_at_park = taxi1.drop_off_all(park)
        s_3 = s_2b.apply(dropoff_all_at_park, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)
        all_at_park = ForAllCondition([alice, bob], lambda p: p.location.equals(park))
        self.assertTrue(s_3.entails(all_at_park))

        logger.debug("finished")

    def test_rideshare_to_park(self):
        self.skipTest("need to finish this test!")
        logger.debug("")
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: TaxiVan = problem.taxivan1
        park: Location = problem.park
        people = [alice, bob]

        result = ApplyResult()

        """
        goal = ForAllCondition(people, lambda x: place_of(x).equals(park))
        gn1: GoalNetwork = GoalNetwork(goal)
        logger.debug(f"Network: \n{gn1}")
        rideshare_to_park: Rideshare = domain.method(Rideshare)(people, taxi1, park)

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")
        rideshare_to_park.decompose(gn1.root, s_0)
        logger.debug(f"Goal Network:\n{gn1}")

        self.assertEqual(len(gn1.root.children), 3)

        s_1 = s_0.copy()
        gn1.apply(s_1, result)
        self.assertEqual(result.status, Result.ALL_ACTIONS_APPLIED)
        self.assertTrue(goal.is_entailed_by(s_1))
        """

    def test_fare_function_works_correctly(self):
        domain = ExtendedTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxivan1(problem)
        domain.test_add_bob_and_taxivan2(problem)
        taxi1 = problem.taxivan1

        s = problem.current_state()

        cond = taxi1.fare[LOC_PARK, LOC_HOME_B].equals(3)
        self.assertTrue(cond.is_entailed_by(s), True)

        cond = taxi1.fare[LOC_PARK, LOC_HOME_B].not_equals(3)
        self.assertFalse(cond.is_entailed_by(s))
