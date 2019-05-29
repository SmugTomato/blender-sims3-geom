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

    def execute(self, context):
        geom_data = Geom()
        ob = context.active_object
        me = ob.data

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
                assignment[j] = g.group
            vtx.weights = weights
            vtx.assignment = assignment

            g_element_data.append(vtx)
        
        # Set Vertex IDs
        for key, values in ob.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Create a temporary mesh to reference normals from
        mesh_instance = ob.to_mesh()
        tricorner_normals = self.get_tricorner_normals(mesh_instance)

        # Reassign temporary mesh to export mesh
        mesh_instance = ob.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh_instance)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh_instance)
        bm.free()
 
        # Normals
        normals_to_merge = self.get_merge_normals(mesh_instance, tricorner_normals)
        vertex_positions = [v.co for v in mesh_instance.vertices]
        faces = [f.vertices for f in mesh_instance.polygons]
        normals = self.calc_normals(vertex_positions, faces, merge_sets=normals_to_merge)
        for i, element in enumerate(g_element_data):
            element.normal = (
                normals[i][0],
                normals[i][2],
                -normals[i][1]
            )

        # Set Faces
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

        # Fill the bone array
        geom_data.bones = []
        for group in ob.vertex_groups:
            geom_data.bones.append(group.name)
        
        # Apply Seam fix
        # Fixes normals and bone assignments on seams
        count = 0
        if self.seamfix_type != 'None':
            for element in g_element_data:
                for thing in Globals.SEAM_FIX[self.seamfix_lod][self.seamfix_type]['base']:
                    a = self.veclength(self.delta(element.position, thing['position']))
                    if a > 0.0001:
                        continue
                    count += 1
                    element.normal = thing['normal']
                    assign = thing['assign']
                    weight = thing['weight']
                    element.assignment = [0,0,0,0]
                    element.weights = [0,0,0,0]
                    for i in range(4):
                        # No reason to clutter the bonehash array with unused bones
                        if weight[i] == 0:
                            continue
                        # If the bone is actually used, add it to the bonehash array
                        if not assign[i] in geom_data.bones:
                            geom_data.bones.append(assign[i])
                        # Set assignment and weight of the bone
                        element.assignment[i] = geom_data.bones.index(assign[i])
                        element.weights[i] = weight[i]
                    break
            print("base", count)

        
        # Set Header Info
        geom_data.internal_chunks = []
        for x in ob['rcol_chunks']:
            geom_data.internal_chunks.append(x.to_dict())
        geom_data.external_resources = []
        for x in ob['rcol_external']:
            geom_data.internal_chunks.append(x.to_dict())
        geom_data.shaderdata = []
        for x in ob['shaderdata']:
            geom_data.shaderdata.append(x.to_dict())
        geom_data.tgi_list = []
        for x in ob['tgis']:
            geom_data.tgi_list.append(x.to_dict())
        geom_data.sort_order = ob['sortorder']
        geom_data.merge_group = ob['mergegroup']
        geom_data.skin_controller_index = ob['skincontroller']
        geom_data.embeddedID = ob['embedded_id']
            
        geom_data.element_data = g_element_data
        GeomWriter.writeGeom(self.filepath, geom_data)

        # Morphs
        if me.shape_keys and len(me.shape_keys.key_blocks) > 1:
            self.export_morphs(ob, mesh_instance, normals_to_merge, normals, geom_data.bones)

        ob.to_mesh_clear()

        return {'FINISHED'}
    

    def get_tricorner_normals(self, mesh_instance) -> tuple:
        """ Collect normals info from face corners of a mesh with doubles removed """
        bm = bmesh.new()
        bm.from_mesh(mesh_instance)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        edges = []
        for edge in bm.edges:
            if not edge.smooth:
                edges.append(edge)
        bmesh.ops.split_edges(bm, edges=edges)
        bm.to_mesh(mesh_instance)
        bm.free()

        tricorner_normals = []
        for tri in mesh_instance.polygons:
            trian = []
            for ind in tri.vertices:
                trian.append( mesh_instance.vertices[ind].normal )
            tricorner_normals.append(trian)

        return tuple(tricorner_normals)


    def get_merge_normals(self, mesh_instance, tricorner_normals) -> tuple:
        """ Look up normals to merge from a mesh with doubles removed and edges split """
        # Vertex Data from copied mesh mapped to original mesh
        vertices = {}
        for face_a, face_b in zip(mesh_instance.polygons, tricorner_normals):
            for ind_a, normal in zip(face_a.vertices, face_b):
                co = mesh_instance.vertices[ind_a].co.to_tuple()
                if not co in vertices.keys():
                    vertices[co] = {ind_a: normal.to_tuple()}
                else:
                    vertices[co][ind_a] = normal.to_tuple()
        
        merge_sets = {}
        for v in vertices.values():
            if len(v) < 2:
                continue
            for index, normal in v.items():
                if not normal in merge_sets.keys():
                    merge_sets[normal] = [index]
                else:
                    merge_sets[normal].append(index)

        return tuple(merge_sets.values())


    def calc_normals(self, vertex_positions, faces, merge_sets: List[List[int]] = None):
        """
        Although calculating normals can be done in blender, it ended up being easier doing it manually
        due to shape keys not agreeing with bmesh.ops.remove_doubles()
        """
        # Manually calculate face normals
        verts = {}
        normals = {}
        for face in faces:
            u = vertex_positions[face[1]] - vertex_positions[face[0]]
            v = vertex_positions[face[2]] - vertex_positions[face[0]]
            f_normal = u.cross(v)   
            for index in face:
                if not index in verts.keys():
                    verts[index] = [f_normal]
                else:
                    verts[index].append(f_normal)

        # Average face normals to vertex normals
        for k, v in verts.items():
            if len(v) == 1:
                normals[k] = v[0]
                continue
            total = Vector((0,0,0))
            for n in v:
                total += n
            normals[k] = total.normalized()

        # Merge Normals
        if merge_sets:
            for set in merge_sets:
                total = Vector((0,0,0))
                for index in set:
                    total += normals[index]
                normal = total.normalized()
                for index in set:
                    normals[index] = normal

        return normals
    

    def calc_tangents(self, element_data, geom_data):
        """Calculate Tangents of the mesh to make normalmaps work"""
        # Calculating Tangents
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
            element_data[i].tangent = average.normalized().to_tuple()
    

    # TODO: Fix mangled morphs
    def export_morphs(self, original_object, mesh_instance, normals_to_merge, original_normals, bones):
        """Create geom files for all morphs"""
        original_mesh = original_object.data
        bm = bmesh.new()
        bm.from_mesh(original_mesh)
        bm.verts.ensure_lookup_table()

        for keyname in bm.verts.layers.shape.keys()[1:]:
            val = bm.verts.layers.shape.get(keyname)
            geom_data = Geom()
            element_data: List[Vertex] = []
            vertex_positions = []
            for i in range(len(bm.verts)):
                v = bm.verts[i]
                vertex_positions.append( v[val] )
            faces = [f.vertices for f in mesh_instance.polygons]
            normals = self.calc_normals(vertex_positions, faces, normals_to_merge)

            # Set Position and Normal deltas
            positions_absolute = []
            for i in range(len(vertex_positions)):
                vertex = Vertex()
                pos_delta = vertex_positions[i] - original_mesh.vertices[i].co
                nor_delta = normals[i] - original_normals[i]
                vertex.position = (
                    pos_delta.x,
                    pos_delta.z,
                    -pos_delta.y
                )
                vertex.normal = (
                    nor_delta.x,
                    nor_delta.z,
                    -nor_delta.y
                )
                element_data.append(vertex)
                positions_absolute.append( (vertex_positions[i].x, vertex_positions[i].z, -vertex_positions[i].y) )
            
            geom_data.faces = faces

            # Set Vertex IDs
            for key, values in original_object.get('vert_ids').items():
                for v in values:
                    element_data[v].vertex_id = [int(key, 0)]

            # Fill the bone array
            geom_data.bones = bones

            # Apply Seam fix
            count = 0
            if self.seamfix_type != 'None' and keyname in Globals.SEAM_FIX[self.seamfix_lod][self.seamfix_type]:
                for i in range(len(element_data)):
                    element = element_data[i]
                    for thing in Globals.SEAM_FIX[self.seamfix_lod][self.seamfix_type][keyname]:
                        a = self.veclength(self.delta(positions_absolute[i], thing['position']))
                        if a > 0.0001:
                            continue
                        count += 1
                        element_data[i].normal = thing['normal']
                        break
                print(keyname, count)
            
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
            geom_data.sort_order = original_object['sortorder']
            geom_data.merge_group = original_object['mergegroup']
            geom_data.skin_controller_index = 0
            geom_data.embeddedID = "0x0"

            geom_data.element_data = element_data

            filepath = self.filepath.split(".simgeom")[0] + "_" + keyname + ".simgeom"
            GeomWriter.writeGeom(filepath, geom_data)
        
        bm.free()
    

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