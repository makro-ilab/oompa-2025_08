import unittest

from makro_utils.log_manager import TraceLogger
from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.domain.stateful import Stateful


def test_and_reset(
    test_case: unittest.TestCase,
    logger: TraceLogger,
    result: ApplyResult,
    initial_state: Stateful,
    resulting_state: Stateful,
    condition: Condition,
):
    logger.debug(f"state diff:\n{resulting_state.diff_str(initial_state)}")
    test_case.assertEqual(result.status, ApplyResult.Status.SUCCESS)
    test_case.assertTrue(resulting_state.entails(condition))
    result.reset()
