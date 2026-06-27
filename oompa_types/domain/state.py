from __future__ import annotations

from pprint import pformat
from typing import TYPE_CHECKING, Any, override

import makro_utils
import makro_utils.class_utils
from frozendict import frozendict
from oompa_types.state_property.state_property import StateProperty
from oompa_types.state_property.state_property_descriptor import StatePropertyDescriptor

from .stateful import Stateful

if TYPE_CHECKING:
    from oompa_types.domain.problem_bases import AbstractProblem


class AbstractState[SUBCLASS_T: AbstractState](Stateful[SUBCLASS_T]):
    def __init__(
        self,
        problem: AbstractProblem,
        static_state: AbstractState,
    ):
        self._is_frozen: bool = False
        self._is_static_state = False
        self.problem = problem
        self.static_state = static_state

    def __str__(self):
        return self.str_state()

    def __repr__(self):
        return self.str_state()

    @property
    def is_static_state(self) -> bool:
        return self._is_static_state

    def str_full_state(self):
        return self.str_state(hide_static_state=False)

    def str_mutable_state(self):
        return self.str_state(hide_static_state=True)

    def str_state(self, hide_static_state=True):
        str = ""
        for member in self.members:
            state_content = getattr(self, member.name, None)
            if state_content is None:
                member_str = self._get_missing_member_str(member)
            else:
                member_str = self._get_member_str(member, hide_static_state)
            str += member_str

        return str.replace("frozendict.frozendict", "FZN")

    def __getattr__(self, name: str):
        member = self._get_normal_or_static_member_content(name)
        if member is None:
            raise AttributeError(f"State does not have an attribute {name}")
        return member

    def _get_normal_or_static_member_content(self, name: str):
        content = None
        if name in self.__dict__:
            content = self.__dict__[name]
        if content is None:
            if self.static_state:
                if name in self.static_state.__dict__:
                    content = self.static_state.__dict__[name]
        return content

    def _get_member_str(self, member: StatePropertyDescriptor, hide_static_state=True):
        if member.is_read_only and not self.is_static_state and hide_static_state:
            return f"   {member.name}: <static-state hidden>\n"
        member_content = self._get_normal_or_static_member_content(member.name)
        return f"   {member.name}: {pformat(member_content, indent=6)}\n"

    def _get_missing_member_str(self, member):
        return f"   {member.name}: <missing-from-state>\n"

    def diff_str(self, other: AbstractState):
        str = ""
        for member in self.members:
            member_name = member.name
            if hasattr(self, member_name):
                member_content = getattr(self, member_name)
                include = True
                if hasattr(other, member_name):
                    other_member_content = getattr(other, member_name)
                    if member_content == other_member_content:
                        include = False
                if include:
                    str += self._get_member_str(member)
        if str == "":
            str = "   <no diff>"
        return str

    @property
    def members(self) -> tuple[StateProperty]: ...

    @property
    def member_names(self) -> tuple[str]:
        member_names: list[str] = set()
        for member in self.members:
            member_name = member.name
            member_names.add(member_name)
        return tuple(sorted(member_names))

    @override
    def hash_members(self) -> tuple[Any]:
        """Hashes using the mutable members of this state."""
        member_content = []
        for member in self.members:
            if hasattr(self, member.name):
                member_content.append(getattr(self, member.name))
        return tuple(member_content)

    def copy(self, freeze: bool) -> SUBCLASS_T:
        cls = makro_utils.class_utils.determine_class(self)
        new_state = cls(self.problem, self.static_state)
        for member in self.members:
            member_name = member.name
            if hasattr(self, member_name):
                self_member = getattr(self, member_name)
                new_copy = self._copy_dict(self_member, freeze)
                setattr(new_state, member_name, new_copy)
        new_state.is_frozen = freeze
        return new_state

    def _copy_dict(self, dict_to_copy, freeze):
        if freeze:
            return frozendict(dict_to_copy)
        return dict.copy(dict_to_copy)

    def frozen_copy(self) -> AbstractState:
        return self.copy(freeze=True)

    # TODO convert this to a descriptor using __get__?
    def get(self, *keys: str) -> Any:
        tmp = self
        for index in range(len(keys)):
            key = keys[index]
            found = False
            if hasattr(tmp, key):
                tmp = getattr(tmp, key)
                found = True
            elif key in tmp:
                tmp = tmp[key]
                found = True

            if not found:
                tmp = None
                break
        return tmp

    def as_pddl(self) -> dict:
        """Returns a PDDL representation of this state."""
        raise NotImplementedError

    @override
    @property
    def is_frozen(self) -> bool:
        return self._is_frozen

    @is_frozen.setter
    def is_frozen(self, value):
        self._is_frozen = value

    def __hash__(self):
        if self.is_frozen:
            return hash(self.hash_members())
        raise TypeError("Cannot take the hash of an thawed state; freeze it first.")

    def __eq__(self, other):
        if isinstance(other, AbstractState):
            return self.matches(other)
        return super().__eq__(other)

    def matches(self, other: AbstractState):
        """Compares immutable members of this state."""
        member_names = self.member_names
        for member_name in member_names:
            if hasattr(self, member_name):
                self_member = getattr(self, member_name)
                if hasattr(other, member_name):
                    other_member = getattr(other, member_name)
                    if self_member != other_member:
                        return False
                else:  # other is missing a member that self has
                    return False
            elif hasattr(other, member_name):  # self is missing a member that other has
                return False
        return True


class AutoState(AbstractState["AutoState"]):
    def __init__(self, problem: AbstractProblem, static_state: AbstractState):
        AbstractState.__init__(self, problem, static_state)

    @property
    def members(self) -> list[StateProperty]:
        return self.problem.state_members


class StaticState(AutoState):
    def __init__(self, problem):
        super().__init__(problem, None)
        self._is_static_state = True

    @property
    def members(self) -> list[StateProperty]:
        return self.problem.state_members_static
