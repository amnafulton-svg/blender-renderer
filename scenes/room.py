"""Dark room: sunlight through blinds, a mannequin figure typing at an old computer. 10 s, 1080p.
blender -b -P room.py -- <out_dir> F0 F1 samples      (engine from env BL_ENGINE: CYCLES | EEVEE)
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/room"
F0 = int(argv[1]) if len(argv) > 1 else 1
F1 = int(argv[2]) if len(argv) > 2 else 250
SAMPLES = int(argv[3]) if len(argv) > 3 else 32
ENGINE = os.environ.get("BL_ENGINE", "CYCLES").upper()

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, hexc, rough=0.6, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hexc), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(hexc), 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def box(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    o.data.materials.append(m)
    return o


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


def ball(loc, scale, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    smooth(o)
    return o


def limb(a, b, r, m):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    smooth(o)
    ball(a, (r, r, r), m)
    ball(b, (r, r, r), m)
    return o


WALL = mat("wall", "#8d877c", 0.9)
FLOOR = mat("floor", "#4a3a2c", 0.7)
DESK = mat("desk", "#5b4030", 0.5)
SLAT = mat("slat", "#d8d4cc", 0.6)
SKIN = mat("mannequin", "#e9e1d6", 0.45)
CLOTH = mat("cloth", "#3d4a3a", 0.85)
BEIGE = mat("beige", "#cfc6b0", 0.6)
SCREEN = mat("screen", "#9fc4ff", 0.3, emit=4.0)
KEYS = mat("keys", "#bdb5a0", 0.6)
CHAIR = mat("chair", "#2b2b2b", 0.6)

# --- room: x -2..1.6, y -2..2.5, z 0..2.8; window in the +x wall --------------------------------
box((-0.2, 0.25, -0.05), (3.6, 4.5, 0.1), FLOOR)
box((-0.2, 0.25, 2.85), (3.6, 4.5, 0.1), WALL)
box((-2.05, 0.25, 1.4), (0.1, 4.5, 2.8), WALL)
box((-0.2, 2.55, 1.4), (3.6, 0.1, 2.8), WALL)
box((-0.2, -2.05, 1.4), (3.6, 0.1, 2.8), WALL)
WX = 1.65
box((WX, -0.95, 1.4), (0.1, 2.3, 2.8), WALL)        # wall left of the window (y < 0.2)
box((WX, 1.95, 1.4), (0.1, 1.1, 2.8), WALL)         # right of the window (y > 1.4)
box((WX, 0.8, 0.45), (0.1, 1.2, 0.9), WALL)         # below (z < 0.9)
box((WX, 0.8, 2.45), (0.1, 1.2, 0.7), WALL)         # above (z > 2.1)
z = 0.92
while z < 2.1:                                       # tilted blind slats
    box((WX - 0.08, 0.8, z), (0.036, 1.2, 0.004), SLAT, rot=(0, math.radians(-50), 0))
    z += 0.042

# --- desk, computer, chair ----------------------------------------------------------------------
box((0, 0.8, 0.735), (1.6, 0.7, 0.03), DESK)
for lx in (-0.75, 0.75):
    for ly in (0.5, 1.1):
        box((lx, ly, 0.36), (0.04, 0.04, 0.72), DESK)
box((0, 0.98, 0.95), (0.42, 0.38, 0.38), BEIGE)       # CRT body
box((0, 1.12, 0.92), (0.30, 0.25, 0.28), BEIGE)       # CRT back
box((0, 0.789, 0.96), (0.32, 0.004, 0.25), SCREEN)    # glowing screen
box((0, 0.6, 0.762), (0.44, 0.15, 0.025), KEYS)       # keyboard
box((0.45, 0.95, 0.80), (0.18, 0.4, 0.1), BEIGE)      # computer case
box((0, 0, 0.45), (0.46, 0.46, 0.05), CHAIR)
box((0, -0.22, 0.78), (0.46, 0.04, 0.6), CHAIR)
for lx in (-0.2, 0.2):
    for ly in (-0.2, 0.2):
        box((lx, ly, 0.22), (0.03, 0.03, 0.44), CHAIR)

# --- seated mannequin, facing +y, hands on the keyboard -----------------------------------------
ball((0, 0.0, 0.56), (0.17, 0.12, 0.09), CLOTH)                      # pelvis
limb((0, 0.0, 0.6), (0, 0.06, 0.98), 0.13, CLOTH)                   # torso
ball((0, 0.06, 0.92), (0.19, 0.12, 0.15), CLOTH)                     # chest
limb((0, 0.07, 1.06), (0, 0.09, 1.15), 0.045, SKIN)                 # neck
head = ball((0, 0.12, 1.26), (0.085, 0.105, 0.115), SKIN)            # head
for sx in (-1, 1):
    limb((sx * 0.09, 0.0, 0.53), (sx * 0.1, 0.42, 0.53), 0.068, CLOTH)     # thigh
    limb((sx * 0.1, 0.42, 0.53), (sx * 0.1, 0.46, 0.09), 0.052, CLOTH)     # shin
    box((sx * 0.1, 0.52, 0.04), (0.09, 0.22, 0.07), CHAIR)                 # shoe
    limb((sx * 0.19, 0.05, 1.0), (sx * 0.23, 0.24, 0.83), 0.05, CLOTH)     # upper arm
    limb((sx * 0.23, 0.24, 0.83), (sx * 0.14, 0.52, 0.79), 0.04, SKIN)     # forearm
    ball((sx * 0.13, 0.58, 0.785), (0.04, 0.065, 0.022), SKIN)             # hand
# small typing motion: hands bob slightly
for o in [o for o in bpy.data.objects if o.name.startswith("Sphere") and abs(o.location.y - 0.58) < 0.001]:
    for f in range(1, 251, 6):
        o.location.z = 0.785 + (0.006 if (f // 6) % 2 else 0.0)
        o.keyframe_insert("location", frame=f)

# --- light: low sun through the blinds, dim fill, haze in the room ------------------------------
bpy.ops.object.light_add(type="SUN", location=(4, 0.8, 4))
sun = bpy.context.object
sun.data.energy = 9.0
sun.data.angle = math.radians(0.6)
sun.data.color = (1.0, 0.88, 0.72)
sun.rotation_euler = (0, math.radians(62), math.radians(-12))
bpy.ops.object.light_add(type="AREA", location=(-1.2, -1.0, 2.4))
fill = bpy.context.object
fill.data.energy = 6
fill.data.size = 1.5
fill.data.color = (0.55, 0.65, 1.0)
fill.rotation_euler = (math.radians(30), math.radians(-30), 0)
world = bpy.data.worlds.new("w")
scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.95, 1.0, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
haze = bpy.data.materials.new("haze")
haze.use_nodes = True
hn = haze.node_tree
hn.nodes.remove(hn.nodes["Principled BSDF"])
vol = hn.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.22
hn.links.new(vol.outputs[0], hn.nodes["Material Output"].inputs["Volume"])
hz = box((-0.2, 0.25, 1.4), (3.5, 4.4, 2.7), haze)
hz.visible_shadow = False

# --- camera: slow sideways drift, focus on the head ---------------------------------------------
bpy.ops.object.empty_add(location=(0.05, 0.45, 1.0))
tgt = bpy.context.object
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.lens = 32
cam.data.dof.use_dof = True
cam.data.dof.focus_object = head
cam.data.dof.aperture_fstop = 2.8
c = cam.constraints.new("TRACK_TO")
c.target = tgt
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
for f, pos in [(1, (-1.55, -1.25, 1.45)), (250, (-1.0, -1.55, 1.3))]:
    cam.location = pos
    cam.keyframe_insert("location", frame=f)


def setup_render():
    r = scn.render
    r.fps = 25
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.image_settings.file_format = "PNG"
    r.filepath = OUT.rstrip("/") + "/f_"
    scn.view_settings.view_transform = "AgX"
    if ENGINE == "EEVEE":
        r.engine = "BLENDER_EEVEE"
        e = scn.eevee
        e.taa_render_samples = SAMPLES
        for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2),
                     ("volumetric_tile_size", "4"), ("volumetric_samples", 96),
                     ("use_volumetric_shadows", True), ("volumetric_shadow_samples", 32)):
            if hasattr(e, k):
                try:
                    setattr(e, k, v)
                except (TypeError, ValueError):
                    pass
    else:
        r.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = SAMPLES
        scn.cycles.use_denoising = True
        scn.cycles.max_bounces = 4
    scn.frame_start, scn.frame_end = F0, F1


setup_render()
print("ENGINE", scn.render.engine, "objects", len(bpy.data.objects))
bpy.ops.render.render(animation=True)
