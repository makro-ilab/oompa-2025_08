from __future__ import annotations

from typing import Any

from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.placeholder_bases import AnyPlaceholder, PropertyPlaceholder


class PlaceholderFactory:
    @staticmethod
    def build(obj: Any):
        """Constructs a Placeholder around obj or returns obj if it is already a Placeholder."""
        if isinstance(obj, Placeholder):
            return obj
        elif isinstance(obj, property):
            ph = PropertyPlaceholder(obj)
            return ph
        else:
            ph = AnyPlaceholder(obj)
            return ph
