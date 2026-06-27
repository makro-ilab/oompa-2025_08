from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, get_args

from makro_utils.log_manager import LogManager
from oompa_types.action.action import Action
from oompa_types.action.action_bases import ActionTemplate
from oompa_types.condition.condition import Condition
from oompa_types.effect.effect import Effect
from oompa_types.objects.named import Named

logger = LogManager.get_logger("oompa.action")

PRECONDITION_FUNC_T = TypeVar("PRECONDITION_FUNC_T", bound=Callable[[list[Any]], Condition])
EFFECT_FUNC_T = TypeVar("EFFECT_FUNC_T", bound=Callable[[list[Any]], Effect])
EXECUTE_FUNC_T = TypeVar("EXECUTE_FUNC_T", bound=Callable[[list[Any]], Any])
ACTION_OWNER_T = TypeVar("ACTION_OWNER_T")


class ActionDescriptor:  # noqa: N801
    """A descriptor protocol for declaring action instances using a functional interface.

    TODO update this documentation
    This class implements python decorator functions so that it mostly behaves like
    a standard property except that:
    - it stores the `Action` in the _action_name of the owning class instance;
    - it _adds_ this `Action` to any class listed in the target(s) of the effect

    This code is adapted from three sources:
     -[Descriptor Guide — Python 3.12.2 documentation](https://docs.python.org/3/howto/descriptor.html#properties)
    - A partial solution for this version was provided at the SO Answer for
      [Extending @property.setter decorator in Python](https://stackoverflow.com/a/61633119)
    - Improvements to the generic typing were adapted from the SO answer for
      [Using Typing and Mypy with Descriptors](https://stackoverflow.com/a/57401731)
    """

    ACTION_PREFIX: str = "_action_"

    def __init__(
        self,
        instantiate_func: Callable[[list[Any]], Action],
        precondition_func: PRECONDITION_FUNC_T = None,
        effect_func: EFFECT_FUNC_T = None,
        execute_func: EXECUTE_FUNC_T = None,
    ) -> None:
        self.cls = None
        self.name = None
        # TODO read the args from the function
        self.args: list[Named] = None
        self.private_name = None
        self._instantiate_func = instantiate_func
        self._precondition_func: PRECONDITION_FUNC_T = precondition_func
        self._effect_func: EFFECT_FUNC_T = effect_func
        self._execute_func: EXECUTE_FUNC_T = execute_func

    def __str__(self) -> str:
        return f"action: {self.name}(..)"

    def __repr__(self) -> str:
        return self.__str__()

    def get_owner_type(self):
        types = get_args(self.__orig_class__)
        return types[0]

    @property
    def precondition_func(self) -> PRECONDITION_FUNC_T:
        return self._precondition_func

    @property
    def effect_func(self) -> EFFECT_FUNC_T:
        return self._effect_func

    @property
    def execute_func(self) -> EXECUTE_FUNC_T:
        return self._execute_func

    # --------------------------------------------------------------
    # region Decorator Functions
    def __set_name__(self, cls, name: str):
        """Called at owner class construction to set the name of this action."""
        self.cls = cls
        self.name = name
        self.private_name = f"{ActionDescriptor.ACTION_PREFIX}{name}"

    def __get__(
        self, instance: ACTION_OWNER_T, owner: ACTION_OWNER_T
    ) -> ActionDescriptor | ActionTemplate:
        if instance is not None:
            return self.get_action_instance(instance)

        if owner is not None:
            return self

        return self

    def __set__(self, instance: ACTION_OWNER_T, value: Any):
        # TODO this probably shouldn't be called, but do something sensible if it is called
        raise NotImplementedError

    def precondition(self, precondition_func: PRECONDITION_FUNC_T):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            precondition_func=precondition_func,
            effect_func=self._effect_func,
            execute_func=self._execute_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    def effect(self, effect_func: EFFECT_FUNC_T):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            precondition_func=self._precondition_func,
            effect_func=effect_func,
            execute_func=self._execute_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    def reference(self, action_ref: ActionDescriptor):
        # TODO make it possible to reference an action defined in another class
        pass

    def execute(self, execute_func):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            precondition_func=self._precondition_func,
            effect_func=self._effect_func,
            execute_func=execute_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    # endregion Decorator Functions
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # region Helper Functions
    def get_action_template(self) -> ActionTemplate:
        action_template = None
        if not hasattr(self.cls, self.private_name):
            logger.debug(f"initializing Action instance {self}")
            action_template = ActionTemplate(
                descriptor=self,
            )

            setattr(self.cls, self.private_name, action_template)
            logger.debug(f"initialized Action {self} for {type(self.cls)}")
        else:
            action_template = getattr(self.cls, self.private_name)
        return action_template

    def get_action_instance(self, owner: ACTION_OWNER_T) -> ActionTemplate.ActionInstance:
        action_template = self.get_action_template()
        action_instance = action_template.partially_bound_instance(owner)
        return action_instance

    # endregion Helper Functions
    # --------------------------------------------------------------


class OompaAction(ActionDescriptor):
    def __init__(self, instantiate_func, **kwargs):
        super().__init__(instantiate_func, **kwargs)
