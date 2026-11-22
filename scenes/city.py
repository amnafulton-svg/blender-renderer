"""Low-poly city test: 10 s slow camera glide over a procedural city. Cycles CPU, headless.
Run: blender -b -P city.py -- <out_dir> [frame_start frame_end] [samples]
"""
import math
import random
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/city"
F0 = int(argv[1]) if len(argv) > 1 else 1
F1 = int(argv[2]) if len(argv) > 2 else 250
SAMPLES = int(argv[3]) if len(argv) > 3 else 24

random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def hexrgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)  # sRGB -> linear


BUILDING = [mat(f"b{i}", hexrgb(h)) for i, h in enumerate(
    ["#d9b98f", "#c98f6b", "#8fa9bf", "#e6d3b3", "#9fb39a", "#d08a6a", "#b9aea0", "#7f95b0"])]
ROOF = mat("roof", hexrgb("#8a8f94"))
WINDOW = mat("win", hexrgb("#3c4a5c"), 0.25)
GROUND = mat("ground", hexrgb("#7fa36b"))
ROAD = mat("road", hexrgb("#4a4d52"), 0.9)
WALK = mat("walk", hexrgb("#bdb7ab"))
LEAF = mat("leaf", hexrgb("#5d8a4a"))
TRUNK = mat("trunk", hexrgb("#6b4f3a"))
WATER = mat("water", hexrgb("#4f86a8"), 0.1)


def box(name, loc, size, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(m)
    return o


# --- ground, river, roads -------------------------------------------------------------
N, BLOCK, STREET = 9, 14.0, 5.0          # 9x9 blocks
PITCH = BLOCK + STREET
HALF = N * PITCH / 2
box("ground", (0, 0, -0.1), (6000, 6000, 0.2), GROUND)
box("river", (0, HALF + 18, -0.05), (6000, 18, 0.2), WATER)
for i in range(N + 1):
    p = -HALF + STREET / 2 + i * PITCH
    box(f"rx{i}", (p, STREET / 2, 0.01), (STREET, N * PITCH + STREET, 0.02), ROAD)
    box(f"ry{i}", (STREET / 2, p, 0.012), (N * PITCH + STREET, STREET, 0.024), ROAD)

# --- blocks: buildings or parks -------------------------------------------------------
for ix in range(N):
    for iy in range(N):
        cx = -HALF + STREET / 2 + ix * PITCH + BLOCK / 2 + STREET / 2
        cy = -HALF + STREET / 2 + iy * PITCH + BLOCK / 2 + STREET / 2
        box(f"walk{ix}_{iy}", (cx, cy, 0.08), (BLOCK + 1.2, BLOCK + 1.2, 0.16), WALK)
        d = min(1.0, math.hypot(cx, cy) / HALF)                      # tall in the middle, low at the edge
        if random.random() < 0.12:                            # park
            for _ in range(6):
                tx, ty = cx + random.uniform(-5, 5), cy + random.uniform(-5, 5)
                box("trunk", (tx, ty, 0.9), (0.4, 0.4, 1.6), TRUNK)
                bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=1.6, depth=3.2, location=(tx, ty, 3.0))
                bpy.context.object.data.materials.append(LEAF)
            continue
        lots = random.choice([1, 2, 4])
        sub = BLOCK / (2 if lots > 1 else 1)
        spots = [(0, 0)] if lots == 1 else ([(-1, 0), (1, 0)] if lots == 2 else [(-1, -1), (-1, 1), (1, -1), (1, 1)])
        for sx, sy in spots:
            w = sub * random.uniform(0.62, 0.86) if lots > 1 else BLOCK * random.uniform(0.6, 0.85)
            dep = (BLOCK if lots == 2 else sub) * random.uniform(0.62, 0.86)
            h = min(48, max(4, random.gauss(30 * (1 - d) ** 1.6 + 6, 6)))
            bx, by = cx + sx * sub / 2, cy + sy * sub / 2
            m = random.choice(BUILDING)
            box("bld", (bx, by, h / 2 + 0.16), (w, dep, h), m)
            box("roof", (bx, by, h + 0.16 + 0.25), (w * 0.9, dep * 0.9, 0.5), ROOF)
            if h > 14:                                         # window bands on taller towers
                for k in range(int(h // 4)):
                    z = 3 + k * 4
                    if z > h - 2:
                        break
                    box("winband", (bx, by, z), (w + 0.06, dep + 0.06, 1.1), WINDOW)
            if h > 40 and random.random() < 0.5:               # setback top
                box("top", (bx, by, h + 4), (w * 0.55, dep * 0.55, 7), m)

# street trees along one avenue
for i in range(-int(HALF), int(HALF), 8):
    for side in (-1, 1):
        x, y = side * 3.3, i + 2
        if abs(((y + HALF) % PITCH) - PITCH + STREET / 2) < STREET:
            continue
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.3, location=(x + PITCH / 2 - STREET / 2, y, 2.6))
        bpy.context.object.data.materials.append(LEAF)

# --- light and sky --------------------------------------------------------------------
bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
sun = bpy.context.object
sun.data.energy = 2.2
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-35))
world = bpy.data.worlds.new("w")
scn.world = world
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(215)
except (AttributeError, TypeError):
    pass
nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 0.25

haze = bpy.data.materials.new("haze")
haze.use_nodes = True
hn = haze.node_tree
hn.nodes.remove(hn.nodes["Principled BSDF"])
vol = hn.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.00035
vol.inputs["Color"].default_value = (0.82, 0.87, 0.95, 1)
hn.links.new(vol.outputs[0], hn.nodes["Material Output"].inputs["Volume"])
hb = box("haze", (0, 0, 0), (5000, 5000, 3000), haze)
hb.visible_shadow = False

# --- camera: slow glide down the avenue, easing upward ---------------------------------
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.lens = 32
bpy.ops.object.empty_add(location=(0, 0, 0))
tgt = bpy.context.object
c = cam.constraints.new("TRACK_TO")
c.target = tgt
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
scn.frame_start, scn.frame_end = 1, 250
scn.render.fps = 25
for f, cpos, tpos in [(1, (-80, -165, 42), (-8, -15, 14)), (250, (-40, -85, 78), (12, 35, 10))]:
    cam.location = cpos
    tgt.location = tpos
    cam.keyframe_insert("location", frame=f)
    tgt.keyframe_insert("location", frame=f)
for o in (cam, tgt):
    for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "EASE_IN_OUT"

# --- render settings -----------------------------------------------------------------
r = scn.render
r.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 4
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
r.image_settings.file_format = "PNG"
r.filepath = OUT.rstrip("/") + "/f_"
scn.view_settings.view_transform = "AgX"
scn.view_settings.exposure = -0.3
scn.cycles.use_animated_seed = False
scn.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [
    i.identifier for i in scn.view_settings.bl_rna.properties["look"].enum_items] else "None"
scn.frame_start, scn.frame_end = F0, F1
print("CITY objects:", len(bpy.data.objects))
bpy.ops.render.render(animation=True)
