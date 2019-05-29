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


class SIMGEOM_OT_export_test(Operator, ExportHelper):
    """Sims 3 TEST Exporter"""
    bl_idname = "simgeom.export_test"
    bl_label = "Export TEST"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = ".TEST"

    filter_glob: StringProperty(
        default="*.TEST",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    apply_modifiers: bpy.props.BoolProperty(name="Apply Modifiers")

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'INFO'}, "No active mesh object to convert to mesh")
            return {'CANCELLED'}
        
        # Normals Mesh
        mesh_instance = obj.to_mesh()

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
        tricorner_normals = tuple(tricorner_normals)
        
        # Export Mesh
        mesh_instance = obj.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(mesh_instance)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh_instance)
        bm.free()

        # Merge sets
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
        
        print(merge_sets.values())

        for vset in merge_sets.values():
            total = Vector((0,0,0))
            for ind in vset:
                total += mesh_instance.vertices[ind].normal
            normal = total / len(vset)
            for ind in vset:
                obj.data.vertices[ind].normal = normal

        obj.to_mesh_clear()

        return {'FINISHED'}