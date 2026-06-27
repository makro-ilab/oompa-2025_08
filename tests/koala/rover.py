"""OOMPA port of the Rover domain at https://github.com/koala-planner/domains/tree/main/Rover."""

from __future__ import annotations

from dataclasses import dataclass, field

import aenum
from oompa_types.objects.named import Named
from oompa_types.state_property.old_state_variable_descriptor import StateVariableDescriptor


@dataclass
class Waypoint(Named):
    name: str = "Waypoint"
    visible_from: list[Waypoint] = field(default_factory=list)


@dataclass
class Objective(Named):
    name: str = "Objective"
    visible_from: list[Waypoint] = field(default_factory=list)


class Mode(aenum.AutoNumberEnum):
    NONE = ()
    COLOUR = ()
    HIGH_RES = ()
    LOW_RES = ()


@dataclass
class Camera(Named):
    name: str = "Camera"
    mode: Camera.Mode = StateVariableDescriptor(Mode.NONE)


@dataclass
class Store(Named):
    name: str = "Store"
    is_empty: bool = StateVariableDescriptor[bool](True)


@dataclass
class Rover(Named):
    name: str = "Rover"
    available: bool = StateVariableDescriptor[bool](True)
    at: Waypoint | None = StateVariableDescriptor[Waypoint | None](None)
    camera: Camera | None = StateVariableDescriptor[Camera | None](None)
    store: Store | None = StateVariableDescriptor[Store | None](None)
    equipped_for_soil_analysis: bool = StateVariableDescriptor[bool](True)
    equipped_for_rock_analysis: bool = StateVariableDescriptor[bool](True)
    equipped_for_imaging: bool = StateVariableDescriptor[bool](True)
    can_traverse: list[(Waypoint, Waypoint)] = field(default_factory=list)


class Lander(Named):
    name: str = "Lander"
