from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, override

from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import Condition
from oompa_types.domain.operator import Operator
from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.placeholder_factories import PlaceholderFactory
from oompa_types.domain.stateful import Stateful
from oompa_types.effect.effect import Effect, EffectOwner, logger
from oompa_types.state_property.state_property import StateProperty

if TYPE_CHECKING:
    from oompa_types.domain.problem import Problem


class AbstractEffect(Effect):
    def __init__(self) -> None:
        super().__init__()
        self._owner = None

    def __repr__(self):
        return self.__str__()

    @property
    def owner(self) -> EffectOwner | None:
        return self._owner

    @owner.setter
    def owner(self, owner: EffectOwner):
        self._owner = owner

    def apply(self, state: Stateful, result: ApplyResult):
        result.status = ApplyResult.Status.NO_OP


class NoopEffect(AbstractEffect):
    pass


NOOP_EFFECT = NoopEffect()

# ===================================================================
# region QuantifiedEffects


class QuantifiedEffect(AbstractEffect):
    effects: list[Effect] = []

    def __init__(self, *effects: Effect) -> None:
        self.effects = effects

    def add(self, effect: Effect):
        self.effects.append(effect)

    @override
    @property
    def children(self):
        return self.effects


class AndEffect(QuantifiedEffect):
    def __init__(self, *effects: Effect) -> None:
        QuantifiedEffect.__init__(self, *effects)

    def __str__(self):
        return f"and([..{len(self.effects)} effects..])"

    @override
    def apply(self, state: Stateful, result: ApplyResult):
        for effect in self.effects:
            logger.debug(f"Applying effect: {effect.str_dereferenced(state)}")
            effect.apply(state, result)
            if isinstance(effect, ConditionalEffect):
                if (
                    result.status == ApplyResult.Status.SUCCESS
                    or result.status == ApplyResult.Status.NO_OP
                ):
                    continue
            elif result.status != ApplyResult.Status.SUCCESS:
                return
        return


class OrEffect(QuantifiedEffect):
    def __init__(self, *effects: Effect) -> None:
        QuantifiedEffect.__init__(self, *effects)

    def __str__(self):
        return f"or([..{len(self.effects)} effects..])"

    @override
    def apply(self, state: Stateful, result: ApplyResult):
        """Applies conditions in order until one succeeds or they all fail."""
        state_copy = state.copy()
        for effect in self.effects:
            effect.apply(state_copy, result)
            if result.status == ApplyResult.Status.SUCCESS:
                return
        return


class ForAllEffect[OPERAND_T](AbstractEffect):
    def __init__(
        self,
        context: list[OPERAND_T] | Placeholder,
        functor: Callable[[OPERAND_T], Effect],
    ):
        self.context = context
        self.functor = functor

    def __str__(self):
        return f"forall([..{self.context} objs..])"

    def apply(self, state: Stateful, result: ApplyResult):
        objs = self.context
        if isinstance(self.context, Placeholder):
            objs = list(self.context.dereference(self, state))
        for obj in objs:
            effect = self.functor(obj)
            logger.debug(f"Applying effect: {effect.str_dereferenced(state)}")
            effect.apply(state, result)
            if result.status != ApplyResult.Status.SUCCESS:
                return
        return


# endregion QuantifiedEffects
# ===================================================================

# ===================================================================
# region ProbabilisticEffect


class ProbabilisticEffect(AbstractEffect):
    outcomes: list[tuple[Effect, float]]

    def __init__(self, *outcomes: tuple[Effect, float]) -> None:
        self.outcomes = outcomes

    def add(self, effect: Effect, probability: float = 1.0):
        self.effects.append((effect, probability))

    @override
    def apply(self, state: Stateful, result: ApplyResult):
        # TODO David: is this correct?
        if not self.outcomes:
            result.status = ApplyResult.Status.SUCCESS
            return
        effects, probabilities = zip(*self.outcomes)
        outcome = random.choices(effects, weights=probabilities, k=1)[0]
        outcome.apply(state, result)

    @override
    @property
    def children(self):
        return [effect for effect, probability in self.outcomes]


# endregion ProbabilisticEffect
# ===================================================================

# ===================================================================
# region EffectOfStateProperty


class EffectOfStateProperty(AbstractEffect):
    def __init__(self, target: StateProperty, op: Operator, desired: Placeholder) -> None:
        super().__init__()
        self._target: StateProperty = target
        self._op = op
        self._desired_ph = PlaceholderFactory.build(desired)

    def __str__(self) -> str:
        return self.str_dereferenced()

    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""):
        target_str = f"{self._target.name}{self._target.args}"
        desired_str = str(self._desired_ph.dereference(self, state))
        return f"{indent}{target_str} {self.op} {desired_str}{sep}"

    @property
    def op(self) -> Operator:
        return self._op

    def apply(self, state: Stateful, result: ApplyResult):
        attribute = self._target
        desired = self._desired_ph.dereference(self, state)
        name = attribute.name
        if hasattr(state, name):
            name_dict = getattr(state, name)
            param = attribute.dereferenced_arg_name(self.owner, state)
            if param in name_dict:
                # TODO modify this logic so it calls a single function; move logic to Operator
                if self.op.modifies_value:
                    new_value = self.op.calculate(name_dict[param], desired)
                    name_dict[param] = new_value
                    result.status = ApplyResult.Status.SUCCESS
                elif self.op.modifies_container:
                    container = name_dict[param]
                    self.op.update(container, desired)
                    result.status = ApplyResult.Status.SUCCESS
                return
        result.status = ApplyResult.Status.NO_OP


# endregion EffectOfStateProperty
# ===================================================================


# ===================================================================
# region InsertNewObjectEffect


class InsertNewObjectEffect(AbstractEffect):
    caller: type
    sp: StateProperty
    problem: Problem
    new_obj_class: type
    obj_args: list[Any]
    problem_kwargs: list[Any]
    update_state: bool

    def __init__(
        self,
        caller: type,
        sp: StateProperty,
        new_obj_class: type,
        obj_args: list[Any],
        problem: Problem,
        problem_kwargs: list[Any],
        update_state=True,
    ):
        super().__init__()
        self.caller = caller
        self.sp = sp
        self.problem = problem
        self.new_obj_class = new_obj_class
        self.obj_args = obj_args
        self.problem_kwargs = problem_kwargs
        self.update_state = update_state

    def apply(self, state: Stateful, result: ApplyResult):
        dereferenced_args = []
        for arg in self.obj_args:
            deref_arg = arg
            if isinstance(arg, Placeholder):
                deref_arg = arg.dereference(self.caller, state)
            dereferenced_args.append(deref_arg)
        new_obj = self.new_obj_class(*dereferenced_args)
        self.problem.add_objects(new_obj)
        effect = EffectOfStateProperty(self.sp, Operator.ASSIGNED, new_obj)
        effect.apply(state, result)
        if self.update_state:
            self.problem.update_state_for_object(state, new_obj)

        result.added = new_obj
        result.status = ApplyResult.Status.SUCCESS


# endregion InsertNewObjectEffect
# ===================================================================

# ===================================================================
# region ConditionalEffect


class ConditionalEffect(AbstractEffect):
    def __init__(self, condition: Condition, effect: Effect):
        super().__init__()
        self.condition = condition
        self.effect = effect

    def apply(self, state, result):
        if self.condition.is_entailed_by(state):
            self.effect.apply(state, result)
        else:
            result.status = ApplyResult.Status.NO_OP


# endregion ConditionalEffect
# ===================================================================
