from __future__ import annotations

import importlib
from inspect import get_annotations, signature
from pydoc import locate
from types import FunctionType
from typing import TypeVar, get_args

from makro_utils.log_manager import LogManager
from oompa_types.state_property.state_property_bases import (
    StatePropertyOfAttribute,
    StatePropertyTemplate,
)

logger = LogManager.get_logger("oompa.sp")


OWNER_T = TypeVar("OWNER_T")
VALUE_T = TypeVar("VALUE_T")
VALUE_T_OR_NONE = VALUE_T | None


# TODO: eventually allow StatePropertyDecorator accept a Config object as its argument, see https://stackoverflow.com/questions/30809814/python-descriptors-with-arguments
class StatePropertyDescriptor:
    """Provides a property-like descriptor for creating a class-based StateProperty.

    This class implements python decorator functions so that it mostly behaves like
      a standard property except that:
      - it stores the `StatePropertyTemplate` in the _sp_<name> of the owning class instance;
      - it raises a ValueError for setting invalid values

      This code is adapted from three sources:
       -[Descriptor Guide — Python 3.12.2 documentation](https://docs.python.org/3/howto/descriptor.html#properties)
      - A partial solution for this version was provided at the SO Answer for
        [Extending @property.setter decorator in Python](https://stackoverflow.com/a/61633119)
      - Improvements to the generic typing were adapted from the SO answer for
        [Using Typing and Mypy with Descriptors](https://stackoverflow.com/a/57401731)
    """

    NAME_PREFIX: str = "_sp_"
    KW_READ_ONLY: str = "is_read_only"

    def __init__(
        self,
        initial_value: VALUE_T_OR_NONE = None,
        default_value: VALUE_T_OR_NONE = None,
        fget=None,
        fset=None,
        fset_post_hook=None,
        args_type=None,
        value_type=None,
        is_read_only: bool = False,
        is_template_only=False,
        default_factory=None,
    ) -> None:
        self.owning_class = None
        self.name = None
        self.private_name = None
        self.fget = fget
        self.fset = fset
        self.fset_post_hook = fset_post_hook
        self._initial_value = initial_value
        self._default = default_value
        self.default_factory = default_factory
        self._attribute_factory = None
        self._args_type = args_type
        self._value_type = value_type
        self._value_type_determined = value_type is not None
        self.is_read_only = is_read_only
        self.is_template_only = is_template_only
        logger.trace(f"initialized {self}")

    def __str__(self) -> str:
        return f"spd: {self.name}=init:{self._initial_value}[{self._default}]"

    def __repr__(self) -> str:
        return self.__str__()

    def __lt__(self, other):
        if isinstance(other, StatePropertyDescriptor):
            return self.name < other.name
        return self < other

    @property
    def initial_value(self):
        initial_value = None
        if self.default_factory is not None:
            initial_value = self.default_factory()
        else:
            initial_value = self._initial_value
        return initial_value

    def validate_typing(self):
        types = []
        if hasattr(self, "__orig_class__"):
            types = get_args(self.__orig_class__)
        if len(types) != 1:
            msg = "StatePropertyDescriptor requires [VALUE_T] typing; see docstring."
            logger.error(msg)
            raise AttributeError(msg)

    def get_owner_type(self) -> OWNER_T:
        types = get_args(self.__orig_class__)
        return types[0]

    @property
    def args_type(self) -> list[type]:
        arg_types = []
        if self._args_type is None:
            # if this property is on a function, then get the args of that function
            if self.fget is not None:
                if isinstance(self.fget, property):
                    return [self.owning_class]
                function_sig = signature(self.fget, eval_str=True)
                parameters = function_sig.parameters
                for k, v in parameters.items():
                    if k == "self":
                        arg_types.append(self.owning_class)
                    else:
                        arg_types.append(v.annotation)
            # if this property has an owning class, it only has one argument: self
            elif self.owning_class is not None:
                arg_types.append(self.owning_class)
        return arg_types

    @property
    def value_type(self) -> type:
        if not self._value_type_determined:
            self._determine_value_type()
        return self._value_type

    def _determine_value_type(self):
        if self.owning_class is not None:
            owner_annotations = get_annotations(self.owning_class, eval_str=True)
            if self.name in owner_annotations:
                value_t = owner_annotations[self.name]
                if isinstance(value_t, str):
                    # TODO eventually drop this code if it is not used; without the eval_str above,
                    #  the annotations can be stringified; this was a first attempt to unstringify them
                    try_locate = locate(value_t)
                    if try_locate is not None:
                        value_t = try_locate
                    else:
                        if value_t in globals():
                            value_t = globals()[value_t]
                        else:
                            owner_mod_str = self.owning_class.__module__
                            mod = importlib.import_module(owner_mod_str)
                            value_t = getattr(mod, value_t)
                self._value_type = value_t
                self._value_type_determined = True
                return

        if not self._value_type_determined and self.fget is not None:
            function_sig = signature(self.fget, eval_str=True)
            return_type = function_sig.return_annotation
            self._value_type = return_type
            return

        if hasattr(self, "__orig_class__"):
            types = get_args(self.__orig_class__)
            self._value_type = types[0]
            self._value_type_determined = True
            return

        value_t = type(self._initial_value)
        self._value_type = value_t
        self._value_type_determined = True

    # --------------------------------------------------------------
    # region Decorator Functions
    def __set_name__(self, cls, name: str):
        """Called at owner class construction to set the name of this SV."""
        self.owning_class = cls
        self.name = name
        self.private_name = f"{StatePropertyDescriptor.NAME_PREFIX}{name}"

    def __get__(self, instance: OWNER_T, owner: OWNER_T, **args) -> VALUE_T:
        if instance is None:
            return self
        sp = self.get_state_property_instance(instance)
        return sp

    def __set__(self, instance: OWNER_T, new_value: VALUE_T):
        if self == new_value:
            msg = f"cannot set value of self for {self}, ignoring call"
            return
        sp = self.get_state_property_instance(instance)
        if not sp.is_assignable:
            msg = f"{self.owner}{self.name} is a read-only StateProperty."
            logger.error(msg)
            raise TypeError(msg)
        if self.fget is not None and self.fset is None:
            # TODO make sure there is a test for this
            msg = f"{self.owning_class}.{self.name} declared a getter function but not a setter function."
            logger.error(msg)
            raise TypeError(msg)
        if sp.type_check_value and not sp.allows_value_type(new_value):
            msg = f"for {self} new_value_t:{type(new_value)} does not match the expected type value_t: {type(sp.value)} "
            logger.error(msg)
            raise TypeError(msg)
        if self.fset is not None:
            self.fset(instance, new_value)
        else:
            sp.value = new_value
        if self.fset_post_hook is not None:
            self.fset_post_hook(instance, new_value)

    def getter(self, fget):
        sv_descriptor = type(self)(
            initial_value=self._initial_value,
            default_value=self._default,
            fget=fget,
            fset=self.fset,
            fset_post_hook=self.fset_post_hook,
        )
        sv_descriptor.private_name = self.private_name
        return sv_descriptor

    def setter(self, fset):
        sv_descriptor = type(self)(
            initial_value=self._initial_value,
            default_value=self._default,
            fget=self.fget,
            fset=fset,
            fset_post_hook=self.fset_post_hook,
        )
        sv_descriptor.private_name = self.private_name
        return sv_descriptor

    def setter_post_hook(self, fset_post_hook):
        sv_descriptor = type(self)(
            initial_value=self._initial_value,
            default_value=self._default,
            fget=self.fget,
            fset=self.fset,
            fset_post_hook=fset_post_hook,
        )
        sv_descriptor.private_name = self.private_name
        return sv_descriptor

    # endregion Decorator Functions
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # region Helper Functions
    def get_state_property_template(self, instance: OWNER_T) -> StatePropertyTemplate:
        if not hasattr(instance, self.private_name):
            self.init_state_property_template(instance)
        template: StatePropertyTemplate = getattr(instance, self.private_name)
        return template

    def get_state_property_instance(self, instance: OWNER_T) -> StatePropertyOfAttribute:
        if not hasattr(instance, self.private_name):
            self.init_state_property_template(instance)
        template: StatePropertyTemplate = getattr(instance, self.private_name)
        sp_instance = template.get_instance((instance,))
        return sp_instance

    def init_state_property_template(self, instance: OWNER_T):
        logger.trace(
            f"initializing {type(instance)}.{self.name} at {type(instance)}{self.private_name}"
        )
        # TODO should the descriptor track these details, rather than the template?
        args_type = self.args_type
        value_type = self.value_type
        if not hasattr(instance, self.private_name):
            spt = StatePropertyTemplate(
                name=self.name,
                args=[instance],
                descriptor=self,
                instance=instance,
                args_type=args_type,
                value_type=value_type,
            )
            setattr(instance, self.private_name, spt)
            logger.trace(f"initialized {type(instance)}{self.name} at {self.private_name}")

    def inject(self, instance, name):
        if self._value_type is None:
            raise ValueError("You must declare a value type")
        logger.trace(f"Attempting to inject state_property '{name}'")
        cls = type(instance)
        self.__set_name__(self, name)
        setattr(cls, self.name, self)  # sets this descriptor in the class
        self.init_state_property_template(instance)  # initializes the descriptor for instance

    # endregion Helper Functions
    # --------------------------------------------------------------


class StatePropertyFactory(StatePropertyDescriptor):
    def __init__(self, context=None, **kwargs):
        if context is not None:
            if isinstance(context, FunctionType):
                super().__init__(fget=context, **kwargs)
                return
            else:
                super().__init__(initial_value=context, **kwargs)
                return
        super().__init__(**kwargs)


class StaticStatePropertyFactory(StatePropertyFactory):
    def __init__(self, context=None, **kwargs):
        kwargs[self.KW_READ_ONLY] = True
        if context is not None:
            if isinstance(context, FunctionType):
                super().__init__(fget=context, **kwargs)
                return
            else:
                super().__init__(initial_value=context, **kwargs)
                return
        super().__init__(**kwargs)
