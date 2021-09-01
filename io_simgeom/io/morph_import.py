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
from typing                 import List

import bpy

from mathutils              import Vector
from bpy_extras.io_utils    import ImportHelper
from bpy.props              import StringProperty, CollectionProperty, BoolProperty
from bpy.types              import Operator, PropertyGroup
from rna_prop_ui            import rna_idprop_ui_prop_get

from io_simgeom.io.geom_load    import GeomLoader
from io_simgeom.models.geom     import Geom


class SIMGEOM_OT_import_morph(Operator, ImportHelper):
    """Import one or multiple morph GEOM files as shape keys"""
    bl_idname = "simgeom.import_morph"
    bl_label = "Import Morph .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"
    filter_glob: StringProperty( default = "*.simgeom", options = {'HIDDEN'} )
    files: CollectionProperty(type=PropertyGroup)

    do_import_normals: BoolProperty(
        name = "Preserve Normals",
        description = "Import the original normals as custom split normals (recommended)",
        default = True
    )

    do_vertexid_order: BoolProperty(
        name = "VertexID Lookup",
        description = "Rely on vertexIDs instead of vertex order when importing morphs (recommended)",
        default = True
    )

    def execute(self, context):
        geom_obj = context.active_object
        geom_mesh = geom_obj.data

        if geom_obj == None:
            self.report({'ERROR'}, "No base mesh selected, can't import morphs")
            return {'CANCELLED'}
        if not geom_obj.get('__GEOM__'):
            self.report({'ERROR'}, "Selected base mesh is not a GEOM, can't import morphs")
            return {'CANCELLED'}
        
        # Get list of original normals for later
        geom_normals = [[0,0,0]] * len(geom_mesh.vertices)
        geom_mesh.calc_normals_split()
        for loop in geom_mesh.loops:
            geom_normals[loop.vertex_index] = loop.normal

        for geom_file in self.files:
            directory = os.path.dirname(self.filepath)
            filepath = os.path.join(directory, geom_file.name)
            # Load the GEOM data
            morph_geomdata = GeomLoader.readGeom(filepath)

            if len(morph_geomdata.element_data) != len(geom_mesh.vertices):
                self.report({'ERROR'}, "Vertex count mismatch, can't import morphs")
                continue
            
            # Name the morph
            filename = os.path.split(filepath)[1].lower()
            morphcount = self.get_morph_count(geom_obj)
            morphname = f"MORPH"
            if "fat" in filename:
                morphname = f"{morphname}_FAT"
            elif "fit" in filename:
                morphname = f"{morphname}_FIT"
            elif "thin" in filename:
                morphname = f"{morphname}_THIN"
            elif "special" in filename:
                morphname = f"{morphname}_SPECIAL"
            else:
                morphname = f"{morphname}_{morphcount}"
            morph_obj_name = f"{geom_obj.name}_{morphname}"

            # Get final positions and normals from adding the offsets
            morph_vertices = [[0,0,0]] * len(geom_mesh.vertices)
            morph_normals  = [[0,0,0]] * len(geom_mesh.vertices)

            # EA morphs and/or sliders seem to be inconsistent with their vertex order
            # so I map the morphs to vertexIDs instead if left enabled by user
            vertIDMap = geom_obj.get('vert_ids', dict())

            for i in range(len(geom_mesh.vertices)):
                vertexID = hex(morph_geomdata.element_data[i].vertex_id[0])

                if self.do_vertexid_order:
                    baseIndex = vertIDMap.get(vertexID, [0])[0]
                else:
                    baseIndex = i

                morph_vertices[i] = [
                    geom_mesh.vertices[baseIndex].co[0] + morph_geomdata.element_data[i].position[0],
                    geom_mesh.vertices[baseIndex].co[1] - morph_geomdata.element_data[i].position[2],
                    geom_mesh.vertices[baseIndex].co[2] + morph_geomdata.element_data[i].position[1]
                ]
                morph_normals[i] = [
                    geom_normals[baseIndex][0] + morph_geomdata.element_data[i].normal[0],
                    geom_normals[baseIndex][1] - morph_geomdata.element_data[i].normal[2],
                    geom_normals[baseIndex][2] + morph_geomdata.element_data[i].normal[1]
                ]
            
            faces = morph_geomdata.faces
            mesh  = bpy.data.meshes.new(morph_obj_name)
            obj   = bpy.data.objects.new(morph_obj_name, mesh)
            mesh.from_pydata(morph_vertices, [], faces)

            # Shade smooth before applying custom normals
            for poly in mesh.polygons:
                poly.use_smooth = True

            # Add custom split normals layer if enabled
            if self.do_import_normals:
                mesh.normals_split_custom_set_from_vertices(morph_normals)
                mesh.use_auto_smooth = True

            # Link the newly created object to the active collection
            context.view_layer.active_layer_collection.collection.objects.link(obj)

            # Deselect everything but newly imported mesh, then make it the active object
            for o in context.selected_objects:
                o.select_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Custom Properties
            obj['__GEOM_MORPH__'] = 1
            obj.morph_name = morphname
            obj.morph_link = geom_obj

            self.report({'INFO'}, "Imported Morph: " + morphname + " For Object: " + geom_obj.name)
        return {'FINISHED'}

    
    def get_morph_count(self, base_obj):
        morphs = list()
        
        for o in bpy.data.objects.values():
            if o.type != 'MESH':
                continue
            if o.get('__GEOM_MORPH__', None) == None:
                continue
            if o.get('morph_link', None) == base_obj:
                morphs.append(o)
        
        return len(morphs)
