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

        vertices = []
        for v in geomdata.element_data:
            vert = v['position']
            vertices.append( (vert[0], -vert[2], vert[1]) )
        faces = geomdata.groups

        scene = bpy.context.scene

        mesh = bpy.data.meshes.new("thingy")
        object = bpy.data.objects.new("object", mesh)

        mesh.from_pydata(vertices, [], faces)

        scene.collection.objects.link(object)
        object.select_set(True)
        bpy.context.view_layer.objects.active = object

        return {'FINISHED'}