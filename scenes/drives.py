"""Hard drives on a wooden table: slow push-in, shallow focus. 10 s, 1080p.
blender -b -P drives.py -- <out_dir> F0 F1 samples      (engine from env BL_ENGINE: CYCLES | EEVEE)
"""
import math
import os
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/drives"
F0 = int(argv[1]) if len(argv) > 1 else 1
F1 = int(argv[2]) if len(argv) > 2 else 250
SAMPLES = int(argv[3]) if len(argv) > 3 else 32
ENGINE = os.environ.get("BL_ENGINE", "CYCLES").upper()

random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, hexc, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hexc), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def box(loc, size, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    o.data.materials.append(m)
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        mod = o.modifiers.new("b", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    if parent:
        o.parent = parent
    return o


# --- wooden table (procedural grain) ----------------------------------------------------
wood = bpy.data.materials.new("wood")
wood.use_nodes = True
nt = wood.node_tree
bsdf = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.0, 0.15, 1.0)
wave = nt.nodes.new("ShaderNodeTexWave")
wave.wave_type = "BANDS"
wave.bands_direction = "X"
wave.inputs["Scale"].default_value = 45.0
wave.inputs["Distortion"].default_value = 6.0
wave.inputs["Detail"].default_value = 6.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (*lin("#3a2414"), 1)
ramp.color_ramp.elements[1].color = (*lin("#7a4e2a"), 1)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.45
bpy.ops.mesh.primitive_plane_add(size=3)
bpy.context.object.data.materials.append(wood)

ALU = mat("alu", "#b9bcbf", 0.35, 1.0)
DARK = mat("dark", "#2a2c2e", 0.5, 0.6)
LABEL = mat("label", "#f2f2ee", 0.5)
GREEN = mat("green", "#4caf50", 0.5)
PCB = mat("pcb", "#1f5c35", 0.4)
CHIP = mat("chip", "#111111", 0.3)
INK = mat("ink", "#222222", 0.6)
GRAIN = mat("grain", "#5a3d26", 0.9)


def drive(x, y, rz, z=0.0, flipped=False):
    """3.5-inch drive, ~147 x 101 x 26 mm, built around an empty so it moves as one piece."""
    bpy.ops.object.empty_add(location=(x, y, z + 0.013))
    root = bpy.context.object
    root.rotation_euler = (math.pi if flipped else 0, 0, rz)
    box((0, 0, 0), (0.147, 0.101, 0.024), ALU, parent=root, bevel=0.002)
    box((0, 0, 0.0122), (0.140, 0.094, 0.001), ALU, parent=root)                 # top cover plate
    box((0.006, 0, 0.0128), (0.092, 0.072, 0.0004), LABEL, parent=root)          # white label
    box((0.006, 0.026, 0.0131), (0.092, 0.018, 0.0004), GREEN, parent=root)      # green band
    bpy.ops.object.text_add(location=(-0.03, -0.012, 0.0134))
    t = bpy.context.object
    t.data.body = "2TB  SATA 6Gb/s"
    t.data.size = 0.008
    t.data.materials.append(INK)
    t.parent = root
    for k in range(4):                                                           # barcode lines
        box((-0.025 + k * 0.004, -0.026, 0.0132), (0.0015, 0.012, 0.0003), INK, parent=root)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0025, depth=0.001,
                                                location=(sx * 0.066, sy * 0.042, 0.0128))
            s = bpy.context.object
            s.data.materials.append(DARK)
            s.parent = root
    box((0, 0, -0.0125), (0.11, 0.09, 0.0016), PCB, parent=root)                  # board underneath
    for cx, cy, w in ((0.02, 0.01, 0.02), (-0.03, -0.02, 0.012), (0.035, -0.025, 0.01)):
        box((cx, cy, -0.0137), (w, w, 0.0015), CHIP, parent=root)
    box((0.073, 0, -0.002), (0.003, 0.05, 0.008), DARK, parent=root)             # SATA connector
    return root


drive(0.00, 0.00, math.radians(12))
drive(0.17, 0.05, math.radians(-25), flipped=True)
drive(-0.15, 0.09, math.radians(70))
drive(-0.05, -0.15, math.radians(-8))
drive(-0.045, -0.145, math.radians(-2), z=0.026)                                   # stacked on top
for _ in range(500):                                                              # dust and crumbs
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.0006, 0.002),
                                          location=(random.uniform(-0.4, 0.4), random.uniform(-0.35, 0.35), 0.0005))
    bpy.context.object.data.materials.append(GRAIN)

# --- light ---------------------------------------------------------------------------------
bpy.ops.object.light_add(type="AREA", location=(-0.6, -0.3, 0.9))
key = bpy.context.object
key.data.energy = 35
key.data.size = 0.6
key.data.color = (1.0, 0.85, 0.68)
key.rotation_euler = (math.radians(35), math.radians(-30), 0)
bpy.ops.object.light_add(type="AREA", location=(0.7, 0.5, 0.6))
fill = bpy.context.object
fill.data.energy = 8
fill.data.size = 1.0
fill.data.color = (0.7, 0.8, 1.0)
fill.rotation_euler = (math.radians(-40), math.radians(45), 0)
world = bpy.data.worlds.new("w")
scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.018, 0.016, 1)

# --- camera: slow push-in with a slight turn, shallow focus ---------------------------------
bpy.ops.object.empty_add(location=(0, 0, 0.01))
tgt = bpy.context.object
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.lens = 50
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 2.0
c = cam.constraints.new("TRACK_TO")
c.target = tgt
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
for f, pos, tp in [(1, (-0.25, -0.62, 0.55), (0.0, 0.02, 0.01)), (250, (-0.12, -0.38, 0.36), (-0.02, -0.03, 0.015))]:
    cam.location = pos
    tgt.location = tp
    cam.keyframe_insert("location", frame=f)
    tgt.keyframe_insert("location", frame=f)


# --- render ------------------------------------------------------------------------------
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
        for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2)):
            if hasattr(e, k):
                setattr(e, k, v)
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
