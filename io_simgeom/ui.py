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

    bpy.types.Scene.simgeom_rig_type = bpy.props.EnumProperty(
        name = "Choose Rig:",
        description = "Rig to import alongside the mesh",
        items = [
            ('auRig','Adult','auRig'), 
            ('cuRig','Child','cuRig'), 
            ('puRig','Toddler','puRig'), 
            ('adRig','Dog Adult','adRig'),
            ('alRig','Dog Adult(small)','alRig'),
            ('cdRig','Dog Child','cdRig'),
            ('acRig','Cat Adult','acRig'),
            ('ccRig','Cat Child','ccRig'),
            ('ahRig','Horse Adult','ahRig'),
            ('chRig','Horse Child','chRig')
        ],
        default = 'auRig'
    )

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("simgeom.import_geom", text="Import GEOM", icon='IMPORT')
        row.operator("simgeom.export_geom", text="Export GEOM", icon='EXPORT')
        row = col.row(align=True)
        row.operator("simgeom.import_rig_helper", text="Import Rig", icon='IMPORT')
        row.prop(scene, "simgeom_rig_type", expand=False, text="")

        if not obj is None and obj.type == 'ARMATURE' and obj.get('__S3_RIG__', 0):
            col.operator("simgeom.rebuild_bone_database")

        if obj is not None and obj.get('__GEOM__', 0):
            col.operator("simgeom.import_morph", text="Import Morphs", icon='IMPORT')
            self.draw_object(context)
        
        row = layout.row(align=True)
        row.operator("simgeom.copy_data", text="Transfer GEOM data")
    

    def draw_object(self, context):
        layout = self.layout
        obj = context.active_object        

        col = layout.column(align=True)
        col.label(text="Vertex IDs:")
        row = col.row(align=True)
        row.prop(obj, '["start_id"]')
        sub = row.row()
        sub.alignment = 'RIGHT'
        uniques = len(obj.get('vert_ids'))
        sub.label( text = str( obj.get('start_id') + uniques ) + " (" + str(uniques) + ")" )
        col.operator("simgeom.recalc_ids", text="Recalculate IDs")
        col.operator("simgeom.remove_ids", text="Remove IDs")

        col = layout.column(align=True)
        col.label(text="Misc.:")
        col.operator("simgeom.split_seams", text="Split UV Seams")
        col.operator("simgeom.clean_groups", text="Clean Empty Bone Groups")
        col.operator("simgeom.rename_bone_groups")