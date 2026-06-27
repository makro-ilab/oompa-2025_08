# OOMPA v2025.08: Object-Oriented Modeling for Planning and Acting

**OOMPA is a Python 3.13+ toolkit for modeling hierarchical AI planning domains in an object-oriented style,** allowing developers to annotate Python classes directly with planning primitives (state properties, actions, methods) rather than writing separate PDDL/HDDL files.

> 📄 For a one-page overview, see the **[Executive Summary](EXECUTIVE_SUMMARY.md)**.

## What Is OOMPA?

OOMPA bridges the gap between how software developers naturally think (in terms of objects, attributes, and methods) and how formal planners represent domains (via logical predicates). Instead of requiring expertise in both domain knowledge and planning languages like PDDL or HDDL, developers annotate standard Python classes with decorators to declare:

- **State variables** (typed attributes and relations) via `StatePropertyFactory`
- **Actions** (primitive operators) via `@OompaAction` decorators with preconditions and effects
- **Hierarchical methods** (goal decompositions) via `@OompaMethod` decorators with goal conditions and task networks

The toolkit then introspects these annotations and projects the domain into a flat dictionary-of-dictionaries state representation compatible with planning algorithms. This approach was inspired by OOMPA's predecessor **ActorSim** (a Java-based system developed at the Naval Research Laboratory, 2018–2023) and combines principles from the open-source **GTPyhop** hierarchical task-network planner, adapted for the accessibility and expressiveness of Python 3.13.

## Status: Research-Grade, Partially Implemented

**OOMPA 2025.08 is a first-cut release.** Many core features are functional and demonstrable on realistic domains (restaurant, transport, logistics), but several planned capabilities remain incomplete or unproven:

- **PDDL translation** (`as_pddl()` export) is **unimplemented**—the planner interface is designed but no concrete translator to PDDL has been written.
- **Planner integration** lacks a built-in planning algorithm; the toolkit provides `get_applicable_actions(state)` for integration with external planners, but no example planner is shipped.
- **Partial-order goal networks (POHGN)** are implemented but lightly tested; examples use only total-order decompositions.
- **Temporal, resource, and concurrency constraints** are out of scope in this release.

See `KNOWN_ISSUES.md` in the release for a detailed list of bugs and TODOs.

## Installation & Requirements

**Python version:** 3.13 or later (leverages Python 3.13's type-introspection and descriptor protocols).

**Installation:**
```bash
pip install oompa-toolkit
```

**Dependencies:** 
- `networkx` (for partial-order goal networks)
- `typing` and standard library descriptors (built-in)

**Verify installation:**
```python
from oompa_types.objects import AbstractNamed
from oompa_types.state_property import StatePropertyFactory
print("OOMPA 2025.08 ready")
```

## Quick Example: Simple Restaurant

Here's a minimal domain showing how a patron sits at a table using `@OompaAction` and `StatePropertyFactory`:

```python
from oompa_types.objects import AbstractNamed
from oompa_types.state_property import StatePropertyFactory
from oompa_types.action import OompaAction

class Table(AbstractNamed):
    occupied: bool = StatePropertyFactory(False)
    server: str | None = StatePropertyFactory(None)

class Patron(AbstractNamed):
    table: Table | None = StatePropertyFactory(None)
    
    @OompaAction
    def sit(self, table: Table):
        """Patron sits at a table."""
        pass
    
    @sit.precondition
    def sit(self, table: Table):
        # Table must not be occupied
        return table.occupied.equals(False)
    
    @sit.effect
    def sit(self, table: Table):
        # Occupy the table and assign patron
        return (
            table.occupied.assigned(True),
            table.server.assigned(self.name)
        )

# Usage:
patron = Patron(name="Alice")
table = Table(name="Table1")
result = patron.sit.apply(state, result={})
```

The `StatePropertyFactory` fields declare mutable, typed state properties that the planner can inspect. Preconditions and effects use a restricted, declarative operator set (not arbitrary Python) to enable domain introspection and future translation to PDDL.

## Core Concepts

### StateProperty: Unified Attribute/Relation Model

A **StateProperty** represents a typed, mutable attribute or relation visible to the planner. Attributes have arity 1 (one parameter: the object itself); relations have arity > 1 (multiple parameters). The toolkit unifies both under a single `StateProperty` abstraction:

```python
# Unary attribute (arity 1)
table.occupied: bool = StatePropertyFactory(False)

# Binary relation (arity 2) — declared on a container class
class Map(AbstractNamed):
    distance: Callable = StatePropertyFactory(lambda loc1, loc2: ...)
```

The `StatePropertyFactory` descriptor handles type validation, getter/setter logic, and provides a **fluent API** for building conditions and effects via method chaining (e.g., `table.occupied.assigned(True)` rather than direct assignment).

### @OompaAction: Primitive Operators with Preconditions & Effects

Actions are methods decorated with `@OompaAction`, with two required sub-decorators:

```python
@OompaAction
def sit(self, table: Table):
    """Actor is self; parameters come from the function signature."""
    pass

@sit.precondition
def sit(self, table: Table):
    """Returns a Condition; must use declarative operators."""
    return table.occupied.equals(False)

@sit.effect
def sit(self, table: Table):
    """Returns an Effect or Effect sequence."""
    return table.occupied.assigned(True)
```

**Key differences from GTPyhop:** Preconditions and effects are **declarative** (use curated operators like `equals`, `contains`, `assigned`, `appends`) and **inspectable**, not arbitrary Python code. This restriction enables domain analysis and future export to PDDL.

### @OompaMethod: Goal Decomposition via Total/Partial-Order Networks

Methods decompose goals into subgoals and actions using three sub-decorators:

```python
@OompaMethod
def m_order(self, desired: Dish):
    """Method to achieve patron's order."""
    pass

@m_order.goal
def m_order(self, desired: Dish):
    """The goal this method achieves."""
    return self.desired_order.equals(desired)

@m_order.precondition
def m_order(self, desired: Dish):
    """Precondition for applicability."""
    return self.is_hungry.equals(True)

@m_order.body
def m_order(self, desired: Dish):
    """Decomposition into ordered subgoals/actions."""
    return TotalOrderGoalTaskNetwork([
        self.sit,          # Action
        self.pickup_menu,  # Action
        self.request_server,  # Action
        self.place_order   # Action
    ])
```

**Total-order networks (TOHGN)** process goals sequentially; **partial-order networks (POHGN)** use NetworkX directed graphs for arbitrary precedence constraints. Both are supported; examples primarily use total-order.

### Flat Dictionary-of-Dictionaries State Representation

State is a flat dict-of-dicts: `state[property_name][object_name] = value`. This representation is **GTPyhop-compatible** and enables efficient planning:

```python
state = {
    'occupied': {'table1': True, 'table2': False},
    'server': {'table1': 'Sam', 'table2': None},
    'table': {'Alice': 'table1', 'Bob': None}
}
```

State snapshots are frozen (hashable) for use in search algorithms and can be unfrozen for mutation during planning or acting.

### Domain and Problem Classes

The `Domain` class registers types and auto-discovers actions/methods via introspection:

```python
domain = Domain()
domain.declare_types(Patron, Table, Server)
problem = domain.instantiate_problem(
    objects=[Alice, Table1, Sam],
    initial_goal=Goal(Alice.is_hungry.equals(False))
)
state = problem.current_state()
applicable_actions = problem.get_applicable_actions(state)
```

No separate PDDL/HDDL file is needed; the domain is defined entirely in Python.

## Bundled Example Domains

The toolkit includes several fully-implemented example domains:

1. **Restaurant** (running example in the paper) — Patrons order meals; involves roles (Patron, Server, Cook, Table, Menu). Demonstrates `@OompaAction`, `@OompaMethod`, `InsertNewObjectEffect` (dynamic object creation), and total-order goal networks.

2. **Simple Travel** & **Extended Travel** (GTPyhop ports) — A person travels between locations by foot or taxi. Demonstrates numeric preconditions, static computed relations (`Map.distance`), and ForAll patterns.

3. **Transport/Koala** — Vehicles deliver packages across a map. Demonstrates n-ary relations (e.g., `Map.road(loc1, loc2)`), probabilistic effects, and domain-level relation declarations.

4. **Depot** (logistics benchmark) — Hoists stack/unstack crates on trucks. Demonstrates 3-ary relations (reified via relation containers), probabilistic effects, and method-based decomposition.

Each domain includes a test suite exercising action applicability, state mutation, goal decomposition, and search scenarios.

## Limitations & Future Work

**Major limitations:**

1. **PDDL export is unimplemented.** The planned `as_pddl()` method is a stub; translation to PDDL or other planning languages remains to be proven.

2. **No bundled planner.** OOMPA provides `get_applicable_actions(state)` for integration with external planners, but does not ship a planning algorithm. Integration with GDP (Goal Decomposition Planner), A*, or other solvers must be implemented by the user.

3. **Temporal and resource constraints out of scope.** This release handles discrete state changes; continuous time, duration constraints, resource allocation, and concurrency are not supported.

4. **Partial-order networks lightly tested.** POHGN support is implemented but examples use only total-order decompositions.

5. **Design burden on developers.** Declarative preconditions/effects and state-property annotations add overhead compared to free-form Python (as in GTPyhop). This is the price paid for inspectability and translatability.

**Planned enhancements:**

- PDDL export and compatibility with standard planners (UP, Fast Downward)
- LLM-assisted domain engineering (agentic workflows to generate OOMPA annotations from natural language or existing code)
- Tighter integration with HTN/HGN research tools
- Benchmark evaluation against IPC domains

See `KNOWN_ISSUES.md` for detailed lists of bugs, unimplemented features, and TODO items.

## Citation & License

**Citation:** If you use OOMPA in research, please cite the KEPS 2026 workshop paper:

```bibtex
@inproceedings{Roberts2026OOMPA,
  author = {Roberts, Mark C. and Chan, David H. and Nau, Dana S. and Macbeth, Jamie C.},
  title = {OOMPA v2025.08: Object-Oriented Modeling for Planning and Acting},
  booktitle = {Proceedings of the ICAPS 2026 Knowledge Engineering for Planning and Scheduling (KEPS) Workshop},
  year = {2026}
}
```

**License:** [License type to be determined and included in final release—see LICENSE file in the repository.]

## Acknowledgments

OOMPA 2025.08 was developed at the **Naval Research Laboratory (NRL)** Navy Center for Applied Research in AI. The toolkit builds on three decades of hierarchical planning research and directly descends from the **ActorSim** system (NRL, 2018–2023). We thank the HTN/HGN research community for foundational concepts, and acknowledge the open-source **GTPyhop** project for the state-representation design that inspired OOMPA's flat dictionary interface.



---

## Getting Started

1. Install: `pip install oompa-toolkit`
2. Read the [examples/](examples/) directory for runnable domain templates.
3. Study the bundled domains (restaurant, transport, depot) in `tests/` for reference implementations.
4. Consult `KNOWN_ISSUES.md` for known limitations before starting your own domain.
5. Reach out to the authors or open an issue on GitHub if you encounter problems or have feedback.

---

*OOMPA is research-grade software. Feedback, pull requests, and collaboration are welcome.*
