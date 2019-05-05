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
            # tan = v.normal.orthogonal().normalized()
            # vtx.tangent = (tan[0], tan[2], -tan[1])

            # Bone Assignments
            weights = [0.0]*4
            assignment = [0]*4
            for j, g in enumerate(v.groups):
                weights[j] = g.weight
                assignment[j] = g.group
            vtx.weights = weights
            vtx.assignment = assignment

            g_element_data[i] = vtx
        
        # Vertex IDs    
        for key, values in obj.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Smooth Normals
        # edges = {}
        # verts_to_smooth = {}
        # sharp_verts = []
        # for edge in mesh.edges:
        #     if edge.use_edge_sharp:
        #         sharp_verts.append( edge.vertices[0] )
        #         sharp_verts.append( edge.vertices[1] )
        #         continue
        #     edge_center = ( ( mesh.vertices[edge.vertices[0]].co + mesh.vertices[edge.vertices[1]].co ) / 2 ).to_tuple(3)
        #     if not edge_center in edges.keys():
        #         edges[edge_center] = [edge.vertices[0], edge.vertices[1]]
        #         continue
        #     if not edge.vertices[0] in edges[edge_center]:
        #         edges[edge_center].append(edge.vertices[0])
        #     if not edge.vertices[1] in edges[edge_center]:
        #         edges[edge_center].append(edge.vertices[1])
        
        # test = {}
        # for k, v in edges.items():
        #     if len(v) > 2:
        #         test[k] = v
        # print(test)
        # print(len(edges), len(test))

        edges = {}
        sharp = []
        for e in mesh.edges:
            if e.use_edge_sharp:
                sharp.append(e.vertices[0])
                sharp.append(e.vertices[1])
                continue
            center = ( ( mesh.vertices[e.vertices[0]].co + mesh.vertices[e.vertices[1]].co ) / 2 ).to_tuple(3)
            if not center in edges.keys():
                edges[center] = [e.index]
            else:
                edges[center].append(e.index)
        
        edges2 = []
        for k, v in edges.items():
            if len(v) > 1:
                for n in v:
                    edges2.append(n)
        
        verts_to_smooth = {}
        for idx in edges2:
            for v_idx in mesh.edges[idx].vertices:
                key = mesh.vertices[v_idx].co.to_tuple(3)
                if not key in verts_to_smooth.keys():
                    verts_to_smooth[key] = [v_idx]
                    continue
                if not v_idx in verts_to_smooth[key]:
                    verts_to_smooth[key].append(v_idx)
        
        for values in verts_to_smooth.values():
            count = len(values)
            total = Vector((0,0,0))
            for n in values:
                total += mesh.vertices[n].normal
            average = total / count
            for n in values:
                g_element_data[n].normal = (average.x, average.z, -average.y)

        print(verts_to_smooth)
        print(len(verts_to_smooth))
        
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