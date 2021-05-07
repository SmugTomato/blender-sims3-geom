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

from bpy_extras import object_utils
import bpy
import bmesh

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ImportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator
from rna_prop_ui            import rna_idprop_ui_prop_get

from collections            import defaultdict
import json

from io_simgeom.io.geom_load    import GeomLoader
from io_simgeom.models.geom     import Geom
from io_simgeom.util.globals    import Globals


class SIMGEOM_OT_import_geom(Operator, ImportHelper):
    """Sims 3 GEOM Importer"""
    bl_idname = "simgeom.import_geom"
    bl_label = "Import .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".simgeom"
    filter_glob: StringProperty( default = "*.simgeom", options = {'HIDDEN'} )
    rig_type:   EnumProperty(
        name = "Choose Rig:",
        description = "Rig to import alongside the mesh",
        items = [
            ('None','None','None'),
            ('auRig','Adult','auRig'), 
            ('cuRig','Child','cuRig'), 
            ('puRig','Toddler','puRig'), 
            ('adRig','Dog Adult','adRig'),
            ('alRig','Dog Adult(small)','alRig'),
            ('cdRig','Dog Child','cdRig'),
            ('acRig','Cat Adult','acRig'),
            ('ccRig','Cat Child','ccRig'),
            ('ahRig','Horse Adult','ahRig'),
            ('chRig','Horse Child','chRig')
        ],
        default = 'None'
    )
    do_import_normals: BoolProperty(
        name = "Preserve Normals",
        description = "Import the original normals as custom split normals (recommended)",
        default = True
    )

    def execute(self, context):
        # Import Rig, checks are done in Rig Importer
        rigpath = Globals.ROOTDIR + '/data/rigs/' + self.rig_type + '.grannyrig'
        bpy.ops.simgeom.import_rig(filepath = rigpath)

        # Load the GEOM data
        geomdata = GeomLoader.readGeom(self.filepath)

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

        # Build vertex array and get face array to build the mesh
        vertices = [ (v.position[0], -v.position[2], v.position[1] ) for v in geomdata.element_data ]
        faces    = geomdata.faces
        mesh     = bpy.data.meshes.new("geom")
        obj      = bpy.data.objects.new("geom", mesh)
        mesh.from_pydata(vertices, [], faces)
        print(obj)

        # Shade smooth before applying custom normals
        for poly in mesh.polygons:
            poly.use_smooth = True

        # Add custom split normals layer if enabled
        if self.do_import_normals:
            normals = [ (v.normal[0], -v.normal[2], v.normal[1]) for v in geomdata.element_data ]
            mesh.normals_split_custom_set_from_vertices(normals)
            mesh.use_auto_smooth = True

        # Link the newly created object to the active collection
        context.view_layer.active_layer_collection.collection.objects.link(obj)
        
        # Deselect everything but newly imported mesh, then make it the active object
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Set Vertex Groups
        for bone in geomdata.bones:
            obj.vertex_groups.new(name=bone)
        
        # Set Vertex Group Weights
        if geomdata.element_data[0].assignment:
            for i, vert in enumerate(geomdata.element_data):
                for j in range(4):
                    group_index = vert.assignment[j]
                    if group_index >= len(geomdata.bones):
                        print(f"{group_index} out of range, skipping...")
                        continue
                    groupname = geomdata.bones[group_index]
                    vertgroup = obj.vertex_groups[groupname]
                    weight = vert.weights[j]
                    if weight > 0:
                        vertgroup.add( [i], weight, 'ADD' )
        
        # Set UV Coordinates for every UV channel
        if geomdata.element_data[0].uv:
            for i in range(len(geomdata.element_data[0].uv)):
                mesh.uv_layers.new(name='UV_' + str(i))
                mesh.uv_layers.active = mesh.uv_layers['UV_' + str(i)]

                for j, polygon in enumerate(mesh.polygons):
                    for k, loopindex in enumerate(polygon.loop_indices):
                        meshuvloop = mesh.uv_layers.active.data[loopindex]
                        vertex_index = geomdata.faces[j][k]
                        uv = geomdata.element_data[vertex_index].uv[i]
                        meshuvloop.uv = (uv[0], -uv[1] + 1)
            mesh.uv_layers.active = mesh.uv_layers['UV_0']

        bpy.ops.object.mode_set(mode='OBJECT')

        # Set Vertex Colors
        if geomdata.element_data[0].tagvalue:
            float_colors = []
            for el in geomdata.element_data:
                float_color = []
                for val in el.tagvalue:
                    float_color.append(val / 255)
                float_colors.append(float_color)
            
            vcol_layer = mesh.vertex_colors.new(name="SIMGEOM_TAGVAL", do_init=False)
            for poly in mesh.polygons:
                for vert_index, loop_index in zip(poly.vertices, poly.loop_indices):
                    vcol_layer.data[loop_index].color = float_colors[vert_index]

        # Add text data to blend file
        # TODO: build dictionary of desired editable data, write to file as json
        # Not sure yet how useful this is, not sure if shaderdata in geom is even used
        num_texts = len(bpy.context.blend_data.texts)
        textname = f"GEOMDATA_{num_texts}"
        bpy.context.blend_data.texts.new(textname)
        active_text = bpy.context.blend_data.texts.get(textname, None)
        if active_text != None:
            geomdict = dict()
            geomdict['rcol_chunks'] = geomdata.internal_chunks
            geomdict['rcol_external'] = geomdata.external_resources
            geomdict['embedded_id'] = geomdata.embeddedID
            geomdict['mergegroup'] = geomdata.merge_group
            geomdict['sortorder'] = geomdata.sort_order
            geomdict['skincontroller'] = geomdata.skin_controller_index
            geomdict['tgis'] = geomdata.tgi_list
            geomdict['shaderdata'] = geomdata.shaderdata

            fnvdict_path = f'{Globals.ROOTDIR}/data/json/fnv_hashmap.json'
            data_dict: dict
            with open(f'{fnvdict_path}', 'r') as data:
                data_dict = json.load(data)
                for data in geomdict['shaderdata']:
                    data['name'] = data_dict['shader_parameters'].get(data['name'], data['name'])

            active_text.write( json.dumps(geomdict, indent=4))
        
        obj.geom_data = active_text

        # Set Custom Properties
        # TODO: See which of these might be better suited to be editable in integrated text editor
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


    def add_prop(self, obj, key, value, minmax: List[int] = [0, 2147483647], descript: str = "prop"):
        obj[key] = value
        prop_ui = rna_idprop_ui_prop_get(obj, key)
        prop_ui["min"] = minmax[0]
        prop_ui["max"] = minmax[1]
        prop_ui["soft_min"] = minmax[0]
        prop_ui["soft_max"] = minmax[1]
        prop_ui["description"] = descript

        for area in bpy.context.screen.areas:
            area.tag_redraw()