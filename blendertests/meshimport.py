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

# filename = "S:/Projects/Python/Sims3Geom/blendertesting.py"
# exec(compile(open(filename).read(), filename, 'exec'))

import json
import bpy

f = open("S:/Projects/Python/Sims3Geom/io_simgeom/data/json/dump.json", "r")
meshdata = json.loads(f.read())

# vertices = [
#     [0.5, 0.5, -0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5]
# ]

# faces = [
#     [0, 1, 3], [0, 3, 2]
# ]

vertexdata = meshdata['GEOM_DATA']['vertexdata']
vertices = []
for v in vertexdata:
    vert = v['position']
    vertices.append( (vert[0], -vert[2], vert[1]) )
faces = meshdata['GEOM_DATA']['faces']

scene = bpy.context.scene

mesh = bpy.data.meshes.new("thingy")
object = bpy.data.objects.new("object", mesh)

mesh.from_pydata(vertices, [], faces)

scene.collection.objects.link(object)
object.select_set(True)
bpy.context.view_layer.objects.active = object