# ClassCAD Python Examples

Python examples and PyVista visualization helper for the [ClassCAD](https://classcad.ch/) API.

## Prerequisites

- Python 3.10+
- ClassCAD running in SocketIO server mode (see [Getting Started](https://classcad.ch/docs/api-usage/getting-started))
- ClassCAD API and Connector packages installed (see below)

## Installation

### 1. Install the ClassCAD API and Connector

Get the download URLs for your ClassCAD version from the [Downloads](https://classcad.ch/downloads) page and install them:

```bash
pip install <API_PY_URL>
pip install <API_PY_CONNECTOR_URL>
```

### 2. Clone this repository

```bash
git clone https://github.com/awv-informatik/classcad-python-examples.git
cd classcad-python-examples
```

### 3. Install the packages

```bash
pip install ./classcadpyvista
pip install ./examples
```

Or install directly from GitHub without cloning:

```bash
pip install "classcad-api-py-pyvista @ git+https://github.com/awv-informatik/classcad-python-examples.git#subdirectory=classcadpyvista"
pip install "classcad-api-py-examples @ git+https://github.com/awv-informatik/classcad-python-examples.git#subdirectory=examples"
```

## Packages

### classcadpyvista

A helper library to convert ClassCAD geometry data into [PyVista](https://docs.pyvista.org/) meshes for 3D visualization.

### examples

Example scripts demonstrating ClassCAD API usage including solid modeling, part creation, assemblies, sketches, and more.

## Running examples

Make sure ClassCAD is running in SocketIO server mode, then:

```bash
python -m examples.examplesapp
```

## License

Copyright (c) AWV Informatik AG. See [license](https://awv-informatik.ch/license/).
