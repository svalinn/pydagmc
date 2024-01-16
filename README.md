# PyDAGMC

PyDAGMC is a Python interface for interacting with DAGMC .h5m files through the embedded topological relationships and metadata contained within. These interactions occur through a set of Python classes corresponding to DAGMC’s metadata Group (a grouping of volumes or surfaces), Volume, and Surface groupings in the mesh database. This interface is intended to provide a simple interface for obtaining information about DAGMC models, replacing significant boilerplate code required to perform the same queries with PyMOAB, the Python interface for MOAB itself.

PyDAGMC classes provide the ability to perform basic queries as properties of the class instances. These queries include:

- number of entities contained within a group
- volume and surface relationships
- number of triangles contained underneath any class instance
- triangle connectivity and coordinates underneath any class instance
- movement of volumes or surfaces into and out of groups
- VTK file generation for all triangles contained under any class instance


# Example

Code:

```python
import dagmc

model = dagmc.DAGModel('dagmc.h5m')

print(model.groups)

fuel_group = groups['mat:fuel']

v1 = fuel_group.get_volumes()[1]

print(v1)
```
Output:

```shell
{'picked': Group 1, Name: picked
, 'mat:fuel': Group 2, Name: mat:fuel
Volume IDs:
[1 2]
, 'mat:Graveyard': Group 0, Name: mat:Graveyard
Volume IDs:
[6]
, 'mat:41': Group 0, Name: mat:41
Volume IDs:
[3]
, 'temp:300': Group 0, Name: temp:300
Volume IDs:
[1 2 3]
}

Volume 1, 4092 triangles
```

Code:

```python
# move volume 1 from the fuel group to the group "mat:41"
groups['mat:fuel'].remove_set(v1)
groups['mat:41'].add_set(v1)

print(groups['mat:fuel'])
print(groups['mat:41'])
```

Output:

```shell
Group 2, Name: mat:fuel
Volume IDs:
[2]

Group 0, Name: mat:41
Volume IDs:
[1 3]
```