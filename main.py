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

meshdata = GeomLoader.readGeom("mesh/afBodyDressSunbelt/afBodyDressSunbelt_lod1_0x00000000D9DBB6AB.simgeom")
GeomWriter.writeGeom("mesh/afBodyDressSunbelt/out.simgeom", meshdata)

# with open("io_simgeom/data/json/dump.json", "w+") as f:
#     f.write(
#         json.dumps(meshdata.dataDump(), indent=4)
#     )

# rigdata = RigLoader.loadRig("mesh/auRig.grannyrig")

# import io_simgeom.util.hashlistgen as hashgen


# hashgen.write_hashmap("hashmap")