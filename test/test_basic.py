from pathlib import Path
import urllib.request

import pytest
import numpy as np

from test import config

from pymoab import core

import pydagmc

# same as the DAGMC model used in the OpenMC DAGMC "legacy" test
FUEL_PIN_URL = 'https://tinyurl.com/y3ugwz6w' # 1.2 MB


def download(url, filename="pydagmc.h5m"):
    """
    Helper function for retrieving dagmc models
    """
    u = urllib.request.urlopen(url)

    if u.status != 200:
        raise RuntimeError("Failed to download file.")

    # save file via bytestream
    with open(filename, 'wb') as f:
        f.write(u.read())


@pytest.fixture(autouse=True)
def fuel_pin_model(request):
    """Loads the DAGMC fuel pin model from the test file."""
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    if not Path(test_file).exists():
        download(FUEL_PIN_URL, test_file)
    try:
        model = pydagmc.DAGModel(test_file)
        return model
    except Exception as e: # Catch other potential loading errors
         pytest.fail(f"Fixture setup failed: Could not load model {test_file}. Error: {e}")


@pytest.fixture(autouse=True)
def fuel_pin_volumes(fuel_pin_model):
    # Pre-fetch known volumes to fail early if assumptions are wrong
    try:
        vol1 = fuel_pin_model.volumes_by_id[1]
        vol2 = fuel_pin_model.volumes_by_id[2]
        vol3 = fuel_pin_model.volumes_by_id[3]
        vol4 = fuel_pin_model.volumes_by_id[6]
    except KeyError as e:
        pytest.fail(f"Fixture setup failed: Volume ID {e} not found. "
                    f"Verify assumed IDs match fuel_pin.h5m")
    return (vol1, vol2, vol3, vol4)


def test_model_repr(fuel_pin_model):
    model = fuel_pin_model
    model_str = repr(model)
    assert model_str == 'DAGModel: 4 Volumes, 21 Surfaces, 5 Groups'


def test_basic_functionality(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    groups = model.groups_by_name
    print(groups)
    # ensure that the groups attribude is indexable
    first_group = model.groups[0]
    assert isinstance(first_group, pydagmc.Group)

    fuel_group = groups['mat:fuel']
    print(fuel_group)

    v1 = fuel_group.volumes_by_id[1]
    print(v1)

    groups['mat:fuel'].remove_set(v1)
    groups['mat:41'].add_set(v1)

    print(groups['mat:fuel'])
    print(groups['mat:41'])

    assert fuel_group.name == 'mat:fuel'
    fuel_group.name = 'kalamazoo'
    assert fuel_group.name == 'kalamazoo'

    print(fuel_group.name)

    #####################################
    # All test code must go before here #
    #####################################
    out, err = capfd.readouterr()

    gold_name = request.path.parent / 'gold_files' / f'.{request.node.name}.gold'
    if config['update']:
        f = open(gold_name, 'w')
        f.write(out)
    else:
        f = open(gold_name, 'r')
        assert out == f.read()


def test_group_merge(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    groups = model.groups_by_name

    orig_group = groups['mat:fuel']
    orig_group_size = len(orig_group.volumes)
    # try to create a new group with the same name as another group
    new_group = pydagmc.Group.create(model, 'mat:fuel')
    assert orig_group == new_group

    # check that we can update a set ID
    new_group.id = 100
    assert new_group.id == 100

    # merge the new group into the existing group
    orig_group.merge(new_group)
    assert orig_group == new_group

    # re-add a new group to the instance with the same name
    new_group = pydagmc.Group.create(model, 'mat:fuel')

    # add one of other volumes to the new set
    for vol in model.volumes:
        new_group.add_set(vol)

    # using create_group should give same thing
    assert model.create_group('mat:fuel') == new_group

    assert orig_group == new_group
    assert len((new_group.volume_ids)) == len(model.volumes)

    # now get the groups again
    groups = model.groups_by_name
    # the group named 'mat:fuel' should contain the additional
    # volume set w/ ID 3 now
    fuel_group = groups['mat:fuel']
    assert 3 in fuel_group.volumes_by_id


def test_group_create(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    orig_num_groups = len(model.groups)

    # Create two new groups
    new_group1 = pydagmc.Group.create(model, 'mat:slime')
    new_group2 = model.create_group('mat:plastic')

    assert 'mat:slime' in model.groups_by_name
    assert 'mat:plastic' in model.groups_by_name
    assert model.groups_by_name['mat:slime'] == new_group1
    assert model.groups_by_name['mat:plastic'] == new_group2
    assert len(model.groups) == orig_num_groups + 2


def test_initial_volume_properties_and_groups(fuel_pin_model, fuel_pin_volumes):
    """Tests accessing volumes by ID and their initial material property/group."""
    model = fuel_pin_model
    vol1, vol2, vol3, vol4 = fuel_pin_volumes

    # Check initial material via volume property and group membership
    assert vol1.material == 'fuel'
    assert vol1 in model.groups_by_name['mat:fuel']
    assert vol2.material == 'fuel'
    assert vol2 in model.groups_by_name['mat:fuel']
    assert vol3.material == '41'
    assert vol3 in model.groups_by_name['mat:41']
    assert vol4.material == 'Graveyard'
    assert vol4 in model.groups_by_name['mat:Graveyard']


def test_initial_volumes_by_material_map(fuel_pin_model, fuel_pin_volumes):
    """Tests the initial state of the volumes_by_material property."""
    model = fuel_pin_model
    vol1, vol2, vol3, vol4 = fuel_pin_volumes

    initial_mats = model.volumes_by_material

    assert 'fuel' in initial_mats
    assert '41' in initial_mats
    assert 'Graveyard' in initial_mats
    assert len(initial_mats) == 3

    assert vol1 in initial_mats['fuel']
    assert vol2 in initial_mats['fuel']
    assert len(initial_mats['fuel']) == 2

    assert vol3 in initial_mats['41']
    assert len(initial_mats['41']) == 1

    assert vol4 in initial_mats['Graveyard']
    assert len(initial_mats['Graveyard']) == 1

def test_initial_get_volumes_by_material_method(fuel_pin_model, fuel_pin_volumes):
    """Tests the initial state retrieval using get_volumes_by_material()."""
    model = fuel_pin_model
    vol1, vol2, vol3, vol4 = fuel_pin_volumes

    fuel_vols_method = model.get_volumes_by_material('fuel')
    assert isinstance(fuel_vols_method, list)
    assert vol1 in fuel_vols_method
    assert vol2 in fuel_vols_method
    assert len(fuel_vols_method) == 2

    fortyone_vols_method = model.get_volumes_by_material('41')
    assert isinstance(fortyone_vols_method, list)
    assert vol3 in fortyone_vols_method
    assert len(fortyone_vols_method) == 1

    graveyard_vols_method = model.get_volumes_by_material('Graveyard')
    assert isinstance(graveyard_vols_method, list)
    assert vol4 in graveyard_vols_method
    assert len(graveyard_vols_method) == 1

def test_volume_material_change_and_verification(fuel_pin_model, fuel_pin_volumes):
    """Tests changing a volume's material and verifies the updated state."""
    model = fuel_pin_model
    vol1, vol2, vol3, vol4 = fuel_pin_volumes

    # Material Change (Modify vol1 only)
    vol1.material = 'olive oil'

    # Check volume property directly for the changed volume
    assert vol1.material == 'olive oil'

    # Check group updates
    assert 'mat:olive oil' in model.groups_by_name
    assert vol1 in model.groups_by_name['mat:olive oil']
    # Check it's removed from the old group's content
    assert 'mat:fuel' in model.groups_by_name # Group still exists for vol2
    assert vol1 not in model.groups_by_name['mat:fuel'].volumes # vol1 removed
    assert vol2 in model.groups_by_name['mat:fuel'].volumes # vol2 should still be there

    # Check volumes_by_material property after the change
    mats_after_change = model.volumes_by_material

    # Check new material 'olive oil'
    assert 'olive oil' in mats_after_change
    assert vol1 in mats_after_change['olive oil']
    assert len(mats_after_change['olive oil']) == 1

    # Check material 'fuel' - should now only contain vol2
    assert 'fuel' in mats_after_change
    assert vol2 in mats_after_change['fuel']
    assert vol1 not in mats_after_change['fuel'] # Ensure vol1 is gone
    assert len(mats_after_change['fuel']) == 1 # Count updated

    # Check other materials are unaffected
    assert '41' in mats_after_change
    assert vol3 in mats_after_change['41']
    assert len(mats_after_change['41']) == 1
    assert 'Graveyard' in mats_after_change
    assert vol4 in mats_after_change['Graveyard']
    assert len(mats_after_change['Graveyard']) == 1

    # Check total distinct materials count
    assert len(mats_after_change) == 4 # olive oil, fuel, 41, Graveyard

    # Check get_volumes_by_material after the change
    olive_vols_method = model.get_volumes_by_material('olive oil')
    assert vol1 in olive_vols_method
    assert len(olive_vols_method) == 1

    fuel_vols_method_after = model.get_volumes_by_material('fuel') # Should now only return vol2
    assert vol2 in fuel_vols_method_after
    assert vol1 not in fuel_vols_method_after
    assert len(fuel_vols_method_after) == 1


def test_get_volumes_by_material_error_handling(fuel_pin_model):
    """Tests KeyError exceptions and suggestions for get_volumes_by_material()."""
    model = fuel_pin_model

    # Test suggestion for typo
    with pytest.raises(KeyError, match=r"Did you mean.*Graveyard"): # Regex match
        model.get_volumes_by_material('grave yard')

    # Test no suggestion for unrelated name
    with pytest.raises(KeyError, match="Material 'xyz' not found.") as excinfo:
        model.get_volumes_by_material('xyz')
    # Check that suggestions aren't included if none are close enough
    assert "Did you mean" not in str(excinfo.value)

def test_initial_volumes_without_material(fuel_pin_model):
    """
    Tests that the initial fuel pin model (as loaded) has no volumes
    without assigned materials.
    """
    model = fuel_pin_model

    # Test the property
    unassigned_prop = model.volumes_without_material
    assert isinstance(unassigned_prop, list)
    assert len(unassigned_prop) == 0, "Expected no unassigned volumes initially"


def test_volumes_without_material_after_creation(fuel_pin_model):
    """
    Tests that newly created volumes appear in the unassigned list,
    and are removed when assigned a material.
    """
    model = fuel_pin_model

    # Check initial state (should be empty based on previous test)
    assert len(model.volumes_without_material) == 0

    # Create new volumes
    new_vol_id1 = 101
    new_vol_id2 = 102
    assert new_vol_id1 not in model.volumes_by_id
    assert new_vol_id2 not in model.volumes_by_id

    new_vol1 = model.create_volume(new_vol_id1)
    new_vol2 = model.create_volume(new_vol_id2)

    assert new_vol1.material is None
    assert new_vol2.material is None

    # Verify they are now in the unassigned list (using property)
    unassigned_after_create = model.volumes_without_material
    assert isinstance(unassigned_after_create, list)
    assert len(unassigned_after_create) == 2
    assert new_vol1 in unassigned_after_create
    assert new_vol2 in unassigned_after_create

    # Assign material to one of the new volumes
    new_material = 'test_material'
    new_vol1.material = new_material

    # Verify new_vol1 now has material and is NOT in the unassigned list
    assert new_vol1.material == new_material
    unassigned_after_assign = model.volumes_without_material
    assert isinstance(unassigned_after_assign, list)
    assert len(unassigned_after_assign) == 1 # Should only contain new_vol2 now
    assert new_vol1 not in unassigned_after_assign
    assert new_vol2 in unassigned_after_assign # The other one should still be there

    # Assign material to the second new volume
    new_vol2.material = "another_material"
    assert new_vol2.material == "another_material"
    unassigned_final = model.volumes_without_material
    assert isinstance(unassigned_final, list)
    assert len(unassigned_final) == 0 # Should be empty again
    assert new_vol1 not in unassigned_final
    assert new_vol2 not in unassigned_final


def test_volume_creation(fuel_pin_model):
    """Tests creating new volumes via Volume.create and model.create_volume."""
    model = fuel_pin_model

    # Test Volume.create
    new_vol_id = 100
    assert new_vol_id not in model.volumes_by_id # Ensure ID is unused
    new_vol = pydagmc.Volume.create(model, new_vol_id)
    assert isinstance(new_vol, pydagmc.Volume)
    assert new_vol.id == new_vol_id
    assert model.volumes_by_id[new_vol_id] == new_vol
    assert new_vol.material is None # Should have no material initially

    # Test model.create_volume
    new_vol2_id = 200
    assert new_vol2_id not in model.volumes_by_id # Ensure ID is unused
    new_vol2 = model.create_volume(new_vol2_id)
    assert isinstance(new_vol2, pydagmc.Volume)
    assert new_vol2.id == new_vol2_id
    assert model.volumes_by_id[new_vol2_id] == new_vol2
    assert new_vol2.material is None

    # Check that volumes without materials don't appear in the map
    initial_mat_count = len(model.volumes_by_material) # Get count before checking
    mats_after_creation = model.volumes_by_material
    assert len(mats_after_creation) == initial_mat_count # Count shouldn't change
    found_new_vol = any(new_vol in v_list for v_list in mats_after_creation.values())
    assert not found_new_vol
    found_new_vol2 = any(new_vol2 in v_list for v_list in mats_after_creation.values())
    assert not found_new_vol2


def test_assign_material_to_new_volume(fuel_pin_model):
    """Tests assigning material to a newly created volume."""
    model = fuel_pin_model
    initial_mat_count = len(model.volumes_by_material)

    # Create a new volume
    new_vol_id = 100
    assert new_vol_id not in model.volumes_by_id
    new_vol = model.create_volume(new_vol_id)
    assert new_vol.material is None # Verify initial state

    # Assign material
    new_material_name = 'water'
    assert new_material_name not in model.volumes_by_material # Verify material doesn't exist yet
    new_vol.material = new_material_name

    # Verify assignment
    assert new_vol.material == new_material_name
    assert f'mat:{new_material_name}' in model.groups_by_name
    assert new_vol in model.groups_by_name[f'mat:{new_material_name}']

    # Verify material maps
    mats_final = model.volumes_by_material
    assert new_material_name in mats_final
    assert new_vol in mats_final[new_material_name]
    assert len(mats_final[new_material_name]) == 1
    assert len(mats_final) == initial_mat_count + 1 # Check total count increased by 1

    # Verify get_volumes_by_material
    water_vols_method = model.get_volumes_by_material(new_material_name)
    assert isinstance(water_vols_method, list)
    assert new_vol in water_vols_method
    assert len(water_vols_method) == 1


def test_surface(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)

    s1 = model.surfaces_by_id[1]
    assert s1.volumes == [model.volumes_by_id[1], model.volumes_by_id[2]]
    assert s1.forward_volume == model.volumes_by_id[1]
    assert s1.reverse_volume == model.volumes_by_id[2]

    s1.forward_volume = model.volumes_by_id[3]
    assert s1.forward_volume == model.volumes_by_id[3]
    assert s1.surf_sense == [model.volumes_by_id[3], model.volumes_by_id[2]]

    s1.reverse_volume = model.volumes_by_id[1]
    assert s1.reverse_volume == model.volumes_by_id[1]
    assert s1.surf_sense == [model.volumes_by_id[3], model.volumes_by_id[1]]


def test_id_safety(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)

    v1 = model.volumes_by_id[1]

    used_vol_id = 2
    with pytest.raises(ValueError, match="already"):
        v1.id = used_vol_id

    # set volume 1 to a safe ID and ensure assignment was successful this
    # assignment should free the original ID of 1 for use
    safe_vol_id = 9876
    v1.id = safe_vol_id
    assert v1.id == safe_vol_id

    # create a second volume and ensure it gets the next available ID
    v2 = pydagmc.Volume.create(model)
    assert v2.id == safe_vol_id + 1

    # update the value of the first volume, freeing the ID
    safe_vol_id = 101
    v1.id = safe_vol_id
    # delete the second volume, freeing its ID as well
    v2.delete()

    # create a new volume and ensure that it is automatically assigned the
    # lowest available ID
    v3 = pydagmc.Volume.create(model)
    assert v3.id == safe_vol_id + 1

    s1 = model.surfaces_by_id[1]

    used_surf_id = 2
    with pytest.raises(ValueError, match="already"):
        s1.id = used_surf_id

    safe_surf_id = 9876
    s1.id = safe_surf_id
    assert s1.id == safe_surf_id

    s2 = model.surfaces_by_id[2]
    s2.id = None
    assert s2.id == safe_surf_id + 1

    s2.id = 2
    assert s2.id == 2

    g1 = model.groups_by_name['mat:fuel']

    used_grp_id = 2
    with pytest.raises(ValueError, match="already"):
        g1.id = used_grp_id

    safe_grp_id = 9876
    g1.id = safe_grp_id
    assert g1.id == safe_grp_id

    new_surf = pydagmc.Surface.create(model, 100)
    assert isinstance(new_surf, pydagmc.Surface)
    assert new_surf.id == 100
    assert model.surfaces_by_id[100] == new_surf

    new_surf2 = model.create_surface(200)
    assert isinstance(new_surf2, pydagmc.Surface)
    assert new_surf2.id == 200
    assert model.surfaces_by_id[200] == new_surf2


def test_hash(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)

    d = {group: group.name for group in model.groups}

    # check that an entry for the same volume with a different model can be entered
    # into the dict
    model1 = pydagmc.DAGModel(test_file)

    d.update({group: group.name for group in model1.groups})

    assert len(d) == len(model.groups) + len(model1.groups)


def test_compressed_coords(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = pydagmc.DAGModel(test_file).groups_by_name

    fuel_group = groups['mat:fuel']
    v1 = fuel_group.volumes_by_id[1]

    conn, coords = v1.get_triangle_conn_and_coords()
    uconn, ucoords = v1.get_triangle_conn_and_coords(compress=True)

    for i in range(v1.num_triangles):
        assert (coords[conn[i]] == ucoords[uconn[i]]).all()

    conn_map, coords = v1.get_triangle_coordinate_mapping()
    tris = v1.triangle_handles
    assert (conn_map[tris[0]].size == 3)
    assert (coords[conn_map[tris[0]]].size == 9)


def test_coords(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    groups = model.groups_by_name

    group = groups['mat:fuel']
    conn, coords = group.get_triangle_conn_and_coords()

    volume = next(iter(group.volumes))
    conn, coords = volume.get_triangle_conn_and_coords(compress=True)

    surface = next(iter(volume.surfaces))
    conn, coords = surface.get_triangle_conn_and_coords(compress=True)


def test_to_vtk(tmpdir_factory, request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = pydagmc.DAGModel(test_file).groups_by_name

    fuel_group = groups['mat:fuel']

    vtk_filename = str(tmpdir_factory.mktemp('vtk').join('fuel_pin.vtk'))

    fuel_group.to_vtk(vtk_filename)

    vtk_file = open(vtk_filename, 'r')

    gold_name = request.path.parent / 'gold_files' / f'.{request.node.name}.gold'

    if config['update']:
        f = open(gold_name, 'w')
        f.write(vtk_file.read())
    else:
        gold_file = open(gold_name, 'r')

        # The VTK file header has a MOAB version in it. Filter
        # that line out so running this test with other versions of
        # MOAB doesn't cause a failure
        line_filter = lambda line : not 'MOAB' in line

        vtk_iter = filter(line_filter, vtk_file)
        gold_iter = filter(line_filter, gold_file)
        assert all(l1 == l2 for l1, l2 in zip(vtk_iter, gold_iter))


@pytest.mark.parametrize("category,dim", [('Surface', 2), ('Volume', 3), ('Group', 4)])
def test_empty_category(category, dim):
    # Create a volume that has no category assigned
    model = pydagmc.DAGModel()
    ent_set = pydagmc.DAGSet(model, model.mb.create_meshset())
    ent_set.geom_dimension = dim

    # Instantiating using the proper class (Surface, Volume, Group) should
    # result in the category tag getting assigned
    with pytest.warns(UserWarning):
        obj = getattr(pydagmc, category)(model, ent_set.handle)
    assert obj.category == category


@pytest.mark.parametrize("category,dim", [('Surface', 2), ('Volume', 3), ('Group', 4)])
def test_empty_geom_dimension(category, dim):
    # Create a volume that has no geom_dimension assigned
    mb = core.Core()
    model = pydagmc.DAGModel(mb)
    ent_set = pydagmc.DAGSet(model, mb.create_meshset())
    ent_set.category = category

    # Instantiating using the proper class (Surface, Volume, Group) should
    # result in the geom_dimension tag getting assigned
    with pytest.warns(UserWarning):
        obj = getattr(pydagmc, category)(model, ent_set.handle)
    assert obj.geom_dimension == dim


@pytest.mark.parametrize("cls", [pydagmc.Surface, pydagmc.Volume, pydagmc.Group])
def test_missing_tags(cls):
    model = pydagmc.DAGModel()
    handle = model.mb.create_meshset()
    with pytest.raises(ValueError):
        cls(model, handle)


def test_eq(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model1 = pydagmc.DAGModel(test_file)
    model2 = pydagmc.DAGModel(test_file)

    model1_v0 = model1.volumes[1]
    model2_v0 = model2.volumes[1]

    assert model1_v0.handle == model2_v0.handle

    assert model1_v0 != model2_v0


def test_delete(fuel_pin_model):
    model = fuel_pin_model

    fuel_group = model.groups_by_name['mat:fuel']
    fuel_group.delete()

    # attempt an operation on the group
    with pytest.raises(AttributeError, match="has no attribute 'mb'"):
        fuel_group.volumes

    # ensure the group is no longer returned by the model
    assert 'mat:fuel' not in model.groups_by_name


def test_write(request, tmpdir):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    model.volumes_by_id[1].id = 12345
    model.write_file('fuel_pin_copy.h5m')

    model = pydagmc.DAGModel('fuel_pin_copy.h5m')
    assert 12345 in model.volumes_by_id


def test_volume_value(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    exp_vols = {1: np.pi * 7**2 * 40,
                2: np.pi * (9**2 - 7**2) * 40,
                3: np.pi * (10**2 - 9**2) * 40,}
    pytest.approx(model.volumes_by_id[1].volume, exp_vols[1])
    pytest.approx(model.volumes_by_id[2].volume, exp_vols[2])
    pytest.approx(model.volumes_by_id[3].volume, exp_vols[3])


def test_area(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    exp_areas = {1: 2 * np.pi * 7 * 40,
                 2: np.pi * 7**2,
                 3: np.pi * 7**2,
                 5: 2 * np.pi * 9 * 40,
                 6: np.pi * 9**2,
                 7: np.pi * 9**2,
                 9: 2 * np.pi * 10 * 40,
                 10: np.pi * 10**2,
                 11: np.pi * 10**2 }
    for surf_id, exp_area in exp_areas.items():
        pytest.approx(model.surfaces[surf_id].area, exp_area)


def test_add_groups(request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = pydagmc.DAGModel(test_file)
    volumes = model.volumes_by_id
    surfaces = model.surfaces_by_id

    for group in model.groups:
        group.delete()

    assert len(model.groups) == 0

    group_map = {("mat:fuel", 10): [1, 2],
                 ("mat:Graveyard", 50): [volumes[6]],
                 ("mat:41", 20): [3],
                 ("boundary:Reflecting", 30): [27, 28, 29],
                 ("boundary:Vacuum", 40): [surfaces[24], surfaces[25]]
                 }

    model.add_groups(group_map)

    groups = model.groups_by_name

    assert len(groups) == 5
    assert [1, 2] == sorted(groups['mat:fuel'].volume_ids)
    assert [6] == groups['mat:Graveyard'].volume_ids
    assert [3] == groups['mat:41'].volume_ids
    assert [27, 28, 29] == sorted(groups['boundary:Reflecting'].surface_ids)
    assert [24, 25] == sorted(groups['boundary:Vacuum'].surface_ids)


def test_surface_load_file(request):
    model = pydagmc.DAGModel()
    surface = model.create_surface(filename=request.path.parent / 'cube.stl')
    assert surface.num_triangles == 12

    # Non-STL file should not be allowed
    with pytest.raises(ValueError):
        model.create_surface(filename='badgers.exe')
