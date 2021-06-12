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
import os

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

    OUTDATED: int
    ROOTDIR: str

    @staticmethod
    def init(rootdir: str, outdated: int):
        Globals.OUTDATED = outdated
        Globals.ROOTDIR = rootdir
        datadir = f'{rootdir}/data/json'
        with open(f'{datadir}/fnv_hashmap.json', 'r') as data:
            Globals.HASHMAP = json.loads(data.read())
        for i in range(3):
            with open(f'{datadir}/seams_LOD{i+1}.json', "r") as data:
                Globals.SEAM_FIX[f'LOD{i+1}'] = json.loads(data.read())
    
    @staticmethod
    def get_bone_name(fnv32hash: int) -> str:
        hex_fnv = hex(fnv32hash)
        return Globals.HASHMAP['bones'].get(hex_fnv, hex_fnv)
    
    @staticmethod
    def get_shader_name(fnv32hash: int) -> str:
        hex_fnv = hex(fnv32hash)
        return Globals.HASHMAP['shader'].get(hex_fnv, hex_fnv)
    
    @staticmethod
    def padded_hex(value: int, numbytes: int) -> str:
        return "0x{0:0{1}X}".format(value, numbytes * 2)
    
    @staticmethod
    def rebuild_fnv_database(bones: dict):
        path = f'{Globals.ROOTDIR}/data/json/fnv_hashmap.json'
        data_dict: dict
        if os.path.exists(f'{path}.backup'):
            os.remove(f'{path}.backup')
        os.rename(path, f'{path}.backup')
        with open(f'{path}.backup', 'r') as data:
            data_dict = json.load(data)
            for k, v in bones.items():
                data_dict['bones'][k] = v
        with open(f'{path}', 'w') as data:
            data.write( json.dumps(data_dict, indent=4) )
            Globals.HASHMAP = data_dict
            os.remove(f'{path}.backup')
