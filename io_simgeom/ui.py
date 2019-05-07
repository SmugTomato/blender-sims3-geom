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


class SIMGEOM_PT_utility_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sims 3 GEOM Tools"
    bl_idname = "SIMGEOM_PT_utility_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("simgeom.import_geom", text="Import GEOM", icon='IMPORT')
        row.operator("simgeom.export_geom", text="Export GEOM", icon='EXPORT')
        col.operator("simgeom.import_rig", text="Import Rig", icon='ARMATURE_DATA')

        if not obj or not obj.get('__GEOM__'):
            return

        col = layout.column(align=True)
        col.label(text="Vertex IDs:")
        row = col.row(align=True)
        row.prop(obj, '["start_id"]')
        sub = row.row()
        sub.alignment = 'RIGHT'
        uniques = len(obj.get('vert_ids'))
        sub.label( text = str( obj.get('start_id') + uniques ) + " (" + str(uniques) + ")" )
        col.operator("simgeom.recalc_ids", text="Recalculate IDs", icon='COPY_ID')

        col = layout.column(align=True)
        col.label(text="Misc.")
        col.operator("simgeom.split_seams", text="Split UV Seams", icon='MOD_EDGESPLIT')
        col.operator("simgeom.clean_groups", text="Clean Empty Bone Groups", icon='GROUP_VERTEX')
