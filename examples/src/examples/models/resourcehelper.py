import json
import os

_resource_dirs = None


def _resolve_dirs():
    global _resource_dirs
    if _resource_dirs is not None:
        return _resource_dirs

    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "..", "resources"),
        os.path.join(base, "..", "history", "resources"),
        os.path.join(base, "..", "solid", "resources"),
    ]
    _resource_dirs = [os.path.abspath(c) for c in candidates if os.path.isdir(os.path.abspath(c))]
    if not _resource_dirs:
        raise FileNotFoundError(
            "Could not find Resources directory. Looked in: "
            + ", ".join(os.path.abspath(c) for c in candidates)
        )
    return _resource_dirs


def resolve_path(*parts):
    for d in _resolve_dirs():
        path = os.path.join(d, *parts)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Resource not found: {os.path.join(*parts)}")


def read_bytes(*parts):
    with open(resolve_path(*parts), "rb") as f:
        return f.read()


def read_text(*parts):
    path = resolve_path(*parts)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


def read_json(*parts):
    with open(resolve_path(*parts), "r", encoding="utf-8") as f:
        return json.load(f)
