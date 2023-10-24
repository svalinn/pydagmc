# PyDAGMC

A convenience interface for examining and reassigning metadata in DAGMC models with PyMOAB.

# Example

Code:

```python
from pymoab import core
from dagmc import dagnav

mb = core.Core()
mb.load_file('dagmc.h5m')

groups = dagnav.get_groups(mb)
print(groups)

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