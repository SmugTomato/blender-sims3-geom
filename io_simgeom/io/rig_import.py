# Copyright (C) 2019 SmugTomato
# 
# This file is part of BlenderGeom.
# 
# BlenderGeom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# BlenderGeom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with BlenderGeom.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import os

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ImportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator

from io_simgeom.io.rig_load     import RigLoader
from io_simgeom.util.globals    import Globals

class SIMGEOM_OT_import_rig(Operator, ImportHelper):
    """Sims 3 Rig Importer"""
    bl_idname = "simgeom.import_rig"
    bl_label = "Import .grannyrig"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".grannyrig"

    filter_glob: StringProperty(
            default="*.grannyrig",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    def execute(self, context):
        if not os.path.exists(self.filepath):
            return {'CANCELLED'}

        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[-1]
        rigdata = RigLoader.loadRig(self.filepath)

        rigthing = bpy.data.armatures.new(name=rigdata['name'])
        rig = bpy.data.objects.new(rigdata['name'], rigthing)

        context.scene.collection.children[-1].objects.link(rig)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        rig.show_in_front = True

        # Import bones to placeholder location and set parents
        for i, b in enumerate(rigdata['bones']):
            bone = rig.data.edit_bones.new(b['name'])
            pos = Quaternion(b['rotation']) @ Vector(b['position'])
            par = b['parent_index']
            if par >= 0:
                bone.parent = rig.data.edit_bones[par]
            bone.use_connect = False
            bone.use_deform = True
            bone.use_inherit_rotation = True
            bone.head = 0,0,0
            bone.tail = 0,0.01,0
            bone.use_local_location = False

        # Move the bones to their proper locations in pose mode
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
        # Only create it if it does not exist, use existing one otherwise
        boneshape = bpy.data.objects.get('rig_boneshape', None)
        if boneshape == None:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
            boneshape = bpy.context.active_object
            boneshape.data.name = boneshape.name = "rig_boneshape"
            bpy.context.scene.collection.children[-1].objects.unlink(boneshape) # don't want the user deleting this

        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='POSE')
        for bone in rig.pose.bones:
            bone.custom_shape = boneshape # apply bone shape
        bpy.ops.object.mode_set(mode='OBJECT')

        rig['__S3_RIG__'] = 1

        return {'FINISHED'}
