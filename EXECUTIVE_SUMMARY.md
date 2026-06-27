# Executive Summary — The OOMPA Toolkit

**O**bject-**O**riented **M**odeling for **P**lanning and **A**cting (OOMPA)

**Version 2025.08** · 11 August 2025

Mark "Mak" Roberts
Adaptive Systems Section | Navy Center for Applied Research in AI
Naval Research Laboratory

OOMPA, Object Oriented Modeling for Planning and Acting, is a toolkit to support modeling
planning domains in an object-oriented manner, distinct from the usual formal logic style
found in many planning systems. OOMPA is built around the same design principles as the
ActorSim system was previously built. ActorSim was previously released in a series of pub
releases from 2018 through 2023. ActorSim was developed in Java but was challenging to use
because it required deep expertise in the automated planning languages as well as deep
understanding of the Java language, which is less frequently taught to software developers.
OOMPA builds on lessons learned from the ActorSim and:

- Leverages design principles from ActorSim
- Uses Python 3.13, the latest stable release of Python.
- Supports Python's typing and introspection modules, greatly simplifying modeling tasks.
- Fully supports object-oriented modeling (as opposed to the usual declarative logic
  representations typical in automated planning languages) and provides Python annotations
  that allow programmers to annotate objects to link them to a planning system.
- Leverages a state representation similar to the representation used by an open-source
  library called GTPyhop (https://github.com/dananau/GTPyhop).
- Provides an initial set of example domains to demonstrate how to use OOMPA.
- Provides several draft unit tests and algorithm sketches to demonstrate planning.

Together, these design choices make it much easier for anyone who knows Python to use the
software without needing expertise in automated planning languages. OOMPA is already used
in several NRL projects, notably the GraphWorld Simulator.

This initial draft of the software is to support collaboration with academic collaborators,
who have expressed an interest in using it for their projects.

Distribution A: Approved for public release, distribution is unlimited.
