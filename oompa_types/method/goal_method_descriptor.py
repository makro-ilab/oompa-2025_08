from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, get_args

from makro_utils.log_manager import LogManager
from oompa_types.condition.condition import Condition
from oompa_types.effect.effect import Effect
from oompa_types.goal_network.gtn_bases import TotalOrderGoalTaskNetwork
from oompa_types.method.goal_method import GoalMethod
from oompa_types.method.goal_method_bases import GoalMethodTemplate
from oompa_types.objects.named import Named

logger = LogManager.get_logger("oompa.method")

PRECONDITION_FUNC_T = TypeVar("PRECONDITION_FUNC_T", bound=Callable[[list[Any]], Condition])
GOAL_FUNC_T = TypeVar("GOAL_FUNC_T", bound=Callable[[list[Any]], Condition])
EFFECT_FUNC_T = TypeVar("EFFECT_FUNC_T", bound=Callable[[list[Any]], Effect])
BODY_FUNC_T = TypeVar("BODY_FUNC_T", bound=Callable[[list[Any]], TotalOrderGoalTaskNetwork])
METHOD_OWNER_T = TypeVar("METHOD_OWNER_T")


class MethodDescriptor:  # noqa: N801
    """A descriptor protocol for declaring method instances using a functional interface.

    TODO update this documentation
    This class implements python decorator functions so that it mostly behaves like
    a standard property except that:
    - it stores the `MethodTemplate` in the _action_name of the owning class instance;
    - it _adds_ this `MethodTemplate` to any class listed in the target(s) of the effect

    This code is adapted from three sources:
     -[Descriptor Guide — Python 3.12.2 documentation](https://docs.python.org/3/howto/descriptor.html#properties)
    - A partial solution for this version was provided at the SO Answer for
      [Extending @property.setter decorator in Python](https://stackoverflow.com/a/61633119)
    - Improvements to the generic typing were adapted from the SO answer for
      [Using Typing and Mypy with Descriptors](https://stackoverflow.com/a/57401731)
    """

    METHOD_PREFIX: str = "_method_"

    def __init__(
        self,
        instantiate_func: Callable[[list[Any]], GoalMethod],
        goal_func: GOAL_FUNC_T = None,
        precondition_func: PRECONDITION_FUNC_T = None,
        body_func: BODY_FUNC_T = None,
    ) -> None:
        self.cls = None
        self.name = None
        # TODO read the args from the function
        self.args: list[Named] = None
        self.private_name = None
        self._instantiate_func = instantiate_func
        self._goal_func: GOAL_FUNC_T = goal_func
        self._precondition_func: PRECONDITION_FUNC_T = precondition_func
        self._body_func: BODY_FUNC_T = body_func

    def __str__(self) -> str:
        return f"method: {self.name}(..)"

    def __repr__(self) -> str:
        return self.__str__()

    def get_owner_type(self):
        types = get_args(self.__orig_class__)
        return types[0]

    @property
    def precondition_func(self):
        return self._precondition_func

    @property
    def goal_func(self):
        return self._goal_func

    @property
    def body_func(self):
        return self._body_func

    # --------------------------------------------------------------
    # region Decorator Functions
    def __set_name__(self, cls, name: str):
        """Called at owner class construction to set the name of this action."""
        self.cls = cls
        self.name = name
        self.private_name = f"{MethodDescriptor.METHOD_PREFIX}{name}"

    def __get__(
        self, instance: METHOD_OWNER_T, owner: METHOD_OWNER_T
    ) -> MethodDescriptor | GoalMethodTemplate:
        if instance is not None:
            return self.get_method_instance(instance)
        if owner is not None:
            return self
        return self

    def __set__(self, instance: METHOD_OWNER_T, value: Any):
        # TODO do something sensible if this is called
        raise NotImplementedError

    def goal(self, goal_func: GOAL_FUNC_T):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            goal_func=goal_func,
            precondition_func=self._precondition_func,
            body_func=self._body_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    def precondition(self, precondition_func: PRECONDITION_FUNC_T):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            goal_func=self._goal_func,
            precondition_func=precondition_func,
            body_func=self._body_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    def body(self, body_func: BODY_FUNC_T):
        action_descriptor = type(self)(
            instantiate_func=self._instantiate_func,
            goal_func=self._goal_func,
            precondition_func=self._precondition_func,
            body_func=body_func,
        )
        action_descriptor.private_name = self.private_name
        return action_descriptor

    def reference(self, method_ref: MethodDescriptor):
        # TODO make it possible to reference a method defined in another class
        pass

    # endregion Decorator Functions
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # region Helper Functions
    def get_method_template(self) -> GoalMethodTemplate:
        method_template = None
        if not hasattr(self.cls, self.private_name):
            logger.debug(f"initializing Action instance {self}")
            method_template = GoalMethodTemplate(descriptor=self)
            setattr(self.cls, self.private_name, method_template)
            logger.debug(f"initialized Action {self} for {type(self.cls)}")
        else:
            method_template = getattr(self.cls, self.private_name)
        return method_template

    def get_method_instance(self, owner: METHOD_OWNER_T) -> GoalMethodTemplate.Instance:
        method_template = self.get_method_template()
        method_instance = method_template.partially_bound_instance(owner)
        return method_instance

    # endregion Helper Functions
    # --------------------------------------------------------------


class OompaMethod(MethodDescriptor):
    def __init__(self, instantiate_func, **kwargs):
        super().__init__(instantiate_func, **kwargs)
