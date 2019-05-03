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

from mathutils import Vector, Quaternion
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .geomloader import GeomLoader

class GeomImport(Operator, ImportHelper):
    """Sims 3 GEOM Importer"""
    bl_idname = "import.sims3_geom"
    bl_label = "Import .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"

    def execute(self, context):
        geomdata = GeomLoader.readGeom(self.filepath)
        scene = bpy.context.scene

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
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh)
        uv_layer = bm.loops.layers.uv.verify()

        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                uv = geomdata.element_data[loop.vert.index].uv
                loop_uv.uv = (-uv[0] + 1.0, -uv[1] + 1.0)

        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}