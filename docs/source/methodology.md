<!-- docs/source/methodology.md -->

# Methodology

PyDAGMC provides a Pythonic abstraction layer over PyMOAB for interacting with DAGMC (Direct Accelerated Geometry Monte Carlo) `.h5m` files. This section delves into the underlying concepts, data structures, and design choices that enable PyDAGMC's functionality.

## PyDAGMC's Internal Initialization Process

While PyDAGMC is a tool intended for use within a larger, user-defined workflow, it's helpful to understand the internal sequence of operations that occurs when a `.h5m` file is loaded. The following diagram illustrates this initialization process, which culminates in a fully interactive `Model` object ready for querying and manipulation. This is not a prescribed user workflow, but rather a conceptual map of how PyDAGMC parses and prepares the geometry data.

```mermaid
flowchart TD
    A["Start: Load .h5m File"] ==> B["Initialize pymoab.Core"]
    B ==> C["Load Entity Sets"]
    C ==> D{"CATEGORY_TAG Present?"}
    D ==> E["Create Objects"]
    E ==> F["Assign IDs and Tags"]
    F ==> G["Build Implicit Relationships"]
    G ==> H["Enable Queries"]
    H ==> I["Extract Geometry"]
    I ==> J["Export to VTK / Analyze"]

    style A stroke:#FFD600,fill:#FFFFFF
    style B stroke:#FFD600,fill:#FFFFFF
    style C stroke:#FFD600,fill:#FFFFFF
    style D stroke:#FFD600,fill:#FFF9C4
    style E stroke:#FFD600,fill:#FFFFFF
    style F stroke:#FFD600,fill:#FFFFFF
    style G stroke:#FFD600,fill:#FFFFFF
    style H stroke:#FFD600,fill:#FFFFFF
    style I stroke:#FFD600,fill:#FFFFFF
    style J stroke:#FFD600,fill:#FFFFFF
    linkStyle 0 stroke:#FFD600
    linkStyle 1 stroke:#FFD600
    linkStyle 2 stroke:#FFD600
    linkStyle 3 stroke:#FFD600
    linkStyle 4 stroke:#FFD600
    linkStyle 5 stroke:#FFD600
    linkStyle 6 stroke:#FFD600
    linkStyle 7 stroke:#FFD600
    linkStyle 8 stroke:#FFD600
```

## Core Design Philosophy

The primary goal of PyDAGMC is to simplify common interactions with DAGMC models by:

1. **Object-Oriented Interface:** Representing DAGMC entities (Groups, Volumes, Surfaces) as intuitive Python objects with methods and properties relevant to their roles.
2. **Abstraction of PyMOAB Complexity:** Hiding some of the lower-level details of PyMOAB's API, particularly around tag handling and entity set traversal for common DAGMC use cases.
3. **Focus on DAGMC Semantics:** Leveraging the specific metadata conventions established by DAGMC for identifying and relating geometric entities.
4. **Ease of Use:** Providing a higher-level API that reduces boilerplate code for common queries and manipulations.

## The DAGMC Data Model

For a detailed explanation of the underlying data structures, see the [](data-model.md) page.

## PyDAGMC Class Structure

The main classes in PyDAGMC mirror the DAGMC entity hierarchy:

* **`Model`:**
  * The entry point for loading and interacting with a DAGMC `.h5m` file.
  * It initializes a `pymoab.core.Core` instance.
  * Provides access to all `Group`s, `Volume`s, and `Surface`s in the model via properties like `model.groups_by_name`, `model.volumes_by_id`, etc.
  * Manages cached MOAB tag handles for efficiency.
  * Tracks used entity IDs to assist in assigning unique IDs to newly created entities.

* **`GeometrySet` (Abstract Base Class):**
  * Provides common functionality for `Group`, `Volume`, and `Surface`.
  * Manages the MOAB entity `handle`.
  * Provides properties for common tags (`id`, `geom_dimension`, `category`).
  * Includes methods for triangle data extraction (`triangle_handles`, `triangle_conn`, `triangle_coords`, `get_triangle_conn_and_coords`), VTK export (`to_vtk`), and entity deletion (`delete`).
  * The `_check_category_and_dimension()` method enforces consistency between `CATEGORY_TAG` and `GEOM_DIMENSION_TAG`.

* **`Surface(GeometrySet)`:**
  * Represents a 2D geometric surface.
  * Provides access to its sense data (`senses`, `forward_volume`, `reverse_volume`).
  * Calculates surface area (`area`).
  * Directly contains triangle mesh elements (`MBTRI`).

* **`Volume(GeometrySet)`:**
  * Represents a 3D geometric volume.
  * Provides access to its constituent `Surface`s (`surfaces`, `surfaces_by_id`).
  * Determines its material assignment by looking for a parent `Group` with a name like `"mat:..."` (`material` property).
  * Calculates its geometric volume (`volume`) using the divergence theorem on its bounding surface triangles and their senses.

* **`Group(GeometrySet)`:**
  * Represents a logical collection of `Volume`s and/or `Surface`s.
  * Identified by a `name` (from `NAME_TAG_NAME`).
  * Provides access to its contained `Volume`s (`volumes`, `volumes_by_id`, `volume_ids`) and `Surface`s (`surfaces`, `surfaces_by_id`, `surface_ids`).
  * Supports adding (`add_set`) and removing (`remove_set`) entities.
  * The `merge()` method allows combining two groups with the same name.

## Limitations and Future Directions

* **Curve and Vertex Entities:** While DAGMC specifications include "Curve" and "Vertex" categories, PyDAGMC currently does not provide dedicated classes or extensive support for them.
* **Advanced Meshing Operations:** PyDAGMC focuses on querying and metadata manipulation, not on mesh generation or modification (beyond loading STLs into surfaces).
* **Performance for Extremely Large Models:** While PyMOAB is efficient, some PyDAGMC operations that iterate over many entities might be optimizable. Caching strategies are used (e.g., for tag handles) but could potentially be expanded.

This methodological overview should provide a clearer picture of how PyDAGMC functions internally and interacts with the underlying DAGMC and PyMOAB libraries.
