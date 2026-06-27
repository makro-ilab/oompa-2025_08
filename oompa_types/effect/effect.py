from __future__ import annotations

from typing import Protocol

from makro_utils.log_manager import LogManager
from oompa_types.action.apply_result import ApplyResult
from oompa_types.domain.stateful import Stateful

logger = LogManager.get_logger("oompa.effect")


class EffectOwner(Protocol): ...


class Effect(Protocol):
    def str_dereferenced(self, state: Stateful | None = None, indent="", sep=""): ...

    def apply(self, state: Stateful, result: ApplyResult): ...

    @property
    def children(self) -> list[Effect]:
        return []

    @property
    def owner(self) -> EffectOwner | None:
        return None

    @owner.setter
    def owner(self, owner: EffectOwner): ...
