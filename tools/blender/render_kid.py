import bpy, math, sys
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
blend,out,engine=args[0],args[1],args[2]
bpy.ops.wm.open_mainfile(filepath=blend)
C=bpy.context; S=C.scene
kid=bpy.data.objects['Kid']; rig=bpy.data.objects['KidRig']
# toon material: lit/shadow bands from a sun, vertex colour x atlas
mat=kid.data.materials[0]; nt=mat.node_tree
bsdf=nt.nodes['Principled BSDF']; mix=[n for n in nt.nodes if n.type=='MIX'][0]
diff=nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(mix.outputs['Result'],diff.inputs['Color'])
s2r=nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(diff.outputs[0],s2r.inputs[0])
ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation='CONSTANT'
ramp.color_ramp.elements[0].color=(0.74,0.72,0.9,1); ramp.color_ramp.elements[1].position=0.18; ramp.color_ramp.elements[1].color=(1,1,1,1)
bw=nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s2r.outputs[0],bw.inputs[0]); nt.links.new(bw.outputs[0],ramp.inputs[0])
m2=nt.nodes.new('ShaderNodeMix'); m2.data_type='RGBA'; m2.blend_type='MULTIPLY'; m2.inputs['Factor'].default_value=1
nt.links.new(mix.outputs['Result'],m2.inputs['A']); nt.links.new(ramp.outputs['Color'],m2.inputs['B'])
em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(m2.outputs['Result'],em.inputs['Color'])
outn=nt.nodes['Material Output']; nt.links.new(em.outputs[0],outn.inputs['Surface'])
# ink outline: inverted hull
ol=bpy.data.materials.new('Outline'); ol.use_nodes=True; ol.use_backface_culling=True
on=ol.node_tree; e=on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(0.12,0.09,0.11,1)
on.links.new(e.outputs[0],on.nodes['Material Output'].inputs['Surface'])
kid.data.materials.append(ol)
sol=kid.modifiers.new('outline','SOLIDIFY'); sol.thickness=0.006; sol.offset=1; sol.use_flip_normals=True; sol.material_offset=1
mat.use_backface_culling=True
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); S.collection.objects.link(sun); sun.rotation_euler=(math.radians(50),math.radians(20),math.radians(-30))
S.world=bpy.data.worlds.new('w'); S.world.color=(0.62,0.78,0.95)
S.render.engine=engine; S.view_settings.view_transform='Standard'; S.render.film_transparent=False
S.render.resolution_x=int(args[3]) if len(args)>3 else 900; S.render.resolution_y=int(args[4]) if len(args)>4 else 900
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=1.9
# poses
poses={'stand':{},'run':{'UpperLeg.R':-40,'LowerLeg.R':60,'UpperLeg.L':38,'LowerLeg.L':92,'UpperArm.R':34,'LowerArm.R':-85,'UpperArm.L':-30,'LowerArm.L':-70},
 'kick':{'UpperLeg.R':-80,'LowerLeg.R':5,'UpperLeg.L':10,'LowerLeg.L':14,'UpperArm.R':45,'UpperArm.L':-60,'LowerArm.L':-35}}
import os
for i,(pname,yaw) in enumerate([('stand',-24),('run',-24),('kick',-24),('stand',-90),('stand',200)]):
    for pb in rig.pose.bones: pb.rotation_mode='XYZ'; pb.rotation_euler=(0,0,0)
    for b,a in poses[pname].items(): rig.pose.bones[b].rotation_euler=(math.radians(a),0,0)
    rig.rotation_euler=(0,0,math.radians(yaw)); kid.rotation_euler=(0,0,0)
    cam.location=(0,-5,0.8); cam.rotation_euler=(math.radians(90),0,0)
    S.render.filepath=out.replace('.png',f'_{i}.png'); bpy.ops.render.render(write_still=True)
