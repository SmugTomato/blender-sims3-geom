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

import bpy
import bmesh

from mathutils              import Vector, Quaternion
from bpy_extras.io_utils    import ExportHelper
from bpy.props              import StringProperty, BoolProperty, EnumProperty
from bpy.types              import Operator

from .models.geom           import Geom
from .models.vertex         import Vertex
from .geomwriter            import GeomWriter
from .util.fnv              import fnv32
from .util.globals          import Globals


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

    def execute(self, context):
        geomdata = Geom()
        obj = context.active_object
        mesh = obj.data

        # Create the GEOM vertex array and fill it with the readily available values
        g_element_data: List[Vertex] = []
        for v in mesh.vertices:
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
        for key, values in obj.get('vert_ids').items():
            for v in values:
                g_element_data[v].vertex_id = [int(key, 0)]
        
        # Normals
        # TODO: Reimplement with data transfer modifier
        depsgraph = context.depsgraph
        normals_mesh = obj.to_mesh(depsgraph, apply_modifiers=False)
        normals_obj = bpy.data.objects.new('normals_obj', normals_mesh)
        bm = bmesh.new()
        bm.from_mesh(normals_mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bm.to_mesh(normals_mesh)
        bm.free()

        mod = obj.modifiers.new("DATA_TRANSFER", type='DATA_TRANSFER')
        mod.object = normals_obj
        mod.use_loop_data = True
        mod.data_types_loops = {'CUSTOM_NORMAL'}
        mod.loop_mapping = 'TOPOLOGY'
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
        mesh.calc_normals_split()

        normals = {}
        for loop in mesh.loops:
            index = loop.vertex_index
            normal = loop.normal.to_tuple(5)
            if not index in normals.keys():
                normals[index] = [normal]
                continue
            normals[index].append(normal)

        # Set normals in GEOM vertex array
        for k, v in normals.items():
            print(v)
            g_element_data[k].normal = (
                v[0][0], 
                v[0][2], 
                -v[0][1]
            )  
        
        # Set Faces
        geomdata.faces = []
        for face in mesh.polygons:
            geomdata.faces.append( (face.vertices[0], face.vertices[1], face.vertices[2]) )
        
        # Prefill the UVMap list
        uv_count = len(mesh.uv_layers)
        uvs = []

        # Get UV Data per layer
        for n, uv_layer in enumerate(mesh.uv_layers):
            mesh.uv_layers.active = uv_layer
            uv_list = {}
            for i, polygon in enumerate(mesh.polygons):
                for j, loopindex in enumerate(polygon.loop_indices):
                    meshuvloop = mesh.uv_layers.active.data[loopindex]
                    uv = ( meshuvloop.uv[0], -meshuvloop.uv[1] + 1 )
                    vertidx = geomdata.faces[i][j]
                    uv_list[vertidx] = uv
            uvs.append(uv_list)
        
        for uv_set in uvs:
            for k, v in uv_set.items():
                if not g_element_data[k].uv:
                    g_element_data[k].uv = []
                g_element_data[k].uv.append(v)
        
        # Calculating Tangents
        # http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
        tangents = [[] for _ in range(len(g_element_data))]
        for face in geomdata.faces:
            # Position Shortcuts
            v0 = Vector(g_element_data[face[0]].position)
            v1 = Vector(g_element_data[face[1]].position)
            v2 = Vector(g_element_data[face[2]].position)

            # UV Shortcuts
            # Always Uses primary UV layer
            uv0 = Vector(g_element_data[face[0]].uv[0])
            uv1 = Vector(g_element_data[face[1]].uv[0])
            uv2 = Vector(g_element_data[face[2]].uv[0])

            # Position Delta
            delta_pos1 = v1 - v0
            delta_pos2 = v2 - v0

            # UV Delta
            delta_uv1 = uv1 - uv0
            delta_uv2 = uv2 - uv0

            # Tangent Calculation
            r = 1.0
            g = delta_uv1.x * delta_uv2.y - delta_uv1.y * delta_uv2.x
            if g == 0:
                g += 0.0000005
            r = 1.0 / g
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
            g_element_data[i].tangent = average.normalized().to_tuple(5)

        # Fill the bone array
        geomdata.bones = []
        for group in obj.vertex_groups:
            geomdata.bones.append(group.name)
        
        # Apply Seam fix
        # Fixes normals and bone assignments on seams
        for v in g_element_data:
            if not v.position in Globals.SEAM_FIX.keys():
                continue
            v.normal = Globals.SEAM_FIX[v.position]['normal']
            assign = Globals.SEAM_FIX[v.position]['assign']
            weight = Globals.SEAM_FIX[v.position]['weight']
            v.assignment = [0,0,0,0]
            v.weights = [0,0,0,0]
            for i in range(4):
                # No reason to clutter the bonehash array with unused bones
                if weight[i] == 0:
                    continue
                # If the bone is actually used, add it to the bonehash array
                if not assign[i] in geomdata.bones:
                    geomdata.bones.append(assign[i])
                # Set assignment and weight of the bone
                v.assignment[i] = geomdata.bones.index(assign[i])
                v.weights[i] = weight[i]
        
        # Set Header Info
        geomdata.internal_chunks = []
        for x in obj['rcol_chunks']:
            geomdata.internal_chunks.append(x.to_dict())
        geomdata.external_resources = []
        for x in obj['rcol_external']:
            geomdata.internal_chunks.append(x.to_dict())
        geomdata.shaderdata = []
        for x in obj['shaderdata']:
            geomdata.shaderdata.append(x.to_dict())
        geomdata.tgi_list = []
        for x in obj['tgis']:
            geomdata.tgi_list.append(x.to_dict())
        geomdata.sort_order = obj['sortorder']
        geomdata.merge_group = obj['mergegroup']
        geomdata.skin_controller_index = obj['skincontroller']
        geomdata.embeddedID = obj['embedded_id']
            
        geomdata.element_data = g_element_data
        GeomWriter.writeGeom(self.filepath, geomdata)

        return {'FINISHED'}
    
    def export_morph(self, context, obj):
        depsgraph = context.depsgraph
        print(depsgraph)
        for ob_inst in depsgraph.object_instances:
            ob = ob_inst.object.original
            ob.name = "aabb"
            print(ob, obj)