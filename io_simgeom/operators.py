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
from .util.fnv import fnv32

import math
def truncate(number, digits) -> float:
    stepper = pow(10.0, digits)
    return math.trunc(stepper * number) / stepper

class SIMGEOM_OT_recalc_ids(bpy.types.Operator):
    """Recalculate Vertex IDs"""
    bl_idname = "simgeom.recalc_ids"
    bl_label = "Recalculate Vertex IDs"

    def execute(self, context):
        obj = context.active_object

        start_id = obj.get('start_id')

        # Create an override, or the view3d operator won't work
        win      = bpy.context.window
        scr      = win.screen
        areas3d  = [area for area in scr.areas if area.type == 'VIEW_3D']
        region   = [region for region in areas3d[0].regions if region.type == 'WINDOW']
        view3d_override = {
            'window': win,
            'screen': scr,
            'area'  : areas3d[0],
            'region': region[0],
            'scene' : bpy.context.scene,
            }
        # Make backup of original settings
        system_orig = bpy.context.scene.unit_settings.system
        unit_orig = bpy.context.scene.unit_settings.scale_length

        # Snap vertices to nearest 1/1000th of a unit (1 milimeter precision)
        # This is done to overcome rounding errors in original Maxis meshes
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 1000
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.view3d.snap_selected_to_grid(view3d_override)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.unit_settings.scale_length = 1

        # Restore original settings
        bpy.context.scene.unit_settings.system = system_orig
        bpy.context.scene.unit_settings.scale_length = unit_orig

        mesh = obj.data
        positions = {}
        # Map vertex ID per position
        for v in mesh.vertices:
            t = v.co.to_tuple()
            if not t in positions.keys():
                positions[t] = [v.index]
            else:
                positions[t].append(v.index)

        # Now vertices per vertex ID
        ids = {}
        for i, val in enumerate(positions.values()):
            ids[hex(i + start_id)] = val
        obj['vert_ids'] = ids


        return {'FINISHED'}