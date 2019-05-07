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

class Globals:
    # Shader Paramater Datatypes
    FLOAT = 1
    INTEGER = 2
    TEXTURE = 4

    HASHMAP: dict
    CAS_INDICES: dict
    SEAM_FIX: dict

    @staticmethod
    def init(rootdir: str):
        datadir = rootdir + "/data/json/"
        with open(datadir + "hashmap.json", "r") as data:
            Globals.HASHMAP = json.loads(data.read())
        with open(datadir + "variables.json", "r") as data:
            Globals.CAS_INDICES = json.loads(data.read())['cas_indices']
        with open(datadir + "seamfix.json", "r") as data:
            listvalues = json.loads(data.read())
            seamfix = {}
            for item in listvalues:
                seamfix[ tuple(item[0]) ] = {
                    'normal': tuple( item[1] ),
                    'tangent': tuple( item[2] ),
                    'assign': tuple( item[3] ),
                    'weight': tuple( item[4] )
                }
            Globals.SEAM_FIX = seamfix
    
    @staticmethod
    def get_bone_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['bones'][hex(fnv32hash)]
    
    @staticmethod
    def get_shader_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['shader'][hex(fnv32hash)]
    
    @staticmethod
    def padded_hex(value: int, numbytes: int) -> str:
        return "0x{0:0{1}X}".format(value, numbytes * 2)