from __future__ import annotations

import itertools
import unittest

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.action_bases import ActionTemplate
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition_bases import AndCondition, OrCondition
from oompa_types.domain.stateful import Stateful
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from tests.simple_travel_domain import (
    LOC_HOME_A,
    LOC_HOME_B,
    LOC_PARK,
    Location,
    Person,
    SimpleTravelDomain,
    Taxi,
)

logger = LogManager.get_logger("oompa.test.travel")
LogManager.set_root_level(LogManager.DEBUG)


class TestTravelHGN(unittest.TestCase):
    def test_object_filters(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        alice = problem.alice

        people = problem.objects(type_filter=(Person))
        self.assertIn(alice, people)

        domain = problem.domain
        action_template: ActionTemplate = domain.functional_action(Person.walk_to)
        args_type = action_template.args_types
        people = problem.objects(type_filter=args_type[0])
        self.assertIn(alice, people)

        locations = problem.objects(type_filter=args_type[1])
        self.assertIn(LOC_HOME_A, locations)

    def test_state_copy_and_freeze(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1
        # TODO: bug: s_1.location[alice] is different from s_1.location['alice']

        alice_at_home_a = alice.location.equals(LOC_HOME_A)
        alice_at_home_b = alice.location.equals(LOC_HOME_B)
        taxi_at_alice = taxi1.location.equals(alice.location)
        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")
        self.assertTrue(s_0.entails(alice_at_home_a))
        s_0.location[alice] = LOC_HOME_B

        s_0_frozen = s_0.freeze()
        logger.debug(f"State:{s_0_frozen}")
        with self.assertRaises(TypeError):
            s_0_frozen.location[alice] = LOC_HOME_B
        self.assertTrue(s_0_frozen.entails(alice_at_home_b))

        alice_hail_taxi1 = alice.hail(taxi1)
        s_1 = s_0.apply(alice_hail_taxi1, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        self.assertTrue(taxi_at_alice.is_entailed_by(s_1))

        s_1 = s_0_frozen.apply(alice_hail_taxi1, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        self.assertTrue(taxi_at_alice.is_entailed_by(s_1))

    def test_state_equality(self):
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)

        # Check an empty state
        s_0: Stateful = problem.current_state()
        s_0_unfrozen: Stateful = s_0.copy(freeze=False)
        s_0_frozen: Stateful = s_0.copy(freeze=True)

        # States should be comparable, regardless of whether they are frozen
        self.assertEqual(s_0, s_0_unfrozen)
        self.assertEqual(s_0, s_0_frozen)
        self.assertEqual(s_0_unfrozen, s_0_frozen)

        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1
        alice_hail_taxi1 = alice.hail(taxi1)
        s_1_frozen = s_0_frozen.apply(alice_hail_taxi1)
        s_1_unfrozen = s_0_unfrozen.apply(alice_hail_taxi1)
        self.assertNotEqual(s_0_unfrozen, s_1_unfrozen)
        self.assertNotEqual(s_0_frozen, s_1_frozen)
        self.assertEqual(s_1_frozen, s_1_unfrozen)
        self.assertEqual(s_1_unfrozen, s_1_frozen)

    def test_state_hashing(self):
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1
        result = ApplyResult()

        s_0 = problem.current_state()
        s_0_frozen = s_0.copy(freeze=True)

        # States should be hashable iff they are frozen.
        self.assertRaises(BaseException, hash, s_0)
        self.assertIsInstance(hash(s_0_frozen), int)

        alice_hail_taxi1 = alice.hail(taxi1)
        s_1_frozen_1 = s_0_frozen.apply_and_freeze(alice_hail_taxi1, result.reset())
        s_1_frozen_2 = s_0_frozen.apply_and_freeze(alice_hail_taxi1, result.reset())
        logger.debug(f"s_0_frozen:\n{s_0_frozen}")
        logger.debug(f"s_1_frozen_1:\n{s_1_frozen_1}")
        logger.debug(f"s_1_frozen_2:\n{s_1_frozen_2}")
        self.assertNotEqual(hash(s_0_frozen), hash(s_1_frozen_1))
        self.assertEqual(hash(s_1_frozen_1), hash(s_1_frozen_2))

    def test_condition_for_small_problem(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)

        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1

        s_0 = problem.current_state()
        logger.debug(f"State:{s_0}")

        logger.debug("Creating some true conditions and check entailment")
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
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob

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
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: Taxi = problem.taxi1
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
        a_bob_walk_to_park = bob.walk_to(park)
        logger.debug(f"Applying {a_bob_walk_to_park}")
        s_1 = s_0.apply(a_bob_walk_to_park, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)

        condition4 = bob.location.equals(LOC_PARK)
        self.assertTrue(s_1.entails(condition4))

        alice_hail_taxi1 = alice.hail(taxi1)

        s_2 = s_1.apply(alice_hail_taxi1, result.reset())
        logger.debug(f"state:\n{s_2}")
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition5 = taxi1.location.equals(alice.location)
        self.assertTrue(s_2.entails(condition5))

    def test_numeric_actions_for_full_problem(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1
        result = ApplyResult()

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        alice_hail_taxi1 = alice.hail(taxi1)
        s_2 = s_0.copy(freeze=False)

        logger.debug(f"state:\n{s_2}")
        alice_hail_taxi1.apply(s_2, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition5 = taxi1.location.equals(alice.location)
        self.assertTrue(s_2.entails(condition5))

        taxi_transport_alice_to_park = taxi1.transport(alice, LOC_PARK)
        s_3 = s_2.copy(freeze=False)

        taxi_transport_alice_to_park.apply(s_3, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        condition6 = alice.location.equals(LOC_PARK)
        self.assertTrue(s_3.entails(condition6))
        self.assertTrue(s_3.owe[alice.name], 12)

        alice_pay_taxi = alice.pay_taxi()
        s_4 = s_3.copy(freeze=False)
        alice_pay_taxi.apply(s_4, result.reset())
        self.assertTrue(result.status == ApplyResult.Status.SUCCESS)
        self.assertTrue(s_4.entails(condition6))
        self.assertEqual(s_4.owe[alice.name], 0)
        self.assertEqual(s_4.cash[alice.name], 8)

    def test_method_travel_by_foot(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        bob: Person = problem.bob
        park: Location = problem.park
        result = ApplyResult()

        g_bob_at_park = bob.location.equals(park)
        gn1: TotalOrderGoalTaskNetwork = TotalOrderGoalTaskNetwork(g_bob_at_park)
        bob_travel_by_foot_to_park = bob.travel_by_foot(park)

        s_0 = problem.current_state()
        bob_travel_by_foot_to_park.decompose(gn1, s_0, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.SUCCESS)

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

    def test_method_travel_by_taxi(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        taxi1: Taxi = problem.taxi1
        park: Location = problem.park

        goal = alice.location.equals(park)
        gn1: TotalOrderGoalTaskNetwork = TotalOrderGoalTaskNetwork(goal)
        alice_travel_by_taxi_to_park = taxi1.travel_by_taxi(alice, park)
        result = ApplyResult()

        s_0 = problem.current_state()
        alice_travel_by_taxi_to_park.decompose(gn1, s_0, result.reset())

        alice_hail_taxi1 = alice.hail(taxi1)

        self.assertEqual(str(gn1.get_unconstrained()), str(alice_hail_taxi1))

        s_1 = s_0.copy(freeze=False)
        while isinstance(gn1.get_unconstrained(), Action):
            gn1.get_unconstrained().apply(s_1, result.reset())
            gn1.release()
        self.assertTrue(goal.is_entailed_by(s_1))

        # create a method instance that will not be applicable and test it
        # e.g., bob_take_taxi when he doesn't have enough cash
        bob: Person = problem.bob
        bob.cash = 2
        s_2 = problem.current_state()
        g_bob_at_park = bob.location.equals(park)
        gn2: TotalOrderGoalTaskNetwork = TotalOrderGoalTaskNetwork(g_bob_at_park)
        gn2_copy = gn2.copy()
        bob_travel_by_taxi_to_park = taxi1.travel_by_taxi(bob, park)
        bob_travel_by_taxi_to_park.decompose(gn2, s_2, result.reset())
        self.assertEqual(result.status, ApplyResult.Status.NOT_APPLICABLE)
        self.assertEqual(gn2, gn2_copy)

    def test_fare_function_works_correctly(self):
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)
        domain = SimpleTravelDomain()
        taxi1: Taxi = problem.taxi1

        s = problem.current_state()
        logger.debug(f"Condensed state:\n{s}")
        logger.debug(f"Full state:\n{s.str_full_state()}")

        cond = taxi1.fare[LOC_PARK, LOC_HOME_B].equals(3)
        self.assertTrue(cond.is_entailed_by(s))

        cond = taxi1.fare[LOC_PARK, LOC_HOME_B].not_equals(3)
        self.assertFalse(cond.is_entailed_by(s))

    def test_condition_equality(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: Taxi = problem.taxi1

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        condition_1 = alice.location.equals(LOC_HOME_A)
        condition_1b = alice.location.equals(LOC_HOME_A)

        condition_2 = alice.location.equals(LOC_PARK)
        condition_3 = bob.location.equals(LOC_HOME_B)
        condition_4 = taxi1.location.equals(alice.location)

        false_list = [condition_1, condition_2, condition_3, condition_4]
        false_pairs = itertools.combinations(false_list, 2)
        for left, right in false_pairs:
            logger.debug(f"Expecting comparison to be false: {left} and {right}")
            self.assertFalse(left == right)

        self.assertTrue(condition_1 == condition_1b)
        self.assertTrue(condition_1b == condition_1)
        self.assertFalse(condition_1 is condition_1b)  # using a factory, this will be true
        self.assertFalse(condition_1b is condition_1)  # using a factory, this will be true
        self.assertFalse(condition_1 == condition_2)
        self.assertFalse(condition_2 == condition_1)

        # check conjunctions
        quantified_list = [condition_1, condition_2, condition_3]
        condition_5 = AndCondition(*quantified_list)
        for condition in quantified_list:
            self.assertFalse(condition == condition_5)
            self.assertFalse(condition_5 == condition)
            self.assertTrue(condition_5.matches_contains(condition))
        self.assertFalse(condition_5.matches_contains(condition_4))

        # check disjunctions
        condition_6 = OrCondition(*quantified_list)
        for condition in quantified_list:
            self.assertFalse(condition == condition_6)
            self.assertFalse(condition_6 == condition)
            self.assertTrue(condition_6.matches_contains(condition))
        self.assertFalse(condition_6.matches_contains(condition_4))

    def test_condition_hash(self):
        logger.debug("")
        domain = SimpleTravelDomain()
        problem = domain.instantiate_problem()
        domain.test_add_default_locations(problem)
        domain.test_add_alice_and_taxi1(problem)
        domain.test_add_bob_and_taxi2(problem)

        alice: Person = problem.alice
        bob: Person = problem.bob
        taxi1: Taxi = problem.taxi1

        s_0 = problem.current_state()
        logger.debug(f"State:\n{s_0}")

        condition_1 = alice.location.equals(LOC_HOME_A)
        condition_1b = alice.location.equals(LOC_HOME_A)

        condition_2 = alice.location.equals(LOC_PARK)
        condition_3 = bob.location.equals(LOC_HOME_B)
        condition_4 = taxi1.location.equals(alice.location)

        condition_list = [condition_1, condition_2, condition_3, condition_4]
        condition_pairs = itertools.combinations(condition_list, 2)
        for left, right in condition_pairs:
            logger.debug(f"Expecting comparison to be false: hash({left}) and hash({right})")
            self.assertFalse(hash(left) == hash(right))

        self.assertTrue(hash(condition_1) == hash(condition_1b))
        self.assertFalse(hash(condition_1) is hash(condition_1b))  # using a factory, will be true
        self.assertFalse(hash(condition_1) == hash(condition_2))
