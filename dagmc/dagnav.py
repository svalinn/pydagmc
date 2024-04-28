from __future__ import annotations
from abc import abstractmethod
from functools import cached_property
from itertools import chain
from typing import Optional, Dict
from warnings import warn

import numpy as np
from pymoab import core, types, rng, tag


class DAGModel:

    def __init__(self, moab_file):
        if isinstance(moab_file, core.Core):
            self.mb = moab_file
        else:
            self.mb = core.Core()
            self.mb.load_file(moab_file)

        self.used_ids = {}
        self.used_ids[Surface] = set(self.surfaces_by_id.keys())
        self.used_ids[Volume] = set(self.volumes_by_id.keys())
        self.used_ids[Group] = set(group.id for group in self.groups)

    def _sets_by_category(self, set_type : str):
        """Return all sets of a given type"""
        return self.mb.get_entities_by_type_and_tag(self.mb.get_root_set(), types.MBENTITYSET, [self.category_tag], [set_type])

    @property
    def surfaces(self):
        return [Surface(self, h) for h in self._sets_by_category('Surface')]

    @property
    def surfaces_by_id(self):
        return {s.id: s for s in self.surfaces}

    @property
    def volumes(self):
        return [Volume(self, h) for h in self._sets_by_category('Volume')]

    @property
    def volumes_by_id(self):
        return {v.id: v for v in self.volumes}

    @property
    def groups(self):
        return self.groups_by_name.values()

    @property
    def groups_by_name(self) -> Dict[str, Group]:
        group_handles = self._sets_by_category('Group')

        group_mapping = {}
        for group_handle in group_handles:
            # create a new class instance for the group handle
            group = Group(self, group_handle)
            group_name = group.name
            # if the group name already exists in the group_mapping, merge the two groups
            if group_name in group_mapping:
                group_mapping[group_name].merge(group)
                continue
            group_mapping[group_name] = group
        return group_mapping

    @property
    def group_names(self) -> list[str]:
        return self.groups_by_name.keys()

    def __repr__(self):
        return f'{type(self).__name__} {self.id}, {self.num_triangles} triangles'

    @cached_property
    def id_tag(self):
        """Returns the ID tag.
        """
        return self.mb.tag_get_handle(types.GLOBAL_ID_TAG_NAME)

    @cached_property
    def category_tag(self):
        """Returns the category tag used to intidate the use of meshset. Values include "Group", "Volume", "Surface".
        "Curve" and "Vertex" are also present in the model options but those classes are not supported in this package.
        """
        return self.mb.tag_get_handle(
            types.CATEGORY_TAG_NAME,
            types.CATEGORY_TAG_SIZE,
            types.MB_TYPE_OPAQUE,
            types.MB_TAG_SPARSE,
            create_if_missing=True
        )

    @cached_property
    def name_tag(self):
        return self.mb.tag_get_handle(
            types.NAME_TAG_NAME,
            types.NAME_TAG_SIZE,
            types.MB_TYPE_OPAQUE,
            types.MB_TAG_SPARSE,
            create_if_missing=True,
    )

    @cached_property
    def geom_dimension_tag(self):
        return self.mb.tag_get_handle(
            types.GEOM_DIMENSION_TAG_NAME,
            1,
            types.MB_TYPE_INTEGER,
            types.MB_TAG_SPARSE,
            create_if_missing=True,
        )

    @cached_property
    def surf_sense_tag(self):
        """Surface sense tag."""
        return self.mb.tag_get_handle(
            "GEOM_SENSE_2",
            2,
            types.MB_TYPE_HANDLE,
            types.MB_TAG_SPARSE,
            create_if_missing=True,
        )

    def write_file(self, filename):
        """Write the model to a file.

        Parameters
        ----------
        filename : str
            The file to write to.
        """
        self.mb.write_file(filename)

    def add_groups(self, group_map):
        """Adds groups of DAGSets to the model.

        Parameters
        ----------
        group_map : dict
            A dictionary whose keys are 2-tuples of (str, int) containing the
            group name and group ID respectively and whose values are iterables
            of DAGSet objects or DAGSet ID numbers.
        """
        for (group_name, group_id), dagsets in group_map.items():
            # create a new group or get an existing group
            group = Group.create(self, name=group_name, group_id=group_id)

            for dagset in dagsets:
                if isinstance(dagset, DAGSet):
                    group.add_set(dagset)
                else:
                    if dagset in self.volumes_by_id:
                        group.add_set(self.volumes_by_id[dagset])
                    elif dagset in self.surfaces_by_id:
                        group.add_set(self.surfaces_by_id[dagset])
                    else:
                        raise ValueError(f"DAGSet ID={dagset} could not be "
                                         "found in model volumes or surfaces.")

    def create_group(self, name: Optional[str] = None, group_id: Optional[int] = None) -> Group:
        """Create a new empty group instance with the given name,
        or return an existing group if one exists."""
        return Group.create(self, name, group_id)

    def create_volume(self, global_id: Optional[int] = None) -> Volume:
        """Create a new empty volume set"""
        return Volume.create(self, global_id)

    def create_surface(self, global_id: Optional[int] = None) -> Surface:
        """Create a new empty surface set"""
        return Surface.create(self, global_id)


class DAGSet:
    """
    Generic functionality for a DAGMC EntitySet.
    """
    def __init__(self, model: DAGModel, handle: np.uint64):
        self.model = model
        self.handle = handle

    def _check_category_and_dimension(self):
        """Check for consistency of category and geom_dimension tags"""
        stype = self._category.lower()
        identifier = f"{stype} '{self.name}'" if stype == 'group' else f"{stype} ID={self.id}"
        geom_dimension = self.geom_dimension
        category = self.category

        if geom_dimension != -1:
            # If geom_dimension is assigned but not consistent, raise exception
            if geom_dimension != self._geom_dimension:
                raise ValueError(f"DAGMC {identifier} has geom_dimension={geom_dimension}.")

            # If category is unassigned, assign it based on geom_dimension
            if category is None:
                warn(f"Assigned category {self._category} to {identifier}.")
                self.category = self._category

        if category is not None:
            # If category is assigned but not consistent, raise exception
            if category != self._category:
                raise ValueError(f"DAGMC {identifier} has category={category}.")

            # If geom_dimension is unassigned, assign it based on category
            if geom_dimension == -1:
                warn(f"Assigned geom_dimension={self._geom_dimension} to {identifier}.")
                self.geom_dimension = self._geom_dimension

        if geom_dimension == -1 and category is None:
            raise ValueError(f"{identifier} has no category or geom_dimension tags assigned.")

    def __eq__(self, other):
        return self.model == other.model and self.handle == other.handle

    def __hash__(self):
        return hash((self.handle, id(self.model)))

    def __repr__(self):
        return f'{type(self).__name__} {self.id}, {self.num_triangles} triangles'

    def _tag_get_data(self, tag: tag.Tag):
        return self.model.mb.tag_get_data(tag, self.handle, flat=True)[0]

    def _tag_set_data(self, tag: tag.Tag, value):
        self.model.mb.tag_set_data(tag, self.handle, value)

    @property
    def id(self) -> int:
        """Return the DAGMC set's ID."""
        return self._tag_get_data(self.model.id_tag)

    @id.setter
    def id(self, i: int):
        """Set the DAGMC set's ID."""
        if i is None:
            i = max(self.model.used_ids[type(self)], default=0) + 1
        elif i in self.model.used_ids[type(self)]:
            raise ValueError(f'{self.category} ID {i} is already in use in this model.')

        self.model.used_ids[type(self)].discard(self.id)
        self.model.used_ids[type(self)].add(i)

        self._tag_set_data(self.model.id_tag, i)

    @property
    def geom_dimension(self) -> int:
        """Return the DAGMC set's geometry dimension."""
        return self._tag_get_data(self.model.geom_dimension_tag)

    @geom_dimension.setter
    def geom_dimension(self, dimension: int):
        self._tag_set_data(self.model.geom_dimension_tag, dimension)

    @property
    def category(self) -> Optional[str]:
        """Return the DAGMC set's category."""
        try:
            return self._tag_get_data(self.model.category_tag)
        except RuntimeError:
            return None

    @category.setter
    def category(self, category: str):
        """Set the DAGMC set's category."""
        self._tag_set_data(self.model.category_tag, category)

    @abstractmethod
    def _get_triangle_sets(self):
        """Retrieve all (surface) sets under this set that contain triangle elements.
        """
        pass

    def to_vtk(self, filename):
        """Write the set to a VTK file. This will recursively gather all triangles under
        the group, volume or surface and generate a VTK file.
        """
        if not filename.endswith('.vtk'):
            filename += '.vtk'
        self.model.mb.write_file(filename, output_sets=[self.handle])

    @property
    def triangle_handles(self):
        """Returns a pymoab.rng.Range of all triangle handles under this set.
        """
        r = rng.Range()
        for s in self._get_triangle_sets():
            handle = s if not isinstance(s, DAGSet) else s.handle
            r.merge(self.model.mb.get_entities_by_type(handle, types.MBTRI))
        return r

    @property
    def triangle_conn(self):
        """Returns the triangle connectivity for all triangles under this set.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.uint64
        """
        return self.model.mb.get_connectivity(self.triangle_handles).reshape(-1, 3)

    @property
    def triangle_coords(self):
        """Returns the triangle coordinates for all triangles under this set.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.float64
        """
        conn = self.triangle_conn

        return self.model.mb.get_coords(conn.flatten()).reshape(-1, 3)

    def get_triangle_conn_and_coords(self, compress=False):
        """Returns the triangle connectivity and coordinates for all triangles under this set.

        Triangle vertex values can be retrieved using:
            triangle_conn, coords = Volume.get_triangle_conn_and_coords()
            triangle_zero_coords = coords[triangle_conn[0]]

        Parameters
        ----------
        compress : bool, optional
            If False, a coordinate numpy array of size (N, 3) will be returned.
            If True, the coordinates will be compressed to a unique set of coordinates.
            In either case, entries in the triangle EntityHandle mapping will correspond
            with the appropriate indices in the coordinate array.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.uint64
        numpy.ndarray shape=(N, 3), dtype=np.float64
        """
        conn = self.triangle_conn

        if compress:
            # generate an array of unique coordinates to save space
            coords, idx_inverse = np.unique(self.model.mb.get_coords(conn.flatten()).reshape(-1, 3), axis=0, return_inverse=True)
            # create a mapping from entity handle into the unique coordinates array
            conn = idx_inverse.reshape(-1, 3)
        else:
            coords = self.model.mb.get_coords(conn.flatten()).reshape(-1, 3)
            conn = np.arange(coords.shape[0]).reshape(-1, 3)

        return conn, coords

    def get_triangle_coordinate_mapping(self, compress=False):
        """Returns a maping from triangle EntityHandle to triangle coordinate indices triangle coordinates.

        Triangle vertex values can be retrieved using:
            triangle_handles = Volume.get_triangle_handles()
            triangle_map, coords = Volume.triangle_coordinate_mapping()
            triangle_zero_coords = coords[triangle_map[triangle_handles[0]]]

        Parameters
        ----------
        compress : bool, optional
            If False, a coordinate numpy array of size (N, 3) will be returned.
            If True, the coordinates will be compressed to a unique set of coordinates.
            In either case, entries in the triangle EntityHandle mapping will correspond
            with the appropriate indices in the coordinate array.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.uint64
        """
        conn, coords = self.get_triangle_conn_and_coords(compress)

        # create a mapping from triangle EntityHandle to triangle index
        tri_map = {eh: c for eh, c in zip(self.triangle_handles, conn)}
        return tri_map, coords

    def delete(self):
        """Delete this set from the DAGMC file."""
        self.model.used_ids[type(self)].discard(self.id)
        self.model.mb.delete_entity(self.handle)
        self.handle = None
        self.model = None

    @classmethod
    def create(cls, model: DAGModel, global_id: Optional[int] = None) -> DAGSet:
        """Create new set"""
        # Add necessary tags for this meshset to be identified appropriately
        ent_set = DAGSet(model, model.mb.create_meshset())
        ent_set.geom_dimension = cls._geom_dimension
        ent_set.category = cls._category
        # Now that the entity set has proper tags, create derived class and return
        out = cls(model, ent_set.handle)
        out.id = global_id
        return out


class Surface(DAGSet):

    _category = 'Surface'
    _geom_dimension = 2

    def __init__(self, model: DAGModel, handle: np.uint64):
        super().__init__(model, handle)
        self._check_category_and_dimension()

    @property
    def surf_sense(self) -> list[Optional[Volume]]:
        """Surface sense data."""
        try:
            handles = self.model.mb.tag_get_data(
                self.model.surf_sense_tag, self.handle, flat=True
            )
        except RuntimeError:
            return [None, None]
        return [Volume(self.model, handle) if handle != 0 else None
                for handle in handles]

    @surf_sense.setter
    def surf_sense(self, volumes: list[Optional[Volume]]):
        if len(volumes) != 2:
            raise ValueError("surf_sense should be a list of two volumes.")
        sense_data = [vol.handle if vol is not None else np.uint64(0)
                      for vol in volumes]
        self._tag_set_data(self.model.surf_sense_tag, sense_data)

        # Establish parent-child relationships
        for vol in volumes:
            if vol is not None:
                self.model.mb.add_parent_child(vol.handle, self.handle)

    @property
    def forward_volume(self) -> Optional[Volume]:
        """Volume with forward sense with respect to the surface."""
        return self.surf_sense[0]

    @forward_volume.setter
    def forward_volume(self, volume: Volume):
        self.surf_sense = [volume, self.reverse_volume]

    @property
    def reverse_volume(self) -> Optional[Volume]:
        """Volume with reverse sense with respect to the surface."""
        return self.surf_sense[1]

    @reverse_volume.setter
    def reverse_volume(self, volume: Volume):
        self.surf_sense = [self.forward_volume, volume]

    @property
    def volumes(self) -> list[Volume]:
        """Get the parent volumes of this surface.
        """
        return [Volume(self.model, h) for h in self.model.mb.get_parent_meshsets(self.handle)]

    @property
    def num_triangles(self):
        """Returns the number of triangles in this surface"""
        return len(self.triangle_handles)

    def _get_triangle_sets(self):
        return [self]

    @property
    def area(self):
        """Returns the area of the surface"""
        conn, coords = self.get_triangle_conn_and_coords()
        sum = 0.0
        for _conn in conn:
            tri_coords = coords[_conn]
            sum += np.linalg.norm(np.cross(tri_coords[1] - tri_coords[0], tri_coords[2] - tri_coords[0]))
        return 0.5 * sum


class Volume(DAGSet):

    _category: str = 'Volume'
    _geom_dimension: int = 3

    def __init__(self, model: DAGModel, handle: np.uint64):
        super().__init__(model, handle)
        self._check_category_and_dimension()

    @property
    def groups(self) -> list[Group]:
        """Get list of groups containing this volume."""
        return [group for group in self.model.groups if self in group]

    @property
    def _material_group(self):
        for group in self.groups:
            if "mat:" in group.name:
                return group
        return None

    @property
    def material(self) -> Optional[str]:
        """Name of the material assigned to this volume."""
        group = self._material_group
        if group is not None:
            return group.name[4:]
        return None

    @material.setter
    def material(self, name: str):
        group = self._material_group

        if group is not None:
            # Remove volume from existing group
            group.remove_set(self)

        # create a new group or get an existing group
        group = Group.create(self.model, name=f"mat:{name}")
        group.add_set(self)

    @property
    def surfaces(self):
        """Returns surface objects for all surfaces making up this vollume"""
        return [Surface(self.model, h) for h in self.model.mb.get_child_meshsets(self.handle)]

    @property
    def surfaces_by_id(self):
        return {s.id: s for s in self.surfaces}

    @property
    def num_triangles(self):
        """Returns the number of triangles in this volume"""
        return sum([s.num_triangles for s in self.surfaces])

    def _get_triangle_sets(self):
        return [s.handle for s in self.surfaces]

    @property
    def volume(self):
        """Returns the volume of the volume"""
        volume = 0.0
        for surface in self.surfaces:
            conn, coords = surface.get_triangle_conn_and_coords()
            sum = 0.0
            for _conn in conn:
                tri_coords = coords[_conn]
                c = np.cross(tri_coords[1] - tri_coords[0], tri_coords[2] - tri_coords[0])
                sum += np.dot(c, tri_coords[0])
            sign = 1 if surface.forward_volume == self else -1
            volume += sign * sum
        return volume / 6.0


class Group(DAGSet):

    _category: str = 'Group'
    _geom_dimension: int = 4

    def __init__(self, model: DAGModel, handle: np.uint64):
        super().__init__(model, handle)
        self._check_category_and_dimension()

    def __contains__(self, ent_set: DAGSet):
        return any(vol.handle == ent_set.handle for vol in chain(
            self.volumes, self.surfaces))

    @property
    def name(self) -> Optional[str]:
        """Returns the name of this group."""
        try:
            return self.model.mb.tag_get_data(self.model.name_tag, self.handle, flat=True)[0]
        except RuntimeError:
            return None

    @name.setter
    def name(self, val: str):
        if val.lower() in self.model.group_names:
            raise ValueError(f'Group {val} already used in model.')

        self.model.mb.tag_set_data(self.model.name_tag, self.handle, val)

    def _get_geom_ent_by_id(self, entity_type, id):
        category_ents = self.model.mb.get_entities_by_type_and_tag(self.handle, types.MBENTITYSET, [self.model.category_tag], [entity_type])
        ids = self.model.mb.tag_get_data(self.model.id_tag, category_ents, flat=True)
        return category_ents[int(np.where(ids == id)[0][0])]

    def _remove_geom_ent_by_id(self, entity_type, id):
        geom_ent = self._get_geom_ent_by_id(entity_type, id)
        self.model.mb.remove_entities(self.handle, [geom_ent])

    def _get_triangle_sets(self):
        """Return any sets containing triangles"""
        output = set()
        output.update(self._get_geom_ent_sets('Surfaces'))
        for v in self.volumes:
            output.update(v._get_triangle_sets())
        return list(output)

    def _get_geom_ent_sets(self, entity_type):
        return self.model.mb.get_entities_by_type_and_tag(self.handle, types.MBENTITYSET, [self.model.category_tag], [entity_type])

    def _get_geom_ent_ids(self, entity_type):
        return self.model.mb.tag_get_data(self.model.id_tag, self._get_geom_ent_sets(entity_type), flat=True)

    @property
    def volumes(self):
        """Returns a list of Volume objects for the volumes contained by the group set."""
        return [Volume(self.model, v) for v in self._get_geom_ent_sets('Volume')]

    @property
    def volumes_by_id(self):
        return {v.id: v for v in self.volumes}

    @property
    def surfaces(self):
        """Returns a list of Surface objects for the surfaces contained by the group set."""
        return [Surface(self.model, s) for s in self._get_geom_ent_sets('Surface')]

    @property
    def surfaces_by_id(self):
        return {s.id: s for s in self.surfaces}

    @property
    def volume_ids(self):
        """Returns a list of the contained Volume IDs"""
        return self._get_geom_ent_ids('Volume')

    @property
    def surface_ids(self):
        """Returns a lsit of the contained Surface IDs"""
        return self._get_geom_ent_ids('Surface')

    def remove_set(self, ent_set):
        """Remove an entity set from the group."""
        if isinstance(ent_set, DAGSet):
            self.model.mb.remove_entities(self.handle, [ent_set.handle])
        else:
            self.model.mb.remove_entities(self.handle, [ent_set])

    def add_set(self, ent_set):
        """Add an entity set to the group."""
        if isinstance(ent_set, DAGSet):
            self.model.mb.add_entities(self.handle, [ent_set.handle])
        else:
            self.model.mb.add_entities(self.handle, [ent_set])

    def __repr__(self):
        out = f'Group {self.id}, Name: {self.name}\n'

        vol_ids = self.volume_ids
        if vol_ids.size:
            out += 'Volume IDs:\n'
            out += f'{vol_ids}\n'

        surf_ids = self.surface_ids
        if surf_ids.size:
            out += 'Surface IDs:\n'
            out += f'{surf_ids}\n'

        return out

    def merge(self, other_group):
        """Merge another group into this group. This will remove the other group
        from the DAGMC file.
        """
        if self.name.strip().lower() != other_group.name.strip().lower():
            raise ValueError(f'Group names {self.name} and {other_group.name} do not match')
        # move contained entities from the other group into this one
        other_entities = self.model.mb.get_entities_by_handle(other_group.handle)
        self.model.mb.add_entities(self.handle, other_entities)
        # remove the other group in the MOAB instance
        self.model.mb.delete_entity(other_group.handle)
        # set the other group's handle to this group's handle so that the
        # function the same way
        other_group.handle = self.handle

    @classmethod
    def create(cls, model: DAGModel, name: Optional[str] = None, group_id: Optional[int] = None) -> Group:
        """Create a new group instance with the given name,
        or return an existing group if one exists."""

        # return existing group if one exists with this name
        if name is not None:
            if name.lower() in model.group_names:
                return model.groups_by_name[name]

        # add necessary tags for this meshset to be identified as a group
        ent_set = DAGSet(model, model.mb.create_meshset())
        ent_set.category = cls._category
        ent_set.geom_dimension = cls._geom_dimension

        # Now that entity set has proper tags, create Group, assign name, and return
        group = cls(model, ent_set.handle)

        group.id = group_id

        if name is not None:
            group.name = name

        return group
