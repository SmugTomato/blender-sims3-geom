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

import os

from mathutils              import Vector
from bpy_extras.io_utils    import ImportHelper
from bpy.props              import StringProperty
from bpy.types              import Operator

from .models.geom           import Geom
from .geomloader            import GeomLoader


class SIMGEOM_OT_import_morph(Operator, ImportHelper):
    """Import a morph GEOM file as shape key"""
    bl_idname = "simgeom.import_morph"
    bl_label = "Import Morph .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"
    filter_glob: StringProperty( default = "*.simgeom", options = {'HIDDEN'} )

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        if obj == None:
            self.report({'ERROR'}, "No base mesh selected, can't import morph")
            return {'CANCELLED'}
        if not obj.get('__GEOM__'):
            self.report({'ERROR'}, "Selected base mesh is not a GEOM, can't import morph")
            return {'CANCELLED'}

        # Load the GEOM data
        geomdata = GeomLoader.readGeom(self.filepath)

        if len(geomdata.element_data) != len(mesh.vertices):
            self.report({'ERROR'}, "Vertex count mismatch, can't import morph")
            return {'CANCELLED'}

        # Create Basis shape key if it doesn't exist
        if not mesh.shape_keys:
            obj.shape_key_add(name="Basis", from_mix=False)
        
        # Import the morph
        filename = os.path.split(self.filepath)[1].lower()
        morphcount = len(mesh.shape_keys.key_blocks)
        morphname = "MORPH_" + str(morphcount - 1)
        if "fat" in filename:
            morphname = "fat"
        if "fit" in filename:
            morphname = "fit"
        if "thin" in filename:
            morphname = "thin"
        if "special" in filename:
            morphname = "special"
        shapekey = obj.shape_key_add(name=morphname, from_mix=False)

        for vertex in mesh.vertices:
            shapekey.data[vertex.index].co = Vector((
                vertex.co.x + geomdata.element_data[vertex.index].position[0],
                vertex.co.y - geomdata.element_data[vertex.index].position[2],
                vertex.co.z + geomdata.element_data[vertex.index].position[1]
            ))

        self.report({'INFO'}, "Imported Morph: " + morphname + " For Object: " + obj.name)
        return {'FINISHED'}