# User's Guide

This guide provides an overview of PyDAGMC, installation instructions,
and basic usage examples.

## Installation

### Prerequisites

PyDAGMC relies on [MOAB](https://ftp.mcs.anl.gov/pub/fathom/moab-docs/building.html) with Python bindings.
Please ensure MOAB is installed and functional in your Python environment.

### Installing PyDAGMC

You can install PyDAGMC using pip:

```bash
pip install pydagmc
```

Or, for the latest development version:

```bash
pip install git+https://github.com/svalinn/pydagmc.git
```

For developers, clone the repository and install in editable mode:

```bash
git clone https://github.com/svalinn/pydagmc.git
cd pydagmc
pip install -e .[test,docs]
```

### Example Usage

Here's a quick look at how you can use PyDAGMC:

```python
import pydagmc

# Load a DAGMC model from an .h5m file
model = pydagmc.Model('dagmc.h5m')

# Access groups by their names
group_dict = model.groups_by_name
print("Available groups in the model:", list(group_dict.keys()))

# Get a specific group, e.g., 'mat:fuel'
if 'mat:fuel' in group_dict:
    fuel_group = group_dict['mat:fuel']
    print(f"\nDetails of '{fuel_group.name}':")
    print(fuel_group) # Displays group ID, name, and contained volume/surface IDs

    # Access a volume by its ID from within the group
    # Ensure volume ID 1 actually exists in the 'mat:fuel' group
    try:
        volume_1 = fuel_group.volumes_by_id[1]
        print(f"\nDetails of Volume {volume_1.id}:")
        print(volume_1) # Displays volume ID and its triangle count
        print(f"Material of Volume {volume_1.id}: {volume_1.material}")

    except KeyError:
        print(f"Volume ID 1 not found in the '{fuel_group.name}' group.")

    # Example of moving a volume (if volume_1 was found)
    if 'volume_1' in locals() and 'mat:moderator' in group_dict:
        moderator_group = group_dict['mat:moderator']
        print(f"\nMoving Volume {volume_1.id} from '{fuel_group.name}' to '{moderator_group.name}'...")
        fuel_group.remove_set(volume_1)
        moderator_group.add_set(volume_1)

        print(f"\nUpdated '{fuel_group.name}':")
        print(fuel_group)
        print(f"\nUpdated '{moderator_group.name}':")
        print(moderator_group)

else:
    print("Group 'mat:fuel' not found in the model.")

# Create a new, empty group
new_group = model.create_group(name="my_custom_group", group_id=25)
print(f"\nCreated new group:")
print(new_group)

# Save changes back to a new H5M file
model.write_file('updated_dagmc.h5m')
print("\nModel changes saved to updated_dagmc.h5m")
```

That's it! PyDAGMC makes it easy to work with DAGMC models in Python. For a more in-depth exploration, check out the [Tutorial](tutorial.ipynb).
