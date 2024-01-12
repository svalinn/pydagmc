from abc import abstractmethod
from functools import cached_property
from pathlib import Path

import numpy as np

from pymoab import core, types, rng


class DAGSet:
    """
    Generic functionality for a DAGMC EntitySet.
    """
    def __init__(self, mb, handle):
        self.mb = mb
        self.handle = handle

    def __eq__(self, other):
        return self.handle == other.handle

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
        return self.mb.tag_get_handle(types.CATEGORY_TAG_NAME)

    @property
    def id(self):
        """Return the DAGMC set's ID.
        """
        return self.mb.tag_get_data(self.id_tag, self.handle, flat=True)[0]

    @abstractmethod
    def _get_triangle_sets(self):
        """Retrieve all (surface) sets under this set that contain triangle elements.
        """
        pass

    def to_vtk(self, filename):
        """Write the set to a VTK file. This will recursively gather all triangles under
        the group, volume or surface and generate a VTK file.
        """
        tmp_set = self.mb.create_meshset()
        self.mb.add_entities(tmp_set, self._get_triangle_sets())
        if not filename.endswith('.vtk'):
            filename += '.vtk'
        self.mb.write_file(filename, output_sets=[tmp_set])
        self.mb.delete_entity(tmp_set)


class DAGGeomSet(DAGSet):
    """A base class for representing a DAGMC Geometry set. Only Volumes and Surfaces are currently supported.
    """
    def __repr__(self):
        return f'{type(self).__name__} {self.id}, {self.num_triangles()} triangles'

    def get_triangle_handles(self):
        """Returns a pymoab.rng.Range of all triangle handles under this set.
        """
        r = rng.Range()
        for s in self._get_triangle_sets():
            handle = s if not isinstance(s, DAGGeomSet) else s.handle
            r.merge(self.mb.get_entities_by_type(handle, types.MBTRI))
        return r

    def get_triangle_conn(self):
        """Returns the triangle connectivity for all triangles under this set.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.uint64
        """
        return self.mb.get_connectivity(self.get_triangle_handles()).reshape(-1, 3)

    def get_triangle_coords(self):
        """Returns the triangle coordinates for all triangles under this set.

        Returns
        -------
        numpy.ndarray shape=(N, 3), dtype=np.float64
        """
        conn = self.get_triangle_conn()

        return self.mb.get_coords(conn.flatten()).reshape(-1, 3)

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
        conn = self.get_triangle_conn()

        if compress:
            # generate an array of unique coordinates to save space
            coords, idx_inverse = np.unique(self.mb.get_coords(conn.flatten()).reshape(-1, 3), axis=0, return_inverse=True)
            # create a mapping from entity handle into the unique coordinates array
            conn = idx_inverse.reshape(-1, 3)
        else:
            coords = self.mb.get_coords(conn.flatten()).reshape(-1, 3)
            conn = np.arange(coords.shape[0]).reshape(-1, 3)

        return conn, coords

    def triangle_coordinate_mapping(self, compress=False):
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
        triangle_handles = self.get_triangle_handles()
        conn, coords = self.get_triangle_conn_and_coords(compress)

        # create a mapping from triangle EntityHandle to triangle index
        tri_map = {eh: c for eh, c in zip(triangle_handles, conn)}
        return tri_map, conn


class Surface(DAGGeomSet):

    def get_volumes(self):
        """Get the parent volumes of this surface.
        """
        return [Volume(self.mb, h) for h in self.mb.get_parent_meshsets(self.handle)]

    def num_triangles(self):
        """Returns the number of triangles in this surface"""
        return len(self.get_triangle_handles())

    def _get_triangle_sets(self):
        return [self]


class Volume(DAGGeomSet):

    def get_surfaces(self):
        """Returns surface objects for all surfaces making up this vollume"""
        surfs = [Surface(self.mb, h) for h in self.mb.get_child_meshsets(self.handle)]
        return {s.id: s for s in surfs}

    def num_triangles(self):
        """Returns the number of triangles in this volume"""
        return sum([s.num_triangles() for s in self.get_surfaces().values()])

    def _get_triangle_sets(self):
        return [s.handle for s in self.get_surfaces().values()]

class Group(DAGSet):

    @cached_property
    def name_tag(self):
        return self.mb.tag_get_handle(types.NAME_TAG_NAME)

    @property
    def name(self):
        """Returns the name of this group."""
        return self.mb.tag_get_data(self.name_tag, self.handle, flat=True)[0]

    @name.setter
    def name(self, val):
        self.mb.tag_set_data(self.name_tag, self.handle, val)

    def _get_geom_ent_by_id(self, entity_type, id):
        category_ents = mb.get_entities_by_type_and_tag(self.handle, types.MBENTITYSET, [self.category_tag], [entity_type])
        ids = self.mb.tag_get_data(self.id_tag, category_ents, flat=True)
        return category_ents[int(np.where(ids == id)[0][0])]

    def _remove_geom_ent_by_id(self, entity_type, id):
        geom_ent = self._get_geom_ent_by_id(entity_type, id)
        self.mb.remove_entities(self.handle, [geom_ent])

    def _get_triangle_sets(self):
        """Return any sets containing triangles"""
        output = set()
        output.update(self._get_geom_ent_sets('Surfaces'))
        for v in self.get_volumes().values():
            output.update(v._get_triangle_sets())
        return list(output)

    def _get_geom_ent_sets(self, entity_type):
        return self.mb.get_entities_by_type_and_tag(self.handle, types.MBENTITYSET, [self.category_tag], [entity_type])

    def _get_geom_ent_ids(self, entity_type):
        return self.mb.tag_get_data(self.id_tag, self._get_geom_ent_sets(entity_type), flat=True)

    def get_volumes(self):
        """Returns a list of Volume objects for the volumes contained by the group set."""
        vols = [Volume(self.mb, v) for v in self._get_geom_ent_sets('Volume')]
        return {v.id: v for v in vols}

    def get_surfaces(self):
        """Returns a list of Surface objects for the surfaces contained by the group set."""
        surfs = [Surface(self.mb, s) for s in self._get_geom_ent_sets('Surface')]
        return {s.id: s for s in surfs}

    def get_volume_ids(self):
        """Returns a list of the contained Volume IDs"""
        return self._get_geom_ent_ids('Volume')

    def get_surface_ids(self):
        """Returns a lsit of the contained Surface IDs"""
        return self._get_geom_ent_ids('Surface')

    def remove_set(self, ent_set):
        """Remove an entity set from the group."""
        if isinstance(ent_set, DAGGeomSet):
            self.mb.remove_entities(self.handle, [ent_set.handle])
        else:
            self.mb.remove_entities(self.handle, [ent_set])

    def add_set(self, ent_set):
        """Add an entity set to the group."""
        if isinstance(ent_set, DAGGeomSet):
            self.mb.add_entities(self.handle, [ent_set.handle])
        else:
            self.mb.add_entities(self.handle, [ent_set])

    def __repr__(self):
        out = f'Group {self.id}, Name: {self.name}\n'

        vol_ids = self.get_volume_ids()
        if vol_ids.size:
            out += 'Volume IDs:\n'
            out += f'{vol_ids}\n'

        surf_ids = self.get_surface_ids()
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
        other_entities = self.mb.get_entities_by_handle(other_group.handle)
        self.mb.add_entities(self.handle, other_entities)
        # remove the other group in the MOAB instance
        self.mb.delete_entity(other_group.handle)
        # set the other group's handle to this group's handle so that the
        # function the same way
        other_group.handle = self.handle

    @classmethod
    def groups_from_file(cls, filename):
        """Extract metadata groups from a file

        Returns
        -------
        A mapping with group names as keys and dagmc.Group instances as values

        """
        mb = core.Core()
        mb.load_file(filename)
        return cls.groups_from_instance(mb)

    @classmethod
    def groups_from_instance(cls, mb):
        """Extract metadata groups from a pymoab.core.Core instance
           with a DAGMC file already loaded

        Returns
        -------
        A mapping with group names as keys and dagmc.Group instances as values

        """
        category_tag = mb.tag_get_handle(types.CATEGORY_TAG_NAME)
        group_handles = mb.get_entities_by_type_and_tag(mb.get_root_set(), types.MBENTITYSET, [category_tag], ['Group'])

        group_mapping = {}

        for group_handle in group_handles:
            # create a new class instance for the group handle
            group = cls(mb, group_handle)
            group_name = group.name
            # if the group name already exists in the group_mapping, merge the two groups
            if group_name in group_mapping:
                group_mapping[group_name].merge(group)
                continue
            group_mapping[group_name] = cls(mb, group_handle)

        return group_mapping

    @classmethod
    def create(cls, mb, name):
        """Create a new group instance with the given name"""
        group_handle = mb.create_meshset()
        mb.tag_set_data(mb.tag_get_handle(types.NAME_TAG_NAME), group_handle, name)
        mb.tag_set_data(mb.tag_get_handle(types.CATEGORY_TAG_NAME), group_handle, 'Group')
        mb.tag_set_data(mb.tag_get_handle(types.GEOM_DIMENSION_TAG_NAME), group_handle, 4)
        return cls(mb, group_handle)