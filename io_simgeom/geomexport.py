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

from typing import List

import bpy
from mathutils import Vector, Quaternion
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .models.geom import Geom
from .models.vertex import Vertex
from .geomwriter import GeomWriter
from .util.fnv import fnv32

class GeomExport(Operator, ExportHelper):
    """Sims 3 GEOM Importer"""
    bl_idname = "export.sims3_geom"
    bl_label = "Export .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = ".simgeom"

    filter_glob: StringProperty(
            default="*.simgeom",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
    
    # Can be used to give users feedback
    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text = message)

        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

    def execute(self, context):
        geomdata = Geom()

        obj = context.active_object
        mesh = obj.data

        # Prefill vertex array
        g_element_data: List[Vertex] = [None]*len(mesh.vertices)

        for i, v in enumerate(mesh.vertices):
            vtx = Vertex()
            vtx.position = (v.co.x, v.co.z, -v.co.y)
            vtx.normal = (v.normal.x, v.normal.z, -v.normal.y)
            tan = v.normal.orthogonal().normalized()
            vtx.tangent = (tan[0], tan[2], -tan[1])

            # Bone Assignments
            weights = [0.0]*4
            assignment = [0]*4
            for j, g in enumerate(v.groups):
                weights[j] = g.weight
                assignment[j] = g.group
            vtx.weights = weights
            vtx.assignment = assignment

            g_element_data[i] = vtx
        d = {}
        for key, values in obj.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Faces
        geomdata.groups = []
        for face in mesh.polygons:
            geomdata.groups.append( (face.vertices[0], face.vertices[1], face.vertices[2]) )
        
        # UV Map
        uv_layer = mesh.uv_layers[0]
        for i, polygon in enumerate(mesh.polygons):
            for j, loopindex in enumerate(polygon.loop_indices):
                meshuvloop = mesh.uv_layers.active.data[loopindex]
                uv = ( meshuvloop.uv[0], -meshuvloop.uv[1] + 1 )
                vertidx = geomdata.groups[i][j]
                g_element_data[vertidx].uv = uv
        
        # Bonehashes
        geomdata.bones = []
        for group in obj.vertex_groups:
            geomdata.bones.append(group.name)
        
        # Remaining data
        geomdata.internal_chunks = []
        for x in obj['rcol_chunks']:
            geomdata.internal_chunks.append(x.to_dict())
        geomdata.external_resources = []
        for x in obj['rcol_external']:
            geomdata.internal_chunks.append(x.to_dict())
        geomdata.shaderdata = []
        for x in obj['shaderdata']:
            geomdata.shaderdata.append(x.to_dict())
        geomdata.tgi_list = []
        for x in obj['tgis']:
            geomdata.tgi_list.append(x.to_dict())
        geomdata.sort_order = obj['sortorder']
        geomdata.merge_group = obj['mergegroup']
        geomdata.skin_controller_index = obj['skincontroller']
        geomdata.embeddedID = obj['embedded_id']
            
        geomdata.element_data = g_element_data
        GeomWriter.writeGeom(self.filepath, geomdata)
        return {'FINISHED'}