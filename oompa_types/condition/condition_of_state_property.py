from typing import Any

from makro_utils.log_manager import LogManager
from oompa_types.condition.binary_condition_base import DESIRED_T, BinaryConditionBase
from oompa_types.domain.operator import Operator
from oompa_types.domain.stateful import Stateful
from oompa_types.state_property.state_property import StateProperty

logger = LogManager.get_logger("oompa.test.travel")


class ConditionOfStateProperty[DESIRED_T](BinaryConditionBase[StateProperty, DESIRED_T]):
    """A Condition with a target that is an Attribute."""

    def __init__(self, target: StateProperty, op: Operator, desired: DESIRED_T) -> None:
        BinaryConditionBase.__init__(self, target, op, desired)

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        target_str = f"{self._target.name}{self._target.args}"
        desired = self.desired_dereferenced(state)
        return f"{indent}{target_str} {self.op} {desired}{sep}"

    def is_entailed_by(self, state: Stateful, caller: Any = None) -> bool:
        logger.trace(f"checking entailment for {self.str_dereferenced(state)}")
        desired = self.desired_dereferenced(state)
        target: StateProperty = self._target
        name_dict = None
        if hasattr(state, target.name):  # Class-based state
            name_dict = getattr(state, target.name, None)
        elif isinstance(state, dict) and target.name in state:  # dictionary-based state
            name_dict = state[target.name]

        if name_dict is not None:
            param_name = target.dereferenced_arg_name(self.owner, state).strip("()[]")
            if param_name in name_dict:
                value = name_dict[param_name]
                return self.op.compare(value, desired)
        if target.is_relation:
            value = target.dereference(state)
            return self.op.compare(value, desired)
        logger.error(f"could not determine value for {target}.")
        return False
