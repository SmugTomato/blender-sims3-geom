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
from .models.geom import Geom

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
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh)
        uv_layer = bm.loops.layers.uv.verify()

        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                uv = geomdata.element_data[loop.vert.index].uv
                loop_uv.uv = (uv[0], -uv[1] + 1.0)

        bmesh.update_edit_mesh(mesh)

        # Set UV Edges to sharp and remove doubles
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.region_to_loop()
        # bpy.ops.mesh.mark_sharp()
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.remove_doubles()

        bpy.ops.object.mode_set(mode='OBJECT')

        # Set Custom Properties
        self.add_prop(obj, 'rcol_chunks', geomdata.internal_chunks)
        self.add_prop(obj, 'rcol_external', geomdata.external_resources)
        self.add_prop(obj, 'shaderdata', geomdata.shaderdata)
        self.add_prop(obj, 'mergegroup', geomdata.merge_group)
        self.add_prop(obj, 'sortorder', geomdata.sort_order)
        self.add_prop(obj, 'skincontroller', geomdata.skin_controller_index)
        ids = [v.vertex_id[0] for v in geomdata.element_data]
        self.add_prop(obj, 'vert_ids', ids)
        self.add_prop(obj, 'tgis', geomdata.tgi_list)
        self.add_prop(obj, 'embedded_id', geomdata.embeddedID)

        return {'FINISHED'}

    
    def add_prop(self, obj, key, value):
        obj[key] = value
