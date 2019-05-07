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
from .util.globals import Globals

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
        
        # Normals
        # Get seperated egdes that need smoothing
        soft_edges = {}
        for edge in mesh.edges:
            if edge.use_edge_sharp:
                continue
            v0 = mesh.vertices[edge.vertices[0]]
            v1 = mesh.vertices[edge.vertices[1]]
            center = ( ( v0.co + v1.co ) * 0.5 ).to_tuple(3)
            if not center in soft_edges.keys():
                soft_edges[center] = [ [v0.index, v1.index] ]
                continue
            soft_edges[center].append( [v0.index, v1.index] )

        # Create sets of edges sharing a location
        merge = []
        for vals in soft_edges.values():
            if len(vals) < 2:
                continue
            verts = {}
            for e in vals:
                for n in e:
                    co = mesh.vertices[n].co.to_tuple(3)
                    if not co in verts.keys():
                        verts[co] = [n]
                    else:
                        verts[co].append(n)
            merge.append(tuple(verts.values()))

        # Average normals of vertices sharing a location
        for sets in merge:
            for set in sets:
                total = Vector((0,0,0))
                count = len(set)
                if count < 2:
                    continue
                for n in set:
                    total += mesh.vertices[n].normal
                avg = total / count
                for n in set:
                    mesh.vertices[n].normal = avg

        # Set normals in element data
        for v in mesh.vertices:
            g_element_data[v.index].normal = (v.normal.x, v.normal.z, -v.normal.y)  
        
        # Faces
        geomdata.groups = []
        for face in mesh.polygons:
            geomdata.groups.append( (face.vertices[0], face.vertices[1], face.vertices[2]) )
        
        # UV Map
        uv_count = len(mesh.uv_layers)
        uvs = []
        for _ in mesh.vertices:
            l = [None]*uv_count
            uvs.append(l)

        for n, uv_layer in enumerate(mesh.uv_layers):
            mesh.uv_layers.active = uv_layer
            for i, polygon in enumerate(mesh.polygons):
                for j, loopindex in enumerate(polygon.loop_indices):
                    meshuvloop = mesh.uv_layers.active.data[loopindex]
                    uv = ( meshuvloop.uv[0], -meshuvloop.uv[1] + 1 )
                    vertidx = geomdata.groups[i][j]
                    # g_element_data[vertidx].uv.append(uv)
                    uvs[vertidx][n] = uv
        
        for i, uv in enumerate(uvs):
            g_element_data[i].uv = uv
        
        # Tangents
        # http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
        tangents = [[] for _ in range(len(g_element_data))]
        for face in geomdata.groups:
            # Position Shortcuts
            v0 = Vector(g_element_data[face[0]].position)
            v1 = Vector(g_element_data[face[1]].position)
            v2 = Vector(g_element_data[face[2]].position)

            # UV Shortcuts
            uv0 = Vector(g_element_data[face[0]].uv[0])
            uv1 = Vector(g_element_data[face[1]].uv[0])
            uv2 = Vector(g_element_data[face[2]].uv[0])

            # Position Delta
            delta_pos1 = v1 - v0
            delta_pos2 = v2 - v0

            # UV Delta
            delta_uv1 = uv1 - uv0
            delta_uv2 = uv2 - uv0

            # Tangent Calculation
            r = 1.0 / ( delta_uv1.x * delta_uv2.y - delta_uv1.y * delta_uv2.x )
            tangent = ( delta_pos1 * delta_uv2.y - delta_pos2 * delta_uv1.y ) * r

            for v in face:
                tangents[v].append(tangent.normalized())

        # Average the tangents
        for i, v in enumerate(tangents):
            total = Vector((0,0,0))
            length = len(v)
            for n in v:
                total += n
            average = total / length
            g_element_data[i].tangent = average.normalized().to_tuple(5)
        # Average tangents again for vertices sharing the same location and normal
        for sets in merge:
            for set in sets:
                total = Vector((0,0,0))
                count = len(set)
                if count < 2:
                    continue
                for n in set:
                    total += Vector(g_element_data[n].tangent)
                avg = (total / count).normalized().to_tuple(5)
                for n in set:
                    g_element_data[n].tangent = avg

        # Bonehashes
        geomdata.bones = []
        for group in obj.vertex_groups:
            geomdata.bones.append(group.name)
        
        # Apply Seam fix
        # Fixes normals and bone assignments on seams
        for v in g_element_data:
            if not v.position in Globals.SEAM_FIX.keys():
                continue
            v.normal = Globals.SEAM_FIX[v.position]['normal']
            assign = Globals.SEAM_FIX[v.position]['assign']
            weight = Globals.SEAM_FIX[v.position]['weight']
            v.assignment = [0,0,0,0]
            v.weights = [0,0,0,0]
            for i in range(4):
                # No reason to clutter the bonehash array with unused bones
                if weight[i] == 0:
                    continue
                # If the bone is actually used, add it to the bonehash array
                if not assign[i] in geomdata.bones:
                    geomdata.bones.append(assign[i])
                # Set assignment and weight of the bone
                v.assignment[i] = geomdata.bones.index(assign[i])
                v.weights[i] = weight[i]
        
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