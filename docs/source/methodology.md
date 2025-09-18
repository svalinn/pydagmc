<!-- docs/source/methodology.md -->

# Methodology

PyDAGMC provides a Pythonic abstraction layer over PyMOAB for interacting with DAGMC (Direct Accelerated Geometry Monte Carlo) `.h5m` files. This section delves into the underlying concepts, data structures, and design choices that enable PyDAGMC's functionality.

## File Loading

When a file is loaded, its embedded geometric topology relationships and metadata (material/property assignments) are loaded according to the conventions established by the DAGMC library. This process culminates in a fully interactive `Model` object ready for querying and manipulation.

## Core Design Philosophy

The primary goal of PyDAGMC is to simplify common interactions with DAGMC models by:

1. **Object-Oriented Interface:** Representing DAGMC entities (Groups, Volumes, Surfaces) as intuitive Python objects with methods and properties relevant to their roles.
2. **Abstraction of PyMOAB Complexity:** Hiding some of the lower-level details of PyMOAB's API, particularly around tag handling and entity set traversal for common DAGMC use cases.
3. **Focus on DAGMC Semantics:** Leveraging the specific metadata conventions established by DAGMC for identifying and relating geometric entities.
4. **Ease of Use:** Providing a higher-level API that reduces boilerplate code for common queries and manipulations.

## The DAGMC Data Model

PyDAGMC's functionality is deeply tied to the data model established by DAGMC, which uses standard MOAB tags to imbue a `.h5m` file with specific semantic meaning. Understanding this data model is crucial to understanding how PyDAGMC interprets the geometry and its associated metadata.

### Entity Sets (`MBENTITYSET`)

At the core, DAGMC geometry is organized using MOAB **Entity Sets**. These are collections of other entities, which can include mesh elements (like triangles) or other entity sets, forming a hierarchical structure. PyDAGMC maps these entity sets to its `Group`, `Volume`, and `Surface` classes.

### Essential MOAB Tags Used by DAGMC

PyDAGMC uses PyMOAB to query data associated with entity sets through these tags:

1. **`CATEGORY_TAG_NAME` (String, length 32):**
    * **Purpose:** Identifies the type of DAGMC entity.
    * **PyDAGMC Usage:** This is the primary tag used to distinguish between `Group`, `Volume`, and `Surface` entity sets.
        * `"Group"`: Maps to `pydagmc.Group`
        * `"Volume"`: Maps to `pydagmc.Volume`
        * `"Surface"`: Maps to `pydagmc.Surface`
    * PyDAGMC classes (`Group`, `Volume`, `Surface`) have internal `_category` attributes that are checked and can be set via the `.category` property.

2. **`GLOBAL_ID_TAG_NAME` (Integer):**
    * **Purpose:** Provides a unique integer identifier for DAGMC entities (Volumes and Surfaces, and sometimes Groups).
    * **PyDAGMC Usage:** Accessed via the `.id` property of `pydagmc.Group`, `pydagmc.Volume`, and `pydagmc.Surface` objects. PyDAGMC maintains a set of used IDs per entity type within a `Model` instance to help prevent collisions when creating new entities.

3. **`NAME_TAG_NAME` (String, variable length, typically up to `NAME_TAG_SIZE`=256):**
    * **Purpose:** Assigns a human-readable name, primarily to DAGMC Groups. This is often used for material assignments (e.g., `"mat:fuel"`, `"mat:water"`) or other logical groupings (e.g., `"boundary:vacuum"`, `"importance:1"`).
    * **PyDAGMC Usage:** Accessed via the `.name` property of `pydagmc.Group` objects. PyDAGMC parses group names like `"mat:material_name"` to provide convenient access to material information through `Volume.material`.

4. **`GEOM_DIMENSION_TAG_NAME` (Integer):**
    * **Purpose:** Specifies the geometric dimension of the entity.
    * **PyDAGMC Usage:**
        * `Surface`: Expected dimension `2`.
        * `Volume`: Expected dimension `3`.
        * `Group`: Expected dimension `4` (representing a collection of lower-dimensional entities).
    * PyDAGMC classes have internal `_geom_dimension` attributes. The `GeometrySet._check_category_and_dimension()` method ensures consistency between the `CATEGORY_TAG` and `GEOM_DIMENSION_TAG`. If one is set and the other is not, PyDAGMC attempts to infer and assign the missing tag, issuing a warning. If both are set but inconsistent, an error is raised.

5. **`GEOM_SENSE_2_TAG_NAME` ("GEOM_SENSE_2", 2 Handles):**
    * **Purpose (for Surfaces):** Defines the relationship between a `Surface` and its bounding `Volume`(s). It stores two entity handles:
        * The first handle points to the `Volume` on the "forward" side (where the surface normals point outward from this volume).
        * The second handle points to the `Volume` on the "reverse" side.
        * A handle value of `0` indicates no volume on that side (e.g., an external boundary surface).
    * **PyDAGMC Usage:** Accessed via `Surface.senses`, `Surface.forward_volume`, and `Surface.reverse_volume` properties. This tag is crucial for determining adjacency and for calculations like volume computation.

### Implicit Relationships (Parent-Child)

MOAB allows entity sets to contain other entity sets, forming parent-child relationships.

* **Volumes and Surfaces:** A `Volume` entity set typically contains `Surface` entity sets that form its boundary. PyDAGMC uses `mb.get_child_meshsets(volume_handle)` to find a `Volume`'s surfaces and `mb.get_parent_meshsets(surface_handle)` to find a `Surface`'s parent volumes.
* **Groups and Volumes/Surfaces:** A `Group` entity set contains `Volume` and/or `Surface` entity sets. PyDAGMC uses `mb.get_entities_by_type_and_tag` within the group's handle to find its constituent volumes and surfaces.

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