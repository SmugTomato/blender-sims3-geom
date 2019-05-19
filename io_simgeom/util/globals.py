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
    CAS_INDICES = {
        "body":      5000,
        "top":       5000,
        "bottom":    15000,
        "hair":      20000,
        "shoes":     30000,
        "accessory": 40000
    }

    HASHMAP: dict
    SEAM_FIX: dict = {}

    ROOTDIR: str

    @staticmethod
    def init(rootdir: str):
        Globals.ROOTDIR = rootdir
        with open(f'{rootdir}/config.json', 'r') as config_file:
            config = json.load(config_file)
            datadir = f'{rootdir}/data/json/'

            fnv_hashmap = config['paths']['fnv_hashmaps']['hashmap']
            with open(f'{datadir}{fnv_hashmap}', 'r') as data:
                Globals.HASHMAP = json.loads(data.read())
            for k, v in config['paths']['seamfix'].items():
                with open(f'{datadir}{v}', "r") as data:
                    Globals.SEAM_FIX[k] = json.loads(data.read())
    
    @staticmethod
    def get_bone_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['bones'][hex(fnv32hash)]
    
    @staticmethod
    def get_shader_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['shader'][hex(fnv32hash)]
    
    @staticmethod
    def padded_hex(value: int, numbytes: int) -> str:
        return "0x{0:0{1}X}".format(value, numbytes * 2)