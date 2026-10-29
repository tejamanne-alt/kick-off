# Builds the schoolkid in Blender: a smooth skin-modifier body, a rounded head with a painted
# face, soft clumps of hair, a school uniform (shirt, tie, shorts, socks), sneakers and a bag;
# an armature with Unity-friendly bone names; weights; exports FBX. Units: metres, Z up,
# the kid faces -Y, feet at z = 0, about 1.55 m tall.
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix
OUT=sys.argv[sys.argv.index('--')+1]
FACE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'face.png')
bpy.ops.wm.read_factory_settings(use_empty=True)
C=bpy.context
SKIN=(1.0,0.87,0.78,1); SHIRT=(0.97,0.97,0.99,1); SHORTS=(0.2,0.22,0.4,1); SOCK=(0.97,0.97,0.98,1)
HAIR=(0.13,0.1,0.12,1); TIE=(0.78,0.2,0.24,1); SHOE=(0.95,0.95,0.96,1); SOLE=(0.55,0.57,0.62,1); BAG=(0.2,0.28,0.52,1)
WHITE_UV=(0.97,0.03)   # the plain white swatch in the atlas (u, v from the bottom)
PART={'skin':0,'shirt':1,'legwear':2}

def new_obj(name, me):
    o=bpy.data.objects.new(name,me); C.scene.collection.objects.link(o); return o
def activate(o):
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True); C.view_layer.objects.active=o
def apply_mods(o):
    """Apply the object's transform (so mesh coordinates are world coordinates) and its modifiers."""
    activate(o)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
def bake(o):
    activate(o); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

def colorize(o, fn, part_fn=lambda co,c:0, uv_fn=None):
    """Vertex colours (per face corner) from fn(world co) and a part id in UV2.x; UV0 to the white swatch unless uv_fn."""
    me=o.data
    if not me.color_attributes: me.color_attributes.new('Col','BYTE_COLOR','CORNER')
    col=me.color_attributes['Col']
    while len(me.uv_layers)<2: me.uv_layers.new()
    uv0,uv1=me.uv_layers[0],me.uv_layers[1]
    mw=o.matrix_world
    for poly in me.polygons:
        cen=mw@poly.center
        for li in poly.loop_indices:
            v=me.vertices[me.loops[li].vertex_index]; co=mw@v.co
            c=fn(co,cen)
            col.data[li].color=c
            uv0.data[li].uv=uv_fn(co) if uv_fn else WHITE_UV
            uv1.data[li].uv=(part_fn(co,c),0)

# ---------------- body (skin modifier) ----------------
pts={
 'pelvis':((0,0,0.86),(0.11,0.085)),'spine':((0,0.005,0.99),(0.098,0.075)),'chest':((0,0,1.12),(0.112,0.08)),
 'neck0':((0,0.005,1.235),(0.048,0.045)),'neck1':((0,0.01,1.29),(0.043,0.042)),
}
for s,n in((1,'L'),(-1,'R')):
    pts['hip'+n]=((s*0.072,0,0.82),(0.074,0.072)); pts['knee'+n]=((s*0.078,-0.005,0.47),(0.05,0.052))
    pts['calf'+n]=((s*0.078,0.008,0.34),(0.052,0.054)); pts['ankle'+n]=((s*0.078,0.012,0.09),(0.034,0.036))
    pts['shoulder'+n]=((s*0.152,0.0,1.19),(0.046,0.046)); pts['elbow'+n]=((s*0.172,0.0,0.95),(0.035,0.035))
    pts['wrist'+n]=((s*0.178,0.0,0.75),(0.027,0.025)); pts['hand'+n]=((s*0.18,-0.004,0.67),(0.032,0.016))
edges=[('pelvis','spine'),('spine','chest'),('chest','neck0'),('neck0','neck1')]
for n in 'LR':
    edges+= [('pelvis','hip'+n),('hip'+n,'knee'+n),('knee'+n,'calf'+n),('calf'+n,'ankle'+n),('chest','shoulder'+n),('shoulder'+n,'elbow'+n),('elbow'+n,'wrist'+n),('wrist'+n,'hand'+n)]
names=list(pts)
me=bpy.data.meshes.new('body'); me.from_pydata([pts[k][0] for k in names],[(names.index(a),names.index(b)) for a,b in edges],[])
body=new_obj('Body',me)
sk=body.modifiers.new('skin','SKIN'); sk.use_smooth_shade=True; sk.branch_smoothing=0.6
for i,k in enumerate(names):
    body.data.skin_vertices[0].data[i].radius=pts[k][1]
body.data.skin_vertices[0].data[names.index('pelvis')].use_root=True
sub=body.modifiers.new('sub','SUBSURF'); sub.levels=1; sub.render_levels=1
apply_mods(body)
bpy.ops.object.shade_smooth()

# ---------------- clothes cut from the body ----------------
def shell(src,name,keep,offset,flare_fn=None):
    o=src.copy(); o.data=src.data.copy(); o.name=name; C.scene.collection.objects.link(o)
    bm=bmesh.new(); bm.from_mesh(o.data)
    dele=[f for f in bm.faces if not keep(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=dele,context='FACES')
    bm.normal_update()
    for v in bm.verts:
        d=offset+(flare_fn(v.co) if flare_fn else 0)
        v.co+=v.normal*d
    bm.to_mesh(o.data); bm.free()
    return o
def arm_dist(co):
    best=9
    for s in(1,-1):
        a=Vector((s*0.152,0,1.19)); b=Vector((s*0.172,0,0.95))
        ab=b-a; t=max(0,min(1,(co-a).dot(ab)/ab.length_squared)); 
        if abs(co.x)>0.12: best=min(best,t*ab.length if (co-a).dot(ab)>0 else 0)
    return best
shirt=shell(body,'Shirt',lambda c: c.z>0.9 and c.z<1.245 and (abs(c.x)<0.14 or arm_dist(c)<0.12),0.013,
    lambda c: 0.012 if (abs(c.x)>0.13 and arm_dist(c)>0.09) else (0.008 if c.z<0.93 else 0))
shorts=shell(body,'Shorts',lambda c: c.z>0.6 and c.z<0.96 and abs(c.x)<0.135,0.018,lambda c: 0.022*max(0,(0.7-c.z)/0.1))
apply_mods(shirt); apply_mods(shorts)
for o in (shirt,shorts): activate(o); bpy.ops.object.shade_smooth()
# collar and tie
bpy.ops.mesh.primitive_torus_add(major_radius=0.055,minor_radius=0.014,location=(0,0.004,1.245)); collar=C.object; collar.scale=(1,0.92,0.9); collar.name='Collar'; bake(collar)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-0.088,1.08)); tie=C.object; tie.scale=(0.032,0.008,0.16); tie.name='Tie'
bake(tie); tb=tie.modifiers.new('b','BEVEL'); tb.width=0.006; tb.segments=2
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.017,location=(0,-0.08,1.222)); knot=C.object; knot.scale=(1.1,0.6,0.9); knot.name='Knot'
for o in(collar,tie,knot): apply_mods(o); activate(o); bpy.ops.object.shade_smooth()
# the tie follows the chest and hangs forward a little lower down
for v in tie.data.vertices:
    v.co.y-=0.012*max(0,(1.15-v.co.z)/0.2)

# ---------------- head ----------------
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=22,radius=0.15,location=(0,-0.005,1.425)); head=C.object; head.name='Head'
head.scale=(1.0,1.02,1.08); bake(head)
for v in head.data.vertices:
    co=v.co
    if co.z<1.42:   # cheeks and a softly pointed chin
        t=min(1,(1.42-co.z)/0.16)
        co.x*=1-0.32*t*t; co.y=co.y*(1-0.18*t)-0.012*t
    if co.y>0.06: co.y-=0.015*min(1,(co.y-0.06)/0.08)   # flatter back of the head
sub=head.modifiers.new('sub','SUBSURF'); sub.levels=1; apply_mods(head); activate(head); bpy.ops.object.shade_smooth()
# ears and nose
ears=[]
for s in(1,-1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,location=(s*0.142,0.01,1.41)); e=C.object; e.scale=(0.45,0.8,1.15); bake(e); ears.append(e)
for e in ears: apply_mods(e); activate(e); bpy.ops.object.shade_smooth()

# ---------------- hair: a smooth cap and soft clumps ----------------
hair_parts=[]
bpy.ops.mesh.primitive_uv_sphere_add(segments=30,ring_count=20,radius=0.162,location=(0,0.0,1.44)); cap=C.object; cap.scale=(1.03,1.05,1.07); bake(cap)
bm=bmesh.new(); bm.from_mesh(cap.data)
def keep_cap(c):
    d=(c-Vector((0,0,1.44))).normalized()
    front=max(0,-d.y)  # facing the front
    thr=0.34-1.1*(1-front)**1.3*0.9
    return d.z>thr
bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep_cap(f.calc_center_median())],context='FACES'); bm.to_mesh(cap.data); bm.free()
s=cap.modifiers.new('solid','SOLIDIFY'); s.thickness=0.012; s.offset=1; s.use_rim_only=False
hair_parts.append(cap)
def lock(loc,scale,rot):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=loc,rotation=rot); o=C.object; o.scale=scale
    # taper to a soft point at the bottom
    for v in o.data.vertices:
        if v.co.z<0: v.co.x*=1+v.co.z*0.75; v.co.y*=1+v.co.z*0.75
    hair_parts.append(o); return o
for i,x in enumerate([-0.1,-0.05,0.0,0.05,0.1]):   # fringe, ending above the brows
    lock((x,-0.14+abs(x)*0.3,1.548-abs(x)*0.25),(0.04,0.022,0.058),(math.radians(-22),math.radians(x*120),0))
for s in(1,-1):   # sides over the ears, and the back
    lock((s*0.148,-0.03,1.43),(0.03,0.05,0.085),(0,math.radians(s*8),0))
    lock((s*0.12,0.09,1.39),(0.05,0.05,0.09),(math.radians(15),0,0))
lock((0,0.13,1.36),(0.09,0.05,0.1),(math.radians(20),0,0))
lock((0.02,-0.02,1.615),(0.05,0.03,0.035),(math.radians(-30),0,math.radians(20)))   # a little tuft
for o in hair_parts: apply_mods(o); activate(o); bpy.ops.object.shade_smooth()

# ---------------- shoes and bag ----------------
shoes=[]
for s in(1,-1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(s*0.078,-0.03,0.045)); sh=C.object; sh.scale=(0.088,0.21,0.09)
    bake(sh)
    b=sh.modifiers.new('b','BEVEL'); b.width=0.035; b.segments=3; sb=sh.modifiers.new('s','SUBSURF'); sb.levels=1
    apply_mods(sh); activate(sh); bpy.ops.object.shade_smooth()
    for v in sh.data.vertices:   # a rounded, lower toe
        f=max(0,(-0.03-v.co.y)/0.1)
        if f>0: v.co.z=0.0+(v.co.z-0.0)*(1-0.3*f)
    shoes.append(sh)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0.135,0.9)); bag=C.object; bag.scale=(0.26,0.075,0.2); bag.name='Bag'; bake(bag)
b=bag.modifiers.new('b','BEVEL'); b.width=0.03; b.segments=3; apply_mods(bag); activate(bag); bpy.ops.object.shade_smooth()
# strap: a flat band from the bag over the right shoulder and across the chest
curve=bpy.data.curves.new('strap','CURVE'); curve.dimensions='3D'; curve.bevel_depth=0.0; curve.extrude=0.018
spl=curve.splines.new('NURBS'); path=[(0.11,0.12,0.98),(0.13,0.1,1.12),(0.1,0.03,1.255),(0.0,-0.11,1.12),(-0.11,-0.1,0.98),(-0.13,0.0,0.9),(-0.11,0.11,0.95)]
spl.points.add(len(path)-1)
for p,c in zip(spl.points,path): p.co=(c[0],c[1],c[2],1)
spl.use_endpoint_u=True; spl.order_u=3
strap=new_obj('Strap',curve); activate(strap); bpy.ops.object.convert(target='MESH')
s=strap.modifiers.new('solid','SOLIDIFY'); s.thickness=0.006; apply_mods(strap)

# ---------------- colours, UVs, part ids ----------------
def face_uv(co):
    u=co.x/0.34+0.5; v=(co.z-1.27)/0.34
    return (u*0.5, 0.5+v*0.5)
colorize(body,lambda co,c: SOCK if co.z<0.33 else SKIN,lambda co,c: 0)
colorize(head,lambda co,c: (1,1,1,1),uv_fn=face_uv)
for e in ears: colorize(e,lambda co,c: SKIN)
colorize(shirt,lambda co,c: SHIRT,lambda co,c: 1)
colorize(shorts,lambda co,c: tuple(x*0.75 for x in SHORTS[:3])+(1,) if co.z<0.635 or co.z>0.94 else SHORTS,lambda co,c: 2)
colorize(collar,lambda co,c: SHIRT,lambda co,c: 1)
for o in(tie,knot): colorize(o,lambda co,c: TIE)
def hair_col(co,c):
    d=(co-Vector((0,0,1.44)))
    shine=0.44<d.normalized().z<0.6 and d.y>-0.05
    return (0.3,0.26,0.3,1) if shine else HAIR
for o in hair_parts: colorize(o,hair_col)
for sh in shoes: colorize(sh,lambda co,c: SOLE if co.z<0.03 else (SHOE if co.z>0.05 or co.y<-0.08 else (0.35,0.45,0.75,1)))
colorize(bag,lambda co,c: BAG if co.y>0.1 or co.z<0.95 else tuple(min(1,x*1.15) for x in BAG[:3])+(1,))
colorize(strap,lambda co,c: (0.2,0.26,0.48,1))

# ---------------- armature ----------------
arm=bpy.data.armatures.new('Rig'); rig=new_obj('KidRig',arm); activate(rig); bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
def bone(n,h,t,parent=None):
    b=eb.new(n); b.head=h; b.tail=t
    if parent: b.parent=eb[parent]; 
    return b
bone('Hips',(0,0,0.86),(0,0,0.98)); bone('Spine',(0,0,0.98),(0,0,1.12),'Hips'); bone('Chest',(0,0,1.12),(0,0,1.235),'Spine')
bone('Neck',(0,0.005,1.235),(0,0.008,1.3),'Chest'); bone('Head',(0,0.008,1.3),(0,0.008,1.6),'Neck')
for s,n in((1,'L'),(-1,'R')):
    bone('UpperLeg.'+n,(s*0.072,0,0.82),(s*0.078,-0.005,0.47),'Hips')
    bone('LowerLeg.'+n,(s*0.078,-0.005,0.47),(s*0.078,0.012,0.09),'UpperLeg.'+n)
    bone('Foot.'+n,(s*0.078,0.012,0.09),(s*0.078,-0.12,0.03),'LowerLeg.'+n)
    bone('UpperArm.'+n,(s*0.152,0,1.19),(s*0.172,0,0.95),'Chest')
    bone('LowerArm.'+n,(s*0.172,0,0.95),(s*0.178,0,0.75),'UpperArm.'+n)
    bone('Hand.'+n,(s*0.178,0,0.75),(s*0.18,-0.004,0.64),'LowerArm.'+n)
bone('Bag',(0,0.1,1.02),(0,0.13,0.9),'Hips')
for b in eb: b.roll=0
bpy.ops.object.mode_set(mode='OBJECT')

# Body weights from bone heat; everything else follows the body or takes one bone.
activate(body); rig.select_set(True); C.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
def rigid(o,bname):
    vg=o.vertex_groups.new(name=bname); vg.add(range(len(o.data.vertices)),1.0,'REPLACE')
    o.parent=rig; m=o.modifiers.new('arm','ARMATURE'); m.object=rig
def transfer(o):
    m=o.modifiers.new('dt','DATA_TRANSFER'); m.object=body; m.use_vert_data=True; m.data_types_verts={'VGROUP_WEIGHTS'}
    m.vert_mapping='POLYINTERP_NEAREST'; m.layers_vgroup_select_src='ALL'; m.layers_vgroup_select_dst='NAME'
    activate(o); bpy.ops.object.datalayout_transfer(modifier=m.name); bpy.ops.object.modifier_apply(modifier=m.name)
    o.parent=rig; a=o.modifiers.new('arm','ARMATURE'); a.object=rig
for o in(shirt,shorts,collar,tie,knot,strap): transfer(o)
for o in [head]+ears+hair_parts: rigid(o,'Head')
for s,sh in zip('LR',shoes): rigid(sh,'Foot.'+s)
rigid(bag,'Bag')

# Join everything into one skinned mesh with the atlas material.
parts=[body,shirt,shorts,collar,tie,knot,strap,head,bag]+ears+hair_parts+shoes
mat=bpy.data.materials.new('Kid'); mat.use_nodes=True
nt=mat.node_tree; bsdf=nt.nodes['Principled BSDF']; tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(FACE)
vc=nt.nodes.new('ShaderNodeVertexColor'); mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs['Factor'].default_value=1
nt.links.new(tex.outputs['Color'],mul.inputs['A']); nt.links.new(vc.outputs['Color'],mul.inputs['B']); nt.links.new(mul.outputs['Result'],bsdf.inputs['Base Color'])
for o in parts:
    o.data.materials.clear(); o.data.materials.append(mat)
for x in C.scene.objects: x.select_set(False)
for o in parts: o.select_set(True)
C.view_layer.objects.active=body; bpy.ops.object.join(); kid=C.object; kid.name='Kid'
# keep only one armature modifier
mods=[m for m in kid.modifiers if m.type=='ARMATURE']
for m in mods[1:]: kid.modifiers.remove(m)
mods[0].object=rig
print('verts',len(kid.data.vertices),'tris',sum(len(p.vertices)-2 for p in kid.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace('.fbx','.blend'))
for x in C.scene.objects: x.select_set(False)
kid.select_set(True); rig.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT,use_selection=True,apply_scale_options='FBX_SCALE_ALL',add_leaf_bones=False,
    bake_anim=False,mesh_smooth_type='FACE',use_mesh_modifiers=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP')
print('exported')
