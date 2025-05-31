# PyDAGMC

[![CI](https://github.com/svalinn/pydagmc/actions/workflows/ci.yml/badge.svg)](https://github.com/svalinn/pydagmc/actions/workflows/ci.yml)

[![codecov](https://codecov.io/github/svalinn/pydagmc/branch/main/graph/badge.svg?token=TONI94VBED)](https://codecov.io/github/svalinn/pydagmc)

PyDAGMC is a Python interface for interacting with DAGMC .h5m files through the embedded topological relationships and metadata contained within. These interactions occur through a set of Python classes corresponding to DAGMC’s metadata Group (a grouping of volumes or surfaces), Volume, and Surface groupings in the mesh database. This interface is intended to provide a simple interface for obtaining information about DAGMC models, replacing significant boilerplate code required to perform the same queries with PyMOAB, the Python interface for MOAB itself.

For detailed information, including installation, usage guides, tutorials, and the API reference, please visit our [Full Documentation](https://svalinn.github.io/pydagmc/).
