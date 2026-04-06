import math
from datetime import datetime

from classcadconnector import CCApiU

from . import resourcehelper

MIN_GAP_FRAME_SEGMENT = 20
GAP_IN_FRAME = 20


# ───── CreateAsm ─────

async def create_asm(api: CCApiU, p: dict):
    root_asm_id = await api.v1.assembly.create(dict(name="CreateAsm"))
    await _build_create_asm(api, root_asm_id)
    return root_asm_id


async def _build_create_asm(api: CCApiU, root_asm_id: int):
    pt1 = [50, 0, 0]
    pt2 = [100, 0, 0]
    pt3 = [0, 0, 0]
    x_dir = [1, 0, 0]
    y_dir = [0, 1, 0]

    # === Nut part ===
    nut = await api.v1.assembly.partTemplate(dict(name="Nut"))
    wcs_box_nut = await api.v1.part.workCSys(dict(id=nut, type="CUSTOM", offset=[0, 0, 0], rotation=[0, 0, 0], name="wcsBoxNut"))
    wcs_cyl_nut = await api.v1.part.workCSys(dict(id=nut, type="CUSTOM", offset=[15, 15, 0], rotation=[0, 0, 0], name="wcsCylNut"))
    mate1_nut = await api.v1.part.workCSys(dict(id=nut, type="CUSTOM", offset=[15, 15, 0], rotation=[0, 0, 0], name="mate1Nut"))
    box_nut = await api.v1.part.box(dict(id=nut, references=[wcs_box_nut], length=30, width=30, height=10))
    cyl_nut = await api.v1.part.cylinder(dict(id=nut, references=[wcs_cyl_nut], diameter=20, height=40))
    await api.v1.part.boolean(dict(id=nut, type="SUBTRACTION", target=box_nut, tools=[cyl_nut]))

    # === Bolt part ===
    bolt = await api.v1.assembly.partTemplate(dict(name="Bolt"))
    wcs_shaft_bolt = await api.v1.part.workCSys(dict(id=bolt, type="CUSTOM", offset=[0, 0, 0], rotation=[0, 0, 0], name="wcsShaftBolt"))
    wcs_head_bolt = await api.v1.part.workCSys(dict(id=bolt, type="CUSTOM", offset=[0, 0, -10], rotation=[0, 0, 0], name="wcsHeadBolt"))
    mate1_bolt = await api.v1.part.workCSys(dict(id=bolt, type="CUSTOM", offset=[0, 0, 0], rotation=[0, 0, 0], name="mate1Bolt"))
    shaft = await api.v1.part.cylinder(dict(id=bolt, references=[wcs_shaft_bolt], diameter=20, height=60))
    head = await api.v1.part.cylinder(dict(id=bolt, references=[wcs_head_bolt], diameter=30, height=10))
    await api.v1.part.boolean(dict(id=bolt, type="UNION", target=shaft, tools=[head]))

    # === LBracket part ===
    l_bracket = await api.v1.assembly.partTemplate(dict(name="L_Bracket"))
    wcs_base_bracket = await api.v1.part.workCSys(dict(id=l_bracket, type="CUSTOM", offset=[0, 0, 0], rotation=[0, 0, 0], name="wcsBaseBracket"))
    wcs_sub_bracket = await api.v1.part.workCSys(dict(id=l_bracket, type="CUSTOM", offset=[20, 0, 20], rotation=[0, 0, 0], name="wcsSubBracket"))
    base_bracket = await api.v1.part.box(dict(id=l_bracket, references=[wcs_base_bracket], length=100, width=200, height=100))
    sub_bracket = await api.v1.part.box(dict(id=l_bracket, references=[wcs_sub_bracket], length=100, width=200, height=100))
    mate1_l_bracket = await api.v1.part.workCSys(dict(id=l_bracket, type="CUSTOM", offset=[75, 50, 0], rotation=[0, 0, 0], name="mate1LBracket"))
    mate2_l_bracket = await api.v1.part.workCSys(dict(id=l_bracket, type="CUSTOM", offset=[45, 100, 0], rotation=[0, 0, 0], name="mate2LBracket"))
    mate3_l_bracket = await api.v1.part.workCSys(dict(id=l_bracket, type="CUSTOM", offset=[75, 150, 0], rotation=[0, 0, 0], name="mate3LBracket"))
    sub1_bracket = await api.v1.part.cylinder(dict(id=l_bracket, references=[mate1_l_bracket], diameter=20, height=40))
    sub2_bracket = await api.v1.part.cylinder(dict(id=l_bracket, references=[mate2_l_bracket], diameter=20, height=40))
    sub3_bracket = await api.v1.part.cylinder(dict(id=l_bracket, references=[mate3_l_bracket], diameter=20, height=40))
    await api.v1.part.boolean(dict(
        id=l_bracket, type="SUBTRACTION", target=base_bracket,
        tools=[sub_bracket, sub1_bracket, sub2_bracket, sub3_bracket],
    ))

    # === Nut-bolt sub-assembly ===
    nut_bolt_asm = await api.v1.assembly.assemblyTemplate(dict(name="Nut_Bolt_Assembly"))
    nut_ref, bolt_ref = await api.v1.assembly.instance([
        dict(productId=nut, ownerId=nut_bolt_asm),
        dict(productId=bolt, ownerId=nut_bolt_asm),
    ])

    await api.v1.assembly.fastenedOrigin(dict(
        id=nut_bolt_asm,
        mate1=dict(path=[bolt_ref], csys=mate1_bolt, flip="Z", reorient="0"),
        name="FOC1",
    ))
    await api.v1.assembly.fastened(dict(
        id=nut_bolt_asm,
        mate1=dict(path=[nut_ref], csys=mate1_nut),
        mate2=dict(path=[bolt_ref], csys=mate1_bolt),
        zOffset=-20, name="FC1",
    ))

    # === L-Bracket final assembly ===
    nut_bolt_ref0, nut_bolt_ref1, nut_bolt_ref2, l_bracket_ref = await api.v1.assembly.instance([
        dict(productId=nut_bolt_asm, ownerId=root_asm_id),
        dict(productId=nut_bolt_asm, ownerId=root_asm_id, transformation=[pt1, x_dir, y_dir]),
        dict(productId=nut_bolt_asm, ownerId=root_asm_id, transformation=[pt2, x_dir, y_dir]),
        dict(productId=l_bracket, ownerId=root_asm_id, transformation=[pt3, x_dir, y_dir]),
    ])

    await api.v1.assembly.fastenedOrigin(dict(
        id=root_asm_id, mate1=dict(path=[l_bracket_ref], csys=mate1_l_bracket),
        zOffset=20, name="FOC2",
    ))

    bolt_instance0 = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_ref0, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[l_bracket_ref], csys=mate1_l_bracket),
        mate2=dict(path=[bolt_instance0], csys=wcs_shaft_bolt, flip="-Z"),
        zOffset=20, name="FC2",
    ))

    bolt_instance1 = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_ref1, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[l_bracket_ref], csys=mate2_l_bracket),
        mate2=dict(path=[bolt_instance1], csys=wcs_shaft_bolt, flip="-Z"),
        zOffset=20, name="FC3",
    ))

    bolt_instance2 = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_ref2, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[l_bracket_ref], csys=mate3_l_bracket),
        mate2=dict(path=[bolt_instance2], csys=wcs_shaft_bolt, flip="-Z"),
        zOffset=20, name="FC4",
    ))


# ───── NutBoltAssembly ─────

async def nut_bolt_assembly(api: CCApiU, p: dict):
    shaft_diameter = 10
    shaft_length = 37

    root_asm_id = await api.v1.assembly.create(dict(name="NutBoltAssembly"))

    bolt_data = resourcehelper.read_bytes("As1", "Bolt.ofb")
    nut_data = resourcehelper.read_bytes("As1", "Nut.ofb")

    bolt_load = await api.v1.assembly.loadProduct(dict(data=bolt_data, format="OFB"))
    bolt = bolt_load.get("id")

    await api.v1.part.updateExpression(dict(id=bolt, toUpdate=[
        dict(name="Shaft_Length", value=shaft_length),
        dict(name="Shaft_Diameter", value=shaft_diameter),
    ]))
    bolt_ref_id = await api.v1.assembly.instance(dict(productId=bolt, ownerId=root_asm_id))
    wcs_id_bolt_nut = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Nut"))
    wcs_id_origin = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Origin"))

    nut_load = await api.v1.assembly.loadProduct(dict(data=nut_data, format="OFB"))
    nut = nut_load.get("id")

    await api.v1.part.updateExpression(dict(id=nut, toUpdate=[dict(name="Hole_Diameter", value=shaft_diameter)]))
    nut_ref_id = await api.v1.assembly.instance(dict(productId=nut, ownerId=root_asm_id))
    wcs_id_nut = await api.v1.part.getWorkGeometry(dict(id=nut_ref_id, name="WCS_Hole_Top"))

    await api.v1.assembly.fastenedOrigin(dict(
        id=root_asm_id, mate1=dict(path=[bolt_ref_id], csys=wcs_id_origin), name="FOC0",
    ))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[nut_ref_id], csys=wcs_id_nut),
        mate2=dict(path=[bolt_ref_id], csys=wcs_id_bolt_nut),
        name="FC1",
    ))
    return root_asm_id


# ───── LBracketAssembly ─────

async def lbracket_assembly(api: CCApiU, p: dict):
    shaft_diameter = 10
    shaft_length = 37
    rod_diameter = 10

    root_asm_id = await api.v1.assembly.create(dict(name="LBracketAssembly"))

    bolt_data = resourcehelper.read_bytes("As1", "Bolt.ofb")
    nut_data = resourcehelper.read_bytes("As1", "Nut.ofb")
    lbracket_data = resourcehelper.read_bytes("As1", "LBracket.ofb")

    nut_bolt_asm = await api.v1.assembly.assemblyTemplate(dict(name="NutBolt_Asm"))

    bolt_load = await api.v1.assembly.loadProduct(dict(data=bolt_data, format="OFB"))
    bolt = bolt_load.get("id")

    await api.v1.part.updateExpression(dict(id=bolt, toUpdate=[
        dict(name="Shaft_Length", value=shaft_length),
        dict(name="Shaft_Diameter", value=shaft_diameter),
    ]))
    bolt_ref_id = await api.v1.assembly.instance(dict(productId=bolt, ownerId=nut_bolt_asm))
    wcs_id_bolt_nut = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Nut"))
    wcs_id_bolt_head_shaft = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Head-Shaft"))
    wcs_id_bolt_origin = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Origin"))

    nut_load = await api.v1.assembly.loadProduct(dict(data=nut_data, format="OFB"))
    nut = nut_load.get("id")

    await api.v1.part.updateExpression(dict(id=nut, toUpdate=[dict(name="Hole_Diameter", value=shaft_diameter)]))
    nut_ref_id = await api.v1.assembly.instance(dict(productId=nut, ownerId=nut_bolt_asm))
    wcs_id_nut = await api.v1.part.getWorkGeometry(dict(id=nut_ref_id, name="WCS_Hole_Top"))

    await api.v1.assembly.fastenedOrigin(dict(
        id=nut_bolt_asm, mate1=dict(path=[bolt_ref_id], csys=wcs_id_bolt_origin), name="FOC0",
    ))
    await api.v1.assembly.fastened(dict(
        id=nut_bolt_asm,
        mate1=dict(path=[bolt_ref_id], csys=wcs_id_bolt_nut),
        mate2=dict(path=[nut_ref_id], csys=wcs_id_nut),
        name="FC1",
    ))

    lbracket_load = await api.v1.assembly.loadProduct(dict(data=lbracket_data, format="OFB"))
    lbracket = lbracket_load.get("id")

    await api.v1.part.updateExpression(dict(id=lbracket, toUpdate=[
        dict(name="Rod_Hole_Diameter", value=rod_diameter),
        dict(name="Hole_Diameter", value=shaft_diameter),
    ]))
    lbracket_ref1 = await api.v1.assembly.instance(dict(productId=lbracket, ownerId=root_asm_id))

    wcs_id_lbracket_origin = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Origin"))
    wcs_id_lbracket_1 = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole1-Top"))
    wcs_id_lbracket_2 = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole2-Top"))
    wcs_id_lbracket_3 = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole3-Top"))

    await api.v1.assembly.fastenedOrigin(dict(
        id=root_asm_id, mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_origin), name="FOC",
    ))

    nut_bolt_asm_ref1, nut_bolt_asm_ref2, nut_bolt_asm_ref3 = await api.v1.assembly.instance([
        dict(productId=nut_bolt_asm, ownerId=root_asm_id),
        dict(productId=nut_bolt_asm, ownerId=root_asm_id),
        dict(productId=nut_bolt_asm, ownerId=root_asm_id),
    ])

    bolt_instance = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_asm_ref1, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_1),
        mate2=dict(path=[bolt_instance], csys=wcs_id_bolt_head_shaft),
        name="FC2",
    ))

    bolt_instance = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_asm_ref2, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_2),
        mate2=dict(path=[bolt_instance], csys=wcs_id_bolt_head_shaft),
        name="FC3",
    ))

    bolt_instance = await api.v1.assembly.getInstance(dict(ownerId=nut_bolt_asm_ref3, name="Bolt"))
    await api.v1.assembly.fastened(dict(
        id=root_asm_id,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_3),
        mate2=dict(path=[bolt_instance], csys=wcs_id_bolt_head_shaft),
        name="FC4",
    ))
    return root_asm_id


# ───── As1Assembly ─────

async def as1_assembly(api: CCApiU, p: dict):
    shaft_diameter = 10
    shaft_length = 42
    rod_diameter = shaft_diameter

    as1_asm = await api.v1.assembly.create(dict(name="Root_Assembly"))

    l_bracket_asm = await api.v1.assembly.assemblyTemplate(dict(name="LBracket_Asm"))
    nut_bolt_asm = await api.v1.assembly.assemblyTemplate(dict(name="NutBolt_Asm"))
    rod_asm = await api.v1.assembly.assemblyTemplate(dict(name="Rod_Asm"))

    # Load Bolt
    bolt_data = resourcehelper.read_bytes("As1", "Bolt.ofb")
    bolt_load = await api.v1.assembly.loadProduct(dict(data=bolt_data, format="OFB"))
    bolt = bolt_load.get("id")

    await api.v1.part.updateExpression(dict(id=bolt, toUpdate=[
        dict(name="Shaft_Length", value=shaft_length),
        dict(name="Shaft_Diameter", value=shaft_diameter),
    ]))

    bolt_ref_id = await api.v1.assembly.instance(dict(productId=bolt, ownerId=nut_bolt_asm))
    wcs_id_bolt_nut = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Nut"))
    wcs_id_bolt_head_shaft = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Head-Shaft"))
    wcs_id_bolt_origin = await api.v1.part.getWorkGeometry(dict(id=bolt_ref_id, name="WCS_Origin"))

    # Load Nut
    nut_data = resourcehelper.read_bytes("As1", "Nut.ofb")
    nut_load = await api.v1.assembly.loadProduct(dict(data=nut_data, format="OFB"))
    nut = nut_load.get("id")

    await api.v1.part.updateExpression(dict(id=nut, toUpdate=[dict(name="Hole_Diameter", value=shaft_diameter)]))

    nut_ref_id = await api.v1.assembly.instance(dict(productId=nut, ownerId=nut_bolt_asm))
    wcs_id_nut = await api.v1.part.getWorkGeometry(dict(id=nut_ref_id, name="WCS_Hole_Top"))

    # Set bolt to origin of nut-bolt assembly
    await api.v1.assembly.fastenedOrigin(dict(
        id=nut_bolt_asm, mate1=dict(path=[bolt_ref_id], csys=wcs_id_bolt_origin), name="FOC0",
    ))
    # Set nut on bolt
    await api.v1.assembly.fastened(dict(
        id=nut_bolt_asm,
        mate1=dict(path=[bolt_ref_id], csys=wcs_id_bolt_nut),
        mate2=dict(path=[nut_ref_id], csys=wcs_id_nut),
        name="FC1",
    ))

    # Load LBracket
    lbracket_data = resourcehelper.read_bytes("As1", "LBracket.ofb")
    lbracket_load = await api.v1.assembly.loadProduct(dict(data=lbracket_data, format="OFB"))
    l_bracket = lbracket_load.get("id")

    await api.v1.part.updateExpression(dict(id=l_bracket, toUpdate=[
        dict(name="Rod_Hole_Diameter", value=rod_diameter),
        dict(name="Hole_Diameter", value=shaft_diameter),
    ]))

    lbracket_ref1 = await api.v1.assembly.instance(dict(productId=l_bracket, ownerId=l_bracket_asm))
    wcs_id_lbracket_1 = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole1-Top"))
    wcs_id_lbracket_2_top = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole2-Top"))
    wcs_id_lbracket_2_bottom = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole2-Bottom"))
    wcs_id_lbracket_3 = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Hole3-Top"))
    wcs_id_lbracket_rod = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Rod"))
    wcs_id_lbracket_origin = await api.v1.part.getWorkGeometry(dict(id=lbracket_ref1, name="WCS_Origin"))

    # Add nut-bolt assembly three times to lBracket-assembly
    nut_bolt_asm_refs = await api.v1.assembly.instance([
        dict(productId=nut_bolt_asm, ownerId=l_bracket_asm),
        dict(productId=nut_bolt_asm, ownerId=l_bracket_asm),
        dict(productId=nut_bolt_asm, ownerId=l_bracket_asm),
    ])

    # Set lBracket to origin
    await api.v1.assembly.fastenedOrigin(dict(
        id=l_bracket_asm, mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_origin), name="FOC1",
    ))

    # Set 1st nut-bolt on lBracket
    await api.v1.assembly.fastened(dict(
        id=l_bracket_asm,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_1),
        mate2=dict(path=[bolt_ref_id, nut_bolt_asm_refs[0]], csys=wcs_id_bolt_head_shaft),
        name="FC2",
    ))
    # Set 2nd nut-bolt on lBracket
    await api.v1.assembly.fastened(dict(
        id=l_bracket_asm,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_2_top),
        mate2=dict(path=[bolt_ref_id, nut_bolt_asm_refs[1]], csys=wcs_id_bolt_head_shaft),
        name="FC3",
    ))
    # Set 3rd nut-bolt on lBracket
    await api.v1.assembly.fastened(dict(
        id=l_bracket_asm,
        mate1=dict(path=[lbracket_ref1], csys=wcs_id_lbracket_3),
        mate2=dict(path=[bolt_ref_id, nut_bolt_asm_refs[2]], csys=wcs_id_bolt_head_shaft),
        name="FC4",
    ))

    # Load Plate
    plate_data = resourcehelper.read_bytes("As1", "Plate.ofb")
    plate_load = await api.v1.assembly.loadProduct(dict(data=plate_data, format="OFB"))
    plate = plate_load.get("id")

    await api.v1.part.updateExpression(dict(id=plate, toUpdate=[dict(name="Hole_Diameter", value=shaft_diameter)]))

    plate_ref = await api.v1.assembly.instance(dict(productId=plate, ownerId=as1_asm))
    wcs_id_plate_base = await api.v1.part.getWorkGeometry(dict(id=plate_ref, name="WCS_Origin"))
    wcs_id_plate_2 = await api.v1.part.getWorkGeometry(dict(id=plate_ref, name="WCS_Hole2-Top"))
    wcs_id_plate_5 = await api.v1.part.getWorkGeometry(dict(id=plate_ref, name="WCS_Hole5-Top"))

    # Set plate to origin of as1-assembly
    await api.v1.assembly.fastenedOrigin(dict(
        id=as1_asm, mate1=dict(path=[plate_ref], csys=wcs_id_plate_base), name="FOC2",
    ))

    # Add lBracket-assembly twice to as1-assembly
    l_bracket_asm_refs = await api.v1.assembly.instance([
        dict(productId=l_bracket_asm, ownerId=as1_asm),
        dict(productId=l_bracket_asm, ownerId=as1_asm),
    ])

    # Set 1st lBracket-assembly on plate
    await api.v1.assembly.fastened(dict(
        id=as1_asm,
        mate1=dict(path=[plate_ref], csys=wcs_id_plate_2),
        mate2=dict(path=[lbracket_ref1, l_bracket_asm_refs[0]], csys=wcs_id_lbracket_2_bottom),
        name="FC5",
    ))
    # Set 2nd lBracket-assembly on plate
    await api.v1.assembly.fastened(dict(
        id=as1_asm,
        mate1=dict(path=[plate_ref], csys=wcs_id_plate_5),
        mate2=dict(path=[lbracket_ref1, l_bracket_asm_refs[1]], csys=wcs_id_lbracket_2_bottom),
        name="FC6",
    ))

    # Load Rod
    rod_data = resourcehelper.read_bytes("As1", "Rod.ofb")
    rod_load = await api.v1.assembly.loadProduct(dict(data=rod_data, format="OFB"))
    rod = rod_load.get("id")

    await api.v1.part.updateExpression(dict(id=rod, toUpdate=[dict(name="Rod_Diameter", value=rod_diameter)]))

    rod_ref_id = await api.v1.assembly.instance(dict(productId=rod, ownerId=rod_asm))
    wcs_id_rod_left = await api.v1.part.getWorkGeometry(dict(id=rod_ref_id, name="WCS_Nut_Left"))
    wcs_id_rod_right = await api.v1.part.getWorkGeometry(dict(id=rod_ref_id, name="WCS_Nut_Right"))
    wcs_id_rod_origin = await api.v1.part.getWorkGeometry(dict(id=rod_ref_id, name="WCS_Origin"))

    # Add two nuts to rod-assembly
    nut_ref_ids = await api.v1.assembly.instance([
        dict(productId=nut, ownerId=rod_asm),
        dict(productId=nut, ownerId=rod_asm),
    ])

    # Set rod to origin of rod-assembly
    await api.v1.assembly.fastenedOrigin(dict(
        id=rod_asm, mate1=dict(path=[rod_ref_id], csys=wcs_id_rod_origin), name="FOC3",
    ))
    # Set 1st nut on rod
    await api.v1.assembly.fastened(dict(
        id=rod_asm,
        mate1=dict(path=[rod_ref_id], csys=wcs_id_rod_left),
        mate2=dict(path=[nut_ref_ids[0]], csys=wcs_id_nut),
        name="FC7",
    ))
    # Set 2nd nut on rod
    await api.v1.assembly.fastened(dict(
        id=rod_asm,
        mate1=dict(path=[rod_ref_id], csys=wcs_id_rod_right),
        mate2=dict(path=[nut_ref_ids[1]], csys=wcs_id_nut),
        name="FC8",
    ))

    # Add rod-assembly to as1-assembly
    rod_asm_ref = await api.v1.assembly.instance(dict(productId=rod_asm, ownerId=as1_asm))

    # Set rod-assembly on lBracket of first lBracket-assembly
    await api.v1.assembly.fastened(dict(
        id=as1_asm,
        mate1=dict(path=[lbracket_ref1, l_bracket_asm_refs[0]], csys=wcs_id_lbracket_rod),
        mate2=dict(path=[rod_ref_id, rod_asm_ref], csys=wcs_id_rod_left),
        name="FC9",
    ))

    # Set appearances
    bolt_shaft = await api.v1.part.getFeature(dict(id=bolt, name="EXTR_Shaft"))
    bolt_head = await api.v1.part.getFeature(dict(id=bolt, name="EXTR_Head"))
    nut_feat = await api.v1.part.getFeature(dict(id=nut, name="Subtraction"))
    lbracket_feat = await api.v1.part.getFeature(dict(id=l_bracket, name="Subtraction2"))
    plate_feat = await api.v1.part.getFeature(dict(id=plate, name="Subtraction"))
    rod_feat = await api.v1.part.getFeature(dict(id=rod, name="Cylinder"))

    await api.v1.common.setAppearance([
        dict(target=bolt_shaft, color=[203, 67, 22]),
        dict(target=bolt_head, color=[203, 67, 22]),
        dict(target=nut_feat, color=[23, 67, 180]),
        dict(target=lbracket_feat, color=[220, 150, 20]),
        dict(target=plate_feat, color=[120, 80, 79], transparency=0.3),
        dict(target=rod_feat, color=[178, 0, 13]),
    ])
    return as1_asm


# ───── FlangeAsm ─────

async def flange_asm(api: CCApiU, p: dict):
    root_asm_id = await api.v1.assembly.create(dict(name="FlangeAsm"))

    flange_file = resourcehelper.resolve_path("Flange", "FlangePrt.ofb")
    bolt_file = resourcehelper.resolve_path("Flange", "Bolt_M22.ofb")
    nut_file = resourcehelper.resolve_path("Flange", "Nut_M22.ofb")

    flange_product = await api.v1.assembly.loadProduct(dict(file=flange_file))
    bolt_product = await api.v1.assembly.loadProduct(dict(file=bolt_file))
    nut_product = await api.v1.assembly.loadProduct(dict(file=nut_file))

    flange = flange_product.get("id")
    bolt_prod = bolt_product.get("id")
    nut_prod = nut_product.get("id")

    wcs_center = await api.v1.part.getWorkGeometry(dict(id=flange, name="WCSCenter"))
    wcs_hole1_top = await api.v1.part.getWorkGeometry(dict(id=flange, name="WCSBoltHoleTop"))
    wcs_bolt_head = await api.v1.part.getWorkGeometry(dict(id=bolt_prod, name="WCSHead"))
    wcs_nut = await api.v1.part.getWorkGeometry(dict(id=nut_prod, name="WCSNut"))

    flange1_instance, flange2_instance, bolt_instance, nut_instance = await api.v1.assembly.instance([
        dict(productId=flange, ownerId=root_asm_id),
        dict(productId=flange, ownerId=root_asm_id),
        dict(productId=bolt_prod, ownerId=root_asm_id),
        dict(productId=nut_prod, ownerId=root_asm_id),
    ])

    await api.v1.assembly.fastenedOrigin(dict(
        id=root_asm_id, mate1=dict(path=[flange1_instance], csys=wcs_center), name="FOCFlange1",
    ))
    await api.v1.assembly.fastened([
        dict(
            id=root_asm_id,
            mate1=dict(path=[flange1_instance], csys=wcs_center),
            mate2=dict(path=[flange2_instance], csys=wcs_center, flip="-Z", reorient="180"),
            name="FCFlange1Flange2",
        ),
        dict(
            id=root_asm_id,
            mate1=dict(path=[flange1_instance], csys=wcs_hole1_top),
            mate2=dict(path=[bolt_instance], csys=wcs_bolt_head),
            name="FCFlange1Bolt",
        ),
        dict(
            id=root_asm_id,
            mate1=dict(path=[flange2_instance], csys=wcs_hole1_top),
            mate2=dict(path=[nut_instance], csys=wcs_nut, flip="-Z"),
            name="FCFlange2Nut",
        ),
    ])
    return root_asm_id


# ───── RollerAsm ─────

async def roller_asm(api: CCApiU, p: dict):
    walze_length = p.get("Walze Length", 800)
    arrow_direction = int(p.get("Arrow Direction", 0))
    walze_direction = int(p.get("Walze Direction", 0))
    segment_size = p.get("Segment Size", 50)
    nof_segments = int(p.get("Num Segments", 5))
    plug_position = int(p.get("Plug Position", 0))

    data = resourcehelper.read_bytes("RollerTemplate.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    segment_prt = await api.v1.assembly.getPartTemplate(dict(name="Segment"))
    walze_prt = await api.v1.assembly.getPartTemplate(dict(name="Walze"))

    await api.v1.part.updateExpression(dict(id=walze_prt, toUpdate=[dict(name="L", value=walze_length)]))
    await api.v1.part.updateExpression(dict(id=segment_prt, toUpdate=[dict(name="W", value=segment_size)]))

    # Fastened origins
    constr_walze_origin = await api.v1.assembly.getFastenedOrigin(dict(id=loaded_id, name="Fastened_Origin_Walze"))
    constr_end1 = await api.v1.assembly.getFastenedOrigin(dict(id=loaded_id, name="Fastened_Origin_End1"))
    constr_end2 = await api.v1.assembly.getFastenedOrigin(dict(id=loaded_id, name="Fastened_Origin_End2"))

    if constr_walze_origin:
        await api.v1.assembly.updateFastenedOrigin(dict(
            id=constr_walze_origin.get("id"),
            mate1=dict(flip="-X" if walze_direction == 0 else "X"),
        ))

    if constr_end1 and constr_end2:
        await api.v1.assembly.updateFastenedOrigin([
            dict(id=constr_end1.get("id"), zOffset=-walze_length / 2),
            dict(id=constr_end2.get("id"), zOffset=walze_length / 2),
        ])

    # Arrow direction reorientation
    reorient_mapping = {
        0: ("0", "0", "0", "0", "0", "0", "0", "180"),
        1: ("90", "270", "270", "90", "270", "90", "270", "90"),
        2: ("180", "180", "180", "180", "180", "180", "180", "0"),
        3: ("270", "90", "90", "270", "90", "270", "90", "270"),
    }

    arrow0_out = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Arrow0_Out"))
    arrow1_out = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Arrow1_Out"))
    arrow0_in = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Arrow0_In"))
    arrow1_in = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Arrow1_In"))
    logo0 = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Logo0"))
    logo1 = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_Logo1"))

    if (arrow_direction in reorient_mapping
            and arrow0_out and arrow1_out and arrow0_in and arrow1_in
            and logo0 and logo1):
        (reorient_arrow0_in, reorient_arrow0_out,
         reorient_arrow1_in, reorient_arrow1_out,
         reorient_logo0, reorient_logo1,
         reorient_end1, reorient_end2) = reorient_mapping[arrow_direction]

        await api.v1.assembly.updateFastened([
            dict(id=arrow0_out.get("id"), mate2=dict(reorient=reorient_arrow0_out)),
            dict(id=arrow1_out.get("id"), mate2=dict(reorient=reorient_arrow1_out)),
            dict(id=arrow0_in.get("id"), mate2=dict(reorient=reorient_arrow0_in)),
            dict(id=arrow1_in.get("id"), mate2=dict(reorient=reorient_arrow1_in)),
        ])

        await api.v1.assembly.updateFastened([
            dict(id=logo0.get("id"), mate2=dict(reorient=reorient_logo0)),
            dict(id=logo1.get("id"), mate2=dict(reorient=reorient_logo1)),
        ])

        if constr_end1 and constr_end2:
            await api.v1.assembly.updateFastenedOrigin([
                dict(id=constr_end1.get("id"), mate1=dict(reorient=reorient_end1)),
                dict(id=constr_end2.get("id"), mate1=dict(reorient=reorient_end2)),
            ])

    # Plug position
    constr_electric_plug = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_ElectricPlug"))
    constr_pneumatic_plug = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened_PneumaticPlug"))
    frame0 = await api.v1.assembly.getInstance(dict(ownerId=loaded_id, name="Frame0"))
    frame1 = await api.v1.assembly.getInstance(dict(ownerId=loaded_id, name="Frame1"))

    if constr_electric_plug and constr_pneumatic_plug and frame0 and frame1:
        wcs_e_plug_frame0_left = await api.v1.part.getWorkGeometry(dict(id=frame0, name="Plug_csys"))
        wcs_e_plug_frame0_right = await api.v1.part.getWorkGeometry(dict(id=frame0, name="Plug2_csys"))
        wcs_p_plug_frame0_left = await api.v1.part.getWorkGeometry(dict(id=frame0, name="Screw_csys"))
        wcs_p_plug_frame0_right = await api.v1.part.getWorkGeometry(dict(id=frame0, name="Screw2_csys"))

        wcs_e_plug_frame1_left = await api.v1.part.getWorkGeometry(dict(id=frame1, name="Plug_csys"))
        wcs_e_plug_frame1_right = await api.v1.part.getWorkGeometry(dict(id=frame1, name="Plug2_csys"))
        wcs_p_plug_frame1_left = await api.v1.part.getWorkGeometry(dict(id=frame1, name="Screw_csys"))
        wcs_p_plug_frame1_right = await api.v1.part.getWorkGeometry(dict(id=frame1, name="Screw2_csys"))

        if plug_position == 1:
            e_plug, e_csys = frame0, wcs_e_plug_frame0_left
            p_plug, p_csys = frame0, wcs_p_plug_frame0_left
        elif plug_position == 2:
            e_plug, e_csys = frame1, wcs_e_plug_frame1_right
            p_plug, p_csys = frame1, wcs_p_plug_frame1_right
        elif plug_position == 3:
            e_plug, e_csys = frame1, wcs_e_plug_frame1_left
            p_plug, p_csys = frame1, wcs_p_plug_frame1_left
        else:
            e_plug, e_csys = frame0, wcs_e_plug_frame0_right
            p_plug, p_csys = frame0, wcs_p_plug_frame0_right

        await api.v1.assembly.updateFastened([
            dict(id=constr_pneumatic_plug.get("id"), mate1=dict(path=[p_plug], csys=p_csys)),
            dict(id=constr_electric_plug.get("id"), mate1=dict(path=[e_plug], csys=e_csys)),
        ])

    # Delete existing segments and create new ones
    existing_segments = []
    for idx in range(80):
        try:
            segment_instance = await api.v1.assembly.getInstance(dict(ownerId=loaded_id, name=f"Segment{idx}"))
        except Exception:
            segment_instance = None
        if segment_instance:
            existing_segments.append(segment_instance)
        elif idx > 10:
            break

    if existing_segments:
        await api.v1.assembly.deleteInstance(dict(ids=existing_segments))

    z = (walze_length / 2 - MIN_GAP_FRAME_SEGMENT - GAP_IN_FRAME - segment_size / 2) if nof_segments > 1 else 0
    distance_bt_segments = (
        (walze_length - 2 * (MIN_GAP_FRAME_SEGMENT + GAP_IN_FRAME) - segment_size) / (nof_segments - 1)
        if nof_segments > 1 else 0
    )
    z_dir = [0, 0, -1] if walze_direction == 0 else [0, 0, 1]
    segment_dir = [0, 1, 0]

    to_create = []
    for idx in range(nof_segments):
        pos_z = -z + idx * distance_bt_segments
        to_create.append(dict(
            productId=segment_prt, ownerId=loaded_id,
            transformation=[[0, 0, pos_z], z_dir, segment_dir],
            name=f"Segment{idx}",
        ))
    if to_create:
        await api.v1.assembly.instance(to_create)

    return loaded_id


# ───── Wireway ─────

async def wireway(api: CCApiU, p: dict):
    length = p.get("Length", 200)
    height = p.get("Height", 30)
    width = p.get("Width", 30)
    position = p.get("Position", 0)

    data = resourcehelper.read_bytes("WirewayTemplate.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    deckel_prt = await api.v1.assembly.getPartTemplate(dict(name="Deckel"))
    kanal_prt = await api.v1.assembly.getPartTemplate(dict(name="Kanal"))
    constr_deckel = await api.v1.assembly.getFastened(dict(id=loaded_id, name="Fastened"))

    await api.v1.part.updateExpression([
        dict(id=deckel_prt, toUpdate=[dict(name="Laenge", value=length), dict(name="Breite", value=width + 3)]),
        dict(id=kanal_prt, toUpdate=[dict(name="Laenge", value=length), dict(name="Breite", value=width), dict(name="Hoehe", value=height)]),
    ])

    if constr_deckel:
        await api.v1.assembly.updateFastened(dict(id=constr_deckel.get("id"), zOffset=position))

    return loaded_id


# ───── Wall ─────

async def wall(api: CCApiU, p: dict):
    vertical_beam_thickness = 100
    horizontal_beam_thickness = 60
    wall_insulation_width = 525

    wall_length = p.get("Length", 1000)
    wall_height = p.get("Height", 1000)
    plasterboard_thickness = p.get("Plasterboard Thickness", 13)
    chipboard_thickness = p.get("Chipboard Thickness", 15)
    beamwall_thickness = p.get("Wooden Beam Wall Thickness", 140)
    insulation_thickness = p.get("Insulation Thickness", 60)
    wooden_slats_thickness = p.get("Wooden Slats Thickness", 40)
    wooden_formwork_thickness = p.get("Wooden Formwork Thickness", 25)
    explode_distance = p.get("Exploded View", 0)

    # Compute layer positions
    pos_x_gipsplatte = 0
    pos_x_spanplatte = plasterboard_thickness
    pos_x_balkenwand = plasterboard_thickness + chipboard_thickness
    pos_x_daemmung = plasterboard_thickness + chipboard_thickness + beamwall_thickness
    pos_x_holzlattung = plasterboard_thickness + chipboard_thickness + beamwall_thickness + insulation_thickness
    pos_x_holzschalung = plasterboard_thickness + chipboard_thickness + beamwall_thickness + insulation_thickness + 2 * wooden_slats_thickness

    if explode_distance > 0:
        pos_x_spanplatte += explode_distance
        pos_x_balkenwand += 2 * explode_distance
        pos_x_daemmung += 3 * explode_distance
        pos_x_holzlattung += 4 * explode_distance
        pos_x_holzschalung += 5 * explode_distance

    x_dir = [1, 0, 0]
    y_dir = [0, 1, 0]

    # Load template
    data = resourcehelper.read_bytes("Wall.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    root_node = loaded.get("id")

    # Get all needed parts from container
    gipsplatte_prt = await api.v1.assembly.getPartTemplate(dict(name="Gipsplatte"))
    spanplatte_prt = await api.v1.assembly.getPartTemplate(dict(name="Spanplatte"))
    daemmung_prt = await api.v1.assembly.getPartTemplate(dict(name="Daemmung"))
    holzlattung_prt = await api.v1.assembly.getPartTemplate(dict(name="Holzlattung"))
    holzschalung_prt = await api.v1.assembly.getPartTemplate(dict(name="Holzschalung"))
    horizontal_beam_prt = await api.v1.assembly.getPartTemplate(dict(name="HorizontalBeam"))
    vertical_beam_prt = await api.v1.assembly.getPartTemplate(dict(name="VerticalBeam"))
    wall_insulation_prt = await api.v1.assembly.getPartTemplate(dict(name="Insulation"))
    wall_insulation_custom_prt = await api.v1.assembly.getPartTemplate(dict(name="InsulationCustom"))

    balkenwand_asm = await api.v1.assembly.getAssemblyTemplate(dict(name="BalkenWandAsm"))

    # Add default instances to root node
    added_instances = await api.v1.assembly.instance([
        dict(productId=gipsplatte_prt, ownerId=root_node, transformation=[[pos_x_gipsplatte, 0, 0], x_dir, y_dir], name="Gipsplatte"),
        dict(productId=spanplatte_prt, ownerId=root_node, transformation=[[pos_x_spanplatte, 0, 0], x_dir, y_dir], name="Spanplatte"),
        dict(productId=balkenwand_asm, ownerId=root_node, transformation=[[pos_x_balkenwand, 0, 0], x_dir, y_dir], name="Balkenwand"),
        dict(productId=daemmung_prt, ownerId=root_node, transformation=[[pos_x_daemmung, 0, 0], x_dir, y_dir], name="Daemmung"),
        dict(productId=holzlattung_prt, ownerId=root_node, transformation=[[pos_x_holzlattung, 0, 0], x_dir, y_dir], name="Holzlattung"),
        dict(productId=holzschalung_prt, ownerId=root_node, transformation=[[pos_x_holzschalung, 0, 0], x_dir, y_dir], name="Holzschalung"),
    ])
    balkenwand_instance = added_instances[2]

    # Update wall size expressions on all layer parts
    await api.v1.part.updateExpression([
        dict(id=gipsplatte_prt, toUpdate=[
            dict(name="length", value=wall_length), dict(name="height", value=wall_height),
            dict(name="thickness", value=plasterboard_thickness),
        ]),
        dict(id=spanplatte_prt, toUpdate=[
            dict(name="length", value=wall_length), dict(name="height", value=wall_height),
            dict(name="thickness", value=chipboard_thickness),
        ]),
        dict(id=daemmung_prt, toUpdate=[
            dict(name="length", value=wall_length), dict(name="height", value=wall_height),
            dict(name="thickness", value=insulation_thickness),
        ]),
        dict(id=holzlattung_prt, toUpdate=[
            dict(name="wallLength", value=wall_length), dict(name="wallHeight", value=wall_height),
            dict(name="latchThickness", value=wooden_slats_thickness),
        ]),
        dict(id=holzschalung_prt, toUpdate=[
            dict(name="length", value=wall_length), dict(name="height", value=wall_height),
            dict(name="thickness", value=wooden_formwork_thickness),
        ]),
    ])

    # Update balkenwand beam expressions
    await api.v1.part.updateExpression([
        dict(id=horizontal_beam_prt, toUpdate=[
            dict(name="beamLength", value=wall_length), dict(name="beamWidth", value=beamwall_thickness),
        ]),
        dict(id=vertical_beam_prt, toUpdate=[
            dict(name="beamLength", value=wall_height - 2 * horizontal_beam_thickness),
            dict(name="beamWidth", value=beamwall_thickness),
        ]),
        dict(id=wall_insulation_prt, toUpdate=[
            dict(name="insulationHeight", value=wall_height - 2 * horizontal_beam_thickness),
            dict(name="insulationThickness", value=beamwall_thickness),
        ]),
        dict(id=wall_insulation_custom_prt, toUpdate=[
            dict(name="insulationHeight", value=wall_height - 2 * horizontal_beam_thickness),
            dict(name="insulationThickness", value=beamwall_thickness),
        ]),
    ])

    # Build balkenwand beams — compute beam/insulation layout
    distance_bt_segments = vertical_beam_thickness + wall_insulation_width
    to_fill_length = wall_length - distance_bt_segments - vertical_beam_thickness
    nof_beam_insulation_pairs = to_fill_length / distance_bt_segments
    nof_beams = int(math.floor(nof_beam_insulation_pairs))
    nof_wall_insulations = int(math.floor(nof_beam_insulation_pairs))
    nof_beams_custom = 0
    nof_wall_insulations_custom = 0
    wall_insulation_custom_width = 0
    remain_fill_length = (nof_beam_insulation_pairs - nof_beams) * distance_bt_segments

    if remain_fill_length != 0:
        if remain_fill_length > vertical_beam_thickness + 100:
            nof_beams += 1
            nof_wall_insulations_custom = 1
            wall_insulation_custom_width = remain_fill_length - vertical_beam_thickness
        else:
            nof_wall_insulations -= 1
            nof_beams_custom = 1
            nof_wall_insulations_custom = 2
            remain_fill_length = (wall_length
                - (distance_bt_segments
                   + nof_beams * vertical_beam_thickness
                   + nof_wall_insulations * wall_insulation_width
                   + vertical_beam_thickness))
            wall_insulation_custom_width = (remain_fill_length - vertical_beam_thickness) / 2

        await api.v1.part.updateExpression(dict(
            id=wall_insulation_custom_prt,
            toUpdate=[dict(name="insulationLength", value=wall_insulation_custom_width)],
        ))

    # Enter balkenwand sub-assembly context
    await api.v1.assembly.setCurrentInstance(dict(id=balkenwand_instance))

    beam_instances = []

    # Standard vertical beam instances
    for i in range(nof_beams):
        pos = [0, distance_bt_segments + i * distance_bt_segments, horizontal_beam_thickness]
        beam_instances.append(dict(
            productId=vertical_beam_prt, ownerId=balkenwand_instance,
            transformation=[pos, x_dir, y_dir], name=f"VerticalBeam{i}", isLocal=True,
        ))

    # Standard wall insulation instances
    for i in range(nof_wall_insulations):
        pos = [0, distance_bt_segments + vertical_beam_thickness + i * distance_bt_segments, horizontal_beam_thickness]
        beam_instances.append(dict(
            productId=wall_insulation_prt, ownerId=balkenwand_instance,
            transformation=[pos, x_dir, y_dir], name=f"Insulation{i}", isLocal=True,
        ))

    # Custom beam instances
    for i in range(nof_beams_custom):
        pos_y = ((nof_beams + 1) * vertical_beam_thickness
                 + (nof_wall_insulations + 1) * wall_insulation_width
                 + wall_insulation_custom_width
                 + i * (wall_insulation_custom_width + vertical_beam_thickness))
        beam_instances.append(dict(
            productId=vertical_beam_prt, ownerId=balkenwand_instance,
            transformation=[[0, pos_y, horizontal_beam_thickness], x_dir, y_dir],
            name=f"VerticalBeamCustom{i}", isLocal=True,
        ))

    # Custom wall insulation instances
    for i in range(nof_wall_insulations_custom):
        pos_y = ((nof_beams + 1) * vertical_beam_thickness
                 + (nof_wall_insulations + 1) * wall_insulation_width
                 + i * (wall_insulation_custom_width + vertical_beam_thickness))
        beam_instances.append(dict(
            productId=wall_insulation_custom_prt, ownerId=balkenwand_instance,
            transformation=[[0, pos_y, horizontal_beam_thickness], x_dir, y_dir],
            name=f"InsulationCustom{i}", isLocal=True,
        ))

    if beam_instances:
        await api.v1.assembly.instance(beam_instances)

    # Return to root context
    await api.v1.assembly.setCurrentInstance(dict(id=root_node))
    return root_node


# ───── RobotArm ─────

async def robot_arm(api: CCApiU, p: dict):
    a1_deg = p.get("Axis Base/J1", 0)
    a2_deg = p.get("Axis J1/J2", 0)
    a3_deg = p.get("Axis J2/J3", 0)
    a4_deg = p.get("Axis J3/J4", 0)
    a5_deg = p.get("Axis J4/J5", 0)
    a6_deg = p.get("Axis J5/J6", 0)

    data = resourcehelper.read_bytes("Robot6Axis_FC.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    constraint_names = ["Base-J1", "J1-J2", "J2-J3", "J3-J4", "J4-J5", "J5-J6"]
    values_deg = [a1_deg, a2_deg, a3_deg, a4_deg, a5_deg, a6_deg]

    for name, deg in zip(constraint_names, values_deg):
        constraint = await api.v1.assembly.getFastened(dict(id=loaded_id, name=name))
        if constraint:
            await api.v1.assembly.updateFastened(dict(
                id=constraint.get("id"), zRotation=(float(deg) / 180.0) * math.pi,
            ))

    return loaded_id


# ───── MechanicalAssembly ─────

async def mechanical_assembly(api: CCApiU, p: dict):
    cylinder_offset = p.get("Cylinder", 0)
    lever_deg = p.get("Lever", 305)

    data = resourcehelper.read_bytes("MechanicalAssembly.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    slider = await api.v1.assembly.getSlider(dict(id=loaded_id, name="Slider"))
    revolute = await api.v1.assembly.getRevolute(dict(id=loaded_id, name="Revolute"))

    if slider:
        await api.v1.assembly.update3DConstraintValue(dict(id=slider.get("id"), name="Z_OFFSET", value=cylinder_offset))
    if revolute:
        await api.v1.assembly.update3DConstraintValue(dict(id=revolute.get("id"), name="Z_ROTATION", value=lever_deg / 180.0 * math.pi))

    return loaded_id


# ───── MechanicalAssembly2 ─────

async def mechanical_assembly2(api: CCApiU, p: dict):
    handle_deg = p.get("Handle", 0)

    data = resourcehelper.read_bytes("MechanicalAssembly2.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    revolute = await api.v1.assembly.getRevolute(dict(id=loaded_id, name="Revolute"))
    if revolute:
        await api.v1.assembly.update3DConstraintValue(dict(id=revolute.get("id"), name="Z_ROTATION", value=handle_deg / 180.0 * math.pi))

    return loaded_id


# ───── MechanicalAssembly3 ─────

async def mechanical_assembly3(api: CCApiU, p: dict):
    handle_deg = p.get("Handle", 180)

    data = resourcehelper.read_bytes("MechanicalAssembly3.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB"))
    loaded_id = loaded.get("id")

    revolute = await api.v1.assembly.getRevolute(dict(id=loaded_id, name="Revolute"))
    if revolute:
        await api.v1.assembly.update3DConstraintValue(dict(id=revolute.get("id"), name="Z_ROTATION", value=handle_deg / 180.0 * math.pi))

    return loaded_id


# ───── GantryRobot ─────

async def gantry_robot(api: CCApiU, p: dict):
    data = resourcehelper.read_bytes("GantryRobiAssembly.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB", ident="root"))
    loaded_id = loaded.get("id")
    return loaded_id


# ───── CaseAssembly ─────

async def case_assembly(api: CCApiU, p: dict):
    width = p.get("Width", 120)
    height = p.get("Height", 50)
    depth = p.get("Depth", 160)

    data = resourcehelper.read_bytes("CaseAssembly.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB", ident="root"))
    loaded_id = loaded.get("id")

    await api.v1.part.updateExpression([
        dict(id="Case", toUpdate=[dict(name="width", value=width), dict(name="height", value=height), dict(name="depth", value=depth)]),
        dict(id="Cover", toUpdate=[dict(name="width", value=width), dict(name="height", value=height)]),
    ])

    delta_x = (width - 10) / 2
    delta_y = (height - 10) / 2
    delta_z = depth + 2.5

    x_dir = [1, 0, 0]
    y_dir = [0, 1, 0]

    await api.v1.assembly.instance([
        dict(productId="Screw", ownerId="root", transformation=[[-delta_x, delta_y, delta_z], x_dir, y_dir], name="ScrewInstance1", ident="ScrewInstanceIdent1"),
        dict(productId="Screw", ownerId="root", transformation=[[delta_x, delta_y, delta_z], x_dir, y_dir], name="ScrewInstance2"),
        dict(productId="Screw", ownerId="root", transformation=[[-delta_x, -delta_y, delta_z], x_dir, y_dir], name="ScrewInstance3", ident="ScrewInstanceIdent3"),
        dict(productId="Screw", ownerId="root", transformation=[[delta_x, -delta_y, delta_z], x_dir, y_dir], name="ScrewInstance4"),
    ])
    return loaded_id


# ───── TrainStationClock ─────

async def train_station_clock(api: CCApiU, p: dict):
    data = resourcehelper.read_bytes("TrainStationClock.ofb")
    loaded = await api.v1.common.load(dict(data=data, format="OFB", ident="root"))
    loaded_id = loaded.get("id")

    hour_pointer_inst = await api.v1.assembly.getInstance(dict(ownerId=loaded_id, name="hours"))
    revolute_hour = await api.v1.assembly.getRevolute(dict(id=loaded_id, name="Revolute1"))

    if revolute_hour:
        await api.v1.assembly.update3DConstraintValue(dict(id=revolute_hour.get("id"), name="Z_ROTATION", value=0))

    now = datetime.now()
    h = (now.hour % 12) + now.minute / 60.0 + now.second / 3600.0
    angle_h_rad = (360.0 / 12.0) * h / 180.0 * math.pi

    cos_a = math.cos(angle_h_rad)
    sin_a = math.sin(angle_h_rad)

    if hour_pointer_inst:
        await api.v1.assembly.startMovingUnderConstraints(dict(
            id=loaded_id, instanceIds=[hour_pointer_inst],
            pivotInfo=[0, 0, 0], mucType="ROTATION",
        ))
        await api.v1.assembly.moveUnderConstraints(dict(
            id=loaded_id,
            rotation=dict(
                xDir=[cos_a, -sin_a, 0],
                yDir=[sin_a, cos_a, 0],
                zDir=[0, 0, 1],
            ),
        ))
        await api.v1.assembly.finishMovingUnderConstraints(dict(id=loaded_id))

    return loaded_id
