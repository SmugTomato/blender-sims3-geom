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
import bmesh

from bpy_extras.io_utils    import ExportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator

from io_simgeom.util.fnv        import fnv32
from io_simgeom.util.globals    import Globals


class SIMGEOM_OT_rebuild_bone_database(bpy.types.Operator):
    """ Rebuild Bonehash Database from bone names in currently selected rig """
    bl_idname = "simgeom.rebuild_bone_database"
    bl_label = "Rebuild Bonehash Database"
    bl_description = "fnv32hash key to string value"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ob = context.active_object
        
        if not ob:
            return {"CANCELLED"}
        if ob.type != 'ARMATURE':
            return {"CANCELLED"}
        if not ob.get('__S3_RIG__', 0):
            message = f'{ob.name} is not a Sims 3 rig.'
            self.report({'ERROR'}, message)
            return {"CANCELLED"}

        
        bonedict = { hex(fnv32(bone.name)): bone.name for bone in ob.data.bones }
        Globals.rebuild_fnv_database(bonedict)

        message = f'Rebuilt bonehash database for rig: {ob.name}'
        self.report({'INFO'}, message)

        return {"FINISHED"}


class SIMGEOM_OT_rename_bone_groups(bpy.types.Operator):
    """ Rename vertex groups from the fnv hash map """
    bl_idname = "simgeom.rename_bone_groups"
    bl_label = "Rename vertex groups"
    bl_description = "Look up bone names in the fnvhash dict"
    bl_options = {"REGISTER"}

    def execute(self, context):
        
        ob = context.active_object
        
        if not ob:
            return {"CANCELLED"}
        if not ob.get('__GEOM__', 0):
            message = f'{ob.name} is not a Sims 3 GEOM mesh.'
            self.report({'ERROR'}, message)
            return {"CANCELLED"}
        
        for group in ob.vertex_groups:
            if group.name[0:2] == '0x':
                group.name = Globals.get_bone_name(int(group.name, 0))
        
        message = f'Renamed vertex groups for object: {ob.name}'
        self.report({'INFO'}, message)

        return {"FINISHED"}


class SIMGEOM_OT_import_rig_helper(bpy.types.Operator):
    """Import Rig (From Simgeom Panel)"""
    bl_idname = "simgeom.import_rig_helper"
    bl_label = "Import Rig"

    def execute(self, context):
        rigpath = Globals.ROOTDIR + "/data/rigs/" + context.scene.simgeom_rig_type + ".grannyrig"
        bpy.ops.simgeom.import_rig(filepath = rigpath)
        return {'FINISHED'}


class SIMGEOM_OT_make_morph(bpy.types.Operator):
    """Give the selected objects data for a Morph GEOM"""
    bl_idname = "simgeom.make_morph"
    bl_label = "Make Morph"
    def execute(self, context):
        # Selected mesh objects
        selected = [ o for o in bpy.context.scene.objects if o.select_get() and o.type == 'MESH' ]

        # Must have 2 or more meshes selected of which one must be the active object
        if len(selected) == 0:
            self.report({'ERROR'}, "You must select 1 or more meshes to turn into morphs.")
            return {'CANCELLED'}

        n_copied = 0
        for o in selected:
            if o.get('__GEOM_MORPH__') != None:
                continue

            # Clear old properties
            for prop in o.id_data.keys():
                del o[prop]
            
            o['__GEOM_MORPH__'] = 1
            
            n_copied += 1

        self.report({'INFO'}, f"Turned {n_copied} objects into morphs.")

        return {'FINISHED'}


class SIMGEOM_OT_copy_data(bpy.types.Operator):
    """Copy GEOM data from active to selected objects"""
    bl_idname = "simgeom.copy_data"
    bl_label = "Transfer GEOM data"
    def execute(self, context):
        # Selected mesh objects
        selected = [ o for o in bpy.context.scene.objects if o.select_get() and o.type == 'MESH' ]
        active = context.active_object

        # Must have 2 or more meshes selected of which one must be the active object
        if len(selected) < 2 or active not in selected:
            self.report({'ERROR'}, "You must select 2 or more meshes, of which one must be active.")
            return {'CANCELLED'}

        # Check if active object contains GEOM data
        if not active.get('__GEOM__', None):
            self.report({'ERROR'}, "Active object must have valid GEOM data to transfer to selected objects")
            return {'CANCELLED'}
        
        n_copied = 0
        for o in selected:
            if o == active:
                continue

            # Clear old properties
            for prop in o.id_data.keys():
                del o[prop]
            
            # Copy new properties
            for prop in active.id_data.keys():
                o[prop] = active[prop]
            
            n_copied += 1

        self.report({'INFO'}, f"Transfered GEOM data to {n_copied} objects.")

        return {'FINISHED'}


class SIMGEOM_OT_remove_ids(bpy.types.Operator):
    """Delete Vertex IDs"""
    bl_idname = "simgeom.remove_ids"
    bl_label = "Remove All Vertex IDs from active object"

    def execute(self, context):
        ob = context.active_object

        if not ob:
            return {"CANCELLED"}
        if not ob.get('__GEOM__', 0):
            message = f'{ob.name} is not a Sims 3 GEOM mesh.'
            self.report({'ERROR'}, message)
            return {"CANCELLED"}
        
        ob['vert_ids'] = {}
        
        message = "Removed all vertex IDs."
        self.report({'INFO'}, message)

        return {'FINISHED'}


class SIMGEOM_OT_recalc_ids(bpy.types.Operator):
    """Recalculate Vertex IDs"""
    bl_idname = "simgeom.recalc_ids"
    bl_label = "Recalculate Vertex IDs for active object"

    def execute(self, context):
        ob = context.active_object

        if not ob:
            return {"CANCELLED"}
        if not ob.get('__GEOM__', 0):
            message = f'{ob.name} is not a Sims 3 GEOM mesh.'
            self.report({'ERROR'}, message)
            return {"CANCELLED"}

        start_id = ob.get('start_id')

        mesh = ob.data
        positions = {}
        # Map vertex ID per position
        for v in mesh.vertices:
            t = v.co.to_tuple()
            if not t in positions.keys():
                positions[t] = [v.index]
            else:
                positions[t].append(v.index)

        # Now map vertices per vertex ID
        ids = {}
        for i, val in enumerate(positions.values()):
            ids[hex(i + start_id)] = val
        ob['vert_ids'] = ids

        message = "Assigned " + str(len(ids)) + " Unique IDs to " + str(len(mesh.vertices)) + " vertices."
        self.report({'INFO'}, message)

        return {'FINISHED'}
    

class SIMGEOM_OT_split_seams(bpy.types.Operator):
    """Split Mesh along UV Seams"""
    bl_idname = "simgeom.split_seams"
    bl_label = "Split UV Seams"

    def execute(self, context):
        ob = context.active_object
        mesh = ob.data

        if not ob:
            return {"CANCELLED"}
        if not ob.get('__GEOM__', 0):
            message = f'{ob.name} is not a Sims 3 GEOM mesh.'
            self.report({'ERROR'}, message)
            return {"CANCELLED"}

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.seams_from_islands()
        bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(mesh)

        uvsplit = []
        for e in bm.edges:
            if e.seam or not e.smooth:
                uvsplit.append(e)
                e.seam = False

        # Split edges given by above loop
        bmesh.ops.split_edges(bm, edges=uvsplit)

        bm.to_mesh(mesh)
        bm.free()

        message = "Edges Split, make sure to recalculate IDs!"
        self.report({'INFO'}, message)

        return {'FINISHED'}
