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

from .util.fnv import fnv32

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

        return {'FINISHED'}