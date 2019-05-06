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
import bmesh

from mathutils import Vector, Quaternion
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from rna_prop_ui import rna_idprop_ui_prop_get

from .geomloader import GeomLoader
from .models.geom import Geom
from .util.globals import Globals

class GeomImport(Operator, ImportHelper):
    """Sims 3 GEOM Importer"""
    bl_idname = "import.sims3_geom"
    bl_label = "Import .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"

    filter_glob: StringProperty(
            default="*.simgeom",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    def execute(self, context):
        geomdata = GeomLoader.readGeom(self.filepath)
        scene = bpy.context.scene

        # Fill a Dictionairy with hexed ID as key and List of vertex indices
        lowest_id = 0x7fffffff
        ids = {}
        for i, v in enumerate(geomdata.element_data):
            if v.vertex_id[0] < lowest_id:
                lowest_id = v.vertex_id[0]
            if not hex(v.vertex_id[0]) in ids:
                ids[hex(v.vertex_id[0])] = [i]
            else:
                ids[hex(v.vertex_id[0])].append(i)

        # Fix EA's stupid rounding errors on supposedly identically placed vertices
        for verts in ids.values():
            if len(verts) < 2:
                continue
            for i in range(len(verts)-1):
                geomdata.element_data[verts[i+1]].position = geomdata.element_data[verts[0]].position

        vertices = []
        for v in geomdata.element_data:
            vert = v.position
            vertices.append( (vert[0], -vert[2], vert[1]) )
        faces = geomdata.groups

        mesh = bpy.data.meshes.new("geom")
        obj = bpy.data.objects.new("geom", mesh)

        mesh.from_pydata(vertices, [], faces)

        scene.collection.objects.link(obj)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Shade smooth and set autosmooth for sharp edges
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 3.14
        bpy.ops.object.shade_smooth()

        # Vertex Groups
        for bone in geomdata.bones:
            obj.vertex_groups.new(name=bone)
        
        # Group Weights
        for i, vert in enumerate(geomdata.element_data):
            for j in range(4):
                groupname = geomdata.bones[vert.assignment[j]]
                vertgroup = obj.vertex_groups[groupname]
                weight = vert.weights[j]
                if weight > 0:
                    vertgroup.add( [i], weight, 'ADD' )
        
        # UV Coordinates
        for i in range(len(geomdata.element_data[0].uv)):
            mesh.uv_layers.new(name='UV_' + str(i))
            mesh.uv_layers.active = mesh.uv_layers['UV_' + str(i)]

            for j, polygon in enumerate(mesh.polygons):
                for k, loopindex in enumerate(polygon.loop_indices):
                    meshuvloop = mesh.uv_layers.active.data[loopindex]
                    vertex_index = geomdata.groups[j][k]
                    uv = geomdata.element_data[vertex_index].uv[i]
                    meshuvloop.uv = (uv[0], -uv[1] + 1)



        # bpy.ops.object.mode_set(mode='EDIT')
        # bm = bmesh.from_edit_mesh(mesh)
        # uv_layer = bm.loops.layers.uv.verify()

        # for face in bm.faces:
        #     for loop in face.loops:
        #         loop_uv = loop[uv_layer]
        #         uv = geomdata.element_data[loop.vert.index].uv
        #         loop_uv.uv = (uv[0], -uv[1] + 1.0)

        # bmesh.update_edit_mesh(mesh)
        # bm.free()

        bpy.ops.object.mode_set(mode='OBJECT')

        # Set Custom Properties
        self.add_prop(obj, '__GEOM__', 1)
        self.add_prop(obj, 'rcol_chunks', geomdata.internal_chunks)
        self.add_prop(obj, 'rcol_external', geomdata.external_resources)
        self.add_prop(obj, 'shaderdata', geomdata.shaderdata)
        self.add_prop(obj, 'mergegroup', geomdata.merge_group)
        self.add_prop(obj, 'sortorder', geomdata.sort_order)
        self.add_prop(obj, 'skincontroller', geomdata.skin_controller_index)
        self.add_prop(obj, 'tgis', geomdata.tgi_list)
        self.add_prop(obj, 'embedded_id', geomdata.embeddedID)
        
        self.add_prop(obj, 'vert_ids', ids)
        start_id_descript = "Starting Vertex ID"
        for key, value in Globals.CAS_INDICES.items():
            start_id_descript += "\n" + str(key) + " - " + str(value)
        self.add_prop(obj, 'start_id', lowest_id, descript = start_id_descript)

        # SET SHARP
        # d = {}
        # for i, v in enumerate(geomdata.element_data):
        #     k = (v.normal[0], v.normal[1], v.normal[2])
        #     if not k in d.keys():
        #         d[k] = [i]
        #     else:
        #         d[k].append(i)
        # print(len(d), "Unique Normals")

        # multi_normals = []
        # for v in d.values():
        #     if len(v) < 2:
        #         continue
        #     for n in v:
        #         multi_normals.append(n)
        
        #
        # testverts = []
        # for val in ids.values():
        #     if len(val) < 2:
        #         continue
        #     for n in val:
        #         testverts.append(n)
        # print(len(testverts), "Testverts")

        # bpy.ops.object.mode_set(mode='EDIT')
        # bm = bmesh.from_edit_mesh(mesh)

        # for edge in bm.edges:
        #     if edge.verts[0].index in testverts:
        #         if edge.verts[1].index in testverts:
        #             edge.smooth = False
        
        # bmesh.update_edit_mesh(mesh)
        # bpy.ops.object.mode_set(mode='OBJECT')

        edges = {}
        for face in geomdata.groups:
            for i in range(len(face)):
                idx = i + 1
                if i == len(face)-1:
                    idx = 0
                edge = ( ( mesh.vertices[face[i]].co + mesh.vertices[face[idx]].co ) / 2 ).to_tuple()
                if not edge in edges.keys():
                    edges[edge] = [ Vector(geomdata.element_data[face[i]].normal).to_tuple(3), Vector(geomdata.element_data[face[idx]].normal).to_tuple(3) ]
                    continue
                if not Vector(geomdata.element_data[face[i]].normal).to_tuple(3) in edges[edge]:
                    edges[edge].append( Vector(geomdata.element_data[face[i]].normal).to_tuple(3) )
                if not Vector(geomdata.element_data[face[idx]].normal).to_tuple(3) in edges[edge]:
                    edges[edge].append( Vector(geomdata.element_data[face[idx]].normal).to_tuple(3) )

        bm = bmesh.new()
        bm.from_mesh(mesh)

        # bmesh.ops.remove_doubles(bm, verts=bm.verts)

        # Check mesh edges against edge dictionary, mark hard edges sharp
        numedges = 0
        for e in bm.edges:
            edgemid = tuple((e.verts[0].co + e.verts[1].co) / 2)
            if len(edges[edgemid]) > 2:
                numedges += 1
                e.smooth = False

        bm.to_mesh(mesh)
        bm.free()


        return {'FINISHED'}

    
    def add_prop(self, obj, key, value, minmax: List[int] = [0, 9999999], descript: str = "prop"):
        obj[key] = value
        prop_ui = rna_idprop_ui_prop_get(obj, key)
        prop_ui["min"] = minmax[0]
        prop_ui["max"] = minmax[1]
        prop_ui["soft_min"] = minmax[0]
        prop_ui["soft_max"] = minmax[1]
        prop_ui["description"] = descript

        for area in bpy.context.screen.areas:
            area.tag_redraw()

