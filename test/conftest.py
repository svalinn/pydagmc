from test import config as my_config


def pytest_addoption(parser):
    parser.addoption('--update', action='store_true', default=False)


def pytest_configure(config):
    opts = ['update']
    for opt in opts:
        if config.getoption(opt) is not None:
            my_config[opt] = config.getoption(opt)
