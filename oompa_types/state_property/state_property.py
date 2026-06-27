from typing import Protocol

from oompa_types.domain.arguments import LIST_ARGS_BASE, HasArguments
from oompa_types.domain.placeholder import Placeholder
from oompa_types.domain.valued import Valued
from oompa_types.objects.named import Named


class StateProperty[LIST_ARGS_T: LIST_ARGS_BASE, VALUE_T](
    Named,
    HasArguments[LIST_ARGS_T],
    Valued[VALUE_T],
    Placeholder,
    Protocol,
):
    """Annotates attributes or relationships of objects in the world.

    TODO update this documentation
    This abstract base class consolidates comparisons, printing, type checking, etc.

    This class uses a Factory to construct instances, so its constructors
    should only be called by a Factory.

    A StateProperty is distinguished by whether it is bindable or assignable,
    which we will clarify below.  An overview of how these properties relate
    is shown in the following table, where an uppercase item (e.g., {@code DOCK})
    indicates an object type while a lowercase object (e.g., {@code dock1})
    indicates an object instance.
    See <a href="../../../../../notation.html">Notation</a> for details.

                     |                Arguments Bindable?                |
                     |           NO           |           YES            |
    Assignable Value?|       (Template)       |       (Instance)         |
    -----------------|---------------------------------------------------|
           NO        | StateRelationTemplate  | StateRelation            |
       (Relation)    | connected(DOCK, DOCK)  | connected(dock1, dock2)  |
    -----------------|---------------------------------------------------|
          YES        | StateVariableTemplate  | StateVariable            |
       (Variable)    | location(ROBOT) = DOCK | location(robot1) = DOCK  |
    ---------------------------------------------------------------------

    A StateProperty has several components:
    - *name*: is a {@link String} specifying its name.
    For example, "connected" or "location".
    - *args*: is a List of {@link WorldArgument}s specifying the
    argument types (and possibly variable names)
    - *bindings*: (**bindable only**) is a list of {@link WorldObject}s
    specifying bindings for args.
    Bindings must match the types or supertypes of args.
    - *valueTypes*: (**assignable only**) is a list of {@link WorldArgument}s
    specifying the types of allowed assigned values.

    Roughly, the two columns indicate a template vis-a-vis an instance,
    where the abstract template specifies allowed types for an instance.
    If a StateProperty is bindable (right column), then its arguments can
    be bound with actual {@link WorldObject}s.
    The arguments of a StateProperty may be bound completely, partially, or
    not at all. If all arguments are bound then the StateProperty is said to
    be *grounded*, otherwise it is said to be *lifted*.
    *
    Considering unassignable StateProperties (top row):
    <ul>
    <li> A{@link StateRelationTemplate} specifies the name and args
    for a relationship between two objects.  For example,
    {@code connected(DOCK, DOCK)} states that two docks are connected.
    </li>
    <li> a {@link StateRelation} is a *bindable* instance of a StateRelationTemplate
    that can accept bindings for its arguments.
    </li>
    </ul>

    *
    Value binding for a StateProperty works differently than argument binding.
    While argument bindings are stored in the StateProperty class,
    value bindings are instead stored in the {@link Statement} class because
    values change over time.
    {@link Statement}s link {@link StateVariable}s to values and timepoints.
    This design allows flexibility during search for, or execution of, assignments.
    Thus, only the value *type* is specified in a StateProperty;
    the bound value of an *assignable* {@link StateProperty} is in a Statement.
    Considering assignable StateProperties (bottom row), there are three types:
    <ul>
    <li>A {@link StateVariableTemplate} specifies the name, argument types
    and valueType(s) to make an attribute of an object.
    For example, {@code location(ROBOT) = DOCK} states that a robot can
    be assigned a location of type DOCK.
    </li>
    </ul>
    <li> A {@link StateVariable} is an *bindable instance of a StateVariableTemplate
    that can accept bindings for its arguments.
    </li>
    Examples of fully ground StateRelation and StateVariable are shown in the above table.

    """

    @property
    def is_attribute(self) -> bool: ...

    @property
    def is_relation(self) -> bool: ...

    @property
    def is_container(self) -> bool: ...

    @property
    def is_bindable(self) -> bool:
        return False

    @property
    def is_assignable(self) -> bool:
        return False

    @property
    def is_static(self) -> bool:
        return self.is_bindable is False

    @property
    def value_type(self) -> VALUE_T: ...
