# ClassCAD Python Examples

Python examples and PyVista visualization helper for the [ClassCAD](https://classcad.ch/) API.

## Prerequisites

- Python 3.10+
- ClassCAD running in SocketIO server mode (see [Getting Started](https://classcad.ch/docs/api-usage/getting-started))
- ClassCAD API and Connector packages installed (see below)

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/awv-informatik/classcad-python-examples.git
cd classcad-python-examples
```

### 2. Install all dependencies

The `requirements.txt` includes the ClassCAD API and Connector packages as well as all other dependencies:

```bash
pip install -r examples/requirements.txt
```

> **Note:** The `requirements.txt` references specific ClassCAD release versions. To use a different version, replace the wheel URLs with those from the [Downloads](https://classcad.ch/downloads) page.

## Packages

### classcadpyvista

A helper library to convert ClassCAD geometry data into [PyVista](https://docs.pyvista.org/) meshes for 3D visualization.

### examples

Example scripts demonstrating ClassCAD API usage including solid modeling, part creation, assemblies, sketches, and more.

## Running examples

Make sure ClassCAD is running in SocketIO server mode, then:

```bash
cd examples/src
python -m examples.examplesapp
```

## License

Copyright (c) AWV Informatik AG. See [license](https://awv-informatik.ch/license/).
