import math

from classcadconnector import CCApiU

from . import resourcehelper


# ───── CreatePart ─────

async def create_part(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="CreatePart"))
    feature = await api.v1.part.cylinder(dict(id=part_id, diameter=50, height=100))

    top_edges = await api.v1.part.getGeometryIds(dict(id=part_id, circles=[dict(pos=[0, 0, 100])]))
    if top_edges and top_edges.get("circles"):
        feature = await api.v1.part.fillet(dict(id=part_id, references=top_edges["circles"], radius=10))

    bottom_edges = await api.v1.part.getGeometryIds(dict(id=part_id, circles=[dict(pos=[0, 0, 0])]))
    if bottom_edges and bottom_edges.get("circles"):
        feature = await api.v1.part.chamfer(dict(id=part_id, type="EQUAL_DISTANCE", references=bottom_edges["circles"], distance1=10))

    await api.v1.common.setAppearance(dict(target=feature, color=[203, 67, 22], transparency=0.5))
    return part_id


# ───── Sketch ─────

async def sketch(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Sketch"))
    data = resourcehelper.read_text("SketchesTemplate.ofb")
    wp = await api.v1.part.workPlane(dict(id=part_id, normal=[0, 0, 1], name="WP"))
    sk = await api.v1.sketch.create(dict(id=part_id, planeId=wp))
    await api.v1.sketch.loadFrom(dict(id=sk, partId=part_id, data=data, format="OFB"))
    await api.v1.part.extrusion(dict(id=part_id, type="UP", references=[sk], limit2=20))
    return part_id


# ───── Sketch2 ─────

async def sketch2(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Sketch2"))
    data = resourcehelper.read_text("SuspensionBracket.ofb")
    wp = await api.v1.part.workPlane(dict(id=part_id, normal=[0, 0, 1], name="WP"))
    sk = await api.v1.sketch.create(dict(id=part_id, planeId=wp))
    await api.v1.sketch.loadFrom(dict(id=sk, partId=part_id, data=data, format="OFB"))

    sr_outer = await api.v1.sketch.getSketchRegion(dict(id=sk, name="Outer"))
    sr_holes = await api.v1.sketch.getSketchRegion(dict(id=sk, name="Holes"))
    sr_inner = await api.v1.sketch.getSketchRegion(dict(id=sk, name="Inner"))

    extr_outer = await api.v1.part.extrusion(dict(id=part_id, references=[sr_outer], type="SYMMETRIC", limit2=20))
    extr_holes = await api.v1.part.extrusion(dict(id=part_id, references=[sr_holes], type="SYMMETRIC", limit2=15))
    extr_inner = await api.v1.part.extrusion(dict(id=part_id, references=[sr_inner], type="SYMMETRIC", limit2=10))

    await api.v1.part.boolean(dict(id=part_id, type="UNION", target=dict(id=extr_holes), tools=[extr_outer, extr_inner]))
    return part_id


# ───── Sketch3 ─────

async def sketch3(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Sketch3"))
    top = await api.v1.part.getWorkGeometry(dict(id=part_id, name="Top"))
    sk = await api.v1.sketch.create(dict(id=part_id, planeId=top))

    arc1 = await api.v1.sketch.arcByCenter(dict(id=sk, startPos=[0, 30, 0], endPos=[0, -30, 0], centerPos=[0, 0, 0]))
    geom = await api.v1.sketch.geometry(dict(id=sk, lines=[
        dict(startPos=[0, 30, 0], endPos=[50, 30, 0]),
        dict(startPos=[50, 30, 0], endPos=[80, -5, 0]),
        dict(startPos=[80, -5, 0], endPos=[75, -10, 0]),
    ]))
    arc2 = await api.v1.sketch.arcBy3Points(dict(id=sk, startPos=[75, -10, 0], endPos=[0, -30, 0], midPos=[32, -36, 0]))

    await api.v1.sketch.constraint(dict(id=sk, type="TANGENT", geomIds=[arc1, geom.get("lines")[0]]))
    await api.v1.sketch.constraint(dict(id=sk, type="PERPENDICULAR", geomIds=[geom.get("lines")[1], geom.get("lines")[2]]))
    await api.v1.sketch.constraint(dict(id=sk, type="TANGENT", geomIds=[arc2, arc1]))

    await api.v1.sketch.dimension(dict(id=sk, type="RADIUS", geomIds=[arc1], value=30))
    await api.v1.sketch.dimension(dict(id=sk, type="HORIZONTAL_DISTANCE", geomIds=[geom.get("lines")[0]], value=50))
    await api.v1.sketch.dimension(dict(id=sk, type="ANGLE", geomIds=[geom.get("lines")[0], geom.get("lines")[1]], value="135g", dimPos=[40, 20, 0]))
    await api.v1.sketch.dimension(dict(id=sk, type="OFFSET", geomIds=[geom.get("lines")[1]], value=50))
    await api.v1.sketch.dimension(dict(id=sk, type="OFFSET", geomIds=[geom.get("lines")[2]], value=15))
    await api.v1.sketch.dimension(dict(id=sk, type="RADIUS", geomIds=[arc2], value=75))

    await api.v1.part.extrusion(dict(id=part_id, references=[*geom.get("lines"), arc1, arc2], limit2=10))
    return part_id


# ───── Sketch4 ─────

async def sketch4(api: CCApiU, p: dict):
    radius_value = p.get("Radius", 100)
    part_id = await api.v1.part.create(dict(name="Sketch4"))
    top = await api.v1.part.getWorkGeometry(dict(id=part_id, name="Top"))
    sk = await api.v1.sketch.create(dict(id=part_id, planeId=top))

    await api.v1.part.expression(dict(id=part_id, toCreate=[
        dict(name="circle_Radius", value=radius_value),
        dict(name="arc_Radius", value="circle_Radius*0.7"),
        dict(name="rectangle_Height", value="circle_Radius*0.3"),
        dict(name="offset", value="circle_Radius*0.3"),
    ]))

    circle = await api.v1.sketch.circle(dict(id=sk, centerPos=[0, 0, 0], radius=radius_value))
    await api.v1.sketch.dimension(dict(id=sk, type="RADIUS", value="@expr.circle_Radius", geomIds=[circle]))

    line1 = await api.v1.sketch.line(dict(id=sk, startPos=[-70, -20, 0], endPos=[70, -30, 0]))
    arc1 = await api.v1.sketch.arcBy3Points(dict(id=sk, startPos=[70, -30, 0], endPos=[-70, -20, 0], midPos=[-10, -70, 0]))
    points = await api.v1.sketch.getPoints(dict(id=circle))

    await api.v1.sketch.constraint([
        dict(id=sk, type="HORIZONTAL", geomIds=[line1]),
        dict(id=sk, type="MIDPOINT", geomIds=[line1, points.get("centerId")]),
        dict(id=sk, type="CONCENTRIC", geomIds=[arc1, circle]),
    ])
    await api.v1.sketch.dimension([
        dict(id=sk, type="RADIUS", value="@expr.arc_Radius", geomIds=[arc1]),
        dict(id=sk, type="OFFSET", value="@expr.offset", geomIds=[line1, points.get("centerId")]),
    ])

    line2 = await api.v1.sketch.line(dict(id=sk, startPos=[-70, 20, 0], endPos=[70, 30, 0]))
    arc2 = await api.v1.sketch.arcBy3Points(dict(id=sk, startPos=[70, 30, 0], endPos=[-70, 20, 0], midPos=[-10, 70, 0]))

    await api.v1.sketch.constraint([
        dict(id=sk, type="PARALLEL", geomIds=[line1, line2]),
        dict(id=sk, type="EQUAL_LENGTH", geomIds=[line1, line2]),
        dict(id=sk, type="EQUAL_RADIUS", geomIds=[arc1, arc2]),
        dict(id=sk, type="MIDPOINT", geomIds=[line2, points.get("centerId")]),
    ])
    await api.v1.sketch.dimension(dict(id=sk, type="OFFSET", value="@expr.offset", geomIds=[line2, points.get("centerId")]))

    lines = await api.v1.sketch.rectangle(dict(id=sk, startPos=[0, 0, 0], endPos=[-50, 20, 0], isCentered=True))
    points2 = await api.v1.sketch.getPoints(dict(id=line1))
    await api.v1.sketch.constraint(dict(id=sk, type="COLINEAR", geomIds=[points2.get("startId"), lines[1]]))
    await api.v1.sketch.dimension(dict(id=sk, type="VERTICAL_DISTANCE", value="@expr.rectangle_Height", geomIds=[lines[1]]))

    geom = await api.v1.sketch.getGeometry(dict(id=sk))
    extrusion = await api.v1.part.extrusion(dict(id=part_id, references=[*geom.get("lines"), *geom.get("arcs"), *geom.get("circles")]))
    await api.v1.part.setAppearance(dict(target=extrusion, color=[125, 196, 145]))
    return part_id


# ───── Twist ─────

TWIST_OPTIONS = [
    'Sketch region "triangle" (Up)',
    'Sketch region "rectangle" (Down without cap)',
    'Sketch region "moon" (Down)',
    'Sketch region "cross" (Custom limits)',
    'Sketch region "square" (Custom twist center)',
    'Composite curve (Custom limits)',
    'Sketch curves (Up)',
    'Sketch "0" (Up)',
    'Sketch "1" (Up)',
]

async def twist(api: CCApiU, p: dict):
    opt_idx = max(0, min(int(p.get("Options", 0)), len(TWIST_OPTIONS) - 1))
    selected = TWIST_OPTIONS[opt_idx]

    template_data = resourcehelper.read_bytes("SketchRegionsTemplate.ofb")
    loaded = await api.v1.common.load(dict(data=template_data, format="OFB"))
    part_id = loaded.get("id")

    if selected == 'Sketch region "triangle" (Up)':
        sr = await api.v1.part.getSketchRegion(dict(id=part_id, name="Triangle"))
        await api.v1.part.twist(dict(id=part_id, references=[sr], type="UP", limit2=100, twistAngle=math.pi))
    elif selected == 'Sketch region "rectangle" (Down without cap)':
        sr = await api.v1.part.getSketchRegion(dict(id=part_id, name="Rectangle"))
        await api.v1.part.twist(dict(id=part_id, references=[sr], type="DOWN", limit1=0, limit2=80, twistAngle=math.pi / 2, capEnds=False))
    elif selected == 'Sketch region "moon" (Down)':
        sr = await api.v1.part.getSketchRegion(dict(id=part_id, name="Moon"))
        await api.v1.part.twist(dict(id=part_id, references=[sr], type="DOWN", limit2=60, twistAngle=2 * math.pi))
    elif selected == 'Sketch region "cross" (Custom limits)':
        sr = await api.v1.part.getSketchRegion(dict(id=part_id, name="Cross"))
        await api.v1.part.twist(dict(id=part_id, references=[sr], type="UP", limit1=40, limit2=120, twistAngle=math.pi))
    elif selected == 'Sketch region "square" (Custom twist center)':
        sr = await api.v1.part.getSketchRegion(dict(id=part_id, name="Square"))
        await api.v1.part.twist(dict(id=part_id, references=[sr], type="CUSTOM", limit2=60, twistAngle="180g", twistCenter=[10, 10, 0]))
    elif selected == 'Composite curve (Custom limits)':
        comp_curve = await api.v1.part.getFeature(dict(id=part_id, name="Composite Curve"))
        await api.v1.part.twist(dict(id=part_id, references=[comp_curve], type="UP", limit1=40, limit2=120, twistAngle=math.pi))
    elif selected == 'Sketch "0" (Up)':
        sketch0 = await api.v1.part.getSketch(dict(id=part_id, name="Sketch0"))
        await api.v1.part.twist(dict(id=part_id, references=[sketch0], type="UP", limit1=40, limit2=120, twistAngle=math.pi))
    elif selected == 'Sketch "1" (Up)':
        sketch1 = await api.v1.part.getSketch(dict(id=part_id, name="Sketch1"))
        await api.v1.part.twist(dict(id=part_id, references=[sketch1], type="UP", limit1=40, limit2=120, twistAngle=math.pi))
    elif selected == 'Sketch curves (Up)':
        sketch_lines = [481, 487, 495, 503, 511, 519]
        await api.v1.part.twist(dict(id=part_id, references=sketch_lines, type="UP", limit1=0, limit2=120, twistAngle=math.pi))

    return part_id


# ───── Gripper ─────

async def gripper(api: CCApiU, p: dict):
    data = resourcehelper.read_bytes("GripperTemplate.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB", ident="root"))
    loaded_id = loaded.get("id")

    await api.v1.part.updateExpression(dict(id=loaded_id, toUpdate=[
        dict(name="W", value=float(p.get("Width", 60))),
        dict(name="H", value=float(p.get("Height", 170))),
        dict(name="D", value=float(p.get("Distance", 40))),
        dict(name="W1", value=float(p.get("Taper", 50))),
    ]))
    return loaded_id


# ───── FlangePart ─────

async def flange_part(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="FlangePrt"))
    await _build_flange_prt(api, part_id)
    return part_id


# ───── Flange (Configurator) ─────

async def flange(api: CCApiU, p: dict):
    hole_count = int(p.get("Holes Count", 6))
    flange_height = p.get("Flange Height", 100)
    part_id = await api.v1.part.create(dict(name="FlangeConfigurator"))
    await _build_flange_prt(api, part_id, hole_count=hole_count, flange_height=flange_height)
    return part_id


async def _build_flange_prt(api, part_id, hole_count=4, flange_height=110):
    thickness = 30
    upper_cyl_diam = 190
    upper_cyl_hole_diam = upper_cyl_diam - thickness
    base_cyl_diam = upper_cyl_diam + 4 * thickness
    hole_offset = (upper_cyl_diam / 2) + thickness
    hole_angle = (2 * math.pi) / hole_count

    await api.v1.part.expression(dict(id=part_id, toCreate=[
        dict(name="thickness", value=thickness),
        dict(name="upperCylDiam", value=upper_cyl_diam),
        dict(name="upperCylHoleDiam", value=upper_cyl_hole_diam),
        dict(name="flangeHeight", value=flange_height),
        dict(name="baseCylDiam", value=base_cyl_diam),
        dict(name="holeOffset", value=hole_offset),
        dict(name="holeCount", value=hole_count),
        dict(name="holeAngle", value=hole_angle),
    ]))

    wcs_center = await api.v1.part.workCSys(dict(id=part_id, offset=[0, 0, 0], rotation=[0, 0, 0], name="WCSCenter"))
    base_cyl = await api.v1.part.cylinder(dict(id=part_id, references=[wcs_center], diameter=base_cyl_diam, height=thickness))
    upper_cyl = await api.v1.part.cylinder(dict(id=part_id, references=[wcs_center], diameter=upper_cyl_diam, height=flange_height))
    flange_solid = await api.v1.part.boolean(dict(id=part_id, type="UNION", target=base_cyl, tools=[upper_cyl]))
    sub_cyl = await api.v1.part.cylinder(dict(id=part_id, references=[wcs_center], diameter=upper_cyl_hole_diam, height=flange_height))
    flange_solid = await api.v1.part.boolean(dict(id=part_id, type="SUBTRACTION", target=flange_solid, tools=[sub_cyl]))

    wcs_hole1_bottom = await api.v1.part.workCSys(dict(id=part_id, offset=[0, hole_offset, 0], rotation=[0, 0, 0], name="WCSBoltHoleBottom"))
    sub_cyl_hole1 = await api.v1.part.cylinder(dict(id=part_id, references=[wcs_hole1_bottom], diameter=30, height=50))

    z_axis = await api.v1.part.getWorkGeometry(dict(id=part_id, name="ZAxis"))
    pattern = await api.v1.part.circularPattern(dict(
        id=part_id, targets=[dict(id=sub_cyl_hole1)], references=[z_axis],
        angle=hole_angle, count=hole_count, merged=True,
    ))
    await api.v1.part.boolean(dict(id=part_id, type="SUBTRACTION", target=flange_solid, tools=[pattern]))
    await api.v1.part.workCSys(dict(id=part_id, offset=[0, hole_offset, thickness], rotation=[0, 0, 0], name="WCSBoltHoleTop"))


# ───── Shadowbox ─────

async def shadowbox(api: CCApiU, p: dict):
    depth = p.get("Depth", 20)
    height = p.get("Height", 200)
    width = p.get("Width", 400)
    min_gap = p.get("Min. Gap", 5)
    hole_diameter = p.get("Hole Diameter", 35)
    columns = int(p.get("Columns", 8))
    rows = int(p.get("Rows", 4))

    data = resourcehelper.read_bytes("Shadowbox.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB", ident="root"))
    loaded_id = loaded.get("id")

    max_columns = int(math.floor((width - (columns + 1) * min_gap) / hole_diameter))
    max_rows = int(math.floor((height - (rows + 1) * min_gap) / hole_diameter))
    if width - columns * hole_diameter < (columns + 1) * min_gap:
        columns = max(0, max_columns)
    if height - rows * hole_diameter < (rows + 1) * min_gap:
        rows = max(0, max_rows)

    await api.v1.part.updateExpression(dict(id=loaded_id, toUpdate=[
        dict(name="Columns", value=columns),
        dict(name="Rows", value=rows),
        dict(name="HoleDiameter", value=hole_diameter),
        dict(name="FoamDepth", value=depth),
        dict(name="FoamHeight", value=height),
        dict(name="FoamWidth", value=width),
    ]))
    return loaded_id


# ───── MechanicalPart ─────

async def mechanical_part(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="MechanicalPart"))

    box = await api.v1.part.box(dict(id=part_id, length=50, height=40, width=40))
    wp = await api.v1.part.workPlane(dict(id=part_id, position=[50, 20, 20], normal=[1, 0, 1]))
    slice_id = await api.v1.part.slice(dict(id=part_id, targets=[box], reference=wp, inverted=True))

    front = await api.v1.part.getWorkGeometry(dict(id=part_id, name="Front"))
    sk1 = await api.v1.part.sketch(dict(id=part_id, planeId=front))
    await api.v1.sketch.setReferences(dict(id=sk1, invertPlane=True))
    res = await api.v1.sketch.geometry(dict(id=sk1, lines=[
        dict(startPos=[50, 10, 0], endPos=[30, 10, 0]),
        dict(startPos=[30, 10, 0], endPos=[30, 20, 0]),
        dict(startPos=[30, 20, 0], endPos=[20, 20, 0]),
        dict(startPos=[20, 20, 0], endPos=[20, 30, 0]),
        dict(startPos=[20, 30, 0], endPos=[10, 30, 0]),
        dict(startPos=[10, 30, 0], endPos=[10, 40, 0]),
        dict(startPos=[10, 40, 0], endPos=[50, 40, 0]),
        dict(startPos=[50, 40, 0], endPos=[50, 10, 0]),
    ]))

    extrusion = await api.v1.part.extrusion(dict(id=part_id, references=res.get("lines"), limit2=-30))
    subtraction = await api.v1.part.boolean(dict(id=part_id, type="SUBTRACTION", target=slice_id, tools=[extrusion]))

    top = await api.v1.part.getWorkGeometry(dict(id=part_id, name="Top"))
    sk2 = await api.v1.part.sketch(dict(id=part_id, planeId=top))
    res2 = await api.v1.sketch.geometry(dict(id=sk2, lines=[
        dict(startPos=[30, 0, 0], endPos=[40, 30, 0]),
        dict(startPos=[40, 30, 0], endPos=[30, 30, 0]),
        dict(startPos=[30, 30, 0], endPos=[30, 0, 0]),
    ]))

    extrusion2 = await api.v1.part.extrusion(dict(id=part_id, references=res2.get("lines"), limit2=20))
    union = await api.v1.part.boolean(dict(id=part_id, target=subtraction, tools=[extrusion2]))
    await api.v1.part.setAppearance(dict(target=union, color=[125, 36, 39], transparency=0.75))
    return part_id


# ───── MechanicalPart2 ─────

async def mechanical_part2(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="MechanicalPart2"))

    await api.v1.part.expression(dict(id=part_id, toCreate=[
        dict(name="length", value=41),
        dict(name="height", value="0.65*length"),
        dict(name="thickness", value="0.2*length"),
        dict(name="length2", value="0.6*length"),
        dict(name="height2", value="0.26*length"),
    ]))

    box1 = await api.v1.part.box(dict(id=part_id, length="@expr.length", height="@expr.height", width="@expr.thickness"))
    wcs2 = await api.v1.part.workCSys(dict(id=part_id, offset="[@expr.thickness,0,@expr.thickness]"))
    box2 = await api.v1.part.box(dict(id=part_id, references=[wcs2], length="@expr.length2", height="@expr.height2", width="@expr.thickness"))

    subtraction = await api.v1.part.boolean(dict(id=part_id, type="SUBTRACTION", target=dict(id=box1), tools=[box2]))
    expr = await api.v1.part.getExpression(dict(id=part_id, name="length"))
    faces = await api.v1.part.getGeometryIds(dict(id=part_id, planes=[dict(positions=[[expr.get("value"), 1, 1]])]))
    wp = await api.v1.part.workPlane(dict(id=part_id, type="PLANE", references=[faces.get("planes")[0]]))
    mirror = await api.v1.part.mirror(dict(id=part_id, references=[wp], targets=[subtraction]))
    await api.v1.part.setAppearance(dict(target=mirror, color=[125, 36, 145]))

    work_axis = await api.v1.part.workAxis(dict(id=part_id, position="[0,@expr.thickness/2,@expr.height/2]"))
    rotation = await api.v1.part.rotation(dict(id=part_id, targets=[dict(id=mirror, indices=[1])], references=[work_axis], angle="90g"))
    translation = await api.v1.part.translation(dict(id=part_id, targets=[rotation], references=[work_axis], distance="-2*@expr.thickness"))
    await api.v1.part.setAppearance(dict(target=translation, color=[25, 96, 145]))
    return part_id


# ───── MechanicalPart3 ─────

async def mechanical_part3(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="MechanicalPart3"))

    ei = await api.v1.part.entityInjection(dict(id=part_id, name="SolidContainer"))
    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.polyline2d(dict(id=shape, points=[
        [0, 0, 0], [0, 4, 0], [2.6, 4, 0], [6.8, 8.2, 0], [2.5, 8.2, 0], [2.5, 10, 0],
        [10, 10, 0], [10, 2.5, 0], [8.2, 2.5, 0], [8.2, 6.8, 0], [4, 2.6, 0], [4, 0, 0],
    ], bulges=[0] * 12, close=True))

    await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, 100]))

    z_axis = await api.v1.part.getWorkGeometry(dict(id=part_id, name="ZAxis"))
    circular_pattern = await api.v1.part.circularPattern(dict(
        id=part_id, targets=[dict(id=ei, indices=[1])], references=[z_axis],
        angle="90g", count=4, merged=True,
    ))

    ei2 = await api.v1.part.entityInjection(dict(id=part_id, name="SolidContainer2"))
    cp_solids = await api.v1.solid.useSolid(dict(**{"in": ei2, "from": [circular_pattern]}))
    sliced = await api.v1.solid.slice(dict(id=ei2, target=cp_solids[0], originPos=[0, 0, 50], normal=[0, 1, 1]))

    translated = await api.v1.solid.translation(dict(id=ei2, target=sliced, translation=[0, 0, -50]))
    rotated = await api.v1.solid.rotation(dict(id=ei2, target=translated, rotation=[-math.pi / 2, 0, 0]))
    rotated = await api.v1.solid.rotation(dict(id=ei2, target=rotated, rotation=[0, math.pi, 0]))
    await api.v1.solid.translation(dict(id=ei2, target=rotated, translation=[0, 0, 50]))
    return part_id
