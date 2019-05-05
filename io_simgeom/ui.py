import bpy

# filename = "S:\\Projects\\Python\\Sims3Geom\\io_simgeom\\ui.py"
# exec(compile(open(filename).read(), filename, 'exec'))

class SIMGEOM_PT_utility_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sims 3 GEOM Tools"
    bl_idname = "SIMGEOM_PT_utility_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    # Placeholder
    bpy.types.Scene.simgeom_lod0 = bpy.props.PointerProperty(name="LOD 0", type=bpy.types.Object)
    bpy.types.Scene.simgeom_lod1 = bpy.props.PointerProperty(name="LOD 1", type=bpy.types.Object)
    bpy.types.Scene.simgeom_lod2 = bpy.props.PointerProperty(name="LOD 2", type=bpy.types.Object)
    bpy.types.Scene.simgeom_lod3 = bpy.props.PointerProperty(name="LOD 3", type=bpy.types.Object)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("import.sims3_geom", text="Import GEOM", icon='IMPORT')
        row.operator("export.sims3_geom", text="Export GEOM", icon='EXPORT')
        col.operator("import.sims3_grannyrig", text="Import Rig", icon='ARMATURE_DATA')

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
        col.operator("simgeom.recalc_ids", text="RECALCULATE IDS", icon='COPY_ID')
        col.operator("simgeom.split_seams", text="Split UV Seams", icon='COPY_ID')

        col = layout.column(align=True)
        col.label(text="LOD (Not in use yet):")
        col.prop(scene, 'simgeom_lod0')
        col.prop(scene, 'simgeom_lod1')
        col.prop(scene, 'simgeom_lod2')
        col.prop(scene, 'simgeom_lod3')
