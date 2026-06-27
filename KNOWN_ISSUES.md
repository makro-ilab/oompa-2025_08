# Known Issues — OOMPA 2025.08

OOMPA 2025.08 is an **initial, research-grade release** (the StateProperty line). It is
published as-is to support academic collaboration; the items below are documented rather than
fixed. Contributions welcome.

## Capability limitations / future work

Intended scope limits of this early release, drawn from the accompanying paper and talk:

- **No PDDL / HDDL export yet.** A planned `as_pddl()` export would compile OOMPA models to
  PDDL/HDDL, but it is unimplemented and the translation is **unproven** (formal correspondence
  is future work).
- **PDDL / HDDL import is harder still** and is not provided.
- **No temporal, resource, or concurrency constraints** — capabilities OOMPA does not yet
  provide.
- **Not a planner.** OOMPA is a modeling language; it ships no search engine, and integration
  with existing planners is not yet available.
- **No `action.cost` field yet** — planners cannot read or customize per-action costs.
- **Example algorithms are illustrative.** The bundled GDP and A* sketches are simplified
  (e.g. the GDP variant omits cycle detection) and are not production search implementations.
- **Acting linkage is untested.** The `@OompaAction.execute` subdecorator exists but is not
  exercised.
- **No standard-benchmark evaluation** and **no SAS+ / Finite-Domain-Representation export**
  yet — left as future work.
- **Goal interference / replanning** (replanning when expected scene paths are blocked) is not
  implemented.

## Known bugs

Real defects on this line, not yet fixed:

- **`domain/operator_bases.py`** — `SupportsOperators.not_contains()` recurses on itself (the
  surrounding `contains()` / operator methods are protocol stubs).
- **`domain/operator.py`** — `Operator.invert()` does not apply DeMorgan when inverting `AND` /
  `OR`.
- **`effect/effect_bases.py`** — `ProbabilisticEffect` mis-references its outcomes collection;
  `apply()` correctness is also flagged in-code.
- **`action/action_bases.py`** — `ForAllAction.effect` builds an `AndCondition` rather than an
  effect conjunction.
- **`objects/typed.py`** — the `Typed.type` property returns `type(T)` (always `type`) instead
  of the bound type.

## Unimplemented / stubs

- `domain/state.py` — `as_pddl()` stub (see above).
- `domain/quantification.py` — `ExistsList.dereference()` is a `pass` stub.
- `.reference` subdecorator — unimplemented on `ActionDescriptor` and `MethodDescriptor`.
- `goal_network/gtn_node_bases.py` — `TaskNode` is a stub.

## Coverage notes

- **Partial-order** goal-task networks are implemented but only lightly exercised; total-order
  is the well-trodden path.
- The restaurant example covers the Entering / Ordering scenes in detail; Eating / Exiting are
  present but less developed.
- A large legacy `@deprecated` goal-network layer remains in-tree for reference.

## Test status

On this release line the suite runs **32 passing, 1 skipped**, with these **pre-existing**
failures (independent of the 2025.08 cleanup):

- `tests/test_transport_probabilistic.py::test_probabilistic_effects` — incomplete test
  (`TransportProblem` undefined).
- `tests/test_simple_travel_hgn.py::TestTravelHGN::test_method_travel_by_foot`.
- `tests/test_helpers.py::test_and_reset` and `tests/test_restaurant.py::test_and_reset`
  (fixture / collection errors).
