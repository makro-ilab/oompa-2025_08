from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from oompa_types.action.apply_result import ApplyResult
from oompa_types.condition.condition import ConditionOwner
from oompa_types.condition.condition_bases import NULL_CONDITION
from oompa_types.domain.arguments import HasArguments
from oompa_types.domain.domain import DOMAIN_BASE_T, Domain
from oompa_types.domain.stateful import Stateful
from oompa_types.effect.effect_bases import NOOP_EFFECT, EffectOwner
from oompa_types.objects.named import Named

if TYPE_CHECKING:
    from oompa_types.condition.condition import Condition
    from oompa_types.effect.effect import Effect

TEMPLATE_T = TypeVar("TEMPLATE_T", bound="Action")

"""
    # The following is a handy snippet to insert an action that conforms to the style guide.
    # You can insert it and replace: TEMPLATE with the name, ARGS with the arguments.
    # Alternatively, in VSCode, the snippet oompa_action is defined in oompa.code-snippets

    # =======================================================
    # region action TEMPLATE

    @OompaAction
    def TEMPLATE(self, ARGS):
        pass

    @TEMPLATE.precondition
    def TEMPLATE(self, ARGS):
        return AndCondition(...)
        )

    @TEMPLATE.effect
    def TEMPLATE(self, ARGS):
        return AndEffect(...)

    # endregion action TEMPLATE
    # =======================================================

"""


@runtime_checkable
class Action[DOMAIN_T: DOMAIN_BASE_T, TEMPLATE_T](
    Named,
    HasArguments,
    ConditionOwner,
    EffectOwner,
    Protocol,
):
    def set_as_template(self, domain: Domain = None): ...

    @property
    def template(self) -> TEMPLATE_T: ...

    @property
    def is_template(self) -> bool:
        return self.template == self

    @property
    def is_instance(self) -> bool:
        return self.template != self

    @property
    def domain(self) -> DOMAIN_T: ...

    @property
    def precondition(self) -> Condition:
        return NULL_CONDITION

    @property
    def effect(self) -> Effect:
        return NOOP_EFFECT

    def is_applicable(self, state: Stateful):
        precondition = self.precondition
        is_entailed = precondition.is_entailed_by(state, self)
        return is_entailed

    def apply(self, state: Stateful, result: ApplyResult, check_applicable=True):
        """Apply action to state; directly modifies state."""
        ...
