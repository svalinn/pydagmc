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


@pytest.fixture
def fuel_pin_model(request):
    if Path("fuel_pin.h5m").exists():
        return
    download(FUEL_PIN_URL, request.path.parent / "fuel_pin.h5m")


def test_basic_functionality(request, fuel_pin_model, capfd):
    test_file = str(request.path.parent / 'fuel_pin.h5m')
    groups = dagmc.Group.groups_from_file(test_file)

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
