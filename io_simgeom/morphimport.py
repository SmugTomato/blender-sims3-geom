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
import bmesh

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ImportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator
from rna_prop_ui            import rna_idprop_ui_prop_get

from .models.geom           import Geom
from .geomloader            import GeomLoader
from .util.globals          import Globals


class SIMGEOM_OT_import_morph(Operator, ImportHelper):
    """Sims 3 GEOM Importer"""
    bl_idname = "simgeom.import_morph"
    bl_label = "Import Morph .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"
    filter_glob: StringProperty( default = "*.simgeom", options = {'HIDDEN'} )

    def execute(self, context):
        base_obj = context.active_object
        if base_obj == None:
            return {'CANCELLED'}

        # Load the GEOM data
        geomdata = GeomLoader.readGeom(self.filepath)

        # Set Active Collection
        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[-1]
        scene = context.scene

        # Fill a Dictionairy with hexed Vertex ID as key and List of vertex indices
        lowest_id = 0x7fffffff
        ids = {}
        if geomdata.element_data[0].vertex_id:
            for i, v in enumerate(geomdata.element_data):
                if v.vertex_id[0] < lowest_id:
                    lowest_id = v.vertex_id[0]
                if not hex(v.vertex_id[0]) in ids:
                    ids[hex(v.vertex_id[0])] = [i]
                else:
                    ids[hex(v.vertex_id[0])].append(i)

        # Fix EA's stupid rounding errors on supposedly identically placed vertices
        # This is achieved by setting verts with the same ID to the same position
        for verts in ids.values():
            if len(verts) < 2:
                continue
            for i in range(len(verts)-1):
                geomdata.element_data[verts[i+1]].position = geomdata.element_data[verts[0]].position

        # Build vertex array and get face array to build the mesh
        vertices = []
        for v in base_obj.data.vertices:
            vertices.append((
                v.co.x + geomdata.element_data[v.index].position[0],
                v.co.y + -geomdata.element_data[v.index].position[2],
                v.co.z + geomdata.element_data[v.index].position[1]
            ))
        faces    = geomdata.faces
        mesh     = bpy.data.meshes.new("geom_morph")
        obj      = bpy.data.objects.new("geom_morph", mesh)
        mesh.from_pydata(vertices, [], faces)

        # Link the newly created object to the active collection
        scene.collection.children[-1].objects.link(obj)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Shade smooth and set autosmooth for sharp edges
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 3.14
        bpy.ops.object.shade_smooth()

        # Set Vertex Groups
        for bone in geomdata.bones:
            obj.vertex_groups.new(name=bone)

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