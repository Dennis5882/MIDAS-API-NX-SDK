# Document, operations, view

These endpoint families wrap their body in `"Argument"` rather than an
ID-keyed `"Assign"`, so they are plain functions rather than resource classes.

!!! danger "Most of the destructive surface is here"
    `/doc/NEW` discards unsaved work. `/doc/OPEN` replaces the open document.
    Every path resolves on the machine running NX, not the one running your
    script. See [Destructive operations and recovery](../safety.md).

## Document lifecycle

::: midas_nx.doc

## Operations

::: midas_nx.ope
    options:
      members:
        - divide_elements
        - auto_mesh
        - convert_surface_spring
        - calculate_story

## View

::: midas_nx.view
    options:
      members:
        - select_by_identity
        - capture_view
