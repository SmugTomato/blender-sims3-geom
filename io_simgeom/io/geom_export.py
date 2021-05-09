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

from typing                 import List
import math

import bpy
import bmesh

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ExportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator

from io_simgeom.io.geom_write   import GeomWriter
from io_simgeom.models.geom     import Geom
from io_simgeom.models.vertex   import Vertex
from io_simgeom.util.fnv        import fnv32
from io_simgeom.util.globals    import Globals

MAX_BONES = 59

class SIMGEOM_OT_export_geom(Operator, ExportHelper):
    """Sims 3 GEOM Exporter"""
    bl_idname = "simgeom.export_geom"
    bl_label = "Export .simgeom"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = ".simgeom"

    filter_glob: StringProperty(
        default="*.simgeom",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    seamfix_type:   EnumProperty(
        name = "Seamfix Type:",
        description = "Age/Gender to use for seamfix",
        items = [
            ('None','None',         'None'),
            ('af',  'Adult Female', 'Adult Female'),
            ('am',  'Adult Male',   'Adult Male'),
            ('ef',  'Elder Female', 'Elder Female'),
            ('em',  'Elder Male',   'Elder Male'),
            ('tf',  'Teen Female',  'Teen Female'),
            ('tm',  'Teen Male',    'Teen Male'),
            ('cu',  'Child',        'Child'),
            ('pu',  'Toddler',      'Toddler')
        ],
        default = 'None'
    )

    seamfix_lod:   EnumProperty(
        name = "Seamfix Type:",
        description = "LOD Index to use for seamfix",
        items = [
            ('LOD1',    'LOD1',     'LOD1'),
            ('LOD2',    'LOD2',     'LOD2'),
            ('LOD3',    'LOD3',     'LOD3')
        ],
        default = 'LOD1'
    )

    do_export_morphs: BoolProperty(
        name = "Export Morphs",
        description = "Export all morphs belonging to the selected GEOM.",
        default = True
    )

    def execute(self, context):
        geom_data = Geom()
        ob = context.active_object
        me = ob.data

        # Get a list of bones that are assigned to vertices
        bones_used = []
        for v in me.vertices:
            for g in v.groups:
                if not g.group in bones_used:
                    bones_used.append(g.group)
        
        # Cancel import if amount of bones is over the limit
        if len(bones_used) > MAX_BONES:
            message = (
                f"GEOM has {len(bones_used)} bones assigned, but only {MAX_BONES} are allowed, export cancelled!\n"
                "Please split up the mesh into multiple groups an/or make sure to limit bone assignments to 4."
            )
            self.report({'ERROR'}, message)
            return {"CANCELLED"}
        
        # Build a mapping of Blender's vertex group indices to the indices bones will have in the GEOM file
        bones_map = dict()
        for i, b_ind in enumerate(bones_used):
            bones_map[b_ind] = i

        # Create the GEOM vertex array and fill it with the readily available values
        g_element_data: List[Vertex] = []
        for v in me.vertices:
            vtx = Vertex()
            vtx.position = (v.co.x, v.co.z, -v.co.y)

            # Bone Assignments
            weights = [0.0]*4
            assignment = [0]*4
            for j, g in enumerate(v.groups):
                weights[j] = g.weight
                assignment[j] = bones_map[g.group]
            vtx.weights = weights
            vtx.assignment = assignment

            g_element_data.append(vtx)

        # Fill the bone array
        geom_data.bones = [""] * len(bones_used) 
        for key, val in bones_map.items():
            geom_data.bones[val] = ob.vertex_groups[key].name
        
        # Set Vertex IDs
        for key, values in ob.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Temporary mesh for export
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = ob.evaluated_get(depsgraph)
        mesh_instance = obj_eval.to_mesh()

        # Triangulate the mesh
        bm = bmesh.new()
        bm.from_mesh(mesh_instance)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh_instance)
        bm.free()
        
        # Get per vertex normals from mesh loops, assumes 1 normal per real vertex
        mesh_instance.calc_normals_split()
        normals = [list()] * len(mesh_instance.vertices)
        for loop in mesh_instance.loops:
            normals[loop.vertex_index] = loop.normal
        
        for i, element in enumerate(g_element_data):
            element.normal = (
                normals[i][0],
                normals[i][2],
                -normals[i][1]
            )

        # Set Faces
        faces = [f.vertices for f in mesh_instance.polygons]
        geom_data.faces = faces

        # Prefill the UVMap list
        uv_count = len(mesh_instance.uv_layers)
        uvs = []
        for _ in mesh_instance.vertices:
            l = [None]*uv_count
            uvs.append(l)

        # Get UV Data per layer
        for n, uv_layer in enumerate(mesh_instance.uv_layers):
            mesh_instance.uv_layers.active = uv_layer
            for i, polygon in enumerate(mesh_instance.polygons):
                for j, loopindex in enumerate(polygon.loop_indices):
                    meshuvloop = mesh_instance.uv_layers.active.data[loopindex]
                    uv = ( meshuvloop.uv[0], -meshuvloop.uv[1] + 1 )
                    vertidx = geom_data.faces[i][j]
                    uvs[vertidx][n] = uv
        
        # Set UV Data per layer in GEOM vertex array
        for i, uv in enumerate(uvs):
            g_element_data[i].uv = uv
        
        # Set Vertex Colors (Tagvalue)
        vcol_layer = me.vertex_colors.get('SIMGEOM_TAGVAL')
        if vcol_layer:
            for poly in me.polygons:
                for vert_index, loop_index in zip(poly.vertices, poly.loop_indices):
                    color = [ int(round(255 * val, 0)) for val in vcol_layer.data[loop_index].color]
                    g_element_data[vert_index].tagvalue = color
        
        # Tangents
        self.calc_tangents(g_element_data, geom_data)
        
        # Set Header Info
        geom_data.internal_chunks = []
        for x in ob.get('rcol_chunks', []):
            geom_data.internal_chunks.append(x.to_dict())
        geom_data.external_resources = []
        for x in ob.get('rcol_external', []):
            geom_data.internal_chunks.append(x.to_dict())
        geom_data.shaderdata = []
        for x in ob.get('shaderdata', []):
            geom_data.shaderdata.append(x.to_dict())
        geom_data.tgi_list = []
        for x in ob.get('tgis', []):
            geom_data.tgi_list.append(x.to_dict())
        geom_data.sort_order = ob.get('sortorder', 0)
        geom_data.merge_group = ob.get('mergegroup', 0)
        geom_data.skin_controller_index = ob.get('skincontroller', 3)
        geom_data.embeddedID = ob.get('embedded_id', "SimSkin")
            
        geom_data.element_data = g_element_data
        GeomWriter.writeGeom(self.filepath, geom_data)

        # Morphs
        if self.do_export_morphs:
            self.export_morphs(ob, mesh_instance, normals, geom_data.faces, geom_data.bones)

        ob.to_mesh_clear()

        return {'FINISHED'}
    

    def calc_tangents(self, element_data, geom_data):
        """Calculate Tangents of the mesh to make normalmaps work"""
        # Calculating Tangents, can be done in blender but would require trial and error to flip axis
        # http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
        tangents = [[] for _ in range(len(element_data))]
        for face in geom_data.faces:
            # Position Shortcuts
            v0 = Vector(element_data[face[0]].position)
            v1 = Vector(element_data[face[1]].position)
            v2 = Vector(element_data[face[2]].position)

            # UV Shortcuts
            uv0 = Vector(element_data[face[0]].uv[0])
            uv1 = Vector(element_data[face[1]].uv[0])
            uv2 = Vector(element_data[face[2]].uv[0])

            # Position Delta
            delta_pos1 = v1 - v0
            delta_pos2 = v2 - v0

            # UV Delta
            delta_uv1 = uv1 - uv0
            delta_uv2 = uv2 - uv0

            # Tangent Calculation
            result = ( delta_uv1.x * delta_uv2.y - delta_uv1.y * delta_uv2.x )
            if result != 0:
                r = 1.0 / result
            else:
                r= 1.0 / 0.001
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
            element_data[i].tangent = average.normalized().to_tuple()
    

    def get_morphs(self, base_obj):
        morphs = list()
        
        for o in bpy.data.objects.values():
            if o.type != 'MESH':
                continue
            if o.get('__GEOM_MORPH__', None) == None:
                continue
            if o.get('morph_link', None) == base_obj:
                morphs.append(o)
        
        return morphs


    def export_morphs(self, original_object, mesh_instance, original_normals, faces, bones):
        """Create geom files for all morphs"""

        vert_count = len(mesh_instance.vertices)

        morphs = self.get_morphs(original_object)
        for morph_obj in morphs:
            morph_mesh = morph_obj.data

            if vert_count != len(morph_mesh.vertices):
                continue
            
            geom_data = Geom()
            element_data = []
            
            # Get per vertex normals from mesh loops, assumes 1 normal per real vertex
            morph_mesh.calc_normals_split()
            morph_normals = [list()] * len(mesh_instance.vertices)
            for loop in mesh_instance.loops:
                morph_normals[loop.vertex_index] = loop.normal

            # Positions
            original_positions = [v.co for v in mesh_instance.vertices]
            morph_positions    = [v.co for v in morph_mesh.vertices]

            final_positions = [[0,0,0]] * vert_count
            final_normals   = [[0,0,0]] * vert_count

            # Get deltas, swap axis and put into element_data
            for i in range(vert_count):
                vertex = Vertex()
                pos_delta = self.delta(morph_positions[i], original_positions[i])
                nor_delta = self.delta(morph_normals[i], original_normals[i])
                vertex.position = (
                    pos_delta[0],
                    pos_delta[2],
                    -pos_delta[1]
                )
                vertex.normal = (
                    nor_delta[0],
                    nor_delta[2],
                    -nor_delta[1]
                )
                element_data.append(vertex)
            
            geom_data.faces = faces

            # Set Vertex IDs
            for key, values in original_object.get('vert_ids').items():
                for v in values:
                    element_data[v].vertex_id = [int(key, 0)]

            geom_data.element_data = element_data

            # Fill the bone array
            geom_data.bones = bones
            
            # Set Header data
            emtpy_tgi = {
                'type': "0x0",
                'group': "0x0",
                'instance': "0x0"
            }

            # Set Header Info
            geom_data.internal_chunks = []
            geom_data.internal_chunks.append(emtpy_tgi)
            geom_data.external_resources = []
            geom_data.shaderdata = []
            geom_data.tgi_list = []
            geom_data.tgi_list.append(emtpy_tgi)
            geom_data.sort_order = original_object.get('sortorder', 0)
            geom_data.merge_group = original_object.get('mergegroup', 0)
            geom_data.skin_controller_index = 0
            geom_data.embeddedID = "0x0"

            morph_name = morph_obj.get('morph_name', morph_obj.name)
            filepath = self.filepath.split(".simgeom")[0] + "_" + morph_name + ".simgeom"
            GeomWriter.writeGeom(filepath, geom_data)
    

    def delta(self, a: tuple, b: tuple):
        """ Calculate the delta between two 3D lists/tuples """
        c = (
            a[0] - b[0],
            a[1] - b[1],
            a[2] - b[2]
        )
        return c
    

    def veclength(self, v: tuple):
        """ Calculate the length of a 3D list/tuple """
        return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
