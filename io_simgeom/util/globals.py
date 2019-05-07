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
                    'tangent': tuple( item[2] )
                }
            Globals.SEAM_FIX = seamfix
    
    @staticmethod
    def get_bone_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['bones'][hex(fnv32hash)]
    
    @staticmethod
    def get_shader_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['shader'][hex(fnv32hash)]