from pathlib import Path
import urllib.request

import pytest
from test import config

from pymoab import core

import dagmc

# same as the DAGMC model used in the OpenMC DAGMC "legacy" test
FUEL_PIN_URL = 'https://tinyurl.com/y3ugwz6w' # 1.2 MB


def download(url, filename="dagmc.h5m"):
    """
    Helper function for retrieving dagmc models
    """
    u = urllib.request.urlopen(url)

    if u.status != 200:
        raise RuntimeError("Failed to download file.")

    # save file via bytestream
    with open(filename, 'wb') as f:
        f.write(u.read())


@pytest.fixture(autouse=True, scope='module')
def fuel_pin_model(request):
    if Path("fuel_pin.h5m").exists():
        return
    download(FUEL_PIN_URL, request.path.parent / "fuel_pin.h5m")


def test_basic_functionality(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = dagmc.DAGModel(test_file).groups

    print(groups)

    fuel_group = groups['mat:fuel']
    print(fuel_group)

    v1 = fuel_group.get_volumes()[1]
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
    model = dagmc.DAGModel(test_file)
    groups = model.groups

    orig_group = groups['mat:fuel']
    orig_group_size = len(orig_group.get_volumes())
    # create a new group with the same name as another group
    new_group = dagmc.Group.create(model, 'mat:fuel')
    assert orig_group != new_group

    # merge the new group into the existing group
    orig_group.merge(new_group)
    assert orig_group == new_group

    # re-add a new group to the instance with the same name
    new_group = dagmc.Group.create(model, 'mat:fuel')

    # add one of other volumes to the new set
    for vol in model.volumes.values():
        new_group.add_set(vol)

    assert orig_group != new_group
    assert len((new_group.get_volume_ids())) == len(model.volumes)

    # now get the groups again
    groups = model.groups
    # the group named 'mat:fuel' should contain the additional
    # volume set w/ ID 3 now
    fuel_group = groups['mat:fuel']
    assert 3 in fuel_group.get_volumes()
    assert len(fuel_group.get_volumes()) == orig_group_size + 1


def test_compressed_coords(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = dagmc.DAGModel(test_file).groups

    fuel_group = groups['mat:fuel']
    v1 = fuel_group.get_volumes()[1]
    print(v1)

    conn, coords = v1.get_triangle_conn_and_coords()
    uconn, ucoords = v1.get_triangle_conn_and_coords(compress=True)

    for i in range(v1.num_triangles()):
        assert (coords[conn[i]] == ucoords[uconn[i]]).all()

    conn_map, coords = v1.get_triangle_coordinate_mapping()
    tris = v1.get_triangle_handles()
    assert (conn_map[tris[0]].size == 3)
    assert (coords[conn_map[tris[0]]].size == 9)

def test_coords(request, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    model = dagmc.DAGModel(test_file)
    groups = model.groups

    group = groups['mat:fuel']
    conn, coords = group.get_triangle_conn_and_coords()

    volume = next(iter(group.get_volumes().values()))
    conn, coords = volume.get_triangle_conn_and_coords(compress=True)

    surface = next(iter(volume.get_surfaces().values()))
    conn, coords = surface.get_triangle_conn_and_coords(compress=True)


def test_to_vtk(tmpdir_factory, request):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = dagmc.DAGModel(test_file).groups

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
