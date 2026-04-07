#!/usr/bin/env python

import logging
import asyncio
import time
import os
from typing import TypedDict, Literal, Union
import zlib

from classcadapi import Point, encodeBase64, decodeBase64, deflate
from classcadconnector import *
from classcadconnector.httpclient import _HttpClient  # internal, not part of public API

output_dir = os.path.join(os.path.dirname(__file__), "../../..", "out")
os.makedirs(output_dir, exist_ok=True)

# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")
logger = logging.getLogger(__name__)

useGetScg = False
useSocketIO = True


def createClient() -> AbstractClient:
    if useSocketIO:
        return SocketIOClient(url="ws://localhost:9091")
    else:
        return _HttpClient(url="http://localhost:9094")


async def closeClient(client: AbstractClient):
    await client.close()


class STLSettings(TypedDict, total=False):
    binary: bool


class SaveOption(TypedDict, total=False):
    format: Literal["OFB", "STP", "STL"]
    encoding: Literal["base64"]
    compression: Literal["deflate"]
    stl: STLSettings


async def save_model(content: Union[str, bytes], filename: str, is_compressed: bool = False) -> None:
    file_path = os.path.join(output_dir, filename)

    if isinstance(content, str):
        raw = decodeBase64(content)
        if is_compressed:
            decompressed = zlib.decompressobj(wbits=-15).decompress(raw)
            outfile = open(file_path, "wb")
            outfile.write(decompressed)
            outfile.close()
        else:
            outfile = open(file_path, "wb")
            outfile.write(raw)
            outfile.close()
    else:
        outfile = open(file_path, "wb")
        outfile.write(content)
        outfile.close()


async def save_different_formats(api: CCApiU, name: str) -> None:
    save_options: list[SaveOption] = [
        {"format": "OFB", "encoding": "base64", "compression": "deflate"},
        {"format": "OFB", "encoding": "base64"},
        {"format": "OFB"},
        {"format": "STP", "encoding": "base64", "compression": "deflate"},
        {"format": "STP", "encoding": "base64"},
        {"format": "STP"},
        {"format": "STL", "encoding": "base64", "compression": "deflate"},
        {"format": "STL", "encoding": "base64", "compression": "deflate", "stl": {"binary": False}},
        {"format": "STL", "encoding": "base64"},
        {"format": "STL", "encoding": "base64", "stl": {"binary": False}},
        {"format": "STL"},
        {"format": "STL", "stl": {"binary": False}},
    ]

    for option in save_options:
        encoded = option.get("encoding") == "base64"
        compressed = option.get("compression") == "deflate"
        binary_stl = option["format"] == "STL" and option.get("stl", {}).get("binary", True)

        stream_data = await api.v1.common.save(option)

        if stream_data and stream_data.get("success") and stream_data.get("content"):
            file_name = (
                f"{name}"
                f"{'_' + option['encoding'] if encoded else ''}"
                f"{'_' + option['compression'] if compressed else ''}"
                f"{'_Binary' if binary_stl else ''}"
                f".{option['format'].lower()}"
            )
            await save_model(stream_data["content"], file_name, compressed)

def create_model_1():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()
        partId = await api.v1.part.create(dict(name="Part1"))
        workCSysId = await api.v1.part.workCSys(dict(id=partId))
        boxId = await api.v1.part.box(dict(id=partId, references=[workCSysId], width=20, length=200, height=200))
        workPlaneId = await api.v1.part.workPlane(dict(id=partId, position=[0, 0, 100], normal=[0, 0, 1]))
        sliceId = await api.v1.part.slice(dict(id=partId, targets=[boxId], reference=workPlaneId, inverted=True))
        xAxisId = await api.v1.part.getWorkGeometry(dict(id=partId, name="XAxis"))
        yAxisId = await api.v1.part.getWorkGeometry(dict(id=partId, name="YAxis"))
        lp = await api.v1.part.linearPattern(
            dict(
                id=partId,
                targets=[sliceId],
                dir1=dict(references=[xAxisId], distance=300, count=5, merged=True),
                dir2=dict(references=[yAxisId], distance=100, count=3),
            )
        )
        dimensionIds: list[int] = await api.v1.drawing2d.dimension(
            dict(
                id=partId,
                viewType="FRONT",
                common=dict(type="LINEAR", name="Height", label="Height = ", value=100, textPos=[-30, 0, 50]),
                linear=dict(startPos=[0, 0, 0], endPos=[0, 0, 100], orientation="VERTICAL"),
            )
        )

        await save_different_formats(api, "Model1")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model1: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_2():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()
        params = dict(file="C://tmp/Flange.ofb", doClear=True)  # optional, often useful
        raw_url = "https://raw.githubusercontent.com/awv-informatik/classcad-test-data/main/as1/Bolt.ofb"
        partId = await api.v1.common.load(dict(url=raw_url))
        partId = partId.get("id") if partId != None else None
        workPlaneId = await api.v1.part.workPlane(dict(id=partId, normal=[1, 0, 0]))
        sketchId = await api.v1.sketch.create(dict(id=partId, planeId=workPlaneId))
        line1Id = await api.v1.sketch.line(dict(id=sketchId, startPos=[20, 20, 0], endPos=[50, 30, 0]))
        line2Id = await api.v1.sketch.line(dict(id=sketchId, startPos=[50, 30, 0], endPos=[30, 70, 0]))
        line3Id = await api.v1.sketch.line(dict(id=sketchId, startPos=[30, 70, 0], endPos=[20, 20, 0]))
        region = await api.v1.sketch.sketchRegion(
            dict(id=sketchId, name="SketchRegion", geomIds=[line1Id, line2Id, line3Id])
        )
        extrusionId = await api.v1.part.extrusion(dict(id=partId, references=[region], limit2=80.0, capEnds=False))
        workCSysId = await api.v1.part.workCSys(dict(id=partId, offset=[1, -80, 0]))
        boxId = await api.v1.part.box(dict(id=partId, references=[workCSysId], length=78, width=80, height=80))
        sliceBySheetId = await api.v1.part.sliceBySheet(
            dict(id=partId, target=dict(id=boxId), tool=dict(id=extrusionId))
        )
        xyPlaneId = await api.v1.part.getWorkGeometry(dict(id=partId, name="Top"))
        await api.v1.part.mirror(dict(id=partId, targets=[sliceBySheetId], references=[xyPlaneId]))
        sketchCId = await api.v1.sketch.create(dict(id=partId, planeId=xyPlaneId))
        await api.v1.sketch.copyFrom(dict(id=sketchCId, toCopyId=sketchId))

        await save_different_formats(api, "Model2")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model2: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_3():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()
        part = await api.v1.part.create(dict(name="Part"))
        await api.v1.part.cylinder(dict(id=part, diameter=50, height=100))
        topEdges = await api.v1.part.getGeometryIds(dict(id=part, circles=[dict(pos=[0, 0, 100])]))
        topEdges = topEdges.get("circles")
        await api.v1.part.fillet(dict(id=part, references=topEdges, radius=10))
        bottomEdges = await api.v1.part.getGeometryIds(dict(id=part, circles=[dict(pos=[0, 0, 0])]))
        bottomEdges = bottomEdges.get("circles")
        chamferId = await api.v1.part.chamfer(dict(id=part, references=bottomEdges, distance1=10))
        workAxisId = await api.v1.part.workAxis(dict(id=part, direction=[1, 1, 0]))
        await api.v1.part.translation(dict(id=part, targets=[chamferId], references=[workAxisId], distance=200))
        chamferEdges = await api.v1.part.getGeometryIds(dict(id=part, circles=[dict(pos=[141, 141, 0])]))
        chamferEdges = chamferEdges.get("circles")
        workPointId = await api.v1.part.workPoint(dict(id=part, type="CENTER", references=chamferEdges))
        xAxisId = await api.v1.part.getWorkGeometry(dict(id=part, name="XAxis"))
        yAxisId = await api.v1.part.getWorkGeometry(dict(id=part, name="YAxis"))
        await api.v1.part.workCSys(
            dict(id=part, name="Mate", type="XYAXISORIGIN", references=[workPointId, xAxisId, yAxisId], inverted=True)
        )

        await save_different_formats(api, "Model3")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model3: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_4():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()
        raw_url = "https://raw.githubusercontent.com/awv-informatik/classcad-test-data/main/as1/Plate.ofb"
        partId = await api.v1.common.load(dict(url=raw_url))
        partId = partId.get("id") if partId != None else None

        await api.v1.part.updateExpression(
            dict(id=partId, toUpdate=[dict(name="H", value=50), dict(name="L", value=150), dict(name="W", value=200)])
        )

        await save_different_formats(api, "Model4")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model4: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_5():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()

        asmId = await api.v1.assembly.create(dict(name="Assembly"))

        filename1 = os.path.join(output_dir, "Model3.ofb")
        file1 = open(filename1)
        data = encodeBase64(deflate(file1.read()))
        file1.close()
        part3Id = await api.v1.assembly.loadProduct(
            dict(data=data, format="OFB", encoding="base64", compression="deflate")
        )
        part3Id = part3Id.get("id") if part3Id != None else None

        origin = [0, 0, 0]
        xDir = [1, 0, 0]
        yDir = [0, 1, 0]
        mate = await api.v1.part.getWorkGeometry(dict(id=part3Id, name="Mate"))
        instance1, instance2 = await api.v1.assembly.instance(
            [
                dict(productId=part3Id, ownerId=asmId, transformation=[origin, xDir, yDir], name="Instance1"),
                dict(productId=part3Id, ownerId=asmId, transformation=[origin, xDir, yDir], name="Instance2"),
            ]
        )
        fastenedOriginId = await api.v1.assembly.fastenedOrigin(
            dict(id=asmId, name="FO", mate1=dict(path=[instance1], csys=mate))
        )
        sliderId = await api.v1.assembly.slider(
            dict(
                id=asmId,
                name="S",
                mate1=dict(path=[instance1], csys=mate),
                mate2=dict(path=[instance2], csys=mate, flip="-Z"),
                zOffsetLimits=dict(min=0, max=100),
            )
        )
        await api.v1.assembly.updateFastenedOrigin(dict(id=fastenedOriginId, xOffset=20, yOffset=30))
        await api.v1.assembly.updateSlider(dict(id=sliderId, zOffsetLimits=dict(min=0, max=50)))
        await api.v1.assembly.update3DConstraintValue(dict(id=sliderId, name="Z_OFFSET", value=30))

        await save_different_formats(api, "Model5")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model5: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_6():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()
        partId: int = await api.v1.part.create(dict(name="Part5"))
        workPlaneId: int = await api.v1.part.workPlane(dict(id=partId, normal=Point(0, 0, 1)))
        sketchId = await api.v1.sketch.create(dict(id=partId, planeId=workPlaneId))

        filename1 = os.path.join(output_dir, "Model2.ofb")
        file1 = open(filename1)
        data = encodeBase64(deflate(file1.read()))
        file1.close()
        await api.v1.sketch.loadFrom(
            dict(id=sketchId, partId=partId, name="Sketch", data=data, encoding="base64", compression="deflate")
        )

        originId = await api.v1.part.getWorkGeometry(dict(id=partId, name="Origin"))
        xAxisId = await api.v1.part.getWorkGeometry(dict(id=partId, name="XAxis"))
        xzPlaneId = await api.v1.part.getWorkGeometry(dict(id=partId, name="Front"))
        await api.v1.sketch.setReferences(
            dict(id=sketchId, planeId=xzPlaneId, axisId=xAxisId, isXAxis=True, originId=originId)
        )

        await save_different_formats(api, "Model6")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model6: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def create_model_7():
    async def call():
        success = await client.connect()
        if success == False:
            return

        api = client.getApiU()

        pt0 = Point(0, 0, 0)
        xDir = Point(1, 0, 0)
        yDir = Point(0, 1, 0)

        # Create different variables to control expressions
        shaftDiameter = 10
        shaftLength = 42
        rodDiameter = shaftDiameter

        # Create root assembly
        as1Asm = await api.v1.assembly.create(dict(name="Root_Assembly"))

        # Create assembly templates
        lBracketAsm = await api.v1.assembly.assemblyTemplate(dict(name="LBracket_Asm"))
        nutBoltAsm = await api.v1.assembly.assemblyTemplate(dict(name="NutBolt_Asm"))
        rodAsm = await api.v1.assembly.assemblyTemplate(dict(name="Rod_Asm"))

        # Create Bolt part
        bolt = await api.v1.assembly.partTemplate(dict(name="Bolt"))
        await api.v1.part.expression(
            dict(
                id=bolt,
                toCreate=[
                    dict(name="Shaft_Diameter", value=10),
                    dict(name="Shaft_Length", value=50),
                    dict(name="Head_Diameter", value="Shaft_Diameter+5"),
                    dict(name="Head_Thickness", value=3),
                    dict(name="Distance_Nut_Head", value=30),
                    dict(name="Offset_WCS_Nut", value="Shaft_Length-Distance_Nut_Head"),
                ],
            )
        )
        wcsOrigin = await api.v1.part.workCSys(dict(id=bolt, name="WCS_Origin"))
        cylShaft = await api.v1.part.cylinder(
            dict(id=bolt, references=[wcsOrigin], diameter="@expr.Shaft_Diameter", height="@expr.Shaft_Length")
        )
        wcsHead = await api.v1.part.workCSys(dict(id=bolt, name="WCS_Head-Shaft", offset="{0, 0, @expr.Shaft_Length}"))
        cylHead = await api.v1.part.cylinder(
            dict(id=bolt, references=[wcsHead], diameter="@expr.Head_Diameter", height="@expr.Head_Thickness")
        )
        await api.v1.part.workCSys(dict(id=bolt, name="WCS_Nut", offset="{0, 0, @expr.Offset_WCS_Nut}"))

        # Set appearance of the bolt part
        if useGetScg:
            scg = await client.getScg()
            boltSolids: list[int] = [
                *(scg.structure["tree"][str(cylShaft)]["children"]),
                *(scg.structure["tree"][str(cylHead)]["children"]),
            ]
            await api.v1.common.setAppearance([dict(target=id, color=[73, 79, 101]) for id in boltSolids])
        else:
            await api.v1.common.setAppearance(dict(target=cylShaft, color=[73, 79, 101]))
            await api.v1.common.setAppearance(dict(target=cylHead, color=[73, 79, 101]))

        # Set expressions on bolt part (optional)
        await api.v1.part.updateExpression(
            dict(
                id=bolt,
                toUpdate=[
                    dict(name="Shaft_Length", value=shaftLength),
                    dict(name="Shaft_Diameter", value=shaftDiameter),
                ],
            )
        )

        # Add bolt to nut-bolt assembly template
        boltRefId: int = await api.v1.assembly.instance(
            dict(productId=bolt, ownerId=nutBoltAsm, transformation=[pt0, xDir, yDir], name="Bolt1")
        )

        # Get needed workcoordsystems of bolt
        wcsIdBoltNut = await api.v1.assembly.getWorkGeometry(dict(id=boltRefId, name="WCS_Nut"))
        wcsIdBoltHeadShaft = await api.v1.assembly.getWorkGeometry(dict(id=boltRefId, name="WCS_Head-Shaft"))
        wcsIdBoltOrigin = await api.v1.assembly.getWorkGeometry(dict(id=boltRefId, name="WCS_Origin"))

        # Create Nut part
        nut = await api.v1.assembly.partTemplate(dict(name="Nut"))
        await api.v1.part.expression(
            dict(
                id=nut,
                toCreate=[
                    dict(name="Hole_Diameter", value=10),
                    dict(name="Nut_Width", value="Hole_Diameter*2"),
                    dict(name="Nut_Length", value="Hole_Diameter*2"),
                    dict(name="Nut_Height", value=3),
                    dict(name="Nut_Center_Width", value="Nut_Width/2"),
                    dict(name="Nut_Center_Length", value="Nut_Length/2"),
                ],
            )
        )
        wcsOrigin = await api.v1.part.workCSys(dict(id=nut, name="WCS_Origin"))
        box = await api.v1.part.box(
            dict(
                id=nut,
                references=[wcsOrigin],
                width="@expr.Nut_Width",
                length="@expr.Nut_Length",
                height="@expr.Nut_Height",
            )
        )
        wcsHoleB = await api.v1.part.workCSys(
            dict(id=nut, name="WCS_Hole_Bottom", offset="{@expr.Nut_Center_Length, @expr.Nut_Center_Width, 0}")
        )
        await api.v1.part.workCSys(
            dict(
                id=nut,
                name="WCS_Hole_Top",
                offset="{@expr.Nut_Center_Length, @expr.Nut_Center_Width, @expr.Nut_Height}",
            )
        )
        cyl = await api.v1.part.cylinder(
            dict(id=nut, references=[wcsHoleB], diameter="@expr.Hole_Diameter", height="@expr.Nut_Height")
        )
        subtraction = await api.v1.part.boolean(dict(id=nut, type="SUBTRACTION", target=box, tools=[cyl]))

        # Set appearance of the nut part
        if useGetScg:
            scg = await client.getScg()
            nutSolids: list[int] = scg.structure["tree"][str(subtraction)]["children"]
            await api.v1.common.setAppearance([dict(target=id, color=[78, 85, 91]) for id in nutSolids])
        else:
            await api.v1.common.setAppearance(dict(target=subtraction, color=[78, 85, 91]))

        # Set expressions on bolt part (optional)
        await api.v1.part.updateExpression(dict(id=nut, toUpdate=[dict(name="Hole_Diameter", value=shaftDiameter)]))

        # Add nut to nut-bolt-assembly template
        nutRefId: int = await api.v1.assembly.instance(
            dict(productId=nut, ownerId=nutBoltAsm, transformation=[pt0, xDir, yDir], name="Nut1")
        )

        # Get needed workcoordsystems of nut
        wcsIdNut = await api.v1.assembly.getWorkGeometry(dict(id=nutRefId, name="WCS_Hole_Top"))

        # Set bolt to origin of nut-bolt-assembly
        await api.v1.assembly.fastenedOrigin(
            dict(id=nutBoltAsm, name="FOC0", mate1=dict(path=[boltRefId], csys=wcsIdBoltOrigin))
        )

        # Set nut on bolt
        await api.v1.assembly.fastened(
            dict(
                id=nutBoltAsm,
                name="FC1",
                mate1=dict(path=[boltRefId], csys=wcsIdBoltNut),
                mate2=dict(path=[nutRefId], csys=wcsIdNut),
            )
        )

        # Create LBracket part
        lBracket = await api.v1.assembly.partTemplate(dict(name="LBracket"))
        await api.v1.part.expression(
            dict(
                id=lBracket,
                toCreate=[
                    dict(name="LBracket_Width", value=50),
                    dict(name="LBracket_Depth", value=100),
                    dict(name="LBracket_Height", value=60),
                    dict(name="LBracket_Thickness", value=10),
                    dict(name="LBracket_Depth_Center", value="LBracket_Depth/2"),
                    dict(name="Hole_Diameter", value=10),
                    dict(name="Rod_Hole_Diameter", value=10),
                    dict(name="PI", value=3.14159265359),
                    dict(name="Rotation90", value="PI/2"),
                ],
            )
        )
        wcsOrigin = await api.v1.part.workCSys(dict(id=lBracket, name="WCS_Origin"))
        box1 = await api.v1.part.box(
            dict(
                id=lBracket,
                references=[wcsOrigin],
                width="@expr.LBracket_Depth",
                length="@expr.LBracket_Width",
                height="@expr.LBracket_Thickness",
            )
        )
        box2 = await api.v1.part.box(
            dict(
                id=lBracket,
                references=[wcsOrigin],
                width="@expr.LBracket_Depth",
                length="@expr.LBracket_Thickness",
                height="@expr.LBracket_Height",
            )
        )
        union = await api.v1.part.boolean(dict(id=lBracket, type="UNION", target=box1, tools=[box2]))
        wcsHole1B = await api.v1.part.workCSys(
            dict(id=lBracket, name="WCS_Hole1-Bottom", offset="{35, @expr.LBracket_Depth_Center-15, 0}")
        )
        wcsHole2B = await api.v1.part.workCSys(
            dict(id=lBracket, name="WCS_Hole2-Bottom", offset="{20, @expr.LBracket_Depth_Center, 0}")
        )
        wcsHole3B = await api.v1.part.workCSys(
            dict(id=lBracket, name="WCS_Hole3-Bottom", offset="{35, @expr.LBracket_Depth_Center+15, 0}")
        )
        wcsRod = await api.v1.part.workCSys(
            dict(
                id=lBracket,
                name="WCS_Rod",
                offset="{0, @expr.LBracket_Depth_Center, @expr.LBracket_Height/2+10}",
                rotation="{0, @expr.Rotation90, 0}",
            )
        )
        cyl1 = await api.v1.part.cylinder(
            dict(id=lBracket, references=[wcsHole1B], diameter="@expr.Hole_Diameter", height="@expr.LBracket_Thickness")
        )
        cyl2 = await api.v1.part.cylinder(
            dict(id=lBracket, references=[wcsHole2B], diameter="@expr.Hole_Diameter", height="@expr.LBracket_Thickness")
        )
        cyl3 = await api.v1.part.cylinder(
            dict(id=lBracket, references=[wcsHole3B], diameter="@expr.Hole_Diameter", height="@expr.LBracket_Thickness")
        )
        cylRod = await api.v1.part.cylinder(
            dict(
                id=lBracket, references=[wcsRod], diameter="@expr.Rod_Hole_Diameter", height="@expr.LBracket_Thickness"
            )
        )
        subtraction = await api.v1.part.boolean(
            dict(id=lBracket, type="SUBTRACTION", target=union, tools=[cyl1, cyl2, cyl3, cylRod])
        )
        await api.v1.part.workCSys(
            dict(
                id=lBracket,
                name="WCS_Hole1-Top",
                offset="{35, @expr.LBracket_Depth_Center-15, @expr.LBracket_Thickness}",
            )
        )
        await api.v1.part.workCSys(
            dict(
                id=lBracket, name="WCS_Hole2-Top", offset="{20, @expr.LBracket_Depth_Center, @expr.LBracket_Thickness}"
            )
        )
        await api.v1.part.workCSys(
            dict(
                id=lBracket,
                name="WCS_Hole3-Top",
                offset="{35, @expr.LBracket_Depth_Center+15, @expr.LBracket_Thickness}",
            )
        )

        # Set appearance of the lBracket part
        if useGetScg:
            scg = await client.getScg()
            lBracketSolids: list[int] = scg.structure["tree"][str(subtraction)]["children"]
            await api.v1.common.setAppearance([dict(target=id, color=[89, 99, 113]) for id in lBracketSolids])
        else:
            await api.v1.common.setAppearance(dict(target=subtraction, color=[89, 99, 113]))

        # Set expressions on lBracket part (optional)
        await api.v1.part.updateExpression(
            dict(
                id=lBracket,
                toUpdate=[
                    dict(name="Rod_Hole_Diameter", value=rodDiameter),
                    dict(name="Hole_Diameter", value=shaftDiameter),
                ],
            )
        )

        # Add lBracket to lbracket-assembly template
        lBracketRef1: int = await api.v1.assembly.instance(
            dict(productId=lBracket, ownerId=lBracketAsm, transformation=[pt0, xDir, yDir], name="lBracket1")
        )

        # Get needed workcoordsystems of lBracket
        wcsIdLBracket1 = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Hole1-Top"))
        wcsIdLBracket2Top = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Hole2-Top"))
        wcsIdLBracket2Bottom = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Hole2-Bottom"))
        wcsIdLBracket3 = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Hole3-Top"))
        wcsIdLBracketRod = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Rod"))
        wcsIdLBracketOrigin = await api.v1.assembly.getWorkGeometry(dict(id=lBracketRef1, name="WCS_Origin"))

        # Add nut-bolt assembly three times to lBracket-assembly template
        nutBoltAsmRefs = await api.v1.assembly.instance(
            [
                dict(productId=nutBoltAsm, ownerId=lBracketAsm, transformation=[pt0, xDir, yDir], name="Nut_Bolt1"),
                dict(productId=nutBoltAsm, ownerId=lBracketAsm, transformation=[pt0, xDir, yDir], name="Nut_Bolt2"),
                dict(productId=nutBoltAsm, ownerId=lBracketAsm, transformation=[pt0, xDir, yDir], name="Nut_Bolt3"),
            ]
        )

        # Set lBracket to origin of lBracket-assembly
        await api.v1.assembly.fastenedOrigin(
            dict(id=lBracketAsm, name="FOC1", mate1=dict(path=[lBracketRef1], csys=wcsIdLBracketOrigin))
        )

        # Set 1st nut-bolt-assembly on lBracket
        await api.v1.assembly.fastened(
            dict(
                id=lBracketAsm,
                name="FC2",
                mate1=dict(path=[lBracketRef1], csys=wcsIdLBracket1),
                mate2=dict(path=[boltRefId, nutBoltAsmRefs[0]], csys=wcsIdBoltHeadShaft),
            )
        )

        # Set 2nd nut-bolt-assembly on lBracket
        await api.v1.assembly.fastened(
            dict(
                id=lBracketAsm,
                name="FC3",
                mate1=dict(path=[lBracketRef1], csys=wcsIdLBracket2Top),
                mate2=dict(path=[boltRefId, nutBoltAsmRefs[1]], csys=wcsIdBoltHeadShaft),
            )
        )

        # Set 3rd nut-bolt-assembly on lBracket
        await api.v1.assembly.fastened(
            dict(
                id=lBracketAsm,
                name="FC4",
                mate1=dict(path=[lBracketRef1], csys=wcsIdLBracket3),
                mate2=dict(path=[boltRefId, nutBoltAsmRefs[2]], csys=wcsIdBoltHeadShaft),
            )
        )

        # Create Plate part
        plate = await api.v1.assembly.partTemplate(dict(name="Plate"))
        await api.v1.part.expression(
            dict(
                id=plate,
                toCreate=[
                    dict(name="Plate_Width", value=150),
                    dict(name="Plate_Length", value=180),
                    dict(name="Plate_Height", value=20),
                    dict(name="Hole_Diameter", value=10),
                    dict(name="PI", value=3.14159265359),
                ],
            )
        )
        wcsOrigin = await api.v1.part.workCSys(dict(id=plate, name="WCS_Origin"))
        box = await api.v1.part.box(
            dict(
                id=plate,
                references=[wcsOrigin],
                width="@expr.Plate_Width",
                length="@expr.Plate_Length",
                height="@expr.Plate_Height",
            )
        )
        wcsHole1B = await api.v1.part.workCSys(
            dict(id=plate, name="WCS_Hole1-Bottom", offset="{40, @expr.Plate_Width/2-15, 0}")
        )
        wcsHole2B = await api.v1.part.workCSys(
            dict(id=plate, name="WCS_Hole2-Bottom", offset="{25, @expr.Plate_Width/2, 0}")
        )
        wcsHole3B = await api.v1.part.workCSys(
            dict(id=plate, name="WCS_Hole3-Bottom", offset="{40, @expr.Plate_Width/2+15, 0}")
        )
        cyl1 = await api.v1.part.cylinder(
            dict(id=plate, references=[wcsHole1B], diameter="@expr.Hole_Diameter", height="@expr.Plate_Height")
        )
        cyl2 = await api.v1.part.cylinder(
            dict(id=plate, references=[wcsHole2B], diameter="@expr.Hole_Diameter", height="@expr.Plate_Height")
        )
        cyl3 = await api.v1.part.cylinder(
            dict(id=plate, references=[wcsHole3B], diameter="@expr.Hole_Diameter", height="@expr.Plate_Height")
        )
        wa = await api.v1.part.workAxis(
            dict(
                id=plate,
                name="Workaxis",
                position="{@expr.Plate_Length/2, @expr.Plate_Width/2, 0}",
                direction=[0, 0, 1],
            )
        )
        circPattern: int = await api.v1.part.circularPattern(
            dict(id=plate, targets=[cyl1, cyl2, cyl3], references=[wa], angle="@expr.PI", count=2, merged=True)
        )
        subtraction = await api.v1.part.boolean(dict(id=plate, type="SUBTRACTION", target=box, tools=[circPattern]))
        await api.v1.part.workCSys(
            dict(id=plate, name="WCS_Hole2-Top", offset="{25, @expr.Plate_Width/2, @expr.Plate_Height}")
        )
        await api.v1.part.workCSys(
            dict(
                id=plate,
                name="WCS_Hole5-Top",
                offset="{@expr.Plate_Length-25, @expr.Plate_Width/2, @expr.Plate_Height}",
                rotation="{0, 0, @expr.PI}",
            )
        )
        await api.v1.part.workCSys(dict(id=plate, name="WCS_LBracketOriginLeft", offset="{0, 0, @expr.Plate_Height}"))
        await api.v1.part.workCSys(
            dict(
                id=plate,
                name="WCS_LBracketOriginRight",
                offset="{@expr.Plate_Length, @expr.Plate_Width, @expr.Plate_Height}",
                rotation="{0, 0, @expr.Plate_Height}",
            )
        )

        # Set appearance of the plate part
        if useGetScg:
            scg = await client.getScg()
            plateSolids: list[int] = scg.structure["tree"][str(subtraction)]["children"]
            await api.v1.common.setAppearance([dict(target=id, color=[101, 94, 92]) for id in plateSolids])
        else:
            await api.v1.common.setAppearance(dict(target=subtraction, color=[101, 94, 92]))

        # Set expressions on plate part (optional)
        await api.v1.part.updateExpression(dict(id=plate, toUpdate=[dict(name="Hole_Diameter", value=shaftDiameter)]))

        # Add nut to nut-bolt assembly template
        plateRef: int = await api.v1.assembly.instance(
            dict(productId=plate, ownerId=as1Asm, transformation=[pt0, xDir, yDir], name="Plate1")
        )

        # Get needed workcoordsystems of plate
        wcsIdPlateBase = await api.v1.assembly.getWorkGeometry(dict(id=plateRef, name="WCS_Origin"))
        wcsIdPlate2 = await api.v1.assembly.getWorkGeometry(dict(id=plateRef, name="WCS_Hole2-Top"))
        wcsIdPlate5 = await api.v1.assembly.getWorkGeometry(dict(id=plateRef, name="WCS_Hole5-Top"))

        # Set plate to origin of as1-assembly
        await api.v1.assembly.fastenedOrigin(
            dict(id=as1Asm, name="FOC2", mate1=dict(path=[plateRef], csys=wcsIdPlateBase))
        )

        # Add nut to nut-bolt assembly template
        lBracketAsmRefs: list[int] = await api.v1.assembly.instance(
            [
                dict(productId=lBracketAsm, ownerId=as1Asm, transformation=[pt0, xDir, yDir], name="LBracket1"),
                dict(productId=lBracketAsm, ownerId=as1Asm, transformation=[pt0, xDir, yDir], name="LBracket2"),
            ]
        )

        # Set 1st lBracket-assembly on plate
        await api.v1.assembly.fastened(
            dict(
                id=as1Asm,
                name="FC5",
                mate1=dict(path=[plateRef], csys=wcsIdPlate2),
                mate2=dict(path=[lBracketRef1, lBracketAsmRefs[0]], csys=wcsIdLBracket2Bottom),
            )
        )

        # Set 2nd lBracket-assembly on plate
        await api.v1.assembly.fastened(
            dict(
                id=as1Asm,
                name="FC6",
                mate1=dict(path=[plateRef], csys=wcsIdPlate5),
                mate2=dict(path=[lBracketRef1, lBracketAsmRefs[1]], csys=wcsIdLBracket2Bottom),
            )
        )

        # Create Rod part
        rod = await api.v1.assembly.partTemplate(dict(name="Rod"))
        await api.v1.part.expression(
            dict(
                id=rod,
                toCreate=[
                    dict(name="Rod_Diameter", value=10),
                    dict(name="Rod_Length", value=200),
                    dict(name="Nut_Offset", value=15),
                    dict(name="Nut_Offset_Right", value="Rod_Length-Nut_Offset"),
                    dict(name="PI", value=3.14159265359),
                ],
            )
        )
        wcsOrigin = await api.v1.part.workCSys(dict(id=rod, name="WCS_Origin"))
        cyl = await api.v1.part.cylinder(
            dict(id=rod, references=[wcsOrigin], diameter="@expr.Rod_Diameter", height="@expr.Rod_Length")
        )
        await api.v1.part.workCSys(dict(id=rod, name="WCS_Nut_Left", offset="{0, 0, @expr.Nut_Offset}"))
        await api.v1.part.workCSys(
            dict(id=rod, name="WCS_Nut_Right", offset="{0, 0, @expr.Nut_Offset_Right}", rotation="{0, @expr.PI, 0}")
        )

        # Set appearance of the rod part
        if useGetScg:
            scg = await client.getScg()
            rodSolids: list[int] = scg.structure["tree"][str(cyl)]["children"]
            await api.v1.common.setAppearance([dict(target=id, color=[84, 90, 115]) for id in rodSolids])
        else:
            await api.v1.common.setAppearance(dict(target=cyl, color=[84, 90, 115]))

        # Set expressions on rod part (optional)
        await api.v1.part.updateExpression(dict(id=rod, toUpdate=[dict(name="Rod_Diameter", value=rodDiameter)]))

        # Add nut to nut-bolt assembly template
        rodRefId: int = await api.v1.assembly.instance(
            dict(productId=rod, ownerId=rodAsm, transformation=[pt0, xDir, yDir], name="Rod1")
        )

        # Get needed workcoordsystems of rod
        wscIdRodLeft = await api.v1.assembly.getWorkGeometry(dict(id=rodRefId, name="WCS_Nut_Left"))
        wcsIdRodRight = await api.v1.assembly.getWorkGeometry(dict(id=rodRefId, name="WCS_Nut_Right"))
        wcsIdRodOrigin = await api.v1.assembly.getWorkGeometry(dict(id=rodRefId, name="WCS_Origin"))

        # Add nut to nut-bolt assembly template
        nutRefIds = await api.v1.assembly.instance(
            [
                dict(productId=nut, ownerId=rodAsm, transformation=[pt0, xDir, yDir], name="Nut1"),
                dict(productId=nut, ownerId=rodAsm, transformation=[pt0, xDir, yDir], name="Nut2"),
            ]
        )

        # Set rod to origin of rod-assembly
        await api.v1.assembly.fastenedOrigin(
            dict(id=rodAsm, name="FOC3", mate1=dict(path=[rodRefId], csys=wcsIdRodOrigin))
        )

        # Set 1st nut on rod
        await api.v1.assembly.fastened(
            dict(
                id=rodAsm,
                name="FC7",
                mate1=dict(path=[rodRefId], csys=wscIdRodLeft),
                mate2=dict(path=[nutRefIds[0]], csys=wcsIdNut),
            )
        )

        # Set 2nd nut on rod
        await api.v1.assembly.fastened(
            dict(
                id=rodAsm,
                name="FC8",
                mate1=dict(path=[rodRefId], csys=wcsIdRodRight),
                mate2=dict(path=[nutRefIds[1]], csys=wcsIdNut),
            )
        )

        # Add nut to nut-bolt assembly template
        rodAsmRef: int = await api.v1.assembly.instance(
            dict(productId=rodAsm, ownerId=as1Asm, transformation=[pt0, xDir, yDir], name="RodAsm1")
        )

        # Set rod-assembly on lBracket of first lBracket-assembly
        await api.v1.assembly.fastened(
            dict(
                id=as1Asm,
                name="FC9",
                mate1=dict(path=[lBracketRef1, lBracketAsmRefs[0]], csys=wcsIdLBracketRod),
                mate2=dict(path=[rodRefId, rodAsmRef], csys=wscIdRodLeft),
            )
        )

        await save_different_formats(api, "Model7")

    client = createClient()
    loop = asyncio.get_event_loop()
    start = time.perf_counter()
    loop.run_until_complete(call())
    logger.info(f"Model7: {(time.perf_counter() - start) * 1000:.0f} ms")
    loop.run_until_complete(closeClient(client=client))


def run_examples():
    create_model_1()
    create_model_2()
    create_model_3()
    create_model_4()
    create_model_5()
    create_model_6()
    create_model_7()


if __name__ == "__main__":
    run_examples()
