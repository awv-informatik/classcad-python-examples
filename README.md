# ClassCAD Python Examples

Python examples and PyVista visualization helper for the [ClassCAD](https://classcad.ch/) API.

## Prerequisites

- Python 3.10+
- ClassCAD running in SocketIO server mode (see [Getting Started](https://classcad.ch/docs/api-usage/getting-started))

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/awv-informatik/classcad-python-examples.git
cd classcad-python-examples
```

### 2. Install dependencies

Choose the package depending on what you want to run:

**Console examples** (no UI required):
```bash
cd console
pip install -r requirements.txt
```

**App** (PyVista 3D viewer, requires PyQt5):
```bash
cd app
pip install -r requirements.txt
```

> **Note:** The `requirements.txt` files reference specific ClassCAD release versions. To use a different version, replace the wheel URLs with those from the [Downloads](https://classcad.ch/downloads) page.

## Packages

### classcadpyvista

A helper library to convert ClassCAD geometry data into [PyVista](https://docs.pyvista.org/) meshes for 3D visualization.

### console

Console-based example scripts demonstrating ClassCAD API usage including solid modeling, part creation, assemblies, sketches, and more. No UI or visualization dependencies required.

### app

Interactive 3D viewer application built with PyVista and PyQt5. Demonstrates the same ClassCAD API examples with live 3D visualization.

## Running

Make sure ClassCAD is running in SocketIO server mode, then:

**Console examples:**
```bash
cd console/src
python -m console
```

**App:**
```bash
cd app/src
python -m app
```

## License

Copyright (c) AWV Informatik AG. See [license](https://awv-informatik.ch/license/).
