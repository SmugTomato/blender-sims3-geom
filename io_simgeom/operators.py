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

from .util.fnv      import fnv32
from .util.globals  import Globals


class SIMGEOM_OT_import_rig_helper(bpy.types.Operator):
    """Import Rig (From Simgeom Panel)"""
    bl_idname = "simgeom.import_rig_helper"
    bl_label = "Import Rig"

    def execute(self, context):
        rigpath = Globals.ROOTDIR + "/data/rigs/" + context.scene.simgeom_rig_type + ".grannyrig"
        bpy.ops.simgeom.import_rig(filepath = rigpath)
        return {'FINISHED'}


class SIMGEOM_OT_recalc_ids(bpy.types.Operator):
    """Recalculate Vertex IDs"""
    bl_idname = "simgeom.recalc_ids"
    bl_label = "Recalculate Vertex IDs"

    def execute(self, context):
        obj = context.active_object

        start_id = obj.get('start_id')

        mesh = obj.data
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
        obj['vert_ids'] = ids

        message = "Assigned " + str(len(ids)) + " Unique IDs to " + str(len(mesh.vertices)) + " vertices."
        self.report({'INFO'}, message)

        return {'FINISHED'}
    

class SIMGEOM_OT_split_seams(bpy.types.Operator):
    """Split Mesh along UV Seams"""
    bl_idname = "simgeom.split_seams"
    bl_label = "Split UV Seams"

    def execute(self, context):
        mesh = context.active_object.data

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


class SIMGEOM_OT_clean_groups(bpy.types.Operator):
    """Delete empty vertex groups"""
    bl_idname = "simgeom.clean_groups"
    bl_label = "Delete Empty Vertex Groups"

    def execute(self, context):
        obj = context.active_object

        max_weight = {}
        for g in obj.vertex_groups:
            max_weight[g.index] = [g.name, 0.0]
        
        for v in obj.data.vertices:
            for g in v.groups:
                gn = g.group
                weight = obj.vertex_groups[g.group].weight(v.index)
                if (max_weight.get(gn)[1] is None or weight > max_weight[gn][1]):
                    max_weight[gn][1] = weight

        removed = 0
        for k, v in max_weight.items():
            if v[1] == 0:
                removed += 1
                obj.vertex_groups.remove(obj.vertex_groups[v[0]])
        message = "Removed " + str(removed) + " Unused Vertex Groups."
        self.report({'INFO'}, message)

        return {'FINISHED'}