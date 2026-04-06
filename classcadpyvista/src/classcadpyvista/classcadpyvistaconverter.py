from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pyvista as pv


# ---------- SCG container type constants ----------

class ScgContainerType:
    NONE = 0
    BREP = 1
    CURVEARRAY = 2
    POLYBREP = 3


_MESH_CONTAINER_TYPES = {
    ScgContainerType.BREP, ScgContainerType.POLYBREP,
    "brep", "polyBrep",
}


# ---------- helpers ----------

def _as_points(vertices: Any) -> np.ndarray:
    """Parse SCG vertex data (flat or nested) into an Nx3 array."""
    arr = np.asarray(vertices, dtype=float)
    if arr.ndim == 1:
        if arr.size % 3 != 0:
            raise ValueError(f"Vertex array length {arr.size} is not divisible by 3")
        return arr.reshape((-1, 3))
    if arr.ndim == 2 and arr.shape[1] == 3:
        return arr
    raise ValueError(f"Unsupported vertex array shape: {arr.shape}")


def _tri_faces(indices: Any) -> np.ndarray:
    """Convert triangle indices to PyVista face format [3,i0,i1,i2, ...]."""
    ind = np.asarray(indices, dtype=np.int64).ravel()
    if ind.size % 3 != 0:
        raise ValueError(f"Index array length {ind.size} is not divisible by 3")
    tris = ind.reshape((-1, 3))
    faces = np.empty((tris.shape[0], 4), dtype=np.int64)
    faces[:, 0] = 3
    faces[:, 1:] = tris
    return faces.ravel()


def _csys_to_matrix(csys: Any) -> Optional[np.ndarray]:
    """
    Convert coordinateSystem [origin, xAxis, yAxis, zAxis] to a 4x4 column-vector matrix.
    Equivalent to the WPF Matrix3D constructed in ScgHelixConverter.
    """
    if csys is None or len(csys) < 4:
        return None
    origin, x, y, z = csys[0], csys[1], csys[2], csys[3]
    if len(origin) < 3 or len(x) < 3 or len(y) < 3 or len(z) < 3:
        return None
    return np.array(
        [
            [x[0], y[0], z[0], origin[0]],
            [x[1], y[1], z[1], origin[1]],
            [x[2], y[2], z[2], origin[2]],
            [0.0,  0.0,  0.0,  1.0],
        ],
        dtype=float,
    )


def _resolve_color(
    mesh: Dict[str, Any],
    container: Dict[str, Any],
) -> Tuple[float, float, float, float]:
    """
    Resolve color with priority: mesh > container > default cornflower blue.
    Returns (r, g, b, a) in 0..1 range.  Matches ScgHelixConverter color resolution.
    """
    mesh_mat = (mesh.get("properties") or {}).get("material") or {}
    mesh_color = mesh_mat.get("color")
    mesh_opacity = mesh_mat.get("opacity", 1.0)

    container_mat = (container.get("properties") or {}).get("material") or {}
    container_color = container_mat.get("color")
    container_opacity = container_mat.get("opacity", 1.0)

    if mesh_color and len(mesh_color) >= 3:
        c, opacity = mesh_color, mesh_opacity
    elif container_color and len(container_color) >= 3:
        c, opacity = container_color, container_opacity
    else:
        c = [100.0, 149.0, 237.0]  # cornflower blue default
        opacity = 1.0

    r = max(0.0, min(1.0, c[0] / 255.0))
    g = max(0.0, min(1.0, c[1] / 255.0))
    b = max(0.0, min(1.0, c[2] / 255.0))
    a = max(0.0, min(1.0, float(opacity)))
    return (r, g, b, a)


# ---------- edge helpers ----------

def _append_polyline(points: List[List[float]], lines: List[int], pts: np.ndarray) -> None:
    if pts.size == 0:
        return
    start = len(points)
    points.extend(pts.tolist())
    n = pts.shape[0]
    lines.append(n)
    lines.extend(range(start, start + n))


def _arc_points(
    arc: Dict[str, Any],
    *,
    min_segments: int = 32,
    circle_segments: int = 180,
) -> Optional[np.ndarray]:
    center = np.asarray(arc.get("center", []), dtype=float)
    x_axis = np.asarray(arc.get("xAxis", []), dtype=float)
    z_axis = np.asarray(arc.get("zAxis", []), dtype=float)
    angle = float(arc.get("angle", 0.0))
    radius = float(arc.get("radius", 0.0))

    if center.size != 3 or x_axis.size != 3 or z_axis.size != 3:
        return None
    if radius <= 0.0 or angle == 0.0:
        return None

    x_norm = np.linalg.norm(x_axis)
    z_norm = np.linalg.norm(z_axis)
    if x_norm == 0.0 or z_norm == 0.0:
        return None
    x_axis = x_axis / x_norm
    z_axis = z_axis / z_norm

    y_axis = np.cross(z_axis, x_axis)
    y_norm = np.linalg.norm(y_axis)
    if y_norm == 0.0:
        return None
    y_axis = y_axis / y_norm

    span = abs(angle)
    segs = max(min_segments, int(span / (2.0 * np.pi) * circle_segments))
    if arc.get("isCircle", False):
        segs = max(segs, circle_segments)

    ts = np.linspace(0.0, angle, segs + 1)
    pts = center + radius * (np.cos(ts)[:, None] * x_axis + np.sin(ts)[:, None] * y_axis)
    return pts


def _build_edge_polydata(
    container: Dict[str, Any],
    *,
    min_arc_segments: int = 32,
    circle_segments: int = 180,
) -> Optional[pv.PolyData]:
    points: List[List[float]] = []
    lines: List[int] = []

    for ln in container.get("lines", []) or []:
        pts = _as_points(ln.get("points", []))
        if pts.shape[0] >= 2:
            _append_polyline(points, lines, pts)

    for arc in container.get("arcs", []) or []:
        pts = _arc_points(arc, min_segments=min_arc_segments, circle_segments=circle_segments)
        if pts is not None and pts.shape[0] >= 2:
            _append_polyline(points, lines, pts)

    if not points or not lines:
        return None

    poly = pv.PolyData(np.asarray(points, dtype=float))
    poly.lines = np.asarray(lines, dtype=np.int64)
    try:
        poly = poly.clean(tolerance=1e-6)
        poly = poly.strip()
    except Exception:
        pass
    return poly


# ---------- result container ----------

@dataclass
class ScgPyVistaScene:
    """Convenience wrapper returned by ScgPyVistaConverter."""
    multiblock: pv.MultiBlock
    rgba: Dict[str, Tuple[float, float, float, float]]
    edge_keys: Set[str]
    edge_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    edge_width: float = 1.5

    def add_to_plotter(
        self,
        plotter: pv.Plotter,
        *,
        show_edges: bool = False,
        show_edge_lines: bool = True,
    ) -> None:
        """Add each block with its stored color/opacity (and optional edge lines)."""
        for key in self.multiblock.keys():
            mesh = self.multiblock[key]
            if mesh is None:
                continue
            if key in self.edge_keys:
                if show_edge_lines:
                    actor = plotter.add_mesh(
                        mesh,
                        name=key,
                        color=self.edge_color,
                        line_width=self.edge_width,
                        render_lines_as_tubes=False,
                        point_size=0.0,
                        render_points_as_spheres=False,
                    )
                    prop = actor.GetProperty()
                    prop.SetVertexVisibility(False)
                    prop.SetPointSize(0.001)
                continue
            color = None
            opacity = 1.0
            rgba = self.rgba.get(key)
            if rgba is not None:
                color = rgba[:3]
                opacity = rgba[3]
            plotter.add_mesh(mesh, name=key, color=color, opacity=opacity, show_edges=show_edges)


# ---------- converter (mirrors ScgHelixConverter) ----------

class ScgPyVistaConverter:
    """
    Converts ClassCAD scene graph (Scg) data into PyVista geometry.
    Mirrors the structure of ScgHelixConverter.cs.
    """

    @staticmethod
    def convert_scg(
        scg: Any,
        *,
        include_edges: bool = True,
        min_arc_segments: int = 32,
        circle_segments: int = 180,
    ) -> ScgPyVistaScene:
        """Builds a ScgPyVistaScene from an Scg scene graph starting at the given root."""
        if isinstance(scg, dict):
            structure = scg["structure"]
            graphic = scg["graphic"]
        else:
            structure = scg.structure
            graphic = scg.graphic

        tree = structure["tree"] if isinstance(structure, dict) else structure.tree
        root_id = structure["root"] if isinstance(structure, dict) else structure.root

        # Build container lookup by id (containers may arrive as list or dict)
        raw_containers = graphic["containers"] if isinstance(graphic, dict) else graphic.containers
        if isinstance(raw_containers, list):
            containers: Dict[int, Dict[str, Any]] = {c["id"]: c for c in raw_containers if "id" in c}
        else:
            containers = {int(k): v for k, v in raw_containers.items()}

        out = pv.MultiBlock()
        out_rgba: Dict[str, Tuple[float, float, float, float]] = {}
        out_edge_keys: Set[str] = set()

        # Pre-build base meshes and edges per container so they are created
        # once and then cheaply cloned + transformed for every instance.
        base_mesh_cache: Dict[int, Tuple[pv.PolyData, Tuple[float, float, float, float]]] = {}
        base_edge_cache: Dict[int, pv.PolyData] = {}

        for cid, container in containers.items():
            ctype = container.get("type", ScgContainerType.NONE)
            if ctype not in _MESH_CONTAINER_TYPES:
                continue

            meshes = container.get("meshes") or []
            merged: Optional[pv.PolyData] = None
            last_rgba: Tuple[float, float, float, float] = (0.39, 0.58, 0.93, 1.0)
            for mesh_data in meshes:
                vertices = mesh_data.get("vertices")
                indices = mesh_data.get("indices")
                if not vertices or not indices or len(vertices) < 3 or len(indices) < 3:
                    continue
                pts = _as_points(vertices)
                faces = _tri_faces(indices)
                poly = pv.PolyData(pts, faces)
                normals = mesh_data.get("normals")
                if normals and len(normals) == len(vertices):
                    poly.point_data["Normals"] = _as_points(normals)
                merged = poly if merged is None else merged.merge(poly, inplace=False)
                last_rgba = _resolve_color(mesh_data, container)
            if merged is not None:
                base_mesh_cache[cid] = (merged, last_rgba)

            if include_edges:
                edge_poly = _build_edge_polydata(
                    container,
                    min_arc_segments=min_arc_segments,
                    circle_segments=circle_segments,
                )
                if edge_poly is not None:
                    base_edge_cache[cid] = edge_poly

        ScgPyVistaConverter._convert_node(
            root_id, tree, containers, out, out_rgba, out_edge_keys,
            parent_transform=np.identity(4), is_root=True,
            include_edges=include_edges,
            min_arc_segments=min_arc_segments,
            circle_segments=circle_segments,
            base_mesh_cache=base_mesh_cache,
            base_edge_cache=base_edge_cache,
        )

        return ScgPyVistaScene(multiblock=out, rgba=out_rgba, edge_keys=out_edge_keys)

    @staticmethod
    def load_scg_into_plotter(
        plotter: pv.Plotter,
        scg: Any,
        *,
        show_edges: bool = False,
        show_edge_lines: bool = True,
        include_edges: bool = True,
        min_arc_segments: int = 32,
        circle_segments: int = 180,
    ) -> ScgPyVistaScene:
        """Loads an Scg scene graph into a PyVista plotter, replacing existing meshes."""
        plotter.clear()
        scene = ScgPyVistaConverter.convert_scg(
            scg,
            include_edges=include_edges,
            min_arc_segments=min_arc_segments,
            circle_segments=circle_segments,
        )
        scene.add_to_plotter(plotter, show_edges=show_edges, show_edge_lines=show_edge_lines)
        return scene

    @staticmethod
    def _convert_node(
        obj_id: int,
        tree: Dict[str, Any],
        containers: Dict[int, Dict[str, Any]],
        out: pv.MultiBlock,
        out_rgba: Dict[str, Tuple[float, float, float, float]],
        out_edge_keys: Set[str],
        parent_transform: np.ndarray,
        is_root: bool = False,
        *,
        include_edges: bool,
        min_arc_segments: int,
        circle_segments: int,
        base_mesh_cache: Dict[int, Tuple[pv.PolyData, Tuple[float, float, float, float]]],
        base_edge_cache: Dict[int, pv.PolyData],
    ) -> None:
        key = str(obj_id)
        obj = tree.get(key)
        if obj is None:
            return

        # Build a transform from the object's coordinate system (skip for root)
        node_transform = parent_transform
        if not is_root:
            csys = obj.get("coordinateSystem")
            if csys is not None and len(csys) >= 4:
                local_mat = _csys_to_matrix(csys)
                if local_mat is not None:
                    node_transform = parent_transform @ local_mat

        # Determine content based on object type (matching C# priority order)
        geometry_id_list = obj.get("geometryIdList") or []
        solids = obj.get("solids") or []
        link = obj.get("link")
        children = obj.get("children") or []

        if geometry_id_list:
            ScgPyVistaConverter._convert_solids(
                geometry_id_list,
                out,
                out_rgba,
                out_edge_keys,
                node_transform,
                obj.get("name", "node"),
                include_edges=include_edges,
                base_mesh_cache=base_mesh_cache,
                base_edge_cache=base_edge_cache,
            )
        elif solids:
            ScgPyVistaConverter._convert_part(
                obj_id, tree, out, out_rgba, out_edge_keys,
                node_transform, obj.get("name", "node"),
                include_edges=include_edges,
                base_mesh_cache=base_mesh_cache,
                base_edge_cache=base_edge_cache,
            )
        elif link is not None:
            ScgPyVistaConverter._convert_part(
                link, tree, out, out_rgba, out_edge_keys,
                node_transform, obj.get("name", "node"),
                include_edges=include_edges,
                base_mesh_cache=base_mesh_cache,
                base_edge_cache=base_edge_cache,
            )
        elif children:
            for child_id in children:
                ScgPyVistaConverter._convert_node(
                    child_id, tree, containers, out, out_rgba, out_edge_keys,
                    node_transform, is_root=False,
                    include_edges=include_edges,
                    min_arc_segments=min_arc_segments,
                    circle_segments=circle_segments,
                    base_mesh_cache=base_mesh_cache,
                    base_edge_cache=base_edge_cache,
                )

    @staticmethod
    def _convert_part(
        part_id: int,
        tree: Dict[str, Any],
        out: pv.MultiBlock,
        out_rgba: Dict[str, Tuple[float, float, float, float]],
        out_edge_keys: Set[str],
        transform: np.ndarray,
        name: str,
        *,
        include_edges: bool,
        base_mesh_cache: Dict[int, Tuple[pv.PolyData, Tuple[float, float, float, float]]],
        base_edge_cache: Dict[int, pv.PolyData],
    ) -> None:
        part_key = str(part_id)
        part = tree.get(part_key)
        if part is None:
            return
        solids = part.get("solids") or []
        if not solids:
            return

        ScgPyVistaConverter._convert_solids(
            solids, out, out_rgba, out_edge_keys,
            transform, name,
            include_edges=include_edges,
            base_mesh_cache=base_mesh_cache,
            base_edge_cache=base_edge_cache,
        )

    @staticmethod
    def _convert_solids(
        geometry_ids: List[int],
        out: pv.MultiBlock,
        out_rgba: Dict[str, Tuple[float, float, float, float]],
        out_edge_keys: Set[str],
        transform: np.ndarray,
        name: str,
        *,
        include_edges: bool,
        base_mesh_cache: Dict[int, Tuple[pv.PolyData, Tuple[float, float, float, float]]],
        base_edge_cache: Dict[int, pv.PolyData],
    ) -> None:
        is_identity = np.allclose(transform, np.identity(4))

        for geo_id in geometry_ids:
            cached = base_mesh_cache.get(geo_id) or base_mesh_cache.get(int(geo_id))
            if cached is None:
                continue
            base_mesh, rgba = cached

            inst = base_mesh.copy(deep=True)
            if not is_identity:
                inst.transform(transform, inplace=True)

            block_key = f"{name}::c{geo_id}::m{len(out)}"
            out[block_key] = inst
            out_rgba[block_key] = rgba

            # Edge geometry (clone from cache)
            if include_edges:
                edge_base = base_edge_cache.get(geo_id) or base_edge_cache.get(int(geo_id))
                if edge_base is not None:
                    edge_inst = edge_base.copy(deep=True)
                    if not is_identity:
                        edge_inst.transform(transform, inplace=True)
                    edge_key = f"{name}::c{geo_id}::edges{len(out)}"
                    out[edge_key] = edge_inst
                    out_edge_keys.add(edge_key)


# ---------- convenience file loader ----------

def load_scg_to_pyvista(
    path: str,
    *,
    include_edges: bool = True,
    min_arc_segments: int = 32,
    circle_segments: int = 180,
    **_kwargs: Any,
) -> ScgPyVistaScene:
    """Load an SCG JSON file into a PyVista scene."""
    with open(path, "r", encoding="utf-8") as f:
        scg = json.load(f)
    return ScgPyVistaConverter.convert_scg(
        scg,
        include_edges=include_edges,
        min_arc_segments=min_arc_segments,
        circle_segments=circle_segments,
    )


# ---------- tiny demo (optional) ----------
if __name__ == "__main__":
    import sys
    scene = load_scg_to_pyvista(sys.argv[1])
    pl = pv.Plotter()
    scene.add_to_plotter(pl, show_edges=False)
    pl.show()
