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

import json

from io_simgeom.geomloader import GeomLoader
from io_simgeom.geomwriter import GeomWriter
from io_simgeom.rigloader import RigLoader

top_data = GeomLoader.readGeom("mesh/seamfix/afTopNude_lod1_0x00000000B9A67B74.simgeom")
bot_data = GeomLoader.readGeom("mesh/seamfix/afBottomNude_lod1_0x000000001F686A3C.simgeom")

af_verts = None
with open("mesh/seamfix/afVerts.json", "r") as f:
    af_verts = json.loads(f.read())
af_verts2 = []
for v in af_verts:
    af_verts2.append([v[0], v[2], -v[1]])

vertices = {}
for v in top_data.element_data:
    if v.position in af_verts2:
        vertices[tuple(v.position)] = {
            'normal': tuple(v.normal),
            'tangent': tuple(v.tangent)
        }
for v in bot_data.element_data:
    if v.position in af_verts2:
        vertices[tuple(v.position)] = {
            'normal': tuple(v.normal),
            'tangent': tuple(v.tangent)
        }

vertices2 = []
for k, v in vertices.items():
    vertices2.append({
        'position': k,
        'normal': v['normal'],
        'tangent': v['tangent']
    })

with open("mesh/seamfix/afFix.json", "w+") as f:
    f.write(
        json.dumps(vertices2)
    )

# Blender stuff
# import os
# import json

# import bpy

# mesh = bpy.context.object.data

# vertices = [[v.co.x, v.co.z, -v.co.y] for v in mesh.vertices]

# with open("S:\\Projects\\Python\\Sims3Geom\\mesh\\seamfix\\afVerts.json", "w+") as f:
#     f.write(
#         json.dumps(vertices, indent = 4)
#     )