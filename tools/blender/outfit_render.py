# Renders a character as the game colours it in a shop outfit, flat (no lighting), from four sides: ModelOutfit's recolour
# (each vertex of parts 1 and 2 takes the outfit's colour times its brightness against the model's default; part 0 and the
# hair keep theirs) times the atlas. Faces left out of a garment, or tagged with one they don't belong to, show at once
# in an outfit that isn't the character's own; in its own colours they are invisible (docs/LEARNINGS.md C22).
#   blenv/bin/python outfit_render.py -- <Name>.fbx <Name>Atlas.png <Name>.json /abs/out [top r,g,b,legwear r,g,b]
#     -> /abs/out.png (front, side, back, side). The default outfit is the shop's Holiday kit (a teal top, khaki shorts).
#   MODE=parts      each face by its outfit part (UV2.x): 0 white, 1 red, 2 blue, 3 green, 4 yellow
#   MODE=default    the character's own colours
#   HEAD=1          a close-up of the head
# Cycles on the CPU (no GPU needed), a few samples.
import bpy, sys, os, json, math
import numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
FBX, ATLAS, JSON, OUT = argv[:4]
OUTFIT = [float(x) for x in (argv[4] if len(argv)>4 else '0.16,0.72,0.82,0.82,0.72,0.5').split(',')]
MODE = os.environ.get('MODE','outfit')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX, axis_forward='-Z', axis_up='Y')
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name!='Kid': bpy.data.objects.remove(o)
kid = bpy.data.objects['Kid']; me = kid.data
d = json.load(open(JSON))
def lin(c): c=np.asarray(c,float); return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
default = {1: np.array(d['top']), 2: np.array(d['legwear']), 3: np.array(d['hair']), 4: np.array(d.get('accent',[0.78,0.2,0.24]))}
want = {1: np.array(OUTFIT[:3]), 2: np.array(OUTFIT[3:6])}
col = me.color_attributes['Col']
n = len(me.loops)
cd = np.zeros(n*4); col.data.foreach_get('color', cd); cd = cd.reshape(-1,4)
# Unity reads FBX vertex colours as sRGB bytes; Blender's BYTE_COLOR 'color' is linear: convert to the stored sRGB values
srgb = np.where(cd[:,:3]<=0.0031308, cd[:,:3]*12.92, 1.055*np.power(np.maximum(cd[:,:3],0),1/2.4)-0.055)
u1 = np.zeros(n*2); me.uv_layers[1].data.foreach_get('uv', u1); part = np.round(u1.reshape(-1,2)[:,0]).astype(int)
new = srgb.copy()
if MODE=='parts':
    pal = {0:(1,1,1),1:(1,0,0),2:(0,0.2,1),3:(0,0.8,0),4:(1,0.9,0)}
    for q,c in pal.items(): new[part==q] = c
elif MODE=='default': pass
else:
    for q,c in want.items():
        m = part==q
        k = srgb[m].sum(1) / max(0.01, default[q].sum())
        new[m] = np.clip(c[None,:]*k[:,None],0,1)
lin_new = np.where(new<=0.04045,new/12.92,((new+0.055)/1.055)**2.4)
a = me.color_attributes.new('Show','FLOAT_COLOR','CORNER')
a.data.foreach_set('color', np.concatenate([lin_new, np.ones((n,1))],1).ravel())
mat = bpy.data.materials.new('m'); mat.use_nodes=True; nt=mat.node_tree
for x in list(nt.nodes):
    if x.type!='OUTPUT_MATERIAL': nt.nodes.remove(x)
vc = nt.nodes.new('ShaderNodeAttribute'); vc.attribute_name='Show'
em = nt.nodes.new('ShaderNodeEmission')
if MODE=='parts':
    nt.links.new(vc.outputs['Color'], em.inputs['Color'])
else:
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(ATLAS); tx.interpolation='Closest'
    uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = me.uv_layers[0].name; nt.links.new(uv.outputs[0], tx.inputs[0])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs['Factor'].default_value=1
    nt.links.new(vc.outputs['Color'], mul.inputs['A']); nt.links.new(tx.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
me.materials.clear(); me.materials.append(mat)
S = bpy.context.scene; S.render.engine='CYCLES'; S.cycles.samples=4; S.cycles.use_denoising=False; S.cycles.device='CPU'; S.view_settings.view_transform='Standard'
S.world = bpy.data.worlds.new('w'); S.world.color=(0.35,0.35,0.38)
S.render.resolution_x, S.render.resolution_y = 700, 1100
co = np.array([(kid.matrix_world@v.co)[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0); c=(lo+hi)/2; H=hi[2]-lo[2]
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale = H*1.05
if os.environ.get('HEAD'):
    cam.data.ortho_scale = H*0.16; c = c.copy(); c[2] = hi[2]-H*0.08; S.render.resolution_x = S.render.resolution_y = 900
from mathutils import Vector
from PIL import Image
tiles=[]
for i,yaw in enumerate((0,90,180,270)):
    a_ = math.radians(yaw); dvec = Vector((math.sin(a_), -math.cos(a_), 0))
    cam.location = Vector(c) + dvec*5; cam.rotation_euler = (math.radians(90),0,a_)
    S.render.filepath = OUT+'_%d.png'%i; bpy.ops.render.render(write_still=True); tiles.append(Image.open(S.render.filepath))
rx,ry=S.render.resolution_x,S.render.resolution_y
W = Image.new('RGB',(rx*4,ry)); [W.paste(t.convert('RGB'),(rx*i,0)) for i,t in enumerate(tiles)]; W.save(OUT+'.png')
[os.remove(OUT+'_%d.png'%i) for i in range(4)]
