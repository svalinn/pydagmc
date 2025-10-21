---
title: 'PyDAGMC: A Pythonic Interface for DAGMC'
authors:
  - name: Patrick Shriwise
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Paul Wilson
    orcid: 0000-0000-0000-0000
    affiliation: 2
  - name: Paul Romano
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Ethan Peterson
    orcid: 0000-0000-0000-0000
    affiliation: 3
  - name: Ahnaf Tahmid Chowdhury
    orcid: 0000-0000-0000-0000
    affiliation: 4
  - name: Jonathan Shimwell
    orcid: 0000-0000-0000-0000
    affiliation: 5
affiliations:
 - name: Argonne National Lab
   index: 1
 - name: University of Wisconsin-Madison
   index: 2
 - name: Massachusetts Institute of Technology
   index: 3
 - name: NukeHub
   index: 4
 - name: Proxima Fusion
   index: 5
date: 01 November 2025
language: en
bibliography: paper.bib
---

# Summary

PyDAGMC is a Python library that provides a high-level, object-oriented interface for interacting with Direct Accelerated Geometry Monte Carlo (DAGMC) `.h5m` files. It simplifies the process of querying and manipulating the geometric and metadata information stored in these files, which are commonly used in computational modeling and simulation. By abstracting the complexities of the underlying Mesh-Oriented datABase (MOAB) and its Python binding, PyMOAB, PyDAGMC allows users to work with DAGMC models in a more intuitive and Pythonic way. The library provides classes for representing DAGMC entities such as groups, volumes, and surfaces, and offers a range of features for navigating the geometry hierarchy, accessing metadata, and extracting mesh data.

# Statement of Need

The analysis of complex geometries in Monte Carlo radiation transport simulations often relies on the DAGMC toolkit [@dagmc], which uses MOAB [@moab] as its backend for mesh representation. While PyMOAB provides a Python interface to MOAB, its usage can be verbose and requires a deep understanding of the low-level data structures. This can be a barrier for scientists and engineers who want to perform common tasks such as identifying materials, querying adjacencies, or manipulating geometric entities.

PyDAGMC addresses this need by providing a simplified API that reduces the boilerplate code required for these operations. It allows users to interact with the DAGMC model through a set of intuitive Python objects, making it easier to integrate DAGMC-based workflows into larger Python applications. This lowers the barrier to entry for using DAGMC and enables more rapid development of analysis and simulation tools.

# Features

PyDAGMC offers a range of features to simplify working with DAGMC models:

*   **Object-Oriented Interface:** Represents DAGMC entities (Groups, Volumes, Surfaces) as intuitive Python objects.
*   **Topological Queries:** Easily navigate the relationships between volumes and surfaces, and query entities within groups.
*   **Metadata Access:** Retrieve and modify DAGMC metadata such as names, IDs, and material assignments.
*   **Mesh Data Extraction:** Extract triangle connectivity and vertex coordinates for visualization and analysis.
*   **Geometry Manipulation:** Create, delete, and modify groups, volumes, and surfaces.
*   **VTK Export:** Generate VTK files for visualizing the geometry in tools like ParaView or VisIt.

# Example Usage

```python
import pydagmc

# Load a DAGMC model
model = pydagmc.Model('dagmc.h5m')

# Access volumes by material
fuel_volumes = model.find_volumes_by_material('fuel')

# Get the surfaces of a volume
for volume in fuel_volumes:
    for surface in volume.surfaces:
        print(f'Surface {surface.id} has area {surface.area:.2f} cm^2')

# Create a new group and add a volume to it
new_group = model.create_group(name="new_group")
new_group.add_set(fuel_volumes[0])

# Write the modified model to a new file
model.write_file('new_dagmc.h5m')
```

# Acknowledgements

PyDAGMC is a community-developed project, and we are grateful to all who have contributed.We also acknowledge the foundational work of
the DAGMC and MOAB development teams, as PyDAGMC is built upon these essential tools.

# References