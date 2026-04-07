from . import assemblyexamples, partexamples, solidexamples

PARAM_NUMBER = "number"
PARAM_CHECKBOX = "checkbox"
PARAM_SLIDER = "slider"
PARAM_DROPDOWN = "dropdown"


def get_all_models():
    return [
        # ===== Solid examples =====
        dict(id="Fish", label="Fish", category="Solid", create_func=solidexamples.fish,
             params=[dict(name="Thickness", type=PARAM_NUMBER, default=5)]),
        dict(id="Heart", label="Heart", category="Solid", create_func=solidexamples.heart),
        dict(id="Lego", label="Lego Configurator", category="Solid", create_func=solidexamples.lego,
             params=[dict(name="Rows", type=PARAM_NUMBER, default=2), dict(name="Columns", type=PARAM_NUMBER, default=5)]),
        dict(id="StepImport 1", label="Step Import 1", category="Solid", create_func=solidexamples.step_import1),
        dict(id="StepImport 2", label="Step Import 2", category="Solid", create_func=solidexamples.step_import2),
        dict(id="Whiffleball", label="Whiffleball", category="Solid", create_func=solidexamples.whiffleball),
        dict(id="Profile", label="Profile", category="Solid", create_func=solidexamples.profile),
        dict(id="Hackathon", label="Hackathon", category="Solid", create_func=solidexamples.hackathon),
        dict(id="Mechanical", label="Mechanical", category="Solid", create_func=solidexamples.mechanical),
        dict(id="Mechanical2", label="Mechanical 2", category="Solid", create_func=solidexamples.mechanical2),
        dict(id="Polylines1", label="Polylines 1", category="Solid", create_func=solidexamples.polylines1),
        dict(id="Polylines2", label="Polylines 2", category="Solid", create_func=solidexamples.polylines2),
        dict(id="Smiley", label="Smiley", category="Solid", create_func=solidexamples.smiley,
             params=[dict(name="Happy?", type=PARAM_CHECKBOX, default=1)]),
        dict(id="WheelRim", label="Wheel Rim", category="Solid", create_func=solidexamples.wheel_rim),

        # ===== History (Part) examples =====
        dict(id="CreatePart", label="Simple Part Creator", category="Part", create_func=partexamples.create_part),
        dict(id="Sketch", label="Simple Sketch", category="Part", create_func=partexamples.sketch),
        dict(id="Sketch 2", label="Simple Sketch 2", category="Part", create_func=partexamples.sketch2),
        dict(id="Sketch 3", label="Sketch 3", category="Part", create_func=partexamples.sketch3),
        dict(id="Sketch 4", label="Sketch 4", category="Part", create_func=partexamples.sketch4,
             params=[dict(name="Radius", type=PARAM_SLIDER, default=100, min=50, max=130, step=5)]),
        dict(id="Twist", label="Twist Feature", category="Part", create_func=partexamples.twist,
             params=[dict(name="Options", type=PARAM_DROPDOWN, default=0, options=partexamples.TWIST_OPTIONS)]),
        dict(id="Gripper", label="Gripper Configurator", category="Part", create_func=partexamples.gripper,
             params=[
                 dict(name="Width", type=PARAM_NUMBER, default=60),
                 dict(name="Height", type=PARAM_NUMBER, default=170),
                 dict(name="Distance", type=PARAM_NUMBER, default=40),
                 dict(name="Taper", type=PARAM_NUMBER, default=50),
             ]),
        dict(id="FlangePart", label="Flange Creator", category="Part", create_func=partexamples.flange_part),
        dict(id="Flange", label="Flange Configurator", category="Part", create_func=partexamples.flange,
             params=[
                 dict(name="Holes Count", type=PARAM_SLIDER, default=6, min=2, max=12, step=1),
                 dict(name="Flange Height", type=PARAM_SLIDER, default=100, min=40, max=300, step=5),
             ]),
        dict(id="Shadowbox", label="Shadowbox Configurator", category="Part", create_func=partexamples.shadowbox,
             params=[
                 dict(name="Depth", type=PARAM_NUMBER, default=20),
                 dict(name="Height", type=PARAM_NUMBER, default=200),
                 dict(name="Width", type=PARAM_NUMBER, default=400),
                 dict(name="Min. Gap", type=PARAM_NUMBER, default=5),
                 dict(name="Hole Diameter", type=PARAM_NUMBER, default=35),
                 dict(name="Columns", type=PARAM_NUMBER, default=8),
                 dict(name="Rows", type=PARAM_NUMBER, default=4),
             ]),
        dict(id="MechanicalPart", label="Mechanical Part", category="Part", create_func=partexamples.mechanical_part),
        dict(id="MechanicalPart2", label="Mechanical Part 2", category="Part", create_func=partexamples.mechanical_part2),
        dict(id="MechanicalPart3", label="Mechanical Part 3", category="Part", create_func=partexamples.mechanical_part3),

        # ===== History (Assembly) examples =====
        dict(id="CreateAsm", label="LBracket Creator", category="Assembly", create_func=assemblyexamples.create_asm),
        dict(id="Nut-Bolt_Assembly", label="Nut-Bolt Assembler", category="Assembly", create_func=assemblyexamples.nut_bolt_assembly),
        dict(id="L-Bracket_Assembly", label="LBracket Assembler", category="Assembly", create_func=assemblyexamples.lbracket_assembly),
        dict(id="As1_Assembly", label="As1 Assembler", category="Assembly", create_func=assemblyexamples.as1_assembly),
        dict(id="FlangeAsm", label="Flange Assembler", category="Assembly", create_func=assemblyexamples.flange_asm),
        dict(id="RollerAsm", label="FMS Roller Configurator", category="Assembly", create_func=assemblyexamples.roller_asm,
             params=[
                 dict(name="Walze Length", type=PARAM_NUMBER, default=800),
                 dict(name="Arrow Direction", type=PARAM_SLIDER, default=0, min=0, max=3, step=1),
                 dict(name="Walze Direction", type=PARAM_SLIDER, default=0, min=0, max=1, step=1),
                 dict(name="Segment Size", type=PARAM_NUMBER, default=50),
                 dict(name="Num Segments", type=PARAM_NUMBER, default=5),
                 dict(name="Plug Position", type=PARAM_SLIDER, default=0, min=0, max=3, step=1),
             ]),
        dict(id="Wireway", label="Wireway Configurator", category="Assembly", create_func=assemblyexamples.wireway,
             params=[
                 dict(name="Length", type=PARAM_SLIDER, default=200, min=100, max=400, step=5),
                 dict(name="Height", type=PARAM_SLIDER, default=30, min=20, max=80, step=5),
                 dict(name="Width", type=PARAM_SLIDER, default=30, min=20, max=120, step=5),
                 dict(name="Position", type=PARAM_SLIDER, default=0, min=0, max=100, step=5),
             ]),
        dict(id="Wall", label="Wall Configurator", category="Assembly", create_func=assemblyexamples.wall,
             params=[
                 dict(name="Length", type=PARAM_NUMBER, default=1000),
                 dict(name="Height", type=PARAM_NUMBER, default=1000),
                 dict(name="Plasterboard Thickness", type=PARAM_SLIDER, default=13, min=10, max=20, step=1),
                 dict(name="Chipboard Thickness", type=PARAM_SLIDER, default=15, min=10, max=25, step=1),
                 dict(name="Wooden Beam Wall Thickness", type=PARAM_SLIDER, default=140, min=100, max=200, step=1),
                 dict(name="Insulation Thickness", type=PARAM_SLIDER, default=60, min=40, max=80, step=1),
                 dict(name="Wooden Slats Thickness", type=PARAM_SLIDER, default=40, min=20, max=60, step=1),
                 dict(name="Wooden Formwork Thickness", type=PARAM_SLIDER, default=25, min=20, max=30, step=1),
                 dict(name="Exploded View", type=PARAM_SLIDER, default=0, min=0, max=800, step=1),
             ]),
        dict(id="RobotArm", label="Robot Configurator", category="Assembly", create_func=assemblyexamples.robot_arm,
             params=[
                 dict(name="Axis Base/J1", type=PARAM_SLIDER, default=0, min=0, max=360, step=5),
                 dict(name="Axis J1/J2", type=PARAM_SLIDER, default=0, min=-60, max=160, step=1),
                 dict(name="Axis J2/J3", type=PARAM_SLIDER, default=0, min=-230, max=45, step=1),
                 dict(name="Axis J3/J4", type=PARAM_SLIDER, default=0, min=-180, max=180, step=1),
                 dict(name="Axis J4/J5", type=PARAM_SLIDER, default=0, min=-90, max=90, step=1),
                 dict(name="Axis J5/J6", type=PARAM_SLIDER, default=0, min=-180, max=180, step=1),
             ]),
        dict(id="MechanicalAssembly", label="Mechanical Simulation", category="Assembly", create_func=assemblyexamples.mechanical_assembly,
             params=[
                 dict(name="Cylinder", type=PARAM_SLIDER, default=0, min=-15, max=10, step=1),
                 dict(name="Lever", type=PARAM_SLIDER, default=305, min=285, max=335, step=5),
             ]),
        dict(id="MechanicalAssembly2", label="Mechanical Simulation 2", category="Assembly", create_func=assemblyexamples.mechanical_assembly2,
             params=[dict(name="Handle", type=PARAM_SLIDER, default=0, min=0, max=360, step=1)]),
        dict(id="MechanicalAssembly3", label="Mechanical Simulation 3", category="Assembly", create_func=assemblyexamples.mechanical_assembly3,
             params=[dict(name="Handle", type=PARAM_SLIDER, default=180, min=0, max=360, step=1)]),
        dict(id="GantryRobot", label="Gantry Robot", category="Assembly", create_func=assemblyexamples.gantry_robot),
        dict(id="CaseAssembly", label="Case Configurator", category="Assembly", create_func=assemblyexamples.case_assembly,
             params=[
                 dict(name="Width", type=PARAM_SLIDER, default=120, min=30, max=200, step=2),
                 dict(name="Height", type=PARAM_SLIDER, default=50, min=30, max=200, step=2),
                 dict(name="Depth", type=PARAM_SLIDER, default=160, min=30, max=200, step=2),
             ]),
        dict(id="TrainStationClock", label="Train Station Clock", category="Assembly", create_func=assemblyexamples.train_station_clock),
    ]
