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

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ExportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator

from .models.geom           import Geom
from .models.vertex         import Vertex
from .geomwriter            import GeomWriter
from .util.fnv              import fnv32
from .util.globals          import Globals


class SIMGEOM_OT_export_morphs(Operator, ExportHelper):
    """Export Morphs"""
    bl_idname = "simgeom.export_morphs_helper"
    bl_label = "Export Morphs (.simgeom)"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = ".simgeom"

    filter_glob: StringProperty(
            default="*.simgeom",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
    
    morphs = {
        0: "_thin",
        1: "_fat",
        2: "_fit",
        3: "_special"
    }

    def execute(self, context):
        basepath = self.filepath
        basepath = basepath.split(".simgeom")[0]

        base = context.scene.get("simgeom_morph_base")
        if type(base) is not bpy.types.Object or base.get("__GEOM__") != 1:
            self.report({'INFO'}, "No Base Mesh Supplied")
            return {'CANCELLED'}
        
        for i in range(4):
            key = "simgeom_morph_" + str(i)
            morph = context.scene.get(key)
            if type(morph) is not bpy.types.Object or morph.get("__GEOM__") != 1:
                continue
            if not base.get("vert_ids").to_dict() == morph.get("vert_ids").to_dict():
                continue
            path = basepath + self.morphs[i] + ".simgeom"
            GeomWriter.writeGeom(path, self.export_morph(context, morph, base))
            

        # rigpath = Globals.ROOTDIR + "/data/rigs/" + context.scene.simgeom_rig_type + ".grannyrig"
        # bpy.ops.simgeom.import_rig(filepath = rigpath)
        return {'FINISHED'}
    

    def export_morph(self, context, morph, reference) -> Geom:
        geomdata = Geom()
        morph_mesh = morph.data
        reference_mesh = reference.data

        # Create the GEOM vertex array and fill it with the readily available values
        g_element_data: List[Vertex] = []
        for v in morph_mesh.vertices:
            vtx = Vertex()
            vtx.position = (v.co.x, v.co.z, -v.co.y)
            vtx.position = (
                (v.co.x - reference_mesh.vertices[v.index].co.x),
                -(v.co.z - reference_mesh.vertices[v.index].co.z),
                (v.co.y - reference_mesh.vertices[v.index].co.y)
            )

            vtx.normal = (0,0,0)
            g_element_data.append(vtx)
        
        # Set Vertex IDs
        for key, values in morph.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Set Faces
        geomdata.faces = []
        for face in morph_mesh.polygons:
            geomdata.faces.append( (face.vertices[0], face.vertices[1], face.vertices[2]) )
        
        # Fill the bone array
        geomdata.bones = []
        for group in morph.vertex_groups:
            geomdata.bones.append(group.name)
        
        emtpy_tgi = {
            'type': "0x0",
            'group': "0x0",
            'instance': "0x0"
        }

        # Set Header Info
        geomdata.internal_chunks = []
        geomdata.internal_chunks.append(emtpy_tgi)
        geomdata.external_resources = []
        geomdata.shaderdata = []
        geomdata.tgi_list = []
        geomdata.tgi_list.append(emtpy_tgi)
        geomdata.sort_order = morph['sortorder']
        geomdata.merge_group = morph['mergegroup']
        geomdata.skin_controller_index = 0
        geomdata.embeddedID = "0x0"

        geomdata.element_data = g_element_data
        return(geomdata)