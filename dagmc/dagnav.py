from pymoab import core, types, rng
import numpy as np


def get_groups(mb):
    category_tag = mb.tag_get_handle(types.CATEGORY_TAG_NAME)
    group_handles = mb.get_entities_by_type_and_tag(mb.get_root_set(), types.MBENTITYSET, [category_tag], ['Group'])
    groups = [Group(mb, group_handle) for group_handle in group_handles]
    return {g.name: g for g in groups}


class DAGSet:

    def __init__(self, mb, handle):
        self.mb = mb
        self.handle = handle
        self._id_tag = None
        self._cat_tag = None

    def __eq__(self, other):
        return self.handle == other.handle

    @property
    def id_tag(self):
        if self._id_tag is None:
            self._id_tag = self.mb.tag_get_handle(types.GLOBAL_ID_TAG_NAME)
        return self._id_tag

    @property
    def category_tag(self):
        if self._cat_tag is None:
            self._cat_tag = self.mb.tag_get_handle(types.CATEGORY_TAG_NAME)
        return self._cat_tag

    @property
    def id(self):
        return self.mb.tag_get_data(self.id_tag, self.handle, flat=True)[0]

    def to_vtk(self, filename):
        tmp_set = self.mb.create_meshset()
        self.mb.add_entities(tmp_set, self._get_triangle_sets())
        if not filename.endswith('.vtk'):
            filename += '.vtk'
        self.mb.write_file(filename, output_sets=[tmp_set])
        self.mb.delete_entity(tmp_set)


class DAGGeomSet(DAGSet):

    def __repr__(self):
        return f'{type(self).__name__} {self.id}, {self.num_triangles()} triangles'

    def get_triangles(self):
        r = rng.Range()
        for s in self._get_triangle_sets():
            r.merge(self.mb.get_entities_by_type(s.handle, types.MBTRI))
        return r


class Surface(DAGGeomSet):

    def get_volumes(self):
        return [Volume(self.mb, h) for h in self.mb.get_parent_meshsets(self.handle)]

    def num_triangles(self):
        return len(self.get_triangles())

    def _get_triangle_sets(self):
        return [self]


class Volume(DAGGeomSet):

    def get_surfaces(self):
        surfs = [Surface(self.mb, h) for h in self.mb.get_child_meshsets(self.handle)]
        return {s.id: s for s in surfs}

    def num_triangles(self):
        return sum([s.num_triangles() for s in self.get_surfaces().values()])

    def _get_triangle_sets(self):
        return [s.handle for s in self.get_surfaces().values()]


class Group(DAGSet):

    def __init__(self, mb, handle):
        super().__init__(mb, handle)
        self._name_tag = None

    @property
    def name_tag(self):
        if self._name_tag is None:
            self._name_tag = self.mb.tag_get_handle(types.NAME_TAG_NAME)
        return self._name_tag

    @property
    def name(self):
        return self.mb.tag_get_data(self.name_tag, self.handle, flat=True)[0]

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
        vols = [Volume(self.mb, v) for v in self._get_geom_ent_sets('Volume')]
        return {v.id: v for v in vols}

    def get_surfaces(self):
        surfs = [Surface(self.mb, s) for s in self._get_geom_ent_sets('Surface')]
        return {s.id: s for s in surfs}

    def get_volume_ids(self):
        return self._get_geom_ent_ids('Volume')

    def get_surface_ids(self):
        return self._get_geom_ent_ids('Surface')

    def remove_set(self, vol):
        if isinstance(vol, DAGGeomSet):
            self.mb.remove_entities(self.handle, [vol.handle])
        else:
            self.mb.remove_entities(self.handle, [vol])

    def add_set(self, entity):
        if isinstance(entity, DAGGeomSet):
            self.mb.add_entities(self.handle, [entity.handle])
        else:
            self.mb.add_entities(self.handle, [entity])

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
