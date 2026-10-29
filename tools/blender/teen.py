# Builds one of the two playable teens in Blender (original characters in a Ghibli-like style):
#   --boy   a lean teen in a white open-collared shirt with rolled sleeves, dark trousers,
#           sneakers and a satchel; short, messy dark hair
#   --girl  a slender teen in a short-sleeved coral dress with a belt, white socks and brown
#           shoes and a satchel; wavy, shoulder-length auburn hair
# Same pipeline as kid.py: skin-modifier body, painted face atlas, soft hair clumps, armature
# with the same bone names (plus Nose), weights, FBX. Metres, Z up, facing -Y, feet at z = 0.
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix
OUT=sys.argv[sys.argv.index('--')+1]
GIRL='--girl' in sys.argv
ADULT=False
HERE=os.path.dirname(os.path.abspath(__file__))
FACE=os.path.join(HERE,'face_girl.png' if GIRL else 'face_boy.png')
bpy.ops.wm.read_factory_settings(use_empty=True)
C=bpy.context
SKIN=(1.0,0.89,0.8,1) if GIRL else (0.97,0.83,0.71,1)
SHIRT=(0.86,0.4,0.42,1) if GIRL else (0.97,0.97,0.95,1)      # her dress / his shirt
SHORTS=(0.24,0.28,0.38,1)                                      # his trousers
SOCK=(0.97,0.97,0.98,1)
HAIR=(0.5,0.22,0.14,1) if GIRL else (0.09,0.065,0.07,1)
HAIR_SHINE=(0.72,0.4,0.28,1) if GIRL else (0.24,0.2,0.22,1)
SHOE=(0.42,0.26,0.18,1) if GIRL else (0.3,0.31,0.35,1)
SOLE=(0.25,0.16,0.12,1) if GIRL else (0.95,0.95,0.95,1)
BAG=(0.66,0.5,0.32,1)
WHITE_UV=(0.97,0.03)
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
    """How far down the arm (shoulder to wrist) a point is; 9 if it is not on an arm."""
    best=9
    for s in(1,-1):
        chain=[Vector((s*0.152,0,1.19)),Vector((s*0.172,0,0.95)),Vector((s*0.178,0,0.75))]
        run=0
        for a,b in zip(chain,chain[1:]):
            ab=b-a; t=(co-a).dot(ab)/ab.length_squared
            if abs(co.x)>0.12 and -0.2<=t<=1.0 and (co-(a+ab*max(0,t))).length<0.08:
                best=min(best,run+max(0,t)*ab.length)
            run+=ab.length
    return best

def on_torso(c): return c.z>0.9 and c.z<1.245 and abs(c.x)<0.14
clothes=[]
if GIRL:
    # Dress bodice with short, slightly puffed sleeves...
    shirt=shell(body,'Dress',lambda c: c.z<1.245 and ((c.z>0.84 and abs(c.x)<0.14) or arm_dist(c)<0.1),0.012,
        lambda c: 0.01 if (abs(c.x)>0.13 and arm_dist(c)>0.06) else 0)
    # ...and a skirt that flares from the waist to just above the knee.
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=1,depth=1,end_fill_type='NOTHING',location=(0,0.005,0.76))
    skirt=C.object; skirt.name='Skirt'; bake(skirt)
    for v in skirt.data.vertices:
        t=(0.5-v.co.z+0.76)          # 0 at the waist, 1 at the hem
        t=max(0,min(1,(0.93-v.co.z)/0.35))
        v.co.x*=0.118+0.09*t; v.co.y=(v.co.y-0.005)*(0.092+0.075*t)+0.005
        v.co.z=0.93-0.35*t
    sk=skirt.modifiers.new('sub','SUBSURF'); sk.levels=1
    so=skirt.modifiers.new('solid','SOLIDIFY'); so.thickness=0.008; so.offset=1
    shorts=None
    bpy.ops.mesh.primitive_torus_add(major_radius=1,minor_radius=0.1,location=(0,0.005,0.93)); belt=C.object; belt.scale=(0.125,0.098,0.14); belt.name='Belt'
    clothes=[skirt,belt]
else:
    # Open-collared shirt with the sleeves rolled to just below the elbow, tucked into trousers.
    shirt=shell(body,'Shirt',lambda c: c.z<1.245 and ((c.z>0.9 and abs(c.x)<0.14) or arm_dist(c)<0.27),0.013,
        lambda c: 0.006 if (abs(c.x)>0.13 and arm_dist(c)>0.22) else 0)
    shorts=shell(body,'Trousers',lambda c: c.z>0.07 and c.z<0.96 and abs(c.x)<0.135,0.016)
    for s in(1,-1):   # the rolled cuffs
        a=Vector((s*0.172,0,0.95)); b=Vector((s*0.178,0,0.75)); p=a+(b-a)*0.12
        bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=0.047,depth=0.045,location=p)
        cuff=C.object; cuff.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); cuff.name='Cuff'
        b2=cuff.modifiers.new('b','BEVEL'); b2.width=0.01; b2.segments=2
        clothes.append(cuff)
apply_mods(shirt)
if shorts: apply_mods(shorts)
for o in [shirt]+([shorts] if shorts else []): activate(o); bpy.ops.object.shade_smooth()
for o in clothes: apply_mods(o); activate(o); bpy.ops.object.shade_smooth()
# Collar: a soft band round the neck.
bpy.ops.mesh.primitive_torus_add(major_radius=0.056,minor_radius=0.013,location=(0,0.004,1.245)); collar=C.object; collar.scale=(1,0.92,0.85); collar.name='Collar'; bake(collar)
apply_mods(collar); activate(collar); bpy.ops.object.shade_smooth()

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


# ---------------- hair ----------------
hair_parts=[]
bpy.ops.mesh.primitive_uv_sphere_add(segments=30,ring_count=20,radius=0.162,location=(0,0.0,1.44)); cap=C.object; cap.scale=(1.04,1.06,1.07); bake(cap)
bm=bmesh.new(); bm.from_mesh(cap.data)
def keep_cap(c):
    d=(c-Vector((0,0,1.44))).normalized()
    front=max(0,-d.y)
    thr=(0.3 if GIRL else 0.36)-1.1*(1-front)**1.3*0.9
    return d.z>thr
bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep_cap(f.calc_center_median())],context='FACES'); bm.to_mesh(cap.data); bm.free()
s=cap.modifiers.new('solid','SOLIDIFY'); s.thickness=0.012; s.offset=1
hair_parts.append(cap)
def lock(loc,scale,rot,wave=0.0,point=0.75):
    """A clump of hair: a stretched sphere tapering to a point at its lower end, optionally wavy."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=10,radius=1,location=loc,rotation=rot); o=C.object; o.scale=scale
    for v in o.data.vertices:
        if v.co.z<0: v.co.x*=1+v.co.z*point; v.co.y*=1+v.co.z*point
        if wave: v.co.x+=wave*math.sin(v.co.z*4.5)
    hair_parts.append(o); return o
R=math.radians
if GIRL:
    # Soft, side-swept fringe off a centre parting.
    for s in(1,-1):
        lock((s*0.055,-0.142,1.53),(0.06,0.024,0.06),(R(-25),R(s*25),R(s*35)))
        lock((s*0.105,-0.11,1.49),(0.04,0.024,0.08),(R(-15),R(s*40),R(s*20)))
    # Wavy locks falling to the shoulders all round the sides and back, flicking out at the ends.
    for i in range(11):
        a=R(-75+i*15)                      # from one side round the back to the other
        x=math.sin(a)*0.155; y=math.cos(a)*0.12+0.02
        tilt=R(12+abs(math.sin(a))*6)
        lock((x*1.08,y,1.3),(0.05,0.042,0.2),(R(18)*math.cos(a),-math.sin(a)*R(18),0),wave=0.12,point=0.5)
        lock((x*1.25,y*1.1,1.16),(0.04,0.035,0.07),(R(10),0,(1 if x>0 else -1)*R(40)),wave=0,point=0.6)
    for s in(1,-1):                        # locks framing the face, in front of the ears
        lock((s*0.14,-0.06,1.33),(0.035,0.03,0.17),(R(-5),0,R(s*6)),wave=0.1,point=0.6)
else:
    # Messy short hair: a fringe of pointed locks falling to the right, tufts over the ears,
    # spikes at the crown and the nape.
    for i,x in enumerate([-0.1,-0.055,-0.01,0.035,0.08]):
        lock((x,-0.145+abs(x)*0.3,1.535-abs(x+0.02)*0.25),(0.05,0.026,0.072),(R(-22),R(x*100),R(-12+i*4)),point=0.7)
    for s in(1,-1):
        lock((s*0.152,-0.03,1.43),(0.03,0.045,0.07),(0,R(s*10),R(s*8)),point=1.0)
        lock((s*0.13,0.06,1.4),(0.045,0.045,0.08),(R(20),0,R(s*15)),point=1.0)
    for i,(x,y) in enumerate([(-0.05,0.06),(0.03,0.08),(0.07,0.0),(-0.08,-0.02)]):
        lock((x,y,1.6),(0.035,0.03,0.07),(R(-160+i*15),R(x*200),0),point=1.0)
    for x in(-0.06,0.0,0.06):
        lock((x,0.14,1.37),(0.04,0.03,0.07),(R(25),0,R(x*150)),point=1.0)
for o in hair_parts: apply_mods(o); activate(o); bpy.ops.object.shade_smooth()

# ---------------- shoes and bag ----------------
shoes=[]
for s in(1,-1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(s*0.078,-0.03,0.045)); sh=C.object; sh.scale=(0.085,0.2,0.085 if GIRL else 0.09)
    bake(sh)
    b=sh.modifiers.new('b','BEVEL'); b.width=0.035; b.segments=3; sb=sh.modifiers.new('s','SUBSURF'); sb.levels=1
    apply_mods(sh); activate(sh); bpy.ops.object.shade_smooth()
    for v in sh.data.vertices:
        f=max(0,(-0.03-v.co.y)/0.1)
        if f>0: v.co.z=v.co.z*(1-0.3*f)
    shoes.append(sh)
# A canvas satchel on the back of the hip, its strap over the shoulder and across the chest.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0.0,0.13,0.9)); bag=C.object; bag.scale=(0.24,0.07,0.19); bag.name='Bag'; bake(bag)
b=bag.modifiers.new('b','BEVEL'); b.width=0.03; b.segments=3; apply_mods(bag); activate(bag); bpy.ops.object.shade_smooth()
curve=bpy.data.curves.new('strap','CURVE'); curve.dimensions='3D'; curve.extrude=0.016
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
colorize(body,lambda co,c: SOCK if (GIRL and co.z<0.3) else SKIN,lambda co,c: 0)
colorize(head,lambda co,c: (1,1,1,1),uv_fn=face_uv)
for e in ears: colorize(e,lambda co,c: SKIN)
colorize(shirt,lambda co,c: SHIRT,lambda co,c: 1)
if shorts: colorize(shorts,lambda co,c: tuple(x*0.8 for x in SHORTS[:3])+(1,) if co.z<0.1 else SHORTS,lambda co,c: 2)
for o in clothes:
    if o.name.startswith('Skirt'): colorize(o,lambda co,c: tuple(x*0.85 for x in SHIRT[:3])+(1,) if co.z<0.6 else SHIRT,lambda co,c: 1)
    elif o.name.startswith('Belt'): colorize(o,lambda co,c: (0.8,0.66,0.42,1))
    else: colorize(o,lambda co,c: SHIRT,lambda co,c: 1)
colorize(collar,lambda co,c: (0.97,0.95,0.92,1) if GIRL else SHIRT,lambda co,c: 0 if GIRL else 1)
def hair_col(co,c):
    d=(co-Vector((0,0,1.44)))
    shine=0.42<d.normalized().z<0.6 and d.y>-0.05 and d.length<0.2
    return HAIR_SHINE if shine else HAIR
for o in hair_parts: colorize(o,hair_col,lambda co,c: 3)
for sh in shoes: colorize(sh,lambda co,c: SOLE if co.z<0.025 else SHOE)
colorize(bag,lambda co,c: BAG if co.y>0.1 or co.z<0.95 else tuple(x*0.85 for x in BAG[:3])+(1,))
colorize(strap,lambda co,c: tuple(x*0.75 for x in BAG[:3])+(1,))

# ---------------- teen proportions ----------------
LEG,TORSO,WIDTH=(1.1,1.05,0.95) if GIRL else (1.15,1.12,1.05)
def grow(co):
    x,y,z=co
    if z<0.86: nz=z*LEG
    elif z<1.24: nz=0.86*LEG+(z-0.86)*TORSO
    else: nz=0.86*LEG+0.38*TORSO+(z-1.24)*0.97
    w=1.0 if z>1.24 else WIDTH
    return Vector((x*w,y*(1.0 if z>1.24 else WIDTH),nz))
movable=[body,shirt,collar,head,bag,strap]+([shorts] if shorts else [])+clothes+ears+hair_parts+shoes
for o in movable:
    for v in o.data.vertices: v.co=grow(o.matrix_world@v.co)
    o.matrix_world=Matrix()

# ---------------- armature ----------------
arm=bpy.data.armatures.new('Rig'); rig=new_obj('KidRig',arm); activate(rig); bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
def bone(n,h,t,parent=None):
    b=eb.new(n); b.head=grow(Vector(h)); b.tail=grow(Vector(t))
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
# A marker in front of the face (no weights) so the game can tell which way the model faces.
bone('Nose',(0,-0.2,1.42),(0,-0.26,1.42),'Head')
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
for o in [shirt,collar,strap]+([shorts] if shorts else [])+[c for c in clothes if not c.name.startswith(('Skirt','Belt'))]: transfer(o)
for o in [c for c in clothes if c.name.startswith(('Skirt','Belt'))]: rigid(o,'Hips')
for o in [head]+ears+hair_parts: rigid(o,'Head')
for s,sh in zip('LR',shoes): rigid(sh,'Foot.'+s)
rigid(bag,'Bag')

# Join everything into one skinned mesh with the atlas material.
parts=[body,shirt,collar,head,bag,strap]+([shorts] if shorts else [])+clothes+ears+hair_parts+shoes
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
