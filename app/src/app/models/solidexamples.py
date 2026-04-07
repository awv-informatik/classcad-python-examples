import math

from classcadconnector import CCApiU

from . import resourcehelper


# ───── helpers ─────

def _circle_polyline_pld(cx, cy, radius, segments=48):
    pts = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        pts.append(dict(xa=cx + radius * math.cos(angle), ya=cy + radius * math.sin(angle)))
    return pts


def _generate_profile_path(wf, tf, h, tw):
    half_wf = wf / 2
    half_tw = tw / 2
    half_h = h / 2
    return [
        dict(xa=-half_wf, ya=-half_h - tf, c=2),
        dict(xr=wf, c=2),
        dict(yr=tf, c=2),
        dict(xr=-half_wf + half_tw, r=5),
        dict(yr=h, r=5),
        dict(xr=half_wf - half_tw, c=2),
        dict(yr=tf, c=2),
        dict(xr=-wf, c=2),
        dict(yr=-tf, c=2),
        dict(xr=half_wf - half_tw, r=5),
        dict(yr=-h, r=5),
        dict(xr=-half_wf + half_tw, c=2),
    ]


def _generate_regular_polygon(n, d):
    angle_step = 2.0 * math.pi / n
    side_length = d / math.cos(math.pi / n)
    pld = [dict(xa=0, ya=0), dict(xr=side_length)]
    for _ in range(1, n):
        pld.append(dict(l=side_length, ar=angle_step))
    return pld


def _generate_star_polygon(n, outer_d, inner_d, outer_rad, inner_rad):
    angle_step = 2.0 * math.pi / (n * 2)
    pts = []
    for i in range(n * 2):
        angle = i * angle_step
        radius = outer_d / 2 if i % 2 == 0 else inner_d / 2
        fillet = outer_rad if i % 2 == 0 else inner_rad
        pts.append(dict(xa=math.cos(angle) * radius, ya=math.sin(angle) * radius, r=fillet))
    return pts


# ───── Fish ─────

async def fish(api: CCApiU, p: dict):
    thickness = p.get("Thickness", 5)
    part_id = await api.v1.part.create(dict(name="Fish"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="FishSolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[25, 25, 0], [75, -55, 0], [115, 15, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[115, 15, 0], [125, 15, 0], [140, -15, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[140, -15, 0], [140, 25, 0], [140, 65, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[140, 65, 0], [125, 35, 0], [115, 35, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[115, 35, 0], [75, 105, 0], [25, 25, 0]]))

    fish1 = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, thickness]))
    fish2 = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, thickness]))
    await api.v1.solid.mirror(dict(id=ei, target=fish2, originPos=[0, 0, 0], normal=[1, 0, 0]))

    await api.v1.common.setAppearance([
        dict(target=fish1, color=[88, 55, 99]),
        dict(target=fish2, color=[166, 55, 112], transparency=0.5),
    ])
    return part_id


# ───── Heart ─────

async def heart(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Heart"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="HeartSolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[25, 25, 0], [20, 0, 0], [0, 0, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[0, 0, 0], [-30, 0, 0], [-30, 35, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[-30, 35, 0], [-30, 55, 0], [-10, 77, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[-10, 77, 0], [5, 87, 0], [25, 95, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[25, 95, 0], [45, 87, 0], [60, 77, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[60, 77, 0], [80, 55, 0], [80, 35, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[80, 35, 0], [80, 0, 0], [50, 0, 0]]))
    await api.v1.curve.bezierCurve(dict(id=shape, points=[[50, 0, 0], [35, 0, 0], [25, 25, 0]]))
    heart_body = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, 5]))
    await api.v1.common.setAppearance(dict(target=heart_body, color=[255, 120, 255]))
    return part_id


# ───── Lego ─────

async def lego(api: CCApiU, p: dict):
    rows = int(p.get("Rows", 2))
    columns = int(p.get("Columns", 5))
    part_id = await api.v1.part.create(dict(name="Lego"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="LegoSolidAPI"))

    unit_length = 8
    length = rows * unit_length
    width = columns * unit_length
    thickness = 1.6
    height = unit_length + thickness
    dot_height = 1.7
    dot_radius = 2.4
    dot_gap = dot_radius + thickness
    tube_height = height - thickness
    tube_radius = (2.0 * dot_gap * math.sqrt(2) - 2.0 * dot_radius) / 2.0

    basic = await api.v1.solid.box(dict(id=ei, width=width, height=height, length=length))
    sub_box = await api.v1.solid.box(dict(
        id=ei, width=width - 2 * thickness, height=height - thickness,
        length=length - 2 * thickness, translation=[0, 0, -thickness],
    ))
    await api.v1.solid.subtraction(dict(id=ei, target=basic, tools=[sub_box]))

    for i in range(columns):
        for j in range(rows):
            dot = await api.v1.solid.cylinder(dict(
                id=ei, diameter=2 * dot_radius, height=dot_height,
                translation=[
                    length / 2 - dot_gap - j * (2 * dot_gap),
                    width / 2 - dot_gap - i * (2 * dot_gap),
                    (height + dot_height) / 2,
                ],
            ))
            await api.v1.solid.union(dict(id=ei, target=basic, tools=[dot]))

    if rows > 1 and columns > 1:
        tube = await api.v1.solid.cylinder(dict(id=ei, diameter=2 * tube_radius, height=tube_height))
        sub_cyl = await api.v1.solid.cylinder(dict(id=ei, diameter=2 * (tube_radius - thickness), height=tube_height))
        await api.v1.solid.subtraction(dict(id=ei, target=tube, tools=[sub_cyl]))

        for i in range(columns - 1):
            for j in range(rows - 1):
                copy = await api.v1.solid.copy(dict(
                    id=ei, target=tube,
                    translation=[
                        length / 2 - 2 * dot_gap - j * (2 * dot_gap),
                        width / 2 - 2 * dot_gap - i * (2 * dot_gap),
                        -thickness / 2,
                    ],
                ))
                await api.v1.solid.union(dict(id=ei, target=basic, tools=[copy]))
        await api.v1.solid.deleteSolid(dict(id=ei, ids=[tube]))

    await api.v1.common.setAppearance(dict(target=basic, color=[70, 0, 70]))
    return part_id


# ───── StepImport1 ─────

async def step_import1(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="StepImport1"))
    await api.v1.part.entityInjection(dict(id=part_id, name="StepImport1SolidAPI"))
    step_data = resourcehelper.read_text("Ventil.stp")
    imported_id = await api.v1.part.importFeature(dict(id=part_id, data=step_data, format="STP"))
    await api.v1.common.setAppearance(dict(target=imported_id, color=[203, 159, 22]))
    return part_id


# ───── StepImport2 ─────

async def step_import2(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="StepImport2"))
    await api.v1.part.entityInjection(dict(id=part_id, name="StepImport2SolidAPI"))
    step_data = resourcehelper.read_text("AWVLogoCube.stp")
    await api.v1.part.importFeature(dict(id=part_id, data=step_data, format="STP"))
    return part_id


# ───── Whiffleball ─────

async def whiffleball(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Whiffleball"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="WhiffleballSolidAPI"))

    l_outer = 90
    l_inner = 80
    d_hole = 55

    box1 = await api.v1.solid.box(dict(id=ei, width=l_outer, length=l_outer, height=l_outer))
    box2 = await api.v1.solid.box(dict(id=ei, width=l_inner, length=l_inner, height=l_inner))
    await api.v1.solid.subtraction(dict(id=ei, target=box1, tools=[box2]))

    cyl1 = await api.v1.solid.cylinder(dict(id=ei, diameter=d_hole, height=2 * l_outer))
    await api.v1.solid.subtraction(dict(id=ei, target=box1, tools=[cyl1]))

    cyl2 = await api.v1.solid.cylinder(dict(id=ei, height=2 * l_outer, diameter=d_hole, rotation=[0, math.pi / 2, 0]))
    await api.v1.solid.subtraction(dict(id=ei, target=box1, tools=[cyl2]))

    cyl3 = await api.v1.solid.cylinder(dict(id=ei, height=2 * l_outer, diameter=d_hole, rotation=[math.pi / 2, 0, 0]))
    await api.v1.solid.subtraction(dict(id=ei, target=box1, tools=[cyl3]))

    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[-45, -45, -15.556], normal=[-0.5, -0.5, -0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[45, -45, -15.556], normal=[0.5, -0.5, -0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[45, 45, -15.556], normal=[0.5, 0.5, -0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[-45, 45, -15.556], normal=[-0.5, 0.5, -0.707], keepBoth=False))

    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[-45, -45, 15.556], normal=[-0.5, -0.5, 0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[45, -45, 15.556], normal=[0.5, -0.5, 0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[45, 45, 15.556], normal=[0.5, 0.5, 0.707], keepBoth=False))
    await api.v1.solid.slice(dict(id=ei, target=box1, originPos=[-45, 45, 15.556], normal=[-0.5, 0.5, 0.707], keepBoth=False))

    await api.v1.common.setAppearance(dict(target=box1, color=[203, 67, 22]))
    return part_id


# ───── Profile ─────

async def profile(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Profile"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="ProfileSolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape, pld=[
        dict(xa=-350, ya=-500, c=2), dict(xr=700, c=2), dict(yr=50, c=2),
        dict(xr=-330, r=5), dict(yr=900, r=5), dict(xr=330, c=2),
        dict(yr=50, c=2), dict(xr=-700, c=2), dict(yr=-50, c=2),
        dict(xr=330, r=5), dict(yr=-900, r=5), dict(xr=-330, c=2),
    ], close=True))
    profile_body = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, 1150]))
    await api.v1.common.setAppearance(dict(target=profile_body, color=[203, 67, 188]))
    return part_id


# ───── Hackathon ─────

async def hackathon(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Hackathon"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="HackathonSolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape, pld=[
        dict(xa=0, ya=0), dict(xa=100, ya=0), dict(xa=100, ya=20), dict(xa=20, ya=20),
        dict(xa=20, ya=50), dict(xa=10, ya=50), dict(xa=10, ya=100), dict(xa=0, ya=100),
    ], close=True))
    basic = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, 100]))

    cyl1 = await api.v1.solid.cylinder(dict(
        id=ei, height=200, diameter=40, translation=[-50, 50, 50],
        rotation=[0, math.pi / 2, 0], rotateFirst=False,
    ))
    cyl2 = await api.v1.solid.cylinder(dict(
        id=ei, height=200, diameter=40, translation=[55, 50, 50],
        rotation=[math.pi / 2, 0, 0], rotateFirst=False,
    ))
    await api.v1.solid.subtraction(dict(id=ei, target=basic, tools=[cyl1]))
    await api.v1.solid.subtraction(dict(id=ei, target=basic, tools=[cyl2]))
    offset = await api.v1.solid.offset(dict(id=ei, target=basic, distance=1, extend=False))
    await api.v1.common.setAppearance(dict(target=offset, color=[150, 120, 255]))
    return part_id


# ───── Mechanical ─────

async def mechanical(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Mechanical"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="MechanicalSolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    points = [[0, 0, 0], [0, 26, 0], [0, 26, 5], [0, 0, 26]]
    for i in range(len(points)):
        s = points[i]
        e = points[(i + 1) % len(points)]
        await api.v1.curve.line(dict(id=shape, startPos=s, endPos=e))
    body = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[-53, 0, 0]))

    sub_box1 = await api.v1.solid.box(dict(id=ei, length=11, width=10, height=20, translation=[-5.5, 26, 0]))
    await api.v1.solid.subtraction(dict(id=ei, target=body, tools=[sub_box1], keepTools=True))
    await api.v1.solid.translation(dict(id=ei, target=sub_box1, translation=[-42, 0, 0]))
    await api.v1.solid.subtraction(dict(id=ei, target=body, tools=[sub_box1], keepTools=False))

    side_box = await api.v1.solid.box(dict(id=ei, length=7, width=16.7, height=26, translation=[-3.5, 8.35, 13]))
    await api.v1.solid.union(dict(id=ei, target=body, tools=[side_box], keepTools=True))
    await api.v1.solid.translation(dict(id=ei, target=side_box, translation=[-46, 0, 0]))
    await api.v1.solid.union(dict(id=ei, target=body, tools=[side_box], keepTools=False))

    sub_box2 = await api.v1.solid.box(dict(id=ei, length=17, width=16, height=26, translation=[-26.5, 13, 13]))
    await api.v1.solid.subtraction(dict(id=ei, target=body, tools=[sub_box2], keepTools=False))

    edges1 = await api.v1.part.getGeometryIds(dict(
        id=part_id, lines=[dict(pos=[-3.5, 16.7, 26]), dict(pos=[-49.5, 16.7, 26])],
    ))
    if edges1 and edges1.get("lines"):
        await api.v1.solid.fillet(dict(id=ei, radius=2, geomIds=edges1["lines"]))

    edges2 = await api.v1.part.getGeometryIds(dict(
        id=part_id, lines=[
            dict(pos=[-26.5, 5, 0]), dict(pos=[-26.5, 21, 0]),
            dict(pos=[-18, 13, 0]), dict(pos=[-35, 13, 0]),
        ],
    ))
    if edges2 and edges2.get("lines"):
        await api.v1.solid.fillet(dict(id=ei, radius=2, geomIds=edges2["lines"]))

    await api.v1.common.setAppearance(dict(target=body, color=[99, 120, 255]))
    return part_id


# ───── Mechanical2 ─────

async def mechanical2(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Mechanical2"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="Mechanical2SolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape, pld=[
        dict(xa=0, ya=0), dict(xa=80, ya=0),
        dict(ya=10, a=(135.0 / 180.0) * math.pi),
        dict(xr=-10, yr=0), dict(xr=0, yr=30), dict(xr=-40, yr=0),
        dict(xr=0, yr=-30), dict(xr=-10, yr=0),
    ], close=True))
    extrusion = await api.v1.solid.extrusion(dict(id=ei, direction=[0, 0, 30], curves=shape))

    cyl = await api.v1.solid.cylinder(dict(id=ei, height=40, diameter=40, translation=[40, 40, 20]))
    cyl2 = await api.v1.solid.cylinder(dict(id=ei, height=40, diameter=20, translation=[40, 40, 20]))

    union = await api.v1.solid.union(dict(id=ei, target=extrusion, tools=[cyl]))
    subtraction = await api.v1.solid.subtraction(dict(id=ei, target=union, tools=[cyl2]))
    await api.v1.solid.slice(dict(id=ei, target=subtraction, originPos=[40, 40, 20], normal=[0, 1, 0], keepBoth=False))
    return part_id


# ───── Polylines1 ─────

async def polylines1(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Polylines1"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="Polylines1SolidAPI"))

    shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape, pld=[
        dict(xa=0, ya=25), dict(xa=75, ya=25), dict(xa=75, ya=0, r=10),
        dict(xa=100, ya=0), dict(xa=100, ya=100, r=20), dict(xa=25, ya=75, r=15),
        dict(xa=25, ya=100), dict(xa=0, ya=100),
    ], close=True))
    body = await api.v1.solid.extrusion(dict(id=ei, curves=shape, direction=[0, 0, 25]))
    await api.v1.common.setAppearance(dict(target=body, color=[203, 67, 22]))
    return part_id


# ───── Polylines2 ─────

async def polylines2(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="Polylines2"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="Polylines2SolidAPI"))

    shape0 = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape0, pld=_generate_profile_path(700, 50, 900, 40), close=True))
    extrusion0 = await api.v1.solid.extrusion(dict(id=ei, curves=shape0, direction=[0, 0, 1150]))

    shape1 = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape1, pld=_generate_regular_polygon(7, 125), close=True))
    await api.v1.solid.extrusion(dict(id=ei, curves=shape1, direction=[0, 0, -100]))

    shape2 = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=shape2, pld=_generate_star_polygon(5, 200, 100, 4, 5), close=True))
    await api.v1.solid.extrusion(dict(id=ei, curves=shape2, direction=[0, 0, -500], translation=[500, 200, 500]))

    await api.v1.common.setAppearance(dict(target=extrusion0, color=[203, 67, 188]))
    return part_id


# ───── Smiley ─────

async def smiley(api: CCApiU, p: dict):
    happy = p.get("Happy?", 1) != 0
    part_id = await api.v1.part.create(dict(name="Smiley"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="SmileySolidAPI"))
    direction = [0, 0, 5]

    face_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=face_shape, pld=_circle_polyline_pld(40, 40, 40), close=True))
    smiley_body = await api.v1.solid.extrusion(dict(id=ei, curves=face_shape, direction=direction))

    eye1_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=eye1_shape, pld=_circle_polyline_pld(25, 20, 10), close=True))
    eye1_body = await api.v1.solid.extrusion(dict(id=ei, curves=eye1_shape, direction=direction))

    eye2_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=eye2_shape, pld=_circle_polyline_pld(55, 20, 10), close=True))
    eye2_body = await api.v1.solid.extrusion(dict(id=ei, curves=eye2_shape, direction=direction))

    mouth_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.bezierCurve(dict(id=mouth_shape, points=[[20, 40, 0], [40, 60, 0], [60, 40, 0]]))
    await api.v1.curve.bezierCurve(dict(id=mouth_shape, points=[[60, 40, 0], [70, 45, 0], [60, 60, 0]]))
    await api.v1.curve.bezierCurve(dict(id=mouth_shape, points=[[60, 60, 0], [40, 80, 0], [20, 60, 0]]))
    await api.v1.curve.bezierCurve(dict(id=mouth_shape, points=[[20, 60, 0], [5, 50, 0], [20, 40, 0]]))
    mouth_body = await api.v1.solid.extrusion(dict(id=ei, curves=mouth_shape, direction=direction))

    if not happy:
        await api.v1.solid.rotation(dict(id=ei, target=mouth_body, rotation=[math.pi, 0, 0]))
        await api.v1.solid.translation(dict(id=ei, target=mouth_body, translation=[0, 110, 5]))

    await api.v1.solid.subtraction(dict(id=ei, target=smiley_body, tools=[eye1_body]))
    await api.v1.solid.subtraction(dict(id=ei, target=smiley_body, tools=[eye2_body]))
    await api.v1.solid.subtraction(dict(id=ei, target=smiley_body, tools=[mouth_body]))
    await api.v1.solid.rotation(dict(id=ei, target=smiley_body, rotation=[math.pi, 0, 0]))

    await api.v1.common.setAppearance(dict(target=smiley_body, color=[252, 252, 45]))
    return part_id


# ───── WheelRim ─────

async def wheel_rim(api: CCApiU, p: dict):
    part_id = await api.v1.part.create(dict(name="WheelRim"))
    ei = await api.v1.part.entityInjection(dict(id=part_id, name="WheelRimSolidAPI"))

    rim_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=rim_shape, pld=[
        dict(xa=140, ya=200), dict(xa=-73.676, ya=200), dict(xa=-30, ya=80),
        dict(xa=0, ya=80), dict(xa=0, ya=0), dict(xa=-55, ya=0),
        dict(xa=-55, ya=30), dict(xa=-50, ya=30), dict(xa=-50, ya=80),
        dict(xa=-93.676, ya=200), dict(xa=-140, ya=200), dict(xa=-140, ya=220),
        dict(xa=-135, ya=220), dict(xa=-135, ya=205), dict(xa=135, ya=205),
        dict(xa=135, ya=220), dict(xa=140, ya=220),
    ], close=True))
    await api.v1.curve.rotateShape(dict(id=rim_shape, rotation=[0, math.pi / 2, 0]))

    cutout_shape = await api.v1.curve.shape(dict(id=ei))
    await api.v1.curve.advancedPolyline(dict(id=cutout_shape, pld=[
        dict(xa=-85, ya=-10), dict(xa=-185, ya=-36.795),
        dict(xa=-185, ya=36.795), dict(xa=-85, ya=10),
    ], close=True))
    await api.v1.curve.translateShape(dict(id=cutout_shape, translation=[0, 0, -137.5]))

    basic_body = await api.v1.solid.revolve(dict(
        id=ei, curves=rim_shape, originPos=[0, 0, 0], direction=[0, 0, 100], angle=2 * math.pi,
    ))
    sub_solid = await api.v1.solid.extrusion(dict(id=ei, curves=cutout_shape, direction=[0, 0, 500]))

    nof = 6
    angle = 2 * math.pi / nof
    for i in range(nof):
        copy = await api.v1.solid.copy(dict(id=ei, target=sub_solid, rotation=[0, 0, i * angle]))
        await api.v1.solid.subtraction(dict(id=ei, target=basic_body, tools=[copy]))
    await api.v1.solid.deleteSolid(dict(id=ei, ids=[sub_solid]))

    await api.v1.common.setAppearance(dict(target=basic_body, color=[179, 159, 107]))
    return part_id
