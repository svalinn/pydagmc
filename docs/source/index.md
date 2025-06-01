# Welcome to PyDAGMC

PyDAGMC is a Python interface for interacting with DAGMC `.h5m` files
through the embedded topological relationships and metadata contained within.
These interactions occur through a set of Python classes corresponding to
DAGMC’s metadata Group, Volume, and Surface groupings in the mesh database.
This interface is intended to provide a simple interface for obtaining
information about DAGMC models, replacing significant boilerplate code
required to perform the same queries with PyMOAB, the Python interface
for MOAB itself.

This documentation provides a comprehensive guide to PyDAGMC, from installation
and basic usage to advanced topics and the complete API reference.

## Key Features

PyDAGMC offers a range of features to simplify working with DAGMC models:

* **Intuitive Object Model:** Python classes (`Group`, `Volume`, `Surface`) that mirror DAGMC's hierarchical structure.
* **Metadata Access:** Easily retrieve and modify DAGMC metadata such as names, global IDs, categories, and material assignments.
* **Topological Queries:**
  * Determine the number of entities (volumes, surfaces) contained within a group.
  * Navigate volume-surface relationships (parent/child connections, surface senses).
  * Identify volumes associated with specific materials or those without material assignments.
* **Mesh Data Extraction:**
  * Count the number of triangles contained under any class instance (Group, Volume, or Surface).
  * Retrieve triangle connectivity (vertex indices) and vertex coordinates.
* **Geometry Manipulation:**
  * Move volumes or surfaces into and out of groups.
  * Create new, empty groups, volumes, or surfaces.
  * Load triangle mesh data from STL files directly into `Surface` objects.
* **VTK Export:** Generate VTK files for visualizing all triangles contained under any Group, Volume, or Surface instance, compatible with tools like ParaView or VisIt.
* **Integration with PyMOAB:** Built on PyMOAB, allowing for seamless interoperability if lower-level MOAB access is needed.

## Getting Started

If you're new to PyDAGMC, we recommend starting with the [User's Guide](./user-guide.md) for installation and basic concepts, followed by the [Tutorial](./tutorial.ipynb) for a hands-on example.

```{toctree}
:maxdepth: 1
:caption: Contents:
:hidden: true

user-guide
tutorial
methodology
api/index
contributing
code-of-conduct
security
license
getting-help
```
