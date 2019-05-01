# Copyright (C) 2019 SmugTomato
# 
# This file is part of Blender28xSims3Geom.
# 
# Blender28xSims3Geom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Blender28xSims3Geom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Blender28xSims3Geom.  If not, see <http://www.gnu.org/licenses/>.

# filename = "S:\Projects\Python\Sims3Geom\main.py"
# exec(compile(open(filename).read(), filename, 'exec'))

# from io_simgeom.geomloader import GeomLoader
# from io_simgeom.geomwriter import GeomWriter
# from io_simgeom.rigloader import RigLoader

import json
import bpy
from mathutils import Vector, Quaternion

# meshdata = GeomLoader.readGeom("mesh/afBodyDressSunbelt/afBodyDressSunbelt_lod1_0x00000000D9DBB6AB.simgeom")
# rigdata = RigLoader.loadRig("mesh/auRig.grannyrig")
f = open("S:/Projects/Python/Sims3Geom/io_simgeom/data/json/rig.json", "r")
rigdata = json.loads(f.read())

# GeomWriter.writeGeom("mesh/afBodyDressSunbelt/out.simgeom", meshdata)

# RIG IMPORT
bpy.ops.object.add(
    type='ARMATURE',
    enter_editmode=True,
    location=(0,0,0)
)

rig = bpy.context.object
rig.select_set(True)
rig.name = rigdata['name']
rig.show_in_front = True

for i, b in enumerate(rigdata['bones']):
    bone = rig.data.edit_bones.new(b['name'])
    pos = Quaternion(b['rotation']) @ Vector(b['position'])

    # bone.parent = b['parent_index']
    par = b['parent_index']
    if par >= 0:
        bone.parent = rig.data.edit_bones[par]
    bone.use_connect = False
    bone.use_deform = True
    bone.use_inherit_rotation = True
    bone.head = 0,0,0
    bone.tail = 0,0.01,0
    bone.use_local_location = False

bpy.ops.object.mode_set(mode='POSE')

for i in range(len(rig.pose.bones)):
    bone = rig.pose.bones[i]
    pos = Vector((
        rigdata['bones'][i]['position'][0], 
        rigdata['bones'][i]['position'][1], 
        rigdata['bones'][i]['position'][2]
        ))
    rot = Quaternion((
        rigdata['bones'][i]['rotation'][0],
        rigdata['bones'][i]['rotation'][1],
        rigdata['bones'][i]['rotation'][2],
        rigdata['bones'][i]['rotation'][3]
        ))
    scale = Vector((
        rigdata['bones'][i]['scale'][0], 
        rigdata['bones'][i]['scale'][1], 
        rigdata['bones'][i]['scale'][2]
        ))
    bone.location = pos
    bone.rotation_quaternion = rot
    bone.scale = scale
bpy.ops.pose.armature_apply()

bpy.ops.object.mode_set(mode='EDIT')
for i in rig.data.edit_bones:
    i.use_local_location = True

# Rotate to Z=up
bpy.ops.object.mode_set(mode='OBJECT')            
rig.rotation_euler = 1.5707963705062866,0,0

# Custom bone shape
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
boneshape = bpy.context.active_object
boneshape.data.name = boneshape.name = "rig_boneshape"
boneshape.use_fake_user = True
bpy.context.scene.collection.children[0].objects.unlink(boneshape) # don't want the user deleting this
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
for bone in rig.pose.bones:
    bone.custom_shape = boneshape # apply bone shape
bpy.ops.object.mode_set(mode='OBJECT') 

